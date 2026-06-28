"""Video composition planning module using LLM.

Two separate planners for audio-first, video-second pipeline:

  AudioPlanner  — Generates a natural, fluent narration script + voice direction
                   from the douyin source material. Purely focused on "how it sounds."

  VideoPlanner  — Generates a visual composition plan (scenes, animations, data cards,
                   comparisons, keyword bursts) based on the source material AND the
                   measured audio timestamps. Purely focused on "how it looks."

The two planners are intentionally independent: the audio script is the ground truth
for timing, and the video plan is designed around those timestamps. The result is a
video where the visuals complement the narration rather than duplicating it.
"""

import json
import logging
import re as _re
from typing import Optional
from openai import OpenAI

from modules.config_model import AppConfig

logger = logging.getLogger(__name__)


def _create_planner_client(config: AppConfig) -> tuple[OpenAI | None, str]:
    """Create an OpenAI client and model for the planner based on the configured text provider.

    Shared by AudioPlanner and VideoPlanner to avoid duplicate client creation logic.
    Returns (client, model_name).
    """
    text_provider = config.generation.text_provider
    if text_provider == "ark":
        api_key = config.ark.api_key
        base_url = config.ark.base_url
        model = config.ark.effective_planner_model
    else:
        api_key = config.mimo.api_key
        base_url = config.mimo.base_url
        model = config.mimo.effective_planner_model
    return OpenAI(api_key=api_key, base_url=base_url) if api_key else None, model


# ═══════════════════════════════════════════════════════════════
#  AudioPlanner — generates narration + voice direction
# ═══════════════════════════════════════════════════════════════

AUDIO_PLANNER_SYSTEM_PROMPT = """你是一个专业的短视频配音脚本专家。根据参考素材，创作一段自然流畅的口播配音脚本。

## 角色
你只负责**配音脚本**——写出最适合朗读的文本。不需要关心画面、动画或视觉效果。

## 配音创作原则
1. **自然口语化**：像真人说话，不要书面语、不要朗诵腔
2. **黄金 3 秒**：开场第一句要抓耳、有冲击力
3. **结尾有号召**：最后引导关注/点赞/评论，语气真诚不僵硬
4. **控制时长**：根据内容需要自由决定总时长，该长则长该短则短

## 输出格式
输出纯 JSON（不要 markdown 代码块）：

{
  "narration": "完整的口播文本。用自然流畅的中文写成，段与段之间自然过渡。",
  "segments": [
    {"text": "GPT-5 来了！", "tone": "激昂", "pause_after": 0.2},
    {"text": "推理能力提升了整整十倍", "tone": "沉稳有力", "pause_after": 0.3},
    {"text": "速度更快，成本还更低", "tone": "轻快", "pause_after": 0.2},
    {"text": "关注我，第一时间了解 AI 动态", "tone": "亲切", "pause_after": 0.0}
  ],
  "voice_direction": "用激动、快节奏的语气朗读，像科技新闻主播"
}

## 字段说明
- **narration**：完整口播文本，所有 segment 的 text 拼起来
- **segments**：分段文本，每段一句话。tone 描述语气（激昂/沉稳有力/轻快/亲切/震撼/温暖）
  pause_after 是该段说完后的停顿时长（秒），关键信息后稍长，过渡句后稍短
- **voice_direction**：15-25 字的 TTS 朗读指令，给语音合成系统用。格式如：
  "用激动、快节奏的语气朗读，像科技新闻主播"
  "用沉稳、专业的语气朗读，像纪录片旁白"
  "用温暖、亲切的语气朗读，像朋友聊天"

## tone 选择指南
- 开场 hook → "激昂"、"震撼"
- 数据/事实 → "沉稳有力"、"专业"
- 转折/强调 → "轻快"、"犀利"
- 结尾号召 → "亲切"、"温暖"
- 对比/冲突 → "紧张"、"严肃"

## 示例
参考素材："GPT-5 重磅发布。OpenAI 最新模型推理能力提升 10 倍，速度更快成本更低。这是改变行业格局的产品。"

{
  "narration": "GPT-5 来了！OpenAI 刚刚发布了最新模型。推理能力提升了整整十倍，而且速度更快，成本更低。这将彻底改变行业格局。关注我，第一时间了解 AI 前沿动态！",
  "segments": [
    {"text": "GPT-5 来了！", "tone": "激昂", "pause_after": 1.0},
    {"text": "OpenAI 刚刚发布了最新模型", "tone": "沉稳有力", "pause_after": 0.6},
    {"text": "推理能力提升了整整十倍", "tone": "震撼", "pause_after": 0.8},
    {"text": "而且速度更快，成本更低", "tone": "轻快", "pause_after": 0.6},
    {"text": "这将彻底改变行业格局", "tone": "犀利", "pause_after": 0.8},
    {"text": "关注我，第一时间了解 AI 前沿动态！", "tone": "亲切", "pause_after": 0.5}
  ],
  "voice_direction": "用激动、快节奏的语气朗读，像科技新闻主播"
}
"""

AUDIO_PLANNER_USER_PROMPT_TEMPLATE = """根据以下参考素材，创作一段自然流畅的口播配音脚本。

== 参考素材 ==
原标题：{title}
原始文案：{script}
标签/关键词：{tags}

== 要求 ==
1. 写出适合朗读的自然口语，不要照搬原文
2. 开头第一句要抓耳朵（黄金3秒）
3. 结尾引导关注/评论
4. voice_direction 要具体

请输出 JSON。"""


