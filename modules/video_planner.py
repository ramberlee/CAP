"""Video composition planning module using LLM.

The LLM analyzes a douyin script and generates a structured "composition plan"
that describes the visual style, scene breakdown, and animations for Remotion.
"""

import json
import logging
from typing import Optional
from openai import OpenAI

logger = logging.getLogger(__name__)

# System prompt for video composition planning
VIDEO_PLANNER_SYSTEM_PROMPT = """你是一个专业的短视频导演和文案策划。根据参考文案，重新构思并设计一个"视频构图计划"。

## 角色
你同时是**文案策划**和**视频导演**：先为视频重新创作适合屏幕阅读的文案，再决定视觉风格、场景分解和动画效果。

## 文案创作原则
参考文案是口播用的，你需要重新创作适合屏幕阅读+语音朗读的视频文案：
1. **精炼**：每行控制在一屏可读范围内（中文约10-18字）
2. **一句一屏**：每句话独立成场景，不塞太多信息
3. **适合朗读**：文字顺畅，将作为 TTS 配音脚本
4. **开头抓眼球**：用短促有力的标题
5. **结尾有号召**：引导关注/点赞/转发
6. **时长由内容决定**：不卡固定秒数，内容多就长、少就短，以表达充分为准

## 抖音爆款节奏规则（核心）
1. **黄金3秒**：第一个 scene 必须是高冲击力的 hook/title，用 zoom_in 或 scale_in 动画，时长 2-3 秒。禁止平淡开场。
2. **15秒留人**：每 15 秒必须有一次场景切换（不同 type 或动画），保持视觉新鲜感，防止观众划走。
3. **信息密度递进**：开场短促（2-3s）→ 中段充实（每场景 3-5s）→ 收束简洁（2-3s）。
4. **情绪曲线**：hook（震撼）→ 核心内容（好奇/干货）→ ending（共鸣/行动）。

## 输出格式
输出纯 JSON（不要 markdown 代码块）：

{
  "title": "视频标题（短促有力，作为封面文案）",
  "theme": "dark_tech | light_clean | vibrant | minimal | news",
  "scenes": [
    {
      "type": "hook | title | text_sequence | highlight | bullet_points | ending",
      "text": "显示的文本（单行）",
      "lines": ["逐行动画的文本行（text_sequence 用）"],
      "items": ["列表项（bullet_points 用）"],
      "duration": 3.0,
      "animation": "fade_in | scale_in | slide_up | typewriter | pulse | zoom_in | fade_out"
    }
  ]
}

## 场景类型与默认动画
- **hook**：开场强钩子，大字+冲击力动画。默认 animation=zoom_in，时长 2-3 秒。用于视频第一个 scene，必须有视觉冲击力。
- **title**：开场大字居中。默认 animation=scale_in，时长 2-3 秒
- **text_sequence**：文字逐行滑入，适合叙述性内容。默认 animation=fade_in，每行至少 2 秒
- **highlight**：放大强调文字+光效，适合核心观点。默认 animation=pulse，时长 2.5-3.5 秒
- **bullet_points**：带编号的要点列表。默认 animation=slide_up，每项约 1.5 秒
- **ending**：结尾引导关注。默认 animation=fade_out，时长 2-3 秒

## 主题(theme)
- **dark_tech**：深色背景+蓝色主色+金色强调。科技、AI 内容
- **light_clean**：白色背景+蓝色主色。轻松、生活化内容
- **vibrant**：暗紫背景+橙色主色+金色强调。娱乐、创意内容
- **minimal**：纯黑背景+纯白文字。极简风格
- **news**：浅灰背景+红色强调。新闻资讯

## 动画选择
动画要匹配文案情绪：
- 激昂/震撼 → zoom_in、scale_in
- 平实/叙述 → fade_in、slide_up
- 强调/重点 → pulse
- 结束/告别 → fade_out

## 示例
参考文案："GPT-5 来了！OpenAI 刚刚发布了最新的 GPT-5 模型。推理能力提升了整整 10 倍，而且速度更快、成本更低。这将是改变行业格局的一款产品。"

{
  "title": "GPT-5 重磅发布",
  "theme": "dark_tech",
  "scenes": [
    { "type": "hook", "text": "GPT-5 来了！", "duration": 2.5, "animation": "zoom_in" },
    { "type": "text_sequence", "lines": ["OpenAI 最新力作", "推理能力提升 10 倍"], "duration": 4, "animation": "fade_in" },
    { "type": "bullet_points", "items": ["速度更快", "成本更低", "更智能"], "duration": 4.5, "animation": "slide_up" },
    { "type": "highlight", "text": "改变行业格局", "duration": 3, "animation": "pulse" },
    { "type": "ending", "text": "关注我\n获取更多 AI 资讯", "duration": 3, "animation": "fade_out" }
  ]
}
"""

