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

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════
#  AudioPlanner — generates narration + voice direction
# ═══════════════════════════════════════════════════════════════

AUDIO_PLANNER_SYSTEM_PROMPT = """你是一个专业的短视频配音脚本专家。根据参考素材，创作一段自然流畅的口播配音脚本。

## 角色
你只负责**配音脚本**——写出最适合朗读的文本。不需要关心画面、动画或视觉效果。

## 配音创作原则
1. **自然口语化**：像真人说话，不要书面语、不要朗诵腔
2. **节奏感**：长短句交替，有停顿有加速，情绪有起伏
3. **适合朗读**：每段 10-25 字，避免拗口词汇和长定语
4. **黄金 3 秒**：开场第一句要抓耳、有冲击力
5. **结尾有号召**：最后引导关注/点赞/评论，语气真诚不僵硬
6. **控制时长**：总时长控制在 15-35 秒，简洁有力

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
  pause_after 是该段说完后的停顿时长（秒），通常在 0.1-0.4 之间
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
    {"text": "GPT-5 来了！", "tone": "激昂", "pause_after": 0.3},
    {"text": "OpenAI 刚刚发布了最新模型", "tone": "沉稳有力", "pause_after": 0.2},
    {"text": "推理能力提升了整整十倍", "tone": "震撼", "pause_after": 0.3},
    {"text": "而且速度更快，成本更低", "tone": "轻快", "pause_after": 0.2},
    {"text": "这将彻底改变行业格局", "tone": "犀利", "pause_after": 0.3},
    {"text": "关注我，第一时间了解 AI 前沿动态！", "tone": "亲切", "pause_after": 0.0}
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
4. 总时长控制在 15-35 秒
5. 每段 10-25 字，分段合理
6. voice_direction 要具体，20字以内

请输出 JSON。"""


class AudioPlanner:
    """Generates audio narration scripts from douyin source material using LLM."""

    def __init__(self, config: dict):
        mimo_config = config.get("mimo", {})
        api_key = mimo_config.get("api_key", "")
        base_url = mimo_config.get("base_url", "https://api.xiaomimimo.com/v1")
        self.model = mimo_config.get("planner_model", mimo_config.get("model", "mimo-v2.5-pro"))
        self.client = OpenAI(api_key=api_key, base_url=base_url) if api_key else None

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
            logger.warning("MiMo API key not configured, using fallback audio plan")
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

## 核心原则：画面 ≠ 口播的复读机

音频已经在说细节了，画面要做的是**互补**而非**重复**：
- 音频说完整句子 → 画面给关键词、数据、对比
- 音频讲道理 → 画面给视觉冲击
- 音频叙述过程 → 画面给结果和结论

每个场景的 visual_text（画面上显示的文字）**必须和该时段的口播内容不同**。
口播说"推理能力提升了整整十倍"，画面应该显示 "10x ↑" 而不是重复"推理能力提升了整整十倍"。

## 抖音爆款节奏
1. **黄金3秒**：第一个 scene 必须是 hook，大字+冲击动画(zoom_in)，2-3s
2. **15秒留人**：每 15s 切换场景类型或动画风格
3. **情绪曲线**：hook（震撼）→ 干货（好奇/数据）→ ending（共鸣/行动）
4. **信息密度**：开场短(2-3s) → 中段充实(3-5s) → 收束简洁(2-3s)

## 场景类型详解

### 文字类
- **hook**：开场强钩子，大字居中+冲击动画(zoom_in)。显示关键词而非完整句子。
- **title**：标题大字居中，动画 scale_in，2-3s
- **text_sequence**：文字逐行滑入(fade_in)，适合逐步揭示信息
- **highlight**：放大强调+光效(pulse)，适合核心观点/金句
- **bullet_points**：编号列表(slide_up)，适合要点罗列
- **ending**：结尾引导关注(fade_out)，2-3s

### 数据可视化类（新增 — 优先使用！）
- **data_card**：大数字卡片。visual_label="推理能力"，visual_value=10，visual_unit="倍提升"，visual_trend="up"。
  数字从0动画到目标值，带趋势箭头。动画 scale_in，2-3s
- **comparison**：分屏对比。visual_left="旧方案: 5小时"，visual_right="新方案: 3分钟"。
  左右对比动画 slide_up，2-4s
- **keyword_burst**：关键词炸裂弹入。visual_keywords=["更快", "更智能", "更便宜"]。
  词汇从不同方向弹入屏幕，动画 zoom_in，1.5-3s