class AudioPlanner:
    """Generates audio narration scripts from douyin source material using LLM."""

    def __init__(self, config: AppConfig):
        self.client, self.model = _create_planner_client(config)

    def plan(
        self,
        script: str,
        title: str = "",
        tags: Optional[list[str]] = None,
    ) -> Optional[dict]:
        """Generate an audio narration plan from a douyin script.

        Returns:
            dict with keys: narration, segments, voice_direction — or None on failure.
        """
        if not self.client or not self.client.api_key:
            logger.warning("LLM API key not configured, using fallback audio plan")
            return self._fallback_audio_plan(script, title)

        try:
            format_kwargs = dict(
                title=title or "无标题",
                script=script[:800],
                tags=", ".join(tags[:5]) if tags else "无",
            )
            user_prompt = AUDIO_PLANNER_USER_PROMPT_TEMPLATE.format(**format_kwargs)

            logger.info("Generating audio narration plan via LLM...")
            response = self.client.chat.completions.create(
                model=self.model,
                max_tokens=2048,
                temperature=0.7,
                messages=[
                    {"role": "system", "content": AUDIO_PLANNER_SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
            )

            text = response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"Audio planner LLM call failed: {e}")
            return self._fallback_audio_plan(script, title)

        text_raw = text

        try:
            text = _extract_json(text)
            text = _fix_json(text)
            if not text.strip():
                logger.warning(f"Empty JSON from audio planner: {text_raw[:200]}")
                return self._fallback_audio_plan(script, title)

            plan = json.loads(text)
            self._validate_audio_plan(plan)
            logger.info(
                f"Audio plan generated: {len(plan.get('segments', []))} segments, "
                f"voice_direction={plan.get('voice_direction', 'N/A')[:30]}"
            )
            return plan

        except json.JSONDecodeError as e:
            logger.warning(f"Audio planner returned invalid JSON: {e} | {text_raw[:200]}")
            return self._fallback_audio_plan(script, title)
        except Exception as e:
            logger.warning(f"Audio planning failed: {e}")
            return self._fallback_audio_plan(script, title)

    def _validate_audio_plan(self, plan: dict) -> None:
        """Validate and fix common issues in audio plan."""
        if "narration" not in plan or not plan.get("narration"):
            # Build narration from segments
            segs = plan.get("segments", [])
            if segs:
                plan["narration"] = "".join(s.get("text", "") for s in segs)
            else:
                plan["narration"] = "欢迎关注，获取更多 AI 资讯。"
        if "segments" not in plan or not plan["segments"]:
            plan["segments"] = [{"text": plan["narration"], "tone": "沉稳", "pause_after": 0.0}]
        if "voice_direction" not in plan or not plan.get("voice_direction"):
            plan["voice_direction"] = "用沉稳、专业的语气朗读"

    def _fallback_audio_plan(self, script: str, title: str) -> dict:
        """Generate a simple audio plan when LLM is unavailable."""
        sentences = _re.split(r"[。！？!?]", script)
        sentences = [s.strip() for s in sentences if s.strip()]

        if not sentences:
            sentences = [title or "AI 资讯"]

        segments = []
        tones = ["激昂", "沉稳有力", "轻快", "亲切"]
        for i, s in enumerate(sentences[:8]):
            segments.append({
                "text": s + "。" if not s.endswith(("。", "！", "？", "!", "?")) else s,
                "tone": tones[min(i, len(tones) - 1)],
                "pause_after": 0.2 if i < len(sentences[:8]) - 1 else 0.0,
            })

        narration = "".join(seg["text"] for seg in segments)
        logger.info(f"Using fallback audio plan: {len(segments)} segments")
        return {
            "narration": narration,
            "segments": segments,
            "voice_direction": "用沉稳、专业的语气朗读",
        }


# ═══════════════════════════════════════════════════════════════
#  VideoPlanner — generates visual composition plan
#  The system prompt is itself generated by LLM per-content.
# ═══════════════════════════════════════════════════════════════

# Seed knowledge — fed to the prompt-generator LLM as domain reference.
# The actual system prompt used for plan generation is custom-written
# by an LLM for each piece of content.
VIDEO_PLANNER_SEED_PROMPT = """你是一个专业的短视频视觉导演。根据素材和音频时间戳，设计引人入胜的视频画面编排。

## 核心原则（必须遵守）

### 原则一：画面 ≠ 口播的复读机（最重要）

**画面文字必须和该时段的口播内容不同。** 这是最关键的规则。

❌ 错误示范：口播说"推理能力提升了整整十倍"，画面也显示"推理能力提升了整整十倍"
✅ 正确示范：口播说"推理能力提升了整整十倍"，画面显示 "10x ↑" 或一个增长图表

**互补规则：**
- 口播说完整句子 → 画面只给**关键词、数字、对比符号**
- 口播讲道理/观点 → 画面给**数据、图表、案例**
- 口播叙述过程 → 画面给**结果和结论**
- 口播提到人名/产品 → 画面给**logo、截图、关系图**
- 口播说"第一点…" → 画面给**编号 + 核心词**（不要重复整句）

### 原则二：信息密度 — 每个场景必须有「干货」

每个场景的画面必须包含**具体的、可量化的信息**，不能只有空洞的标题。

❌ 低密度：场景只有标题"效率提升"和一行副标题
✅ 高密度：场景包含"效率提升 300%"、对比数据、关键指标

**信息密度检查清单（每个场景至少满足 2 项）：**
1. 有具体数字（百分比、倍数、金额、时间）
2. 有对比（前后对比、AB 对比、多方案对比）
3. 有列表/要点（3-5 个关键点）
4. 有状态/进度（完成度、加载状态、优先级）
5. 有引用/金句（来源标注）

### 原则三：布局选择 — 看内容，不看偏好

根据**当前场景的内容类型**选择布局，不要重复使用同一个布局超过 3 次。

## 布局选择决策树

遇到每个场景时，按以下顺序判断：

```
场景内容是什么？
├─ 有数据对比/倍增效果？
│  └─→ data_compare（水平进度条 + 乘法/加法）
├─ 是 AI 工具的实际操作/终端回复？
│  └─→ terminal_mockup（模拟终端界面）
├─ 有 3 个并列的步骤/方案/类别？
│  ├─ 需要编号流程？ → connected_cards
│  └─ 需要网格展示？ → card_grid
├─ 有系统架构/流程关系？
│  ├─ 节点+连线？ → architecture_flow
│  └─ 输入→处理→输出？ → flow_diagram
├─ 有多个能力/要素叠加？
│  ├─ 需要逐个高亮？ → stack_highlight
│  └─ 需要发散聚合？ → fan_out
├─ 有文档/代码/手册？
│  └─→ doc_tree
├─ 是封面/章节标题？
│  └─→ title_card
└─ 以上都不匹配？
   └─→ block_tree（自由组合 block 元素）
```

## 可用布局速查

### v3 布局（优先使用）

**data_compare** — 数据对比条 + 乘法效果
适用：前后对比、能力倍增、效果差异、A/B 对比
字段：`dataCompare.items[]`（label, baseValue, multiplier, resultValue, color）
```json
{"layout": "data_compare", "dataCompare": {"title": "AI 是乘法", "items": [{"label": "会写代码的人", "baseValue": 50, "multiplier": 3, "resultValue": 150, "color": "orange"}], "centerText": "越会写代码，越能借上它的力"}}
```

**terminal_mockup** — 终端模拟
适用：AI 工具演示、代码操作、对话展示
字段：`terminalMockup.lines[]`（text, highlight, isUser）
```json
{"layout": "terminal_mockup", "terminalMockup": {"title": "实际操作", "terminalTitle": "Claude 的回复", "lines": [{"text": "用户提问", "isUser": true}, {"text": "AI 回复内容", "highlight": true}], "calloutText": "关键洞察"}}
```

**tech_multi_panel** — 3 列科技面板
适用：功能全景、系统能力、多维度展示
字段：`techMultiPanel`（leftPanel, centerPanel, rightPanel）

**connected_cards** — 3 卡片 + 连线
适用：流程步骤、方案对比、分类体系
字段：`connectedCards.cards[]`（num, title, items, state）

**architecture_flow** — 架构流程图
适用：系统架构、模块关系、数据流向
字段：`architectureFlow`（nodes[], connections[]）

**stack_highlight** — 左列表 + 右高亮卡
适用：能力叠加、特性逐个讲解
字段：`stackHighlight`（leftItems[], rightCard）

### v2 布局（v3 不匹配时使用）

**card_grid** — 3 栏卡片网格：`cardGrid.cards[]`
**numbered_cards** — 编号卡片：`numberedCards.cards[]`
**split_compare** — 左右对比：`splitCompare`（leftItems, barSegments）
**flow_diagram** — 流程图：`flowDiagram`
**fan_out** — 发散聚合：`fanOut`
**doc_tree** — 文档树：`docTree`
**title_card** — 封面：`titleCard`（title, subtitle）
**block_tree** — 自由组合：`blocks[]`

### 备选：基础 type（仅在以上布局都不匹配时）

title / bullet / section_title / highlight / ending / data_card / quote / comparison / timeline / image_caption

## 主题 theme

优先 `dark_glass`（深色玻璃 + 橙色/青色点缀）。架构类内容可用 `dark_tech_v3`。

## 输出格式

```json
{
  "title": "视频标题",
  "theme": "dark_glass",
  "scenes": [
    {
      "layout": "布局名",
      "englishLabel": "右上英文标签",
      "sceneSubtitle": "底部字幕（≤20字）",
      "duration": 秒数,
      "animation": "fade|slideUp|slideRight|scaleIn|typewriter|none",
      "布局字段名": { ... }
    }
  ]
}
```

**必填字段**：`layout`, `duration`, `sceneSubtitle`（每场都填）
**推荐字段**：`englishLabel`, `animation`

## 参考编排

```json
{
  "title": "让 Claude Code 替你干一天的 4 个习惯",
  "theme": "dark_glass",
  "scenes": [
    {"layout": "title_card", "titleCard": {"title": "让 Claude Code 替你干一天", "subtitle": "4 个习惯"}, "duration": 3, "animation": "scaleIn", "sceneSubtitle": "效率翻倍的秘密"},
    {"layout": "data_compare", "dataCompare": {"title": "AI 是乘法，不是加法", "items": [{"label": "会写代码的人", "baseValue": 50, "baseLabel": "底子", "multiplier": 3, "resultValue": 150, "color": "orange"}, {"label": "刚入门的小白", "baseValue": 10, "baseLabel": "底子", "multiplier": 3, "resultValue": 30, "color": "cyan"}], "centerText": "越会写代码，越能借上它的力"}, "duration": 6, "animation": "slideUp", "sceneSubtitle": "AI 放大基础能力"},
    {"layout": "terminal_mockup", "terminalMockup": {"title": "习惯一：让它列待办清单", "terminalTitle": "Claude 的一条回复", "lines": [{"text": "帮我配一下环境变量", "isUser": true}, {"text": "好的，我需要确认几个问题：\n1. 操作系统？\n2. 哪个变量？", "highlight": true}], "calloutText": "你十有八九看漏了"}, "duration": 6, "animation": "fade", "sceneSubtitle": "关键信息容易被忽略"},
    {"layout": "connected_cards", "connectedCards": {"title": "核心就一条", "cards": [{"num": "01", "title": "让它多干活", "items": ["写代码", "跑测试", "改 bug"]}, {"num": "02", "title": "你少干活", "items": ["只做判断", "只做验收"]}, {"num": "03", "title": "省 token", "items": ["精准提问", "减少来回"]}]}, "duration": 5, "animation": "slideUp", "sceneSubtitle": "核心就一条：让它多干活"},
    {"layout": "title_card", "titleCard": {"title": "感谢观看", "subtitle": "关注获取更多技巧"}, "duration": 3, "animation": "fade", "sceneSubtitle": "感谢观看"}
  ]
}
```
"""

VIDEO_PLANNER_USER_PROMPT_TEMPLATE = """根据素材和音频时间戳，设计视频画面的场景编排。

== 素材 ==
原标题：{title}
原始文案：{script}
标签/关键词：{tags}

== 口播配音时长分配 ==
{audio_timeline}

== 关键要求 ==
1. **画面 ≠ 口播**：画面文字必须和口播内容不同。口播说句子，画面只给关键词/数字/符号
2. **每个场景必须有干货**：至少包含具体数字、对比、列表、状态中的 2 项
3. **布局选择**：按决策树选布局。有数据对比 → data_compare，有终端操作 → terminal_mockup，有 3 个并列 → connected_cards/card_grid
4. **每场必填**：sceneSubtitle（≤20字）+ englishLabel + duration
5. **首尾固定**：第一个场景用 title_card 做封面，最后一个用 title_card 做收尾（标题写"感谢观看"或总结语）
6. **时长灵活**：duration 之和不必精确匹配音频，以表达到位为准

请输出 JSON 构图计划。"""

class VideoPlanner:
    """Generates visual composition plans — purely visual, separate from audio.

    Uses a single LLM call with a fixed seed prompt (VIDEO_PLANNER_SEED_PROMPT).
    Audio timestamps are applied after plan generation for precise sync.
    Falls back to a template-based plan when LLM is unavailable.
    """

    def __init__(self, config: AppConfig):
        self.client, self.model = _create_planner_client(config)

    def plan(
        self,
        script: str,
        title: str = "",
        tags: Optional[list[str]] = None,
        audio_timings: Optional[list[dict]] = None,
        total_duration: float | None = None,
    ) -> Optional[dict]:
        """Generate a visual composition plan.

        Uses VIDEO_PLANNER_SEED_PROMPT as the system prompt. On failure,
        retries once with the same seed prompt (to handle transient LLM errors).

        Args:
            script: The douyin source script text.
            title: Content title.
            tags: Optional tags/keywords.
            audio_timings: List of {text, start, end} dicts from measured TTS output.
            total_duration: Fallback total duration (used when no audio_timings).

        Returns:
            Composition plan dict, or None on failure.
        """
        if not self.client or not self.client.api_key:
            logger.warning("LLM API key not configured, skipping video planning")
            return self._fallback_plan(script, title, total_duration)

        audio_timeline = _format_audio_timeline(audio_timings)

        format_kwargs = dict(
            title=title or "无标题",
            script=script[:800],
            tags=", ".join(tags[:5]) if tags else "无",
            audio_timeline=audio_timeline,
        )
        user_prompt = VIDEO_PLANNER_USER_PROMPT_TEMPLATE.format(**format_kwargs)

        # Retry once on failure (transient LLM errors)
        prompts_to_try = [
            ("first attempt", VIDEO_PLANNER_SEED_PROMPT),
            ("retry", VIDEO_PLANNER_SEED_PROMPT),
        ]

        text = ""
        text_raw = ""
        for prompt_label, system_prompt in prompts_to_try:
            try:
                logger.info(f"Generating visual composition plan via LLM ({prompt_label})...")
                response = self.client.chat.completions.create(
                    model=self.model,
                    max_tokens=4096,
                    temperature=0.7,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                )
                text_raw = response.choices[0].message.content.strip()
                text = _extract_json(text_raw)
                text = _fix_json(text)
                if text.strip():
                    break  # Success
                logger.warning(f"Empty JSON from video planner ({prompt_label}). Raw (first 300 chars): {text_raw[:300]}")
            except Exception as e:
                logger.error(f"Video planner LLM call failed ({prompt_label}): {e}")

        if not text.strip():
            logger.warning("All video planner attempts failed, using fallback plan")
            return self._fallback_plan(script, title, total_duration, audio_timings)

        try:

            plan = json.loads(text)
            self._validate_plan(plan)

            # If too few scenes, fall back
            if len(plan.get("scenes", [])) < 4:
                logger.warning(f"LLM returned only {len(plan['scenes'])} scenes, using fallback plan")
                return self._fallback_plan(script, title, total_duration, audio_timings)

            # Override scene durations from audio timings if available
            if audio_timings:
                _apply_audio_timings(plan, audio_timings)

            # Review → regenerate loop: keep revising until score is acceptable
            MAX_REVIEW_ROUNDS = 3
            for round_idx in range(MAX_REVIEW_ROUNDS):
                review = self._review_plan(plan, script, title, tags)
                if not review:
                    break  # Review skipped or failed, accept current plan

                score = review.get("score", 5)
                suggestions = review.get("suggestions", [])
                issues = review.get("issues", [])

                logger.info(f"Review round {round_idx + 1}: score={score}/10, {len(suggestions)} suggestions")

                if score >= 6:
                    logger.info("Plan accepted by review")
                    break

                # Regenerate with review feedback as additional instruction
                critique_text = "之前生成的方案存在以下问题，请重新设计：\n"
                for issue in issues:
                    critique_text += f"- {issue}\n"
                if suggestions:
                    critique_text += "\n具体修改要求：\n"
                    for sug in suggestions:
                        idx = sug.get("scene_index", "?")
                        action = sug.get("action", "")
                        reason = sug.get("reason", "")
                        critique_text += f"- 场景[{idx}]：{action}（{reason}）\n"

                critique_text += "\n请根据以上反馈重新生成一份完整的构图计划，注意不要重复之前的问题。"

                try:
                    response = self.client.chat.completions.create(
                        model=self.model,
                        max_tokens=4096,
                        temperature=0.7,
                        messages=[
                            {"role": "system", "content": VIDEO_PLANNER_SEED_PROMPT},
                            {"role": "user", "content": user_prompt},
                            {"role": "assistant", "content": text_raw},
                            {"role": "user", "content": critique_text},
                        ],
                    )
                    text_raw = response.choices[0].message.content.strip()
                    new_text = _extract_json(text_raw)
                    new_text = _fix_json(new_text)
                    if new_text.strip():
                        plan = json.loads(new_text)
                        self._validate_plan(plan)
                        if audio_timings:
                            _apply_audio_timings(plan, audio_timings)
                        text = new_text
                except Exception as e:
                    logger.warning(f"Review regeneration round {round_idx + 1} failed: {e}")
                    break

            logger.info(
                f"Video plan generated: theme={plan.get('theme')}, "
                f"{len(plan.get('scenes', []))} scenes, "
                f"{sum(s.get('duration', 0) for s in plan.get('scenes', [])):.1f}s"
            )
            return plan

        except json.JSONDecodeError as e:
            logger.warning(f"Video planner returned invalid JSON: {e} | {text_raw[:200]}")
            return self._fallback_plan(script, title, total_duration, audio_timings)
        except Exception as e:
            logger.warning(f"Video planning failed: {e}")
            return self._fallback_plan(script, title, total_duration, audio_timings)

    _VALID_LAYOUTS = {
        # v3 advanced tech layouts (highest priority)
        "tech_multi_panel", "connected_cards", "architecture_flow", "stack_highlight",
        # v3 data & terminal layouts
        "data_compare", "terminal_mockup",
        # v2 layouts
        "title_card", "card_grid", "numbered_cards", "split_compare",
        "flow_diagram", "fan_out", "doc_tree", "block_tree",
    }
    _VALID_TYPES = {
        "title", "bullet", "section_title", "data_card", "quote",
        "comparison", "timeline", "highlight", "image_caption", "ending",
    }
    _VALID_ANIMATIONS = {"fade", "slideUp", "slideRight", "scaleIn", "typewriter", "none"}
    _DEFAULT_ANIMATIONS = {
        # v3 layouts — custom animations for tech style
        "tech_multi_panel": "fade",
        "connected_cards":  "fade",
        "architecture_flow":"fade",
        "stack_highlight":  "fade",
        "data_compare":     "slideUp",
        "terminal_mockup":  "fade",
        # v2 layouts — animate like the legacy equivalents they replace
        "title_card":     "scaleIn",
        "card_grid":      "fade",
        "numbered_cards": "fade",
        "split_compare":  "fade",
        "flow_diagram":   "fade",
        "fan_out":        "fade",
        "doc_tree":       "fade",
        "block_tree":     "fade",
        # v1 legacy (kept)
        "title": "scaleIn",
        "bullet": "slideRight",
        "section_title": "slideUp",
        "data_card": "scaleIn",
        "quote": "typewriter",
        "comparison": "slideUp",
        "timeline": "fade",
        "highlight": "scaleIn",
        "image_caption": "slideUp",
        "ending": "fade",
    }
    _DEFAULT_THEME = "dark_tech_v3"

    # Required-field checks per layout. Used by _validate_plan to detect
    # under-specified layouts and coerce them to title_card (rather than
    # crashing the renderer).
    _LAYOUT_REQUIRED_FIELDS = {
        # v3 layouts
        "tech_multi_panel": ["techMultiPanel.leftPanel.items", "techMultiPanel.centerPanel.body"],
        "connected_cards":  ["connectedCards.cards"],
        "architecture_flow":["architectureFlow.nodes"],
        "stack_highlight":  ["stackHighlight.leftItems", "stackHighlight.rightCard.title"],
        "data_compare":     ["dataCompare.items"],
        "terminal_mockup":  ["terminalMockup.lines"],
        # v2 layouts
        "title_card":     ["titleCard.title"],
        "card_grid":      ["cardGrid.cards"],
        "numbered_cards": ["numberedCards.cards"],
        "split_compare":  ["splitCompare.leftItems", "splitCompare.rightHeader"],
        "flow_diagram":   ["flowDiagram.llmLabel"],
        "fan_out":        ["fanOut.leftItems", "fanOut.rightCardTitle"],
        "doc_tree":       ["docTree.toc"],
        "block_tree":     ["blocks"],
    }

    def _scene_kind(self, scene: dict) -> str:
        """Return 'layout' or 'type' or 'unknown' for routing."""
        if scene.get("layout") in self._VALID_LAYOUTS:
            return "layout"
        if scene.get("type") in self._VALID_TYPES:
            return "type"
        return "unknown"

    def _scene_key(self, scene: dict) -> str:
        return scene.get("layout") or scene.get("type") or "highlight"

    def _has_required_fields(self, scene: dict) -> bool:
        layout = scene.get("layout")
        if layout not in self._LAYOUT_REQUIRED_FIELDS:
            return True
        for dotted in self._LAYOUT_REQUIRED_FIELDS[layout]:
            obj = scene
            ok = True
            for part in dotted.split("."):
                if not isinstance(obj, dict) or part not in obj or obj[part] in (None, "", [], {}):
                    ok = False
                    break
                obj = obj[part]
            if not ok:
                return False
        return True

    def _coerce_to_title_card(self, scene: dict) -> dict:
        """Convert an invalid scene into a title_card so the renderer never sees a broken spec."""
        title = (
            scene.get("title")
            or (scene.get("titleCard") or {}).get("title")
            or (scene.get("cardGrid") or {}).get("title")
            or (scene.get("docTree") or {}).get("title")
            or "亮点"
        )
        return {
            "layout": "title_card",
            "englishLabel": scene.get("englishLabel"),
            "sceneSubtitle": scene.get("sceneSubtitle"),
            "duration": scene.get("duration", 3.0),
            "animation": scene.get("animation", "scaleIn"),
            "titleCard": {"title": title, "sceneSubtitle": scene.get("sceneSubtitle")},
        }

    def _validate_plan(self, plan: dict) -> None:
        """Validate and fix common issues in the plan. Accepts both
        legacy `type` scenes and v2 `layout` scenes.
        """
        if "title" not in plan or not plan.get("title"):
            plan["title"] = "AI 资讯"
        plan["title"] = _re.sub(r"\[VIDEO:.*?]", "", plan["title"]).strip()
        if not plan["title"]:
            plan["title"] = "AI 资讯"
        if "theme" not in plan or not plan.get("theme"):
            plan["theme"] = self._DEFAULT_THEME
        if "scenes" not in plan or not plan["scenes"]:
            plan["scenes"] = [
                {"layout": "title_card", "titleCard": {"title": plan["title"]}, "duration": 3, "animation": "scaleIn"},
                {"layout": "title_card", "titleCard": {"title": "感谢观看"}, "duration": 2, "animation": "fade"},
            ]
        for i, scene in enumerate(plan["scenes"]):
            kind = self._scene_kind(scene)
            if kind == "unknown":
                # Neither layout nor type is set / valid — coerce to title_card.
                plan["scenes"][i] = self._coerce_to_title_card(scene)
                kind = "layout"
                scene = plan["scenes"][i]
            # If first scene is not a cover, force it to title_card.
            if i == 0 and self._scene_key(scene) not in (
                "title_card", "title", "bullet", "section_title", "highlight"
            ):
                scene["layout"] = "title_card"
                scene["animation"] = "scaleIn"
                scene.setdefault("titleCard", {})
                scene["titleCard"].setdefault("title", plan.get("title", "AI 资讯"))
                scene.pop("type", None)
                kind = "layout"
            # Animation
            anim = scene.get("animation", "")
            if anim not in self._VALID_ANIMATIONS:
                scene["animation"] = self._DEFAULT_ANIMATIONS.get(self._scene_key(scene), "fade")
            # Duration
            if "duration" not in scene or scene["duration"] <= 0:
                scene["duration"] = 3.0
            # Required-fields check for layouts
            if kind == "layout" and not self._has_required_fields(scene):
                logger.warning(
                    f"Scene {i} ({scene.get('layout')}) missing required fields, coercing to title_card"
                )
                plan["scenes"][i] = self._coerce_to_title_card(scene)
                scene = plan["scenes"][i]
            # Strip bracketed prompts from text fields
            for key in (
                "title", "subtitle", "body", "highlight", "highlightValue",
                "quote", "quoteAuthor", "leftTitle", "rightTitle",
            ):
                if key in scene and isinstance(scene[key], str):
                    scene[key] = _re.sub(r"\[VIDEO:.*?]", "", scene[key]).strip()
            for key in ("items", "leftItems", "rightItems", "lines"):
                if key in scene and isinstance(scene[key], list):
                    scene[key] = [
                        _re.sub(r"\[VIDEO:.*?]", "", t).strip()
                        for t in scene[key]
                    ]
            # Also strip from layout content
            for layout_key in (
                "titleCard", "cardGrid", "numberedCards", "splitCompare",
                "flowDiagram", "fanOut", "docTree",
            ):
                if layout_key in scene and isinstance(scene[layout_key], dict):
                    self._scrub_brackets_in_place(scene[layout_key])

        # Enforce scene diversity: no single layout/type should exceed 40% of scenes
        scenes = plan["scenes"]
        if len(scenes) >= 4:
            from collections import Counter
            key_counts = Counter(self._scene_key(s) for s in scenes)
            dominant_key, dominant_count = key_counts.most_common(1)[0]
            max_allowed = max(2, int(len(scenes) * 0.4))
            if dominant_count > max_allowed and dominant_key not in (
                "title_card", "title", "ending"
            ):
                # Rotate excess scenes through v2 layouts first, then legacy types.
                alt_keys = [
                    "card_grid", "numbered_cards", "split_compare",
                    "flow_diagram", "fan_out", "doc_tree",
                    "highlight", "data_card", "quote", "comparison",
                ]
                convert_count = dominant_count - max_allowed
                converted = 0
                for i, scene in enumerate(scenes):
                    if converted >= convert_count:
                        break
                    if self._scene_key(scene) == dominant_key and 0 < i < len(scenes) - 1:
                        new_key = alt_keys[converted % len(alt_keys)]
                        self._convert_scene_key(scene, new_key)
                        converted += 1

    def _scrub_brackets_in_place(self, obj: dict) -> None:
        """Recursively remove [VIDEO:...] brackets from any string values."""
        for k, v in list(obj.items()):
            if isinstance(v, str):
                obj[k] = _re.sub(r"\[VIDEO:.*?]", "", v).strip()
            elif isinstance(v, list):
                obj[k] = [
                    _re.sub(r"\[VIDEO:.*?]", "", t).strip() if isinstance(t, str) else t
                    for t in v
                ]
            elif isinstance(v, dict):
                self._scrub_brackets_in_place(v)

    def _convert_scene_key(self, scene: dict, new_key: str) -> None:
        """Convert a scene's layout/type to a new key, populating a minimal
        required shape so the renderer doesn't crash.
        """
        title_hint = (
            scene.get("title")
            or (scene.get("titleCard") or {}).get("title")
            or (scene.get("cardGrid") or {}).get("title")
            or (scene.get("docTree") or {}).get("title")
            or scene.get("highlight")
            or "关键点"
        )
        scene.pop("type", None)
        scene["layout"] = new_key
        scene["animation"] = self._DEFAULT_ANIMATIONS.get(new_key, "fade")
        # Reset layout-specific content with a minimal shape
        for k in ("titleCard", "cardGrid", "numberedCards", "splitCompare",
                  "flowDiagram", "fanOut", "docTree"):
            scene.pop(k, None)
        if new_key == "title_card":
            scene["titleCard"] = {"title": title_hint, "sceneSubtitle": scene.get("sceneSubtitle")}
        elif new_key == "card_grid":
            scene["cardGrid"] = {
                "title": title_hint,
                "cards": [
                    {"title": "维度一", "items": ["关键点 1", "关键点 2"]},
                    {"title": "维度二", "items": ["关键点 1", "关键点 2"]},
                    {"title": "维度三", "items": ["关键点 1", "关键点 2"]},
                ],
                "sceneSubtitle": scene.get("sceneSubtitle"),
            }
        elif new_key == "numbered_cards":
            scene["numberedCards"] = {
                "title": title_hint,
                "cards": [
                    {"name": "类别一", "items": [{"num": "01", "text": "要点 1"}]},
                    {"name": "类别二", "items": [{"num": "01", "text": "要点 1"}]},
                    {"name": "类别三", "items": [{"num": "01", "text": "要点 1"}]},
                ],
                "sceneSubtitle": scene.get("sceneSubtitle"),
            }
        elif new_key == "split_compare":
            scene["splitCompare"] = {
                "title": title_hint,
                "leftTitle": "传统方式",
                "leftItems": [{"text": "问题 1", "icon": "✕"}, {"text": "问题 2", "icon": "✕"}],
                "rightHeader": "新方案",
                "rightHeaderVariant": "orange",
                "barSegments": [
                    {"label": "70%", "color": "#FF6B35", "value": 70},
                    {"label": "30%", "color": "#FFA502", "value": 30},
                ],
                "barTotal": 100,
                "bottomText": "新方案在效率上有显著优势",
                "sceneSubtitle": scene.get("sceneSubtitle"),
            }
        elif new_key == "flow_diagram":
            scene["flowDiagram"] = {
                "title": title_hint,
                "inputs": [{"label": "Prompt"}, {"label": "Context"}],
                "llmLabel": "LLM",
                "agentLabel": "AGENT",
                "harnessLabel": "Harness",
                "toolLabels": [{"label": "Tool"}, {"label": "MCP"}],
                "bottomLegend": [{"label": "组件一"}, {"label": "组件二"}, {"label": "组件三"}],
                "sceneSubtitle": scene.get("sceneSubtitle"),
            }
        elif new_key == "fan_out":
            scene["fanOut"] = {
                "title": title_hint,
                "leftItems": [
                    {"text": "能力 1"}, {"text": "能力 2"}, {"text": "能力 3"},
                    {"text": "能力 4"}, {"text": "能力 5"}, {"text": "能力 6"},
                ],
                "rightCardTitle": "Skill",
                "rightCardBody": "多能力的组合",
                "rightPills": ["生成", "搜索"],
                "sceneSubtitle": scene.get("sceneSubtitle"),
            }
        elif new_key == "doc_tree":
            scene["docTree"] = {
                "title": title_hint,
                "rootName": "SKILL.md",
                "files": [{"name": "config.yml"}, {"name": "task-flow.md"}],
                "tocTitle": "SKILL.md",
                "toc": [{"num": "01", "name": "项目说明"}],
                "codeTitle": "示例",
                "codeContent": "// 示例代码",
                "sceneSubtitle": scene.get("sceneSubtitle"),
            }
        elif new_key == "highlight":
            scene["highlight"] = title_hint
            scene["highlightValue"] = "✨"
            scene["body"] = scene.get("body") or title_hint
        elif new_key == "data_card":
            scene["title"] = title_hint
            scene["dataPoints"] = [{"label": "指标", "value": 80, "unit": "%"}]
        elif new_key == "quote":
            scene["quote"] = title_hint
            scene["quoteAuthor"] = "佚名"
        elif new_key == "comparison":
            scene["leftTitle"] = "传统"
            scene["leftItems"] = ["传统做法 1", "传统做法 2"]
            scene["rightTitle"] = "新方案"
            scene["rightItems"] = ["新方案 1", "新方案 2"]
        elif new_key == "ending":
            scene["title"] = "感谢观看"
            scene["items"] = ["关注获取更多"]
            scene["subtitle"] = "我们下期见"

    # ── Plan Review ──────────────────────────────────────────────────────

    REVIEW_PROMPT = """你是一个短视频画面编排的审核专家。审核一份视频构图计划，判断其质量和表达效果。

审核维度（按重要性排序）：
1. **表达到位**：画面内容是否有效补充了口播？是否有场景在重复口播内容？（最重要）
2. **布局恰当**：场景使用的 layout / type 是否和该场景内容匹配？
   - 多卡片对比 → card_grid / numbered_cards
   - 左右分栏对比 → split_compare
   - 系统关系/流程 → flow_diagram
   - 多能力叠加 → fan_out
   - 文档/手册说明 → doc_tree
   - 数据对比/倍增效果 → data_compare
   - AI 工具演示/终端操作 → terminal_mockup
   - 通用封面/收尾 → title_card
3. **画面美观**：场景类型搭配是否合理？视觉节奏是否有变化？
4. **信息密度**：每个场景的数据量是否充实？是否有场景太空洞？
5. **节奏感**：场景之间的过渡是否自然？开头是否吸引人？结尾是否有力？
6. **合理性**：有没有场景短到让观众完全来不及看（<1s）？有没有场景长到让人失去耐心？

注意：不要用模板思维去评判——允许各种创意编排，只要表达效果好、画面美观即可。

输出 JSON：
{
  "score": 1-10 的评分（>=6 表示通过）,
  "issues": ["问题1", "问题2", ...],
  "suggestions": [
    {"scene_index": 数字, "action": "merge|split|extend|shorten|change_type|enrich", "reason": "为什么", "field": "字段", "new_value": "建议值"}
  ]
}

如果质量不错（score >= 6），issues 和 suggestions 可以为空数组，不需要为了修改而修改。"""

    def _review_plan(
        self,
        plan: dict,
        script: str,
        title: str = "",
        tags: Optional[list[str]] = None,
    ) -> Optional[dict]:
        """Review the generated plan and suggest improvements.

        Uses a lightweight LLM call to critique pacing, density, and diversity.
        Returns None if review is skipped (no API key) or fails.
        """
        if not self.client or not self.client.api_key:
            return None

        scenes_summary = []
        for i, s in enumerate(plan.get("scenes", [])):
            kind = s.get('layout') or s.get('type') or 'unknown'
            fields = {k: v for k, v in s.items() if k in ("type", "layout", "duration", "title", "highlight", "body")}
            scenes_summary.append(f"  [{i}] layout={kind} dur={s.get('duration', '?')}s title={s.get('title', s.get('highlight', ''))[:30]}")

        plan_preview = "\n".join(scenes_summary)
        topic = title or script[:100]

        user_prompt = f"""主题/素材：{topic}
总场景数：{len(plan.get('scenes', []))}

场景列表：
{plan_preview}

请审核这份构图计划的质量，按 REVIEW_PROMPT 的 JSON 格式输出。"""

        try:
            logger.info("Reviewing composition plan...")
            response = self.client.chat.completions.create(
                model=self.model,
                max_tokens=2048,
                temperature=0.3,
                messages=[
                    {"role": "system", "content": self.REVIEW_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
            )
            text = response.choices[0].message.content.strip()
            text = _extract_json(text)
            text = _fix_json(text)
            if not text.strip():
                return None
            review = json.loads(text)
            logger.info(f"Plan review: score={review.get('score', '?')}/10, {len(review.get('suggestions', []))} suggestions")
            return review
        except Exception as e:
            logger.debug(f"Plan review failed (non-critical): {e}")
            return None

    def _fallback_plan(
        self,
        script: str,
        title: str,
        total_duration: float | None = None,
        audio_timings: list[dict] | None = None,
    ) -> dict:
        """Generate a fallback visual plan when LLM fails.

        v2: prefers the new layout catalog (title_card → card_grid → numbered_cards →
        split_compare) and only falls through to the legacy type rotation when needed.
        Default theme is `dark_glass`.
        """
        if total_duration is None:
            if audio_timings:
                total_duration = sum(t["end"] - t["start"] for t in audio_timings)
            else:
                char_count = len(script)
                total_duration = max(15.0, min(60.0, char_count / 4.0 + 3.0))

        sentences = _re.split(r"[。！？!?，,；;：:]", script)
        sentences = [s.strip() for s in sentences if s.strip() and len(s.strip()) > 2]

        if not sentences:
            sentences = [title or "AI 资讯"]

        n_scenes = min(max(len(sentences), 6), 12)
        per_scene = total_duration / max(n_scenes, 3)

        hook_text = sentences[0][:18] if sentences else (title or "AI 资讯")
        scenes: list[dict] = [
            {
                "layout": "title_card",
                "englishLabel": "intro",
                "titleCard": {
                    "title": hook_text,
                    "subtitle": (title or "AI 资讯")[:30],
                    "sceneSubtitle": "今天的核心观点",
                },
                "duration": min(3.0, per_scene * 1.2),
                "animation": "scaleIn",
            }
        ]

        layout_rotation = [
            ("card_grid",      "fade"),
            ("numbered_cards", "fade"),
            ("split_compare",  "fade"),
            ("fan_out",        "fade"),
            ("doc_tree",       "fade"),
        ]

        remaining = sentences[1:] if len(sentences) > 1 else sentences
        for i, sent in enumerate(remaining):
            layout_name, anim = layout_rotation[i % len(layout_rotation)]
            text = sent[:25]
            sub = text[:18] or "关键点"

            scene: dict = {
                "layout": layout_name,
                "duration": round(per_scene, 2),
                "animation": anim,
                "englishLabel": layout_name,
                "sceneSubtitle": sub,
            }

            if layout_name == "card_grid":
                scene["cardGrid"] = {
                    "title": text[:14],
                    "cards": [
                        {"title": "维度一", "items": [text[:10], "细节 1"]},
                        {"title": "维度二", "items": [text[:10], "细节 2"]},
                        {"title": "维度三", "items": [text[:10], "细节 3"]},
                    ],
                    "sceneSubtitle": sub,
                }
            elif layout_name == "numbered_cards":
                scene["numberedCards"] = {
                    "title": text[:14],
                    "cards": [
                        {"name": "类别一", "items": [
                            {"num": "01", "text": text[:10]},
                            {"num": "02", "text": "细节"},
                        ]},
                        {"name": "类别二", "items": [
                            {"num": "01", "text": text[:10]},
                            {"num": "02", "text": "细节"},
                        ]},
                        {"name": "类别三", "items": [
                            {"num": "01", "text": text[:10]},
                            {"num": "02", "text": "细节"},
                        ]},
                    ],
                    "centerText": "三者协同",
                    "sceneSubtitle": sub,
                }
            elif layout_name == "split_compare":
                scene["splitCompare"] = {
                    "title": text[:14],
                    "leftTitle": "传统方式",
                    "leftItems": [
                        {"text": "传统做法 1", "icon": "✕"},
                        {"text": "传统做法 2", "icon": "✕"},
                        {"text": "传统做法 3", "icon": "✕"},
                    ],
                    "rightHeader": "新方案",
                    "rightHeaderVariant": "orange",
                    "barSegments": [
                        {"label": "+70%", "color": "#FF6B35", "value": 70},
                        {"label": "30%", "color": "#FFA502", "value": 30},
                    ],
                    "barTotal": 100,
                    "bottomText": "真正要解决的不是一句话问成，而是整套能力叠加。",
                    "sceneSubtitle": sub,
                }
            elif layout_name == "fan_out":
                scene["fanOut"] = {
                    "title": text[:14],
                    "leftItems": [
                        {"text": "能力 1"}, {"text": "能力 2"},
                        {"text": "能力 3"}, {"text": "能力 4"},
                        {"text": "能力 5"}, {"text": "能力 6"},
                    ],
                    "rightCardTitle": "Skill",
                    "rightCardSubtitle": "叠加之后 →",
                    "rightCardBody": "多能力的组合，按场景调用。",
                    "rightPills": ["生成", "创新", "搜索"],
                    "sceneSubtitle": sub,
                }
            elif layout_name == "doc_tree":
                scene["docTree"] = {
                    "title": text[:14],
                    "rootName": "SKILL.md",
                    "files": [
                        {"name": "config.yml"},
                        {"name": "task-flow.md"},
                        {"name": "quality.md"},
                    ],
                    "tocTitle": "SKILL.md",
                    "toc": [
                        {"num": "01", "name": "项目说明"},
                        {"num": "02", "name": "任务边界"},
                        {"num": "03", "name": "工作流"},
                    ],
                    "codeTitle": "示例",
                    "codeContent": "// 示例代码\n{\n  taskOptions: 'everything',\n}",
                    "sceneSubtitle": sub,
                }

            scenes.append(scene)

        if sentences:
            last = sentences[-1]
            if any(kw in last for kw in ["？", "?", "评论", "关注", "点赞", "转发", "收藏"]):
                ending_text = last[:30]
            else:
                ending_text = f"关注我\n{last[:20]}"
        else:
            ending_text = "关注我\n获取更多 AI 资讯"

        scenes.append({
            "layout": "title_card",
            "englishLabel": "ending",
            "titleCard": {
                "title": ending_text.split("\n")[0] if "\n" in ending_text else ending_text,
                "subtitle": "感谢观看 · 关注获取更多",
                "sceneSubtitle": "感谢观看",
            },
            "duration": min(3.0, per_scene),
            "animation": "fade",
        })

        plan = {"title": title or "AI 资讯", "theme": self._DEFAULT_THEME, "scenes": scenes}

        if audio_timings:
            _apply_audio_timings(plan, audio_timings)
        else:
            _normalize_durations(plan, total_duration)

        logger.info(
            f"Using fallback video plan: {len(scenes)} scenes, theme={self._DEFAULT_THEME}"
        )
        return plan


# ═══════════════════════════════════════════════════════════════
#  Shared utilities
# ═══════════════════════════════════════════════════════════════

def _extract_json(text: str) -> str:
    """Extract JSON object from text that may have markdown fences or surrounding text."""
    if not text or not text.strip():
        return ""

    text = text.strip()

    # Try 1: Strip markdown code fences (```json ... ``` or ``` ... ```)
    import re as _re2
    fence_match = _re2.search(r"```(?:json)?\s*\n?(.*?)\n?\s*```", text, _re2.DOTALL)
    if fence_match:
        candidate = fence_match.group(1).strip()
        if candidate.startswith("{"):
            return candidate

    # Try 2: Find first { and last }
    json_start = text.find("{")
    json_end = text.rfind("}")
    if json_start >= 0 and json_end > json_start:
        return text[json_start:json_end + 1]

    # Try 3: Find [ and ] (array response)
    arr_start = text.find("[")
    arr_end = text.rfind("]")
    if arr_start >= 0 and arr_end > arr_start:
        return text[arr_start:arr_end + 1]

    return ""


def _fix_json(text: str) -> str:
    """Fix common JSON issues in LLM responses."""
    # Remove trailing commas before closing braces/brackets
    text = _re.sub(r",\s*([}\]])", r"\1", text)

    # Fix unterminated strings in last line
    lines = text.split('\n')
    if lines:
        last = lines[-1]
        quote_count = 0
        i = 0
        while i < len(last):
            if last[i] == '\\' and i + 1 < len(last):
                i += 2
                continue
            if last[i] == '"':
                quote_count += 1
            i += 1
        if quote_count % 2 != 0:
            lines[-1] = last.rstrip() + '"'
    text = '\n'.join(lines)

    # Fix truncated JSON: close open brackets/braces
    open_braces = 0
    open_brackets = 0
    in_string = False
    escape_next = False
    for ch in text:
        if escape_next:
            escape_next = False
            continue
        if ch == '\\' and in_string:
            escape_next = True
            continue
        if ch == '"' and not escape_next:
            in_string = not in_string
            continue
        if in_string:
            continue
        if ch == '{':
            open_braces += 1
        elif ch == '}':
            open_braces -= 1
        elif ch == '[':
            open_brackets += 1
        elif ch == ']':
            open_brackets -= 1

    if in_string:
        text += '"'
    text = _re.sub(r',\s*"[^"]*":?\s*$', '', text)
    text = _re.sub(r':\s*$', ': null', text)
    text = _re.sub(r',\s*$', '', text)
    for _ in range(open_brackets):
        text += ']'
    for _ in range(open_braces):
        text += '}'

    return text


def _format_audio_timeline(timings: list[dict] | None) -> str:
    """Format audio timings into a readable string for the LLM prompt."""
    if not timings:
        return "（无音频时间戳，请根据素材自行估算每个场景的合理时长）"

    lines = []
    for i, t in enumerate(timings):
        lines.append(
            f"  段{i+1}: {t['start']:.1f}s - {t['end']:.1f}s "
            f"({t['end'] - t['start']:.1f}s) | 口播内容: 「{t.get('text', '')}」"
        )
    total = timings[-1]["end"] if timings else 0
    lines.insert(0, f"共 {len(timings)} 段，总时长约 {total:.0f} 秒：")
    return "\n".join(lines)


def _apply_audio_timings(plan: dict, timings: list[dict]) -> None:
    """Apply measured audio timestamps to scene durations.

    When scenes > timings (multiple scenes per audio segment), distributes
    each audio segment's duration proportionally among its mapped scenes.
    """
    scenes = plan.get("scenes", [])
    if not scenes or not timings:
        return

    total_audio = sum(t["end"] - t["start"] for t in timings)
    total_scene_dur = sum(s.get("duration", 3.0) for s in scenes)

    if len(scenes) <= len(timings):
        # Fewer or equal scenes: map 1:1
        for i in range(len(scenes)):
            dur = round(timings[i]["end"] - timings[i]["start"], 2)
            if dur > 0:
                scenes[i]["duration"] = dur
        # Extra timings → extend last scene
        if len(timings) > len(scenes) and scenes:
            extra = sum(
                timings[i]["end"] - timings[i]["start"]
                for i in range(len(scenes), len(timings))
            )
            scenes[-1]["duration"] = round(scenes[-1].get("duration", 2.0) + extra, 2)
    else:
        # More scenes than timings: distribute each audio segment's duration
        # among its mapped scenes, proportional to the scene's planned duration
        scenes_per_seg = len(scenes) / len(timings)
        scene_idx = 0
        for seg_i, timing in enumerate(timings):
            seg_dur = timing["end"] - timing["start"]
            # How many scenes map to this segment
            start_idx = round(seg_i * scenes_per_seg)
            end_idx = round((seg_i + 1) * scenes_per_seg)
            end_idx = min(end_idx, len(scenes))
            group_scenes = scenes[start_idx:end_idx]
            if not group_scenes:
                continue
            group_total = sum(s.get("duration", 3.0) for s in group_scenes)
            if group_total <= 0:
                group_total = len(group_scenes) * 3.0
            for s in group_scenes:
                ratio = s.get("duration", 3.0) / group_total
                s["duration"] = round(seg_dur * ratio, 2)

    # Safety net: scenes shorter than 1.5s are unwatchable flickers
    # Borrow from neighbors to bring them up to a minimum
    MIN_SCENE_DURATION = 1.5
    for i, s in enumerate(scenes):
        if s.get("duration", 0) < MIN_SCENE_DURATION and len(scenes) > 1:
            # Try borrowing time from neighbors
            needed = MIN_SCENE_DURATION - s["duration"]
            if i > 0 and scenes[i - 1].get("duration", 0) > MIN_SCENE_DURATION + needed:
                # Borrow from previous scene
                scenes[i - 1]["duration"] = round(scenes[i - 1]["duration"] - needed, 2)
                s["duration"] = MIN_SCENE_DURATION
            elif i < len(scenes) - 1 and scenes[i + 1].get("duration", 0) > MIN_SCENE_DURATION + needed:
                # Borrow from next scene
                scenes[i + 1]["duration"] = round(scenes[i + 1]["duration"] - needed, 2)
                s["duration"] = MIN_SCENE_DURATION
            else:
                # Set to minimum anyway (total will be slightly longer than audio)
                s["duration"] = MIN_SCENE_DURATION

    logger.info(
        f"Applied audio timings: {len(timings)} segments → {len(scenes)} scenes, "
        f"total={sum(s.get('duration', 0) for s in scenes):.1f}s"
    )


def _normalize_durations(plan: dict, target_total: float) -> None:
    """Scale scene durations to match the target total duration exactly."""
    scenes = plan.get("scenes", [])
    if not scenes:
        return

    current_total = sum(s.get("duration", 3.0) for s in scenes)
    if current_total <= 0:
        return

    ratio = target_total / current_total
    for scene in scenes:
        scene["duration"] = round(scene["duration"] * ratio, 1)

    adjusted_total = sum(s["duration"] for s in scenes)
    diff = round(target_total - adjusted_total, 1)
    if scenes and abs(diff) > 0.05:
        scenes[-1]["duration"] = round(scenes[-1]["duration"] + diff, 1)
        if scenes[-1]["duration"] < 1.0:
            scenes[-1]["duration"] = 1.0