# User prompt template - send the douyin script as reference material
PLANNER_USER_PROMPT_TEMPLATE = """根据以下参考素材，重新构思适合"文字视频"展示的视频构图计划。

== 参考素材 ==
原标题：{title}
原始口播文案：{script}
标签/关键词：{tags}

== 要求 ==
1. 不要直接复制口播文案，重新创作更精炼的视频文案
2. 每行控制在10-18字，一句一屏；文字要适合朗读（将作为TTS配音脚本）
3. **第一个 scene 必须是 hook 类型**，用最震撼的一句话开场，动画用 zoom_in，时长 2-3 秒
4. 结尾用号召性语句引导关注/评论
5. 时长由内容决定——以表达充分、节奏舒服为准
6. 根据内容选择最合适的主题和动画
7. 场景类型要多样化：至少包含 hook、text_sequence、highlight/bullet_points、ending 四种类型

请输出 JSON 构图计划。"""


class VideoPlanner:
    """Generates video composition plans from douyin scripts using LLM."""

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
        total_duration: float | None = None,
    ) -> Optional[dict]:
        """Generate a video composition plan from a douyin script.

        Args:
            script: The douyin oral script text.
            title: Optional content title.
            tags: Optional list of tags/keywords.
            total_duration: If set, passed to fallback plan for duration estimation.
                           The LLM plan ignores this — scene durations come from
                           per-scene TTS measurements in generator.py.

        Returns:
            Composition plan dict, or None on failure.
        """
        if not self.client or not self.client.api_key:
            logger.warning("MiMo API key not configured, skipping video planning")
            return self._fallback_plan(script, title, total_duration)

        try:
            # Build format kwargs, omitting total_duration when None
            format_kwargs = dict(
                title=title or "无标题",
                script=script[:800],
                tags=", ".join(tags[:5]) if tags else "无",
            )
            user_prompt = PLANNER_USER_PROMPT_TEMPLATE.format(**format_kwargs)

            logger.info("Generating video composition plan via LLM...")
            response = self.client.chat.completions.create(
                model=self.model,
                max_tokens=4096,
                temperature=0.7,
                messages=[
                    {"role": "system", "content": VIDEO_PLANNER_SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
            )

            text = response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"LLM API call failed: {e}")
            return self._fallback_plan(script, title, total_duration)

        text_raw = text  # keep for debugging

        # Strip markdown code fences if present
        try:
            if text.startswith("```"):
                # Handle ```json\n...\n``` format
                first_newline = text.find("\n")
                if first_newline > 0:
                    text = text[first_newline + 1:]
                if text.endswith("```"):
                    text = text[:-3]
                text = text.strip()

            # Try to extract JSON from the response even if there's surrounding text
            # Find the first { and last }
            json_start = text.find("{")
            json_end = text.rfind("}")
            if json_start >= 0 and json_end > json_start:
                text = text[json_start:json_end + 1]
            else:
                # No JSON found in response - LLM probably returned plain text
                logger.warning(f"No JSON found in LLM response (first 200 chars): {text_raw[:200]}")
                return self._fallback_plan(script, title, total_duration)

            # Fix common JSON issues from LLM output
            text = self._fix_json(text)

            if not text.strip():
                logger.warning(f"Empty JSON after extraction (first 200 chars): {text_raw[:200]}")
                return self._fallback_plan(script, title, total_duration)

            plan = json.loads(text)
            self._validate_plan(plan)
            logger.info(
                f"Video plan generated: theme={plan.get('theme')}, "
                f"{len(plan.get('scenes', []))} scenes, "
                f"{sum(s['duration'] for s in plan['scenes']):.1f}s"
            )
            return plan

        except json.JSONDecodeError as e:
            logger.warning(f"LLM returned invalid JSON: {e} | Response: {text_raw[:200]}")
            return self._fallback_plan(script, title, total_duration)
        except Exception as e:
            logger.warning(f"Video planning failed: {e} | Response: {text_raw[:200] if 'text_raw' in dir() else 'N/A'}")
            return self._fallback_plan(script, title, total_duration)

    def _fix_json(self, text: str) -> str:
        """Fix common JSON issues in LLM responses."""
        import re

        # Remove trailing commas before closing braces/brackets
        text = re.sub(r",\s*([}\]])", r"\1", text)

        # Fix unterminated strings: if the last line has odd number of quotes, close it
        lines = text.split('\n')
        if lines:
            last = lines[-1]
            # Count unescaped double quotes in last line
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

        # Close any open arrays/objects
        if in_string:
            text += '"'
        # Remove trailing incomplete key-value (e.g., "key": without value)
        text = re.sub(r',\s*"[^"]*":?\s*$', '', text)
        text = re.sub(r':\s*$', ': null', text)
        text = re.sub(r',\s*$', '', text)
        for _ in range(open_brackets):
            text += ']'
        for _ in range(open_braces):
            text += '}'

        return text

    _VALID_TYPES = {"hook", "title", "text_sequence", "highlight", "bullet_points", "ending"}
    _VALID_ANIMATIONS = {"fade_in", "scale_in", "slide_up", "typewriter", "pulse", "zoom_in", "fade_out"}
    _DEFAULT_ANIMATIONS = {
        "hook": "zoom_in",
        "title": "scale_in",
        "text_sequence": "fade_in",
        "highlight": "pulse",
        "bullet_points": "slide_up",
        "ending": "fade_out",
    }

    def _validate_plan(self, plan: dict) -> None:
        """Validate and fix common issues in the plan."""
        import re
        if "title" not in plan or not plan.get("title"):
            plan["title"] = "AI 资讯"
        plan["title"] = re.sub(r"\[VIDEO:.*?]", "", plan["title"]).strip()
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
            # Validate scene type
            stype = scene.get("type", "")
            if stype not in self._VALID_TYPES:
                scene["type"] = "text_sequence"
            # Ensure first scene is hook or title (golden 3-second rule)
            if scene == plan["scenes"][0] and scene["type"] not in ("hook", "title"):
                scene["type"] = "hook"
                scene["animation"] = "zoom_in"
            # Validate animation
            anim = scene.get("animation", "")
            if anim not in self._VALID_ANIMATIONS:
                scene["animation"] = self._DEFAULT_ANIMATIONS.get(scene["type"], "fade_in")
            # Validate duration
            if "duration" not in scene or scene["duration"] <= 0:
                scene["duration"] = 3.0
            # Strip video placeholders from text fields
            for key in ("text", "lines", "items"):
                if key in scene:
                    if isinstance(scene[key], str):
                        scene[key] = re.sub(r"\[VIDEO:.*?]", "", scene[key]).strip()
                    elif isinstance(scene[key], list):
                        scene[key] = [re.sub(r"\[VIDEO:.*?]", "", t).strip() for t in scene[key]]

    def _normalize_durations(self, plan: dict, target_total: float) -> None:
        """Scale scene durations to match the target total duration exactly.

        This ensures the video length matches the TTS audio duration,
        so audio and video are in sync throughout.
        """
        scenes = plan.get("scenes", [])
        if not scenes:
            return

        current_total = sum(s.get("duration", 3.0) for s in scenes)
        if current_total <= 0:
            return

        # Scale each scene proportionally
        ratio = target_total / current_total
        for scene in scenes:
            scene["duration"] = round(scene["duration"] * ratio, 1)

        # Adjust last scene to absorb rounding error
        adjusted_total = sum(s["duration"] for s in scenes)
        diff = round(target_total - adjusted_total, 1)
        if scenes and abs(diff) > 0.05:
            scenes[-1]["duration"] = round(scenes[-1]["duration"] + diff, 1)
            # Ensure minimum duration
            if scenes[-1]["duration"] < 1.0:
                scenes[-1]["duration"] = 1.0

    @staticmethod
    def get_audio_script(plan: dict) -> str:
        """Extract a TTS audio script from a composition plan.

        Concatenates all scene texts/lines/items in order,
        with natural pauses between scenes. This text is fed
        to TTS to generate the voiceover for the video.
        """
        scenes = plan.get("scenes", [])
        parts = []
        for scene in scenes:
            scene_type = scene.get("type", "")
            if scene_type in ("title", "hook"):
                text = scene.get("text", "")
                if text:
                    parts.append(text + "。")
            elif scene_type == "text_sequence":
                lines = [l for l in scene.get("lines", []) if l]
                if lines:
                    parts.append("，".join(lines) + "。")
            elif scene_type == "highlight":
                text = scene.get("text", "")
                if text:
                    parts.append(text + "！")
            elif scene_type == "bullet_points":
                items = [i for i in scene.get("items", []) if i]
                if items:
                    parts.append("，".join(items) + "。")
            elif scene_type == "ending":
                text = scene.get("text", "")
                if text:
                    parts.append(text.replace("\n", "。"))

        return "".join(parts)

    def _fallback_plan(self, script: str, title: str, total_duration: float | None = None) -> dict:
        """Generate a simple fallback plan when LLM fails.

        If total_duration is not set, estimates from script length.
        Uses diverse scene types: hook → text_sequence → highlight → ending.
        """
        import re
        if total_duration is None:
            # Estimate: ~4 chars/sec for Chinese speech, with some padding
            char_count = len(script)
            total_duration = max(15.0, min(60.0, char_count / 4.0 + 3.0))

        # Split script into sentences
        sentences = re.split(r"[。！？!?]", script)
        sentences = [s.strip() for s in sentences if s.strip()]

        # Distribute time
        n_scenes = min(len(sentences), 6)
        per_scene = total_duration / max(n_scenes + 1, 3)

        # Scene 1: hook — use the first sentence or title
        hook_text = sentences[0][:18] if sentences else (title or "AI 资讯")
        scenes = [
            {
                "type": "hook",
                "text": hook_text,
                "duration": min(3.0, per_scene * 1.2),
                "animation": "zoom_in",
            }
        ]

        # Middle scenes: alternate between text_sequence and highlight/bullet_points
        remaining = sentences[1:] if len(sentences) > 1 else sentences
        chunk_size = max(1, len(remaining) // max(n_scenes - 1, 1))
        scene_idx = 0
        for i in range(0, len(remaining), chunk_size):
            chunk = remaining[i : i + chunk_size]
            scene_idx += 1

            # Every 3rd middle scene uses highlight for variety
            if scene_idx % 3 == 0 and chunk:
                scenes.append({
                    "type": "highlight",
                    "text": chunk[0][:18],
                    "duration": min(3.0, per_scene),
                    "animation": "pulse",
                })
            elif len(chunk) >= 3:
                # Use bullet_points if we have enough items
                scenes.append({
                    "type": "bullet_points",
                    "items": [c[:15] for c in chunk[:4]],
                    "duration": per_scene * len(chunk) * 0.5,
                    "animation": "slide_up",
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
                    "type": "text_sequence",
                    "lines": chunk,
                    "duration": per_scene * len(chunk) * 0.6,
                    "animation": "fade_in",
                })

        # Ending: extract a CTA-like ending from the last sentence or use dynamic text
        if sentences:
            last = sentences[-1]
            # If last sentence looks like a question/CTA, use it
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

        plan = {
            "title": title or "AI 资讯",
            "theme": "dark_tech",
            "scenes": scenes,
        }
        self._normalize_durations(plan, total_duration)
        logger.info(f"Using fallback plan: {len(scenes)} scenes (LLM unavailable)")
        return plan
