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
VIDEO_PLANNER_SYSTEM_PROMPT = """你是一个专业的短视频导演和文案策划。你的任务是根据一段参考文案，重新构思并设计一个"视频构图计划"。

## 你的角色
你是双重角色：**文案策划** + **视频导演**。首先，你要为这个视频重新创作一套适合"文字视频"展示的文案（不是直接复制参考文案，而是重新构思）；然后，你要决定视觉风格、场景分解、动画效果。

## 核心要求：重新构思视频文案
参考文案是口播用的，不适合直接作为视频字幕。你要重新创作一套适合屏幕阅读的视频文案。同时，**每个场景的文字也会成为配音脚本**，所以文字要朗朗上口、适合朗读。原则是：
1. **更精炼**：每行不超过15个字，方便快速阅读
2. **更有视觉节奏**：一句一屏，信息分块
3. **更适合屏幕阅读**：去掉口语化表达，保留核心信息点
4. **每句话独立成场景**：不要在一个场景里塞太多文字
5. **适合朗读**：文字要顺畅，适合 TTS 语音合成朗读
6. **开头有吸引力的标题**，结尾有号召性语句
7. **总时长控制在 25-30 秒**：所有 scene.duration 之和应在 25 到 30 秒之间

## 输出格式
你必须输出纯 JSON（不要用 markdown 代码块包裹），格式如下：

{
  "title": "视频标题（吸引眼球的短标题，会作为视频封面文案）",
  "theme": "dark_tech | light_clean | vibrant | minimal | news",
  "scenes": [
    {
      "type": "title | text_sequence | highlight | image_text | bullet_points | ending",
      "text": "显示的文本（单行，你自己重新创作的）",
      "lines": ["逐行动画的文本行（text_sequence 类型用，每行你自己创作）"],
      "items": ["列表项（bullet_points 类型用，每项你自己创作）"],
      "duration": 3.0,
      "animation": "fade_in | scale_in | slide_up | typewriter | pulse | zoom_in | fade_out"
    }
  ]
}

## 场景类型说明
- **title**: 开场标题，大字居中，适合展示视频主题
- **text_sequence**: 文字逐行动画，每行从左侧滑入，适合叙述性内容
- **highlight**: 高亮强调，放大的强调文字带光效，适合核心观点
- **image_text**: 上半图片+下半文字，适合需要配图的内容
- **bullet_points**: 带编号的要点列表，适合列举多个观点
- **ending**: 结尾引导关注，含圆形容器+关注按钮

## 主题(theme)说明
- **dark_tech**: 深色背景+蓝色主色+金色强调。适合科技、AI相关内容
- **light_clean**: 白色背景+蓝色主色。适合轻松、生活化内容
- **vibrant**: 暗紫背景+橙色主色+金色强调。适合娱乐、创意内容
- **minimal**: 纯黑背景+纯白文字。适合极简风格
- **news**: 浅灰背景+红色强调。适合新闻资讯

## 设计原则
1. 视频总时长约 15-30 秒（所有 scene.duration 之和）
2. **每个场景的文字都是你重新创作的**——更短、更精炼、更适合屏幕阅读
3. 开场 title 2-3 秒，用吸引眼球的标题文案
4. 结尾 ending 2-3 秒，用号召性语句（关注/点赞/转发）
5. 每段话至少 3-4 秒让观众有时间阅读
6. 核心观点用 highlight 突出，配合 pulse 动画
7. 如果信息中有数据、对比、列表，用 bullet_points
8. 动画选择要与文案情绪匹配：激昂用 zoom_in/scale_in，平实用 fade_in/slide_up
9. 开头标题要抓人眼球，结尾要有行动号召

## 文案创作示例
参考文案（口播用）："GPT-5 来了！OpenAI 刚刚发布了最新的 GPT-5 模型。推理能力提升了整整 10 倍，而且速度更快、成本更低。这将是改变行业格局的一款产品。"
重新构思的视频文案（适合屏幕阅读）：
- 标题："GPT-5 重磅发布"（短促有力）
- 场景1：title → "GPT-5 来了！"（3行以内大字）
- 场景2：text_sequence → ["OpenAI 最新力作", "推理能力提升 10 倍"]
- 场景3：bullet_points → ["速度更快", "成本更低", "更智能"]
- 场景4：highlight → "改变行业格局"
- 场景5：ending → "关注我，获取更多 AI 资讯"

## 输出示例
{
  "title": "GPT-5 重磅发布",
  "theme": "dark_tech",
  "scenes": [
    { "type": "title", "text": "GPT-5 来了！", "duration": 2.5, "animation": "scale_in" },
    { "type": "text_sequence", "lines": ["OpenAI 最新力作", "推理能力提升 10 倍"], "duration": 4, "animation": "fade_in" },
    { "type": "bullet_points", "items": ["速度更快", "成本更低", "更智能"], "duration": 4.5, "animation": "slide_up" },
    { "type": "highlight", "text": "改变行业格局", "duration": 3, "animation": "pulse" },
    { "type": "ending", "text": "关注我\n获取更多 AI 资讯", "duration": 3, "animation": "fade_out" }
  ]
}
"""