### 图文类
- **image_text**：上半部配图+下半部关键词/数据。提供 image_query（英文搜索词10-30字）。3-6s
- **progress_bar**：进度/趋势条。visual_progress=85（表示85%），visual_label="效率提升"。2-3s

## 图片背景 image_query（可用于任意场景类型）
**任何场景都可以添加 image_query 字段**，系统会自动搜索下载对应图片作为背景：
- hook/title：配合冲击力文字，用高对比度图片增强视觉冲击
- highlight：在强调文字背后放氛围图
- data_card：数据卡片背后用相关配图
- ending：结尾用温馨/振奋的背景图
- 图片会做暗化处理保证文字可读性
- image_query 用英文，10-30字，描述具体场景（如 "futuristic AI chip closeup"、"serene mountain sunrise"）

## 输出格式
输出纯 JSON：

{
  "title": "视频标题（封面用，短促有力）",
  "theme": "dark_tech | light_clean | vibrant | minimal | news",
  "scenes": [
    {
      "type": "hook",
      "text": "屏幕上显示的短文本（≠口播内容）",
      "icon": "⚡",
      "visual_style": "explosive neon, bold",
      "mood": "urgent",
      "layout_hint": "spotlight center",
      "duration": 2.5,
      "animation": "zoom_in"
    },
    {
      "type": "data_card",
      "visual_label": "推理能力提升",
      "visual_value": 10,
      "visual_unit": "倍",
      "visual_trend": "up",
      "icon": "📊",
      "visual_style": "clean digital, calm",
      "mood": "serious",
      "layout_hint": "spotlight center",
      "duration": 2.5,
      "animation": "scale_in"
    },
    {
      "type": "keyword_burst",
      "visual_keywords": ["更快", "更智能", "更便宜"],
      "icon": "✨",
      "visual_style": "energetic, vibrant",
      "mood": "inspiring",
      "layout_hint": "wide spread",
      "duration": 3.0,
      "animation": "zoom_in"
    },
    {
      "type": "ending",
      "text": "关注我\\n获取更多 AI 资讯",
      "icon": "👋",
      "visual_style": "warm elegant, hopeful",
      "mood": "hopeful",
      "layout_hint": "spotlight center",
      "duration": 2.5,
      "animation": "fade_out"
    }
  ]
}

## visual_text 创作原则（极其重要）
- **不得与口播重复**：口播说"OpenAI 发布了 GPT-5"，画面显示 "GPT-5" 或 "OpenAI 重磅发布"，不显示完整句子
- **碎片化、关键词化**：画面文字 = 口播内容的提炼，用数字、关键词、短标签
- **数据金句优先**：能用数字就用数字（"10x"、"300%↑"），能用对比就用对比（"A vs B"）
- **金句卡片**：适合 highlight 场景，把口播中最有冲击力的短句做成大字卡片

## 场景类型搭配建议
- 30 秒视频 → 约 8-12 个场景
- 必须包含：hook + 至少 1 个 data_card / comparison + ending
- 文字类和数据类交替出现，保持视觉新鲜感
- 约 30-40% 使用数据可视化类型（data_card / comparison / keyword_burst / progress_bar）

## 图标 icon
- hook/title：🤖📡⚡🔥🎯
- data_card：📊📈💹🔢
- comparison：⚖️🔄📉📋
- keyword_burst：✨💥🎯🔑
- text_sequence：💡📖🔍
- highlight：🧠💎🚀
- bullet_points：✅📋🔑
- image_text：🖼️📸🌐
- progress_bar：⏳📶📊
- ending：👋❤️🔔💬

## 主题 theme
- dark_tech：深色+蓝色+金色 → 科技/AI内容
- light_clean：白色+蓝色 → 轻松/生活
- vibrant：暗紫+橙色+金色 → 娱乐/创意
- minimal：纯黑+纯白 → 极简
- news：浅灰+红色 → 新闻

## 视觉风格 visual_style（2-4 英文词）
- 科技：cyberpunk, neon, holographic, digital, matrix
- 高端：luxurious, cinematic, elegant, premium
- 冲击：explosive, energetic, dynamic, bold, impactful
- 简约：minimal, zen, calm, clean, soft
- 活泼：playful, creative, vibrant, pop

## 情绪 mood
urgent | calm | inspiring | mysterious | serious | hopeful | dramatic

## 布局 layout_hint
spotlight center | left aligned | split left-right | stacked cards | timeline left | wide spread

## 动画 animation
- 激昂 → zoom_in、scale_in
- 平实 → fade_in、slide_up
- 强调 → pulse
- 结尾 → fade_out

## 完整示例
输入素材："GPT-5 发布了，推理能力提升 10 倍，速度更快成本更低。"
音频时间戳：0.0-2.4s (GPT-5 来了) → 2.4-5.8s (推理能力提升) → 5.8-8.0s (更快更便宜)

{
  "title": "GPT-5 重磅发布",
  "theme": "dark_tech",
  "scenes": [
    { "type": "hook", "text": "GPT-5", "icon": "⚡", "visual_style": "explosive neon, bold", "mood": "urgent", "layout_hint": "spotlight center", "duration": 2.4, "animation": "zoom_in" },
    { "type": "data_card", "visual_label": "推理能力", "visual_value": 10, "visual_unit": "倍提升", "visual_trend": "up", "icon": "📊", "visual_style": "clean digital, calm", "mood": "serious", "layout_hint": "spotlight center", "duration": 3.4, "animation": "scale_in" },
    { "type": "keyword_burst", "visual_keywords": ["速度↑", "成本↓", "更智能"], "icon": "✨", "visual_style": "energetic, vibrant", "mood": "inspiring", "layout_hint": "wide spread", "duration": 2.2, "animation": "zoom_in" },
    { "type": "ending", "text": "关注我\\n第一时间了解 AI 动态", "icon": "👋", "visual_style": "warm elegant, hopeful", "mood": "hopeful", "layout_hint": "spotlight center", "duration": 2.0, "animation": "fade_out" }
  ]
}
"""

VIDEO_PLANNER_USER_PROMPT_TEMPLATE = """根据参考素材和音频时间戳，设计视频画面的场景编排。

== 参考素材 ==
原标题：{title}
原始文案：{script}
标签/关键词：{tags}

== 口播配音时长分配 ==
{audio_timeline}

== 要求 ==
1. **画面文字不得与口播重复**——口播说完整句子，画面只显示关键词/数据/对比
2. 第一个 scene 必须是 hook 类型，动画 zoom_in
3. 最后 scene 是 ending，引导关注
4. 优先使用 data_card / comparison / keyword_burst 让画面有数据感和冲击力
5. 场景类型多样化：至少包含 hook、1 个数据可视化类型、ending
6. 每个场景必须设置 visual_style、mood、layout_hint
7. 适当使用 image_text 场景（约占 20%），提供英文 image_query
8. 场景数量 = 音频段数（大约），每个场景的 duration 使用对应音频段的时长

请输出 JSON 构图计划。"""

# ── Prompt-generator: creates custom system prompts per content ──

VIDEO_PLANNER_META_PROMPT = """你是一个世界级的 prompt 工程师，专精于为视频 AI 导演编写系统提示词。

你的任务：根据给定的内容素材和音频时间戳，编写一份**定制化的视频导演系统提示词**。

## 你的输出将被用作另一个 LLM 的 system prompt
那个 LLM 会读取你的提示词 + 用户素材，输出一个 JSON 构图计划。所以你的提示词必须：
1. 清晰定义角色和任务
2. 根据素材的具体主题、情绪、数据，给出**针对性的视觉建议**
3. 推荐最适合这个内容的场景类型组合
4. 禁止泛泛而谈——要具体到"这个内容适合用什么颜色、什么动画、什么对比手法"

## 必须包含的内容
1. **角色定义**：你是短视频视觉导演
2. **核心原则**：画面 ≠ 口播的复读机——画面用关键词/数据/对比，音频说完整句子
3. **可用场景类型**（全部列出，带简短说明）：
   - hook / title / text_sequence / highlight / bullet_points / image_text / ending
   - data_card：大数字卡片(visual_label/visual_value/visual_unit/visual_trend)
   - comparison：分屏对比(visual_left/visual_right)
   - keyword_burst：关键词弹入(visual_keywords[])
   - progress_bar：进度条(visual_progress/visual_label)
   - **任何场景类型都可以添加 image_query 字段**（10-30字英文），系统自动下载图片做背景