# User prompt template - send the douyin script as reference material
PLANNER_USER_PROMPT_TEMPLATE = """请根据以下参考素材，重新构思一套适合"文字视频"展示的视频构图计划。

== 参考素材 ==
原标题：{title}
原始口播文案：{script}
标签/关键词：{tags}

== 要求 ==
1. 不要直接复制上面的口播文案作为场景文字
2. 重新创作一套更精炼、更适合屏幕阅读的视频文案
3. 每行不超过15个字，一句话一屏；文字要适合朗读（将作为TTS配音脚本）
4. 开头有吸引眼球的标题，结尾有号召性语句
5. 总时长控制在 25-30 秒
6. 根据文案内容选择最合适的主题和动画

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
            total_duration: If set, normalize scene durations to this total.
                           If None, the LLM decides the duration (~25-30s recommended).

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
                max_tokens=2048,
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
            if total_duration is not None:
                self._normalize_durations(plan, total_duration)
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

        return '\n'.join(lines)

    def _validate_plan(self, plan: dict) -> None:
        """Validate and fix common issues in the plan."""
        import re
        if "title" not in plan or not plan.get("title"):
            plan["title"] = "AI 资讯"
        # Strip any video placeholders from title
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
        # Ensure required fields per scene type, and strip placeholder text
        for scene in plan["scenes"]:
            if "duration" not in scene or scene["duration"] <= 0:
                scene["duration"] = 3.0
            if "type" not in scene:
                scene["type"] = "text_sequence"
            # Strip video placeholders from any text field
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
            if scene.get("type") == "title":
                # Title is a visual element, read it with emphasis
                text = scene.get("text", "")
                if text:
                    parts.append(text + "。")
            elif scene.get("type") == "text_sequence":
                lines = scene.get("lines", [])
                for line in lines:
                    if line:
                        parts.append(line + "，")
                # Replace last comma with period
                if parts:
                    parts[-1] = parts[-1].rstrip("，") + "。"
            elif scene.get("type") == "highlight":
                text = scene.get("text", "")
                if text:
                    parts.append(text + "！")
            elif scene.get("type") == "bullet_points":
                items = scene.get("items", [])
                for item in items:
                    if item:
                        parts.append(item + "，")
                if parts:
                    parts[-1] = parts[-1].rstrip("，") + "。"
            elif scene.get("type") == "image_text":
                text = scene.get("text", "")
                if text:
                    # Skip hashtag lines for TTS
                    for line in text.split("\n"):
                        if not line.startswith("#"):
                            parts.append(line + "，")
                if parts:
                    parts[-1] = parts[-1].rstrip("，") + "。"
            elif scene.get("type") == "ending":
                text = scene.get("text", "")
                if text:
                    parts.append(text.replace("\n", "。"))

        return "".join(parts)

    def _fallback_plan(self, script: str, title: str, total_duration: float | None = None) -> dict:
        """Generate a simple fallback plan when LLM fails.
        
        If total_duration is not set, uses a default of 25 seconds.
        """
        if total_duration is None:
            total_duration = 25.0
        import re
        # Split script into sentences for a basic text_sequence
        import re
        sentences = re.split(r"[。！？!?]", script)
        sentences = [s.strip() for s in sentences if s.strip()]

        # Distribute time
        n_scenes = min(len(sentences), 6)
        per_scene = total_duration / max(n_scenes + 1, 3)

        scenes = [
            {
                "type": "title",
                "text": title or "AI 资讯",
                "duration": min(3.0, per_scene * 1.2),
                "animation": "scale_in",
            }
        ]

        # Group sentences into chunks for text_sequence scenes
        chunk_size = max(1, len(sentences) // max(n_scenes - 1, 1))
        for i in range(0, len(sentences), chunk_size):
            chunk = sentences[i : i + chunk_size]
            if len(chunk) == 1:
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

        scenes.append({
            "type": "ending",
            "text": "关注我\n获取更多 AI 资讯",
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