4. **针对本内容的场景推荐**：看完素材后，推荐 2-3 个最出彩的视觉手法，并建议哪些场景适合配图
5. **可用 theme**：dark_tech / light_clean / vibrant / minimal / news — 推荐最适合的一个
6. **visual_style 关键词库**（英文）：cyberpunk, neon, holographic, digital, matrix, luxurious, cinematic, elegant, premium, explosive, energetic, dynamic, bold, impactful, minimal, zen, calm, clean, soft, playful, creative, vibrant, pop
7. **mood 选项**：urgent | calm | inspiring | mysterious | serious | hopeful | dramatic
8. **layout_hint 选项**：spotlight center | left aligned | split left-right | stacked cards | timeline left | wide spread
9. **animation 选项**：fade_in | scale_in | slide_up | typewriter | pulse | zoom_in | fade_out
10. **输出格式**：纯 JSON，包含 title/theme/scenes[] 数组
11. **一个完整的示例 JSON 输出**（用与当前素材类似的内容作为示例）

## 风格
- 用中文写提示词
- 语气专业但有创造力
- 约 800-1500 字
- 直接输出提示词正文，不要加"这是提示词"之类的废话

## 素材信息
{content_brief}

请输出定制化的视频导演系统提示词。"""


class VideoPlanner:
    """Generates visual composition plans — purely visual, separate from audio.

    Uses a two-step LLM process:
      1. Meta-LLM generates a custom system prompt tailored to the content.
      2. That custom prompt drives the actual plan generation.
    """

    def __init__(self, config: dict):
        mimo_config = config.get("mimo", {})
        api_key = mimo_config.get("api_key", "")
        base_url = mimo_config.get("base_url", "https://api.xiaomimimo.com/v1")
        self.model = mimo_config.get("planner_model", mimo_config.get("model", "mimo-v2.5-pro"))
        self.client = OpenAI(api_key=api_key, base_url=base_url) if api_key else None

    def _generate_custom_system_prompt(
        self,
        script: str,
        title: str = "",
        tags: Optional[list[str]] = None,
        audio_timeline: str = "",
    ) -> str | None:
        """Generate a custom system prompt tailored to the specific content.

        Calls the LLM with VIDEO_PLANNER_META_PROMPT, which includes the
        seed knowledge (VIDEO_PLANNER_SEED_PROMPT) plus the content brief.
        The LLM returns a bespoke system prompt for plan generation.

        Returns the custom prompt string, or None on failure.
        """
        # Build a compact content brief
        tag_str = ", ".join(tags[:8]) if tags else "无"
        brief_parts = [
            f"标题：{title or '无'}",
            f"素材内容：{script[:600]}",
            f"标签：{tag_str}",
            f"音频时间分配：\n{audio_timeline}" if audio_timeline else "",
        ]
        content_brief = "\n".join(p for p in brief_parts if p)

        user_prompt = VIDEO_PLANNER_META_PROMPT.format(content_brief=content_brief)

        try:
            logger.info("Generating custom system prompt for video planner...")
            response = self.client.chat.completions.create(
                model=self.model,
                max_tokens=2048,
                temperature=0.8,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "你是一个世界级的 prompt 工程师。"
                            "根据素材信息编写定制化的视频导演系统提示词。\n\n"
                            "## 领域知识参考（种子提示词）\n"
                            + VIDEO_PLANNER_SEED_PROMPT
                        ),
                    },
                    {"role": "user", "content": user_prompt},
                ],
            )

            custom_prompt = response.choices[0].message.content.strip()
            if not custom_prompt:
                logger.warning("LLM returned empty custom prompt")
                return None

            logger.debug(f"Custom prompt preview: {custom_prompt[:120]}...")
            return custom_prompt

        except Exception as e:
            logger.warning(f"Custom system prompt generation failed: {e}")
            return None

    def plan(
        self,
        script: str,
        title: str = "",
        tags: Optional[list[str]] = None,
        audio_timings: Optional[list[dict]] = None,
        total_duration: float | None = None,
    ) -> Optional[dict]:
        """Generate a visual composition plan.

        Two-step process:
          1. LLM generates a custom system prompt tailored to this content.
          2. That custom prompt is used to generate the actual plan JSON.

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
            logger.warning("MiMo API key not configured, skipping video planning")
            return self._fallback_plan(script, title, total_duration)

        audio_timeline = _format_audio_timeline(audio_timings)

        # ── Step 1: Generate custom system prompt ──
        custom_system_prompt = self._generate_custom_system_prompt(
            script=script, title=title, tags=tags, audio_timeline=audio_timeline,
        )
        if not custom_system_prompt:
            logger.warning("Custom prompt generation failed, using seed prompt as fallback")
            custom_system_prompt = VIDEO_PLANNER_SEED_PROMPT
        else:
            logger.info(f"Custom system prompt generated ({len(custom_system_prompt)} chars)")

        # ── Step 2: Generate plan with custom prompt ──
        try:
            format_kwargs = dict(
                title=title or "无标题",
                script=script[:800],
                tags=", ".join(tags[:5]) if tags else "无",
                audio_timeline=audio_timeline,
            )
            user_prompt = VIDEO_PLANNER_USER_PROMPT_TEMPLATE.format(**format_kwargs)

            logger.info("Generating visual composition plan via LLM (custom prompt)...")
            response = self.client.chat.completions.create(
                model=self.model,
                max_tokens=4096,
                temperature=0.7,
                messages=[
                    {"role": "system", "content": custom_system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
            )

            text = response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"Video planner LLM call failed: {e}")
            return self._fallback_plan(script, title, total_duration, audio_timings)

        text_raw = text

        try:
            text = _extract_json(text)
            text = _fix_json(text)
            if not text.strip():
                logger.warning(f"Empty JSON from video planner: {text_raw[:200]}")
                return self._fallback_plan(script, title, total_duration, audio_timings)

            plan = json.loads(text)
            self._validate_plan(plan)

            # Override scene durations from audio timings if available
            if audio_timings:
                _apply_audio_timings(plan, audio_timings)

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

    _VALID_TYPES = {
        "hook", "title", "text_sequence", "highlight", "bullet_points",
        "image_text", "ending", "data_card", "comparison", "keyword_burst",
        "progress_bar",
    }
    _VALID_ANIMATIONS = {"fade_in", "scale_in", "slide_up", "typewriter", "pulse", "zoom_in", "fade_out"}
    _DEFAULT_ANIMATIONS = {
        "hook": "zoom_in",
        "title": "scale_in",
        "text_sequence": "fade_in",
        "highlight": "pulse",
        "bullet_points": "slide_up",
        "image_text": "fade_in",
        "ending": "fade_out",
        "data_card": "scale_in",
        "comparison": "slide_up",
        "keyword_burst": "zoom_in",
        "progress_bar": "scale_in",
    }

    def _validate_plan(self, plan: dict) -> None:
        """Validate and fix common issues in the plan."""
        if "title" not in plan or not plan.get("title"):
            plan["title"] = "AI 资讯"
        plan["title"] = _re.sub(r"\[VIDEO:.*?]", "", plan["title"]).strip()
        if not plan["title"]:
            plan["title"] = "AI 资讯"
        if "theme" not in plan:
            plan["theme"] = "dark_tech"
        if "scenes" not in plan or not plan["scenes"]:
            plan["scenes"] = [
                {"type": "title", "text": plan["title"], "duration": 3, "animation": "scale_in"},
                {"type": "ending", "text": "关注我们", "duration": 2, "animation": "fade_out"},
            ]
        for scene in plan["scenes"]:
            stype = scene.get("type", "")
            if stype not in self._VALID_TYPES:
                scene["type"] = "text_sequence"
            if scene == plan["scenes"][0] and scene["type"] not in ("hook", "title"):
                scene["type"] = "hook"
                scene["animation"] = "zoom_in"
            anim = scene.get("animation", "")
            if anim not in self._VALID_ANIMATIONS:
                scene["animation"] = self._DEFAULT_ANIMATIONS.get(scene["type"], "fade_in")
            if "duration" not in scene or scene["duration"] <= 0:
                scene["duration"] = 3.0
            for key in ("text", "lines", "items"):
                if key in scene:
                    if isinstance(scene[key], str):
                        scene[key] = _re.sub(r"\[VIDEO:.*?]", "", scene[key]).strip()
                    elif isinstance(scene[key], list):
                        scene[key] = [_re.sub(r"\[VIDEO:.*?]", "", t).strip() for t in scene[key]]

    def _fallback_plan(
        self,
        script: str,
        title: str,
        total_duration: float | None = None,
        audio_timings: list[dict] | None = None,
    ) -> dict:
        """Generate a fallback visual plan when LLM fails."""
        if total_duration is None:
            char_count = len(script)
            total_duration = max(15.0, min(60.0, char_count / 4.0 + 3.0))

        sentences = _re.split(r"[。！？!?]", script)
        sentences = [s.strip() for s in sentences if s.strip()]

        n_scenes = min(len(sentences), 8)
        per_scene = total_duration / max(n_scenes + 1, 3)

        hook_text = sentences[0][:18] if sentences else (title or "AI 资讯")
        scenes = [
            {
                "type": "hook",
                "text": hook_text,
                "duration": min(3.0, per_scene * 1.2),
                "animation": "zoom_in",
            }
        ]

        remaining = sentences[1:] if len(sentences) > 1 else sentences
        chunk_size = max(1, len(remaining) // max(n_scenes - 1, 1))

        for i in range(0, len(remaining), chunk_size):
            chunk = remaining[i : i + chunk_size]
            idx = len(scenes)

            if idx % 4 == 1:
                # data_card — extract a number from the chunk if present
                text = chunk[0] if chunk else ""
                num_match = _re.search(r"(\d+)\s*(倍|%|万|亿)", text)
                if num_match:
                    scenes.append({
                        "type": "data_card",
                        "visual_label": text[:10],
                        "visual_value": int(num_match.group(1)),
                        "visual_unit": num_match.group(2),
                        "visual_trend": "up",
                        "duration": per_scene,
                        "animation": "scale_in",
                    })
                else:
                    scenes.append({
                        "type": "highlight",
                        "text": text[:18],
                        "duration": per_scene,
                        "animation": "pulse",
                    })
            elif idx % 4 == 2 and len(chunk) >= 2:
                scenes.append({
                    "type": "comparison",
                    "visual_left": chunk[0][:12],
                    "visual_right": chunk[1][:12] if len(chunk) > 1 else "新方案",
                    "duration": per_scene * 1.5,
                    "animation": "slide_up",
                })
            elif idx % 4 == 3:
                scenes.append({
                    "type": "keyword_burst",
                    "visual_keywords": [c[:8] for c in chunk[:3]],
                    "duration": per_scene,
                    "animation": "zoom_in",
                })
            elif len(chunk) == 1:
                scenes.append({
                    "type": "text_sequence",
                    "lines": [chunk[0]],
                    "duration": per_scene,
                    "animation": "fade_in",
                })
            else:
                scenes.append({
                    "type": "bullet_points",
                    "items": [c[:15] for c in chunk[:4]],
                    "duration": per_scene * len(chunk) * 0.5,
                    "animation": "slide_up",
                })

        if sentences:
            last = sentences[-1]
            if any(kw in last for kw in ["？", "?", "评论", "关注", "点赞", "转发", "收藏"]):
                ending_text = last[:30]
            else:
                ending_text = f"关注我\n{last[:20]}"
        else:
            ending_text = "关注我\n获取更多 AI 资讯"

        scenes.append({
            "type": "ending",
            "text": ending_text,
            "duration": min(3.0, per_scene),
            "animation": "fade_out",
        })

        plan = {"title": title or "AI 资讯", "theme": "dark_tech", "scenes": scenes}

        # Apply audio timings if available
        if audio_timings:
            _apply_audio_timings(plan, audio_timings)
        else:
            _normalize_durations(plan, total_duration)

        logger.info(f"Using fallback video plan: {len(scenes)} scenes")
        return plan


# ═══════════════════════════════════════════════════════════════
#  Shared utilities
# ═══════════════════════════════════════════════════════════════

def _extract_json(text: str) -> str:
    """Extract JSON object from text that may have markdown fences or surrounding text."""
    # Strip markdown code fences
    if text.startswith("```"):
        first_newline = text.find("\n")
        if first_newline > 0:
            text = text[first_newline + 1:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()

    # Find first { and last }
    json_start = text.find("{")
    json_end = text.rfind("}")
    if json_start >= 0 and json_end > json_start:
        return text[json_start:json_end + 1]
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

    Maps audio segments to plan scenes in order.  Each scene gets its duration
    set to the corresponding audio segment's actual length.
    """
    scenes = plan.get("scenes", [])
    if not scenes or not timings:
        return

    for i in range(min(len(scenes), len(timings))):
        dur = round(timings[i]["end"] - timings[i]["start"], 2)
        if dur > 0:
            scenes[i]["duration"] = dur

    # If there are more scenes than timings, scale remaining proportionally
    if len(scenes) > len(timings):
        remaining_dur = 1.0  # minimal fallback
        for i in range(len(timings), len(scenes)):
            scenes[i]["duration"] = remaining_dur

    # If there are more timings than scenes, extend last scene
    if len(timings) > len(scenes) and scenes:
        extra = sum(
            timings[i]["end"] - timings[i]["start"]
            for i in range(len(scenes), len(timings))
        )
        scenes[-1]["duration"] = round(scenes[-1].get("duration", 2.0) + extra, 2)

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
