"""AI content generation module using MiMo / Ark API (OpenAI compatible).

Dependencies are injected via constructor. Use ContentGenerator.from_config()
for the default production wiring (called from main.py).

The former imager.py, vgen.py, and tts.py facades have been absorbed into
this module — provider dispatch is handled by ProviderFactory
(modules/providers/factory.py). Audio utility functions live in
modules._audio_utils.
"""

import json
import logging
import re
import shutil
from pathlib import Path
from typing import Optional
from openai import OpenAI
from modules.database import Database
from modules.content_store import ContentStore
from modules.config_model import AppConfig
from modules._audio_utils import (
    clean_script,
    concat_wav_files,
    get_audio_duration,
    split_audio,
    trim_audio,
)
from modules.providers import ImageProvider, VideoProvider, SpeechProvider
from modules.providers.factory import ProviderFactory
from modules.providers._subtitle_builder import SubtitleConfig, burn_subtitles
from modules.providers._ffmpeg_utils import (
    concat_videos as _concat_videos,
    merge_audio as _merge_audio,
)
from modules.video_planner import AudioPlanner, VideoPlanner

logger = logging.getLogger(__name__)

PLATFORMS = ["xiaohongshu", "wechat", "douyin"]
IMAGE_PLACEHOLDER_RE = re.compile(r"\[IMAGE:(.*?)]")
VIDEO_PLACEHOLDER_RE = re.compile(r"\[VIDEO:(.*?)]")

CATEGORY_SYSTEM_PROMPTS = {
    "dao": (
        "你是一个AI领域的内容创作专家。"
        "你正在为一个AI领域的内容账号创作「道」系列内容，账号定位是：「AI时代必备心法。在这里，看懂AI的道与术。」"
        "「道」系列关注社会趋势、人性洞察、时代变迁，用AI思维提供独特的观察视角。"
        "内容要求：从宏观视角解读社会热点，提供认知升级的洞察，而非就事论事。"
        "核心目标：让观众看完觉得「原来这事还能这么看」——提供反常识的认知升级。"
    ),
    "shu": (
        "你是一个AI领域的内容创作专家。"
        "你正在为一个AI领域的内容账号创作「术」系列内容，账号定位是：「AI时代必备心法。在这里，看懂AI的道与术。」"
        "「术」系列关注AI技术本身，解读技术原理、应用场景、实操方法。"
        "内容要求：有具体的技术细节、工具名称、使用方法，提供实操价值，而非泛泛而谈。"
        "核心目标：让观众看完就能用上——提供可复现的实用教程。"
    ),
}


# ── Multi-step generation prompts ──
# Each step focuses on one part of the content, building on the previous step.

STEP_ANGLE_PROMPT = """你是一个AI领域的内容创作专家。

热点话题：{topic}
类别：{category_name}

## 你的任务
为这个话题确定内容创作的「切入点」。不要直接写完整脚本，先回答以下3个问题：

1. **核心论点**：针对这个话题，你的核心观点是什么？必须反常识、有认知冲击，不能是大众都知道的结论。
{category_angle_extra}

2. **情绪基调**：这段口播应该营造什么情绪氛围？（如：震撼/反讽/好奇/深思/紧迫等）

3. **目标感受**：你希望观众看完后产生什么感受或行动？（如：恍然大悟/想去试试/想转发讨论等）

## 输出格式
```json
{{
  "core_argument": "一句话说清楚核心论点",
  "emotional_tone": "情绪基调（2-4字）",
  "target_feeling": "目标感受（一句话）",
  "brief_summary": "用3句话概括整个脚本的脉络：钩子切入点 + 价值段展开方向 + 收尾落点"
}}
```"""

STEP_HOOK_PROMPT = """你是一个抖音短视频脚本创作者。

热点话题：{topic}
核心论点：{core_argument}
情绪基调：{emotional_tone}

## 你的任务
只写口播的「钩子」——也就是前3秒的抓人句。不要写后面的价值段和收尾。

## 钩子要求
1. 一句话，必须能在3秒内说完（20-40字）
2. 制造认知冲突/悬念/反常识，让观众停不下来
3. 必须和你的核心论点直接相关，不能为了hook而hook
4. 禁止用"大家好""今天我们来聊""你知道吗"等平淡开场
5. 语气要口语化，像面对面聊天

## 输出格式
```json
{{
  "hook": "一句话钩子"
}}
```"""

STEP_BODY_DAO_PROMPT = """你是一个抖音短视频脚本创作者。

热点话题：{topic}
核心论点：{core_argument}
情绪基调：{emotional_tone}
钩子：{hook}

## 你的任务
只写口播的「价值段」——也就是核心内容部分。这是整个视频的主体，提供认知升级。

## 内容深度要求
- **必须包含至少 3 个独立论点/案例/视角**，每个论点要展开2-3句话，不能只有一个观点翻来覆去说
- **展开方式**：每个论点用具体的案例、数据、跨领域类比、或逻辑推理来支撑
- **信息密度**：整个价值段建议写 400-800 字，内容要充分展开
- **结构节奏**：每个论点之间用"留人点"过渡（反问句、数据冲击、悬念过渡等）
- **金句**：至少 1 句能让人记住的话

## 反面教材
- ❌ 只说"AI时代来了，我们要拥抱"——这是废话
- ❌ 只罗列新闻事实，没有自己的角度和判断
- ❌ 贩卖焦虑而不给出建设性视角
- ❌ 空洞的鸡汤式结论
- ❌ 内容太短，论点没展开就结束了

## 输出格式
```json
{{
  "body": "价值段全文。至少3个独立论点，每个论点2-3句展开。口语化，有情绪。不用加【价值】前缀。"
}}
```"""

STEP_BODY_SHU_PROMPT = """你是一个抖音短视频脚本创作者。

热点话题：{topic}
核心论点：{core_argument}
情绪基调：{emotional_tone}
钩子：{hook}

## 你的任务
只写口播的「价值段」——也就是核心教程内容。这是整个视频的主体，提供可复现的实操方法。

## 内容深度要求（必须全部覆盖）
1. **具体工具/技术名称**：明确告诉观众用什么工具
2. **分步骤操作**：按"第一步、第二步、第三步"的结构组织，每一步清晰可执行
3. **效果展示**：用具体数据/对比说明效果
4. **避坑提示**：至少1个常见坑或注意事项
5. **适用场景**：说明适合什么场景

## 反面教材
- ❌ 只说"XX 工具很强大"但不展示怎么用
- ❌ 泛泛而谈"AI 能提高效率"而没有具体步骤
- ❌ 理想化的"完美方案"而没有踩坑提醒
- ❌ 不接地气的专业术语堆砌

## 输出格式
```json
{{
  "body": "价值段全文。口语化，分步骤讲解。不用加【价值】前缀。"
}}
```"""

STEP_ENDING_PROMPT = """你是一个抖音短视频脚本创作者。

热点话题：{topic}
核心论点：{core_argument}
情绪基调：{emotional_tone}
钩子：{hook}
价值段内容：{body}

## 你的任务
完成口播的最后两部分：

### 1. 收尾句
一句话留下思考空间或引导互动。必须包含具体的互动话术。
{category_ending_style}

### 2. 视频标题
15-20字，带话题感，适合搜索推荐。突出核心观点。
{category_title_style}

### 3. 话题标签
3-5个热门话题标签，必须包含 #AI 相关标签。

### 4. 视频描述（description）
20-50字短视频简介，用于抖音发布时的文案区。精简有力，包含核心观点，不要重复标题。

## 输出格式
```json
{{
  "title": "视频标题（15-20字）",
  "description": "20-50字短视频简介",
  "ending": "收尾句（包含互动话术）",
  "tags": ["#话题1", "#话题2", "#话题3", "#AI"]
}}
```"""


def get_enabled_platforms(config: AppConfig) -> list[str]:
    """Return the list of platforms that have enabled: true in config.platforms."""
    enabled = []
    for name in PLATFORMS:
        plat = getattr(config.platforms, name, None)
        if plat and plat.enabled:
            enabled.append(name)
    return enabled


# ══════════════════════════════════════════════════════════════════════════════

class ContentGenerator:
    """Generate platform content for hot topics.

    Dependencies are injected via constructor. Use `from_config()` to wire up
    from config.yaml — that's the only place provider-selection logic lives.
    """

    def __init__(
        self,
        db: Database,
        config: AppConfig,
        *,
        # Injected dependencies — testable via fakes / mocks
        client: OpenAI | None = None,
        image_provider: ImageProvider | None = None,
        video_provider: VideoProvider | None = None,
        speech_provider: SpeechProvider | None = None,
        store: ContentStore | None = None,
        # Remotion-specific planners (optional, created by from_config)
        audio_planner: AudioPlanner | None = None,
        video_planner: VideoPlanner | None = None,
        model: str | None = None,
    ):
        self.db = db
        self.config = config
        self.gen_config = config.generation

        # ── Injected dependencies ──
        self.client = client
        self.model = model
        self.image_provider = image_provider
        self.video_provider = video_provider
        self.speech_provider = speech_provider
        self.store = store or ContentStore(
            output_dir=config.output_dir,
            media_dir=config.dashscope.media_dir,
        )
        self._audio_planner = audio_planner
        self._video_planner = video_planner

        # ── Config-derived values (typed access) ──
        self.text_provider = config.generation.text_provider
        self.auto_image = config.generation.auto_image
        self.auto_video = config.generation.auto_video

        # Video provider metadata (used by _process_videos)
        # Reads from the correct config section based on active provider
        self._video_provider_name = config.generation.video_provider
        self._video_model, self._video_size, self._video_max_duration = self._resolve_video_config(config)
        self._video_subtitles = config.generation.video_subtitles
        self._sub_config = SubtitleConfig.from_config(config)

        self._templates = {}

    @staticmethod
    def _resolve_video_config(config: AppConfig) -> tuple[str, str, int]:
        """Resolve video model, size, and max duration from the active provider's config.

        Delegates to ProviderFactory.resolve_video_config().
        """
        return ProviderFactory(config).resolve_video_config()

    @classmethod
    def from_config(cls, db: Database, config: AppConfig) -> "ContentGenerator":
        """Create a fully-wired ContentGenerator from a typed AppConfig.

        This is the production entry-point (used by main.py). It uses
        ProviderFactory to select providers and resolve config.
        """
        factory = ProviderFactory(config)

        # ── LLM client + model ──
        client, model = factory.create_llm_client()

        # ── Providers ──
        image_provider = factory.create_image_provider() if config.generation.auto_image else None
        video_provider = factory.create_video_provider() if config.generation.auto_video else None
        speech_provider = factory.create_speech_provider() if config.generation.auto_video else None

        store = ContentStore(
            output_dir=config.output_dir,
            media_dir=config.dashscope.media_dir,
        )

        # ── Remotion-specific planners ──
        audio_planner = None
        video_planner = None
        if config.generation.video_provider == "remotion" and config.generation.auto_video:
            audio_planner = AudioPlanner(config)
            video_planner = VideoPlanner(config)

        return cls(
            db, config,
            client=client,
            model=model,
            image_provider=image_provider,
            video_provider=video_provider,
            speech_provider=speech_provider,
            store=store,
            audio_planner=audio_planner,
            video_planner=video_planner,
        )

    # ──────────────────────────────────────────────────────────────────────────
    # Template loading
    # ──────────────────────────────────────────────────────────────────────────

    def _load_template(self, platform: str, category: str = "dao") -> str:
        cache_key = f"{platform}_{category}"
        if cache_key not in self._templates:
            category_path = Path(f"templates/{platform}_{category}.md")
            generic_path = Path(f"templates/{platform}.md")

            if category_path.exists():
                self._templates[cache_key] = category_path.read_text(encoding="utf-8")
            elif generic_path.exists():
                self._templates[cache_key] = generic_path.read_text(encoding="utf-8")
            else:
                raise FileNotFoundError(f"Template not found: {category_path} or {generic_path}")
        return self._templates[cache_key]

    # ──────────────────────────────────────────────────────────────────────────
    # Tag utilities
    # ──────────────────────────────────────────────────────────────────────────

    def _ensure_tags(self, result: dict, category: str) -> None:
        """Ensure result has valid tags. Auto-generate from title if empty."""
        tags = result.get("tags", [])
        if tags:
            result["tags"] = tags[:5]
            return

        title = result.get("title", "")
        fallback_tags = ["#AI"]
        if category == "dao":
            fallback_tags.append("#AI时代")
        else:
            fallback_tags.append("#AI技术")

        chunks = re.split(r"[，。！？、：；“”‘’（）\s]+", title)
        stopwords = {"的", "了", "是", "在", "和", "有", "不", "这", "那", "人", "我", "你", "他", "她", "它", "们", "被", "把", "将", "从", "到", "又", "就", "也", "都", "而", "且", "但", "或", "如果"}
        for chunk in chunks:
            chunk = chunk.strip()
            if len(chunk) >= 2 and chunk not in stopwords:
                tag = f"#{chunk}"
                if tag not in fallback_tags and len(fallback_tags) < 5:
                    fallback_tags.append(tag)

        while len(fallback_tags) < 3:
            fallback_tags.append(f"#热点{len(fallback_tags)}")

        result["tags"] = fallback_tags[:5]
        logger.info(f"Auto-generated tags: {result['tags']}")

    # ──────────────────────────────────────────────────────────────────────────
    # Content validation & repair
    # ──────────────────────────────────────────────────────────────────────────

    def _validate_and_repair(self, result: dict, platform: str, category: str) -> dict:
        """Generic platform content validation and repair dispatch."""
        from modules.platforms import get_validator, get_repairer

        validator = get_validator(platform)
        if not validator:
            return result

        if platform == "douyin":
            validator(result, category=category)
            return result

        platform_cfg = getattr(self.config.platforms, platform, None)
        if not platform_cfg or not platform_cfg.validate_content:
            return result

        repairer = get_repairer(platform)
        max_repair = platform_cfg.max_repair

        for attempt in range(max_repair + 1):
            issues = validator(result, category=category, client=self.client, model=self.model)
            if not issues:
                break
            if attempt < max_repair and repairer:
                logger.info(f"[{platform}质量校验] 第 {attempt+1} 次修复...")
                repaired = repairer(
                    result, issues, category=category,
                    client=self.client, model=self.model,
                    max_tokens=self.gen_config.max_tokens,
                )
                if repaired:
                    result = repaired
                else:
                    logger.warning(f"[{platform}质量校验] 修复失败，使用当前版本")
                    break
            else:
                logger.warning(f"[{platform}质量校验] 已达最大修复次数 ({max_repair})，使用当前版本")

        return result

    # ──────────────────────────────────────────────────────────────────────────
    # LLM content generation (single-pass, for non-douyin platforms)
    # ──────────────────────────────────────────────────────────────────────────

    def _generate_for_platform(self, topic: str, platform: str, category: str = "dao") -> Optional[dict]:
        """Generate content for a specific platform.

        For douyin, uses multi-step generation (angle → hook → body → ending).
        For other platforms, uses the single-pass template approach.
        """
        if platform == "douyin":
            result = self._generate_douyin_multi_step(topic, category)
            if result:
                result = self._validate_and_repair(result, platform, category)
            return result

        # ── Non-douyin platforms: single-pass template approach ──
        template = self._load_template(platform, category)
        prompt = template.replace("{topic}", topic)

        system_prompt = CATEGORY_SYSTEM_PROMPTS.get(category, CATEGORY_SYSTEM_PROMPTS["dao"])
        logger.info(f"Generating {platform}/{category} content for: {topic[:50]}...")

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                max_tokens=self.gen_config.max_tokens,
                temperature=self.gen_config.temperature,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt},
                ],
            )

            text = response.choices[0].message.content

            json_start = text.find("{")
            json_end = text.rfind("}") + 1
            if json_start == -1 or json_end == 0:
                logger.error(f"No JSON found in response for {platform}")
                return None

            result = json.loads(text[json_start:json_end])
            logger.info(f"Generated {platform} content: {result.get('title', 'N/A')[:30]}")

            if not result.get("tags"):
                self._ensure_tags(result, category)

            result = self._validate_and_repair(result, platform, category)

            return result

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON for {platform}: {e}")
            return None
        except Exception as e:
            logger.error(f"Generation failed for {platform}: {e}")
            return None

    # ──────────────────────────────────────────────────────────────────────────
    # Multi-step generation for Douyin (angle → hook → body → ending)
    # ──────────────────────────────────────────────────────────────────────────

    def _llm_json(self, system_prompt: str, user_prompt: str, max_tokens: int | None = None) -> dict | None:
        """Call LLM and parse JSON response. Returns parsed dict or None."""
        if max_tokens is None:
            max_tokens = self.gen_config.max_tokens
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                max_tokens=max_tokens,
                temperature=self.gen_config.temperature,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
            )
            text = response.choices[0].message.content

            # Strip markdown code fences (```json ... ``` or ``` ... ```)
            text = text.strip()
            if text.startswith("```"):
                first_nl = text.find("\n")
                text = text[first_nl + 1:] if first_nl >= 0 else text[3:]
            if text.endswith("```"):
                text = text[:-3]
            text = text.strip()

            json_start = text.find("{")
            json_end = text.rfind("}") + 1
            if json_start == -1 or json_end == 0:
                logger.error(f"No JSON found in LLM response. "
                             f"Response ({len(text)} chars): {text[:500]}")
                return None
            return json.loads(text[json_start:json_end])
        except (json.JSONDecodeError, Exception) as e:
            logger.error(f"LLM JSON call failed: {e}")
            return None

    def _generate_douyin_multi_step(self, topic: str, category: str = "dao") -> dict | None:
        """Multi-step content generation for Douyin.

        Steps:
        1. Angle — determine core argument, emotional tone, target feeling
        2. Hook — write the 3-second hook sentence
        3. Body — expand the value section (dao: ≥3 points; shu: step-by-step)
        4. Ending — write ending, title, description, tags
        """
        category_name = "「道」认知提升" if category == "dao" else "「术」实用教程"
        system_prompt = CATEGORY_SYSTEM_PROMPTS.get(category, CATEGORY_SYSTEM_PROMPTS["dao"])

        # ── Step 1: Angle ──
        logger.info(f"[多步生成-1/4] 定调: {topic[:40]}...")
        angle_extra = (
            "2. 至少给出 3 个可能的切入点方向，选择最有冲击力的那个"
            if category == "dao"
            else "2. 确定一个具体的工具/技术作为教程主角"
        )
        angle_prompt = STEP_ANGLE_PROMPT.format(
            topic=topic, category_name=category_name,
            category_angle_extra=angle_extra,
        )
        angle_result = self._llm_json(system_prompt, angle_prompt, max_tokens=self.gen_config.max_tokens)
        if not angle_result:
            logger.warning("Step 1 (angle) failed, falling back to single-pass")
            return self._generate_douyin_single_pass_fallback(topic, category)

        core_argument = angle_result.get("core_argument", "")
        emotional_tone = angle_result.get("emotional_tone", "好奇")
        logger.info(f"  → 论点: {core_argument[:60]}... | 基调: {emotional_tone}")

        # ── Step 2: Hook ──
        logger.info("[多步生成-2/4] 写钩子...")
        hook_prompt = STEP_HOOK_PROMPT.format(
            topic=topic, core_argument=core_argument, emotional_tone=emotional_tone,
        )
        hook_result = self._llm_json(system_prompt, hook_prompt, max_tokens=self.gen_config.max_tokens)
        if not hook_result:
            logger.warning("Step 2 (hook) failed, falling back to single-pass")
            return self._generate_douyin_single_pass_fallback(topic, category)

        hook = hook_result.get("hook", "").strip()
        logger.info(f"  → 钩子: {hook[:50]}...")

        # ── Step 3: Body ──
        logger.info("[多步生成-3/4] 扩展正文...")
        body_template = STEP_BODY_DAO_PROMPT if category == "dao" else STEP_BODY_SHU_PROMPT
        body_prompt = body_template.format(
            topic=topic, core_argument=core_argument,
            emotional_tone=emotional_tone, hook=hook,
        )
        body_result = self._llm_json(system_prompt, body_prompt, max_tokens=self.gen_config.max_tokens)
        if not body_result:
            logger.warning("Step 3 (body) failed, falling back to single-pass")
            return self._generate_douyin_single_pass_fallback(topic, category)

        body_text = body_result.get("body", "").strip()
        logger.info(f"  → 正文: {len(body_text)}字")

        # ── Step 4: Ending ──
        logger.info("[多步生成-4/4] 收尾...")
        ending_style = (
            "道系列适合：反思型/选择型/讨论型互动话术"
            if category == "dao"
            else "术系列适合：行动型/收藏型/挑战型互动话术"
        )
        title_style = (
            "道系列：体现AI洞察和认知角度，带话题感"
            if category == "dao"
            else "术系列：突出技术干货和效果数字"
        )
        ending_prompt = STEP_ENDING_PROMPT.format(
            topic=topic, core_argument=core_argument,
            emotional_tone=emotional_tone, hook=hook,
            body=body_text,
            category_ending_style=ending_style,
            category_title_style=title_style,
        )
        ending_result = self._llm_json(system_prompt, ending_prompt, max_tokens=self.gen_config.max_tokens)
        if not ending_result:
            logger.warning("Step 4 (ending) failed, using fallback ending")
            ending_result = {
                "title": topic[:18],
                "description": core_argument[:40],
                "ending": "你觉得呢？评论区告诉我。",
                "tags": ["#AI", "#人工智能", "#认知升级"],
            }

        title = ending_result.get("title", topic[:18])
        description = ending_result.get("description", "")
        ending = ending_result.get("ending", "你觉得呢？评论区告诉我。")
        tags = ending_result.get("tags") or []
        if not tags:
            tag_holder = {"title": title, "tags": []}
            self._ensure_tags(tag_holder, category)
            tags = tag_holder.get("tags", [])

        # ── Assemble final script ──
        script = f"【钩子】{hook}\n\n---\n\n【价值】{body_text}\n\n---\n\n【收尾】{ending}"
        result = {
            "title": title,
            "description": description,
            "script": script,
            "tags": tags,
        }

        logger.info(f"多步生成完成: {title[:30]} | {len(script)}字")
        return result

    def _generate_douyin_single_pass_fallback(self, topic: str, category: str = "dao") -> dict | None:
        """Fallback: use the template-based single-pass approach for douyin."""
        logger.info("Using single-pass fallback for douyin...")
        template = self._load_template("douyin", category)
        prompt = template.replace("{topic}", topic)
        system_prompt = CATEGORY_SYSTEM_PROMPTS.get(category, CATEGORY_SYSTEM_PROMPTS["dao"])

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                max_tokens=self.gen_config.max_tokens,
                temperature=self.gen_config.temperature,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt},
                ],
            )
            text = response.choices[0].message.content
            json_start = text.find("{")
            json_end = text.rfind("}") + 1
            if json_start == -1 or json_end == 0:
                return None
            result = json.loads(text[json_start:json_end])
            if not result.get("tags"):
                self._ensure_tags(result, category)
            return result
        except Exception as e:
            logger.error(f"Single-pass fallback failed: {e}")
            return None

    # ──────────────────────────────────────────────────────────────────────────
    # Image processing
    # ──────────────────────────────────────────────────────────────────────────

    def _process_images(self, body: str, content_id: int, platform: str) -> tuple[str, list[str]]:
        """Replace [IMAGE:description] placeholders with generated images.

        Returns (processed_body, list_of_local_image_paths).
        """
        if not self.image_provider:
            placeholder_count = len(list(IMAGE_PLACEHOLDER_RE.finditer(body)))
            if placeholder_count > 0:
                logger.info(f"auto_image 未启用，已移除 {placeholder_count} 个 [IMAGE:...] 占位符")
            return IMAGE_PLACEHOLDER_RE.sub("", body), []

        placeholders = list(IMAGE_PLACEHOLDER_RE.finditer(body))
        if not placeholders:
            logger.info("正文中无 [IMAGE:...] 占位符，跳过配图")
            return body, []

        output_media = Path("output") / platform / "media"
        output_media.mkdir(parents=True, exist_ok=True)

        media_urls = []
        processed = body

        for i, match in enumerate(placeholders):
            desc = match.group(1).strip()
            filename = f"content_{content_id}_{i+1}.png"
            logger.info(f"Generating image {i+1}/{len(placeholders)}: {desc[:50]}...")

            image_path = self.image_provider.generate(desc, filename)
            if image_path:
                src = Path(image_path)
                dst = output_media / src.name
                shutil.copy2(src, dst)

                rel_path = f"media/{src.name}"
                processed = processed.replace(match.group(0), f"\n\n![配图]({rel_path})\n", 1)
                media_urls.append(str(dst))
                logger.info(f"图片生成成功 [{i+1}/{len(placeholders)}]: {dst}")
            else:
                processed = processed.replace(match.group(0), "", 1)
                logger.warning(f"图片生成失败 [{i+1}/{len(placeholders)}]: {desc[:50]}...，已移除占位符")

        total = len(placeholders)
        success = len(media_urls)
        failed = total - success
        logger.info(f"配图处理完成: 成功 {success}/{total}，失败 {failed}/{total}")
        return processed, media_urls

    # ──────────────────────────────────────────────────────────────────────────
    # Voice prompt generation
    # ──────────────────────────────────────────────────────────────────────────

    def _generate_voice_prompt(self, script_text: str, category: str = "dao") -> str | None:
        """Generate a TTS voice prompt dynamically based on script content."""
        system_prompt = (
            "你是一个语音导演。根据下面的口播文案，生成一句简短的 TTS 语音指令（20字以内），"
            "告诉语音合成系统应该用什么语气、节奏、情绪来朗读。\n\n"
            "要求：\n"
            "1. 只输出指令本身，不要解释\n"
            "2. 指令要具体，如：'用激动、快节奏的语气朗读，像科技新闻主播'\n"
            "3. 根据文案内容调整：震撼新闻用激动语气，深度分析用沉稳语气，技术干货用专业自信语气\n"
            "4. 必须包含情绪词和风格描述"
        )

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                max_tokens=100,
                temperature=0.7,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"口播文案：\n{script_text[:300]}"},
                ],
            )
            prompt = response.choices[0].message.content.strip()
            prompt = prompt.strip("'\"`").strip()
            if prompt:
                logger.info(f"Generated voice prompt: {prompt}")
                return prompt
            return None
        except Exception as e:
            logger.warning(f"Voice prompt generation failed: {e}")
            return None

    # ──────────────────────────────────────────────────────────────────────────
    # TTS synthesis helper (wraps speech_provider.synthesize + audio utils)
    # ──────────────────────────────────────────────────────────────────────────

    def _synthesize_speech(
        self,
        script: str,
        filename: str,
        max_duration: float | None = 28,
        voice_prompt: str | None = None,
    ) -> tuple[str, float, float] | None:
        """Generate audio from script text. Returns (file_path, duration, original_duration)."""
        text = clean_script(script)
        if not text or not self.speech_provider:
            return None

        if not filename.endswith(".wav"):
            filename = filename.rsplit(".", 1)[0] + ".wav"

        logger.info(f"Generating TTS: {text[:60]}...")
        result = self.speech_provider.synthesize(text, filename, response_format="wav")
        if not result:
            return None
        filepath = result

        duration = get_audio_duration(filepath)
        original_duration = duration
        if max_duration and duration > max_duration:
            logger.info(f"TTS audio {duration:.1f}s exceeds {max_duration}s limit, trimming...")
            trim_audio(filepath, max_duration)
            duration = get_audio_duration(filepath)

        logger.info(f"TTS saved: {filepath} ({duration:.1f}s)")
        return filepath, duration, original_duration

    # ──────────────────────────────────────────────────────────────────────────
    # TTS from AudioPlanner segments (precise sync)
    # ──────────────────────────────────────────────────────────────────────────

    def _generate_tts_from_audio_plan(
        self,
        audio_plan: dict,
        content_id: int,
        output_media: Path,
        voice_prompt: str | None = None,
    ) -> tuple[str | None, float | None, list[dict]]:
        """Generate TTS audio from AudioPlanner segments for precise sync.

        Returns (concat_audio_path, total_duration, segment_timings).
        """
        if not self.speech_provider or not audio_plan.get("segments"):
            return None, None, []

        segments = audio_plan["segments"]
        seg_audio_paths = []
        seg_durations = []
        seg_texts = []
        pauses = []

        for i, seg in enumerate(segments):
            seg_text = seg.get("text", "").strip()
            pause = seg.get("pause_after", 0.2)
            if not seg_text:
                seg_durations.append(0.0)
                seg_texts.append("")
                pauses.append(0.0)
                continue

            audio_filename = f"content_{content_id}_audio_seg_{i}.wav"
            tts_result = self._synthesize_speech(
                seg_text, audio_filename,
                max_duration=30, voice_prompt=voice_prompt,
            )
            if tts_result:
                audio_path, duration, _ = tts_result
                seg_audio_paths.append(audio_path)
                seg_durations.append(duration)
            else:
                seg_durations.append(0.0)
            seg_texts.append(seg_text)
            pauses.append(pause)

        if not seg_audio_paths:
            return None, None, []

        concat_filename = f"content_{content_id}_tts.wav"
        concat_path = str(output_media / concat_filename)
        concat_wav_files(seg_audio_paths, concat_path, gap_seconds=0.0)

        segment_timings = []
        current_time = 0.0
        for i, (duration, text) in enumerate(zip(seg_durations, seg_texts)):
            if duration > 0:
                start = current_time
                end = current_time + duration
                segment_timings.append({"text": text, "start": round(start, 2), "end": round(end, 2)})
                current_time = end + pauses[i]
            else:
                segment_timings.append({"text": text, "start": round(current_time, 2), "end": round(current_time, 2)})

        total_duration = get_audio_duration(concat_path)
        logger.info(f"Audio-plan TTS: {len(seg_audio_paths)} segments, {total_duration:.1f}s total")
        return concat_path, total_duration, segment_timings

    # ──────────────────────────────────────────────────────────────────────────
    # Legacy per-scene TTS (deprecated fallback)
    # ──────────────────────────────────────────────────────────────────────────

    def _generate_tts_per_scene(
        self,
        plan: dict,
        content_id: int,
        output_media: Path,
        max_total_duration: float = 60,
        voice_prompt: str | None = None,
    ) -> tuple[str | None, float | None, list[dict]]:
        """[DEPRECATED] Legacy per-scene TTS from plan scenes."""
        if not self.speech_provider or not plan.get("scenes"):
            return None, None, []

        scenes = plan["scenes"]
        scene_audio_paths = []
        scene_durations = []
        scene_texts = []

        for i, scene in enumerate(scenes):
            scene_text = self._extract_scene_text(scene)
            if not scene_text:
                scene_durations.append(0.0)
                scene_texts.append("")
                continue

            audio_filename = f"content_{content_id}_scene_{i}.wav"
            tts_result = self._synthesize_speech(
                scene_text, audio_filename,
                max_duration=max_total_duration, voice_prompt=voice_prompt,
            )
            if tts_result:
                audio_path, duration, _ = tts_result
                scene_audio_paths.append(audio_path)
                scene_durations.append(duration)
                scene_texts.append(scene_text)
            else:
                scene_durations.append(0.0)
                scene_texts.append(scene_text)

        if not scene_audio_paths:
            return None, None, []

        concat_filename = f"content_{content_id}_tts.wav"
        concat_path = str(output_media / concat_filename)
        concat_wav_files(scene_audio_paths, concat_path, gap_seconds=0.15)

        scene_timings = []
        current_time = 0.0
        gap = 0.15
        for i, (duration, text) in enumerate(zip(scene_durations, scene_texts)):
            if duration > 0:
                start = current_time
                end = current_time + duration
                scene_timings.append({"text": text, "start": round(start, 2), "end": round(end, 2)})
                current_time = end + gap
            else:
                scene_timings.append({"text": text, "start": round(current_time, 2), "end": round(current_time, 2)})

        total_duration = get_audio_duration(concat_path)
        logger.info(f"Per-scene TTS (legacy): {len(scene_audio_paths)} scenes, {total_duration:.1f}s total")
        return concat_path, total_duration, scene_timings

    def _extract_scene_text(self, scene: dict) -> str:
        """Extract speakable text from a composition plan scene."""
        scene_type = scene.get("type", "")
        if scene_type in ("title", "hook"):
            return scene.get("text", "")
        elif scene_type == "text_sequence":
            lines = scene.get("lines", [])
            return "，".join(line for line in lines if line)
        elif scene_type == "highlight":
            return scene.get("text", "")
        elif scene_type == "bullet_points":
            items = scene.get("items", [])
            return "，".join(item for item in items if item)
        elif scene_type == "ending":
            return scene.get("text", "").replace("\n", "。")
        return ""

    # ──────────────────────────────────────────────────────────────────────────
    # Video description generation (for text-to-video providers)
    # ──────────────────────────────────────────────────────────────────────────

    def _generate_video_description(self, script_text: str, title: str, category: str = "dao") -> str | None:
        """Generate a text-to-video prompt from an oral script using the video template."""
        try:
            template = self._load_template("douyin_video", category)
        except FileNotFoundError:
            logger.warning(f"Video template not found for category '{category}', using fallback")
            template = None

        if not template:
            return None

        prompt = template.replace("{script}", script_text).replace("{title}", title)
        system_prompt = CATEGORY_SYSTEM_PROMPTS.get(category, CATEGORY_SYSTEM_PROMPTS["dao"])

        try:
            logger.info("Generating video description via LLM (text-to-video template)...")
            response = self.client.chat.completions.create(
                model=self.model,
                max_tokens=2048,
                temperature=0.7,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt},
                ],
            )
            text = response.choices[0].message.content.strip()

            json_start = text.find("{")
            json_end = text.rfind("}") + 1
            if json_start >= 0 and json_end > json_start:
                try:
                    result = json.loads(text[json_start:json_end])
                    video_prompt = result.get("video_prompt", "")
                    if video_prompt:
                        logger.info(f"Video description generated: {video_prompt[:60]}...")
                        return video_prompt
                except json.JSONDecodeError:
                    pass

            match = re.search(r'"video_prompt"\s*:\s*"((?:[^"\\]|\\.)*)', text)
            if match:
                video_prompt = match.group(1).strip()
                if video_prompt:
                    logger.info(f"Video description extracted (fallback): {video_prompt[:60]}...")
                    return video_prompt

            logger.warning(f"No video_prompt found in LLM response: {text[:200]}")
            return None
        except Exception as e:
            logger.error(f"Video description generation failed: {e}")
            return None

    def _generate_segment_video_descriptions(
        self,
        segments: list[dict],
        title: str,
        category: str = "dao",
    ) -> list[str]:
        """Batch-generate per-segment video descriptions in a single LLM call.

        Each segment has 'index', 'duration', and 'text'. Returns a list of
        video prompt strings in the same order.
        """
        if not segments:
            return []

        # Build a prompt listing all segments
        seg_lines = []
        for s in segments:
            seg_lines.append(
                f"【第{s['index']+1}段】（时长{s['duration']:.0f}秒）\n"
                f"旁白内容：{s['text']}\n"
            )
        segs_text = "\n".join(seg_lines)

        prompt = (
            "你是一个短视频导演。下面是一段抖音口播文案，已按时间分为多段，"
            "每段配有一段旁白。请为**每一段**分别写一个视频画面提示词（中文），"
            "用于文生视频模型生成该段对应的画面。\n\n"
            "要求：\n"
            "1. 每段提示词独立，画面要与该段旁白内容相关\n"
            "2. 相邻段的画面要有变化，避免重复，形成视觉叙事节奏\n"
            "3. 每段提示词控制在50字以内，简洁具体\n"
            "4. 包含镜头描述（如：推近、拉远、特写、平移等）\n"
            "5. 输出 JSON 数组，格式：[\"第1段提示词\", \"第2段提示词\", ...]\n"
            "6. 只输出 JSON，不要解释\n\n"
            f"文案标题：{title}\n\n"
            f"{segs_text}"
        )

        try:
            logger.info(f"Batch-generating {len(segments)} segment video descriptions...")
            response = self.client.chat.completions.create(
                model=self.model,
                max_tokens=2048,
                temperature=0.7,
                messages=[
                    {"role": "system", "content": "你是一个短视频导演，负责为口播文案的每一段生成对应的视频画面提示词。"},
                    {"role": "user", "content": prompt},
                ],
            )
            text = response.choices[0].message.content.strip()

            # Extract JSON array
            array_start = text.find("[")
            array_end = text.rfind("]") + 1
            if array_start >= 0 and array_end > array_start:
                try:
                    prompts = json.loads(text[array_start:array_end])
                    if isinstance(prompts, list) and len(prompts) == len(segments):
                        prompts = [p.strip() for p in prompts if isinstance(p, str)]
                        logger.info(f"Generated {len(prompts)} segment video prompts")
                        return prompts
                except json.JSONDecodeError:
                    pass

            # Fallback: try to extract line by line
            prompts = []
            for line in text.split("\n"):
                line = line.strip().strip('",')
                if line and not line.startswith("[") and not line.startswith("]"):
                    prompts.append(line)
            if len(prompts) >= len(segments):
                logger.info(f"Extracted {len(prompts)} prompts (line-based fallback)")
                return prompts[:len(segments)]

            logger.warning(f"Failed to parse segment prompts, using fallback")
            return []
        except Exception as e:
            logger.error(f"Segment video description batch generation failed: {e}")
            return []

    # ──────────────────────────────────────────────────────────────────────────
    # Video processing (the big one)
    # ──────────────────────────────────────────────────────────────────────────

    def _process_videos(
        self,
        body: str,
        content_id: int,
        platform: str,
        tags: list[str] | None = None,
        category: str = "dao",
    ) -> tuple[str, list[str]]:
        """Generate videos for douyin content.

        Two paths based on video provider:
        - Remotion: uses script text directly with video_planner → text-based animation
        - Text-to-video (DashScope/Agnes): generates cinematic video description
          via dedicated video template, then calls the video generation API

        Returns (processed_body, list_of_local_video_paths).
        """
        if not self.video_provider:
            return body, []

        output_media = Path("output") / platform / "media"
        output_media.mkdir(parents=True, exist_ok=True)

        # Extract clean script text
        script_text = VIDEO_PLACEHOLDER_RE.sub("", body).strip()
        script_text = re.sub(r"【[^】]+】", "", script_text)
        script_text = re.sub(r"\n*---\n*", "，", script_text).strip()
        script_text = re.sub(r"[，。]{2,}", "，", script_text)
        subtitle_text = script_text
        video_plan = None

        topic_title = re.sub(r"【[^】]+】", "", body).strip()
        topic_title = topic_title.split("\n")[0].strip()[:50]
        if not topic_title:
            topic_title = "AI 资讯"

        is_remotion = self._video_provider_name == "remotion"

        # ── Remotion flow: Audio plan first → TTS → Video plan ──
        audio_plan = None
        audio_segments = []
        if is_remotion and self._audio_planner:
            logger.info("Step 1/3: Generating audio narration plan (AudioPlanner)...")
            audio_plan = self._audio_planner.plan(
                script=script_text,
                title=topic_title,
                tags=tags,
            )
            if audio_plan:
                narration = audio_plan.get("narration", "")
                voice_direction = audio_plan.get("voice_direction", "")
                audio_segments = audio_plan.get("segments", [])
                logger.info(
                    f"Audio plan: {len(audio_segments)} segments, "
                    f"voice_direction={voice_direction[:40] if voice_direction else 'N/A'}"
                )
                if narration:
                    script_text = narration
                    subtitle_text = narration
            else:
                logger.warning("AudioPlan failed, falling back to raw script TTS")

        # --- TTS audio generation ---
        src_audio = None
        audio_duration = None
        scene_timings = []
        use_audio_sync = self.speech_provider is not None

        if use_audio_sync:
            if is_remotion and audio_plan:
                voice_prompt = audio_plan.get("voice_direction")
            else:
                voice_prompt = self._generate_voice_prompt(script_text, category)

            if is_remotion and audio_plan and audio_plan.get("segments"):
                # ── Remotion: per-segment TTS from AudioPlanner ──
                logger.info("Step 2/3: Generating per-segment TTS from audio plan...")
                concat_path, total_duration, scene_timings = self._generate_tts_from_audio_plan(
                    audio_plan, content_id, output_media, voice_prompt=voice_prompt,
                )
                if concat_path and total_duration:
                    audio_path = concat_path
                    audio_duration = total_duration
                    src_audio = Path(audio_path)
                    dst_audio = output_media / src_audio.name
                    import time
                    for _retry in range(5):
                        try:
                            shutil.copy2(src_audio, dst_audio)
                            break
                        except PermissionError:
                            time.sleep(1.0)
                    else:
                        dst_audio.write_bytes(src_audio.read_bytes())

                    # Step 3/3: Generate video plan with measured audio timings
                    logger.info("Step 3/3: Generating visual composition plan (VideoPlanner)...")
                    video_plan = self._video_planner.plan(
                        script=script_text,
                        title=topic_title,
                        tags=tags,
                        audio_timings=scene_timings,
                    ) if self._video_planner else None
                    if video_plan:
                        plan_dur = sum(s.get("duration", 0) for s in video_plan["scenes"])
                        logger.info(
                            f"Video plan with audio sync: {len(video_plan['scenes'])} scenes, "
                            f"plan={plan_dur:.1f}s, audio={audio_duration:.1f}s"
                        )
                    else:
                        logger.warning("VideoPlanner failed after TTS, plan will be None")

            elif is_remotion and video_plan and video_plan.get("scenes"):
                # ── Legacy fallback: per-scene TTS from old plan ──
                logger.info("Generating per-scene TTS for precise audio/video sync (legacy)...")
                concat_path, total_duration, scene_timings = self._generate_tts_per_scene(
                    video_plan, content_id, output_media,
                    max_total_duration=60, voice_prompt=voice_prompt,
                )
                if concat_path and total_duration:
                    audio_path = concat_path
                    audio_duration = total_duration
                    src_audio = Path(audio_path)
                    dst_audio = output_media / src_audio.name
                    import time
                    for _retry in range(5):
                        try:
                            shutil.copy2(src_audio, dst_audio)
                            break
                        except PermissionError:
                            time.sleep(1.0)
                    else:
                        dst_audio.write_bytes(src_audio.read_bytes())

                    for i, timing in enumerate(scene_timings):
                        if i < len(video_plan["scenes"]) and timing["end"] > timing["start"]:
                            video_plan["scenes"][i]["duration"] = round(timing["end"] - timing["start"], 2)

                    plan_dur = sum(s.get("duration", 0) for s in video_plan["scenes"])
                    logger.info(
                        f"Plan durations from TTS (legacy): {plan_dur:.1f}s "
                        f"(audio: {audio_duration:.1f}s)"
                    )
            else:
                # --- Text-to-video: full TTS ---
                audio_filename = f"content_{content_id}_tts.wav"
                logger.info("Generating TTS audio for script (no duration limit)...")
                tts_result = self._synthesize_speech(
                    script_text, audio_filename,
                    max_duration=None, voice_prompt=voice_prompt,
                )
                if tts_result:
                    audio_path, audio_duration, _ = tts_result
                    src_audio = Path(audio_path)
                    dst_audio = output_media / src_audio.name
                    shutil.copy2(src_audio, dst_audio)

        # --- Video generation ---
        media_urls = []
        processed = body

        placeholders = list(VIDEO_PLACEHOLDER_RE.finditer(body))

        if is_remotion:
            video_desc = script_text
        elif placeholders:
            video_desc = placeholders[0].group(1).strip()
        else:
            video_desc = self._generate_video_description(script_text, topic_title, category)
            if not video_desc:
                video_desc = f"总时长15秒。{script_text[:200]}"
                logger.warning("Video description generation failed, using fallback")

        filename = f"content_{content_id}_1.mp4"
        logger.info(f"Generating video: {video_desc[:60]}...")

        if is_remotion:
            audio_path_arg = str(src_audio) if src_audio else None
            video_path = self.video_provider.generate(
                prompt=video_desc,
                filename=filename,
                audio_path=audio_path_arg,
                subtitles=subtitle_text,
                keywords=tags,
                audio_duration=audio_duration,
                plan=video_plan,
                scene_timings=scene_timings if scene_timings else None,
            )
            if video_path:
                src = Path(video_path)
                dst = output_media / src.name
                shutil.copy2(src, dst)
                processed += f"\n\n[视频]({f'media/{src.name}'})\n"
                media_urls.append(str(dst))
        else:
            # Text-to-video: multi-segment when audio exceeds API limit
            api_max = self._video_max_duration or 15
            needs_split = audio_duration and audio_duration > api_max

            if needs_split and src_audio:
                seg_dir = output_media / f"segs_{content_id}"
                segments = split_audio(
                    str(src_audio), str(seg_dir),
                    max_segment_duration=float(api_max),
                )
                logger.info(f"Audio split into {len(segments)} segments for multi-segment video")

                # Split script text proportionally by audio segment duration
                script_chars = len(script_text)
                total_audio_dur = audio_duration or 1.0
                segment_scripts = []
                for i, seg in enumerate(segments):
                    seg_frac = seg["duration"] / total_audio_dur
                    seg_start_char = int(sum(s["duration"] for s in segments[:i]) / total_audio_dur * script_chars)
                    seg_end_char = int(seg_start_char + seg_frac * script_chars)
                    seg_script = script_text[seg_start_char:seg_end_char].strip()
                    if not seg_script:
                        seg_script = script_text[:50]
                    segment_scripts.append({
                        "index": i,
                        "duration": seg["duration"],
                        "text": seg_script,
                    })

                # Batch-generate per-segment video descriptions in one LLM call
                seg_video_descs = self._generate_segment_video_descriptions(
                    segment_scripts, topic_title, category,
                )

                segment_videos = []
                for i, seg in enumerate(segments):
                    seg_filename = f"content_{content_id}_seg{i}.mp4"
                    seg_video_desc = seg_video_descs[i] if i < len(seg_video_descs) else video_desc

                    logger.info(
                        f"Generating video segment {i+1}/{len(segments)} ({seg['duration']:.1f}s): "
                        f"{seg_video_desc[:40]}..."
                    )
                    seg_video = self.video_provider.generate(
                        prompt=seg_video_desc,
                        filename=seg_filename,
                        audio_path=seg["path"],
                        audio_duration=seg["duration"],
                    )
                    if seg_video:
                        segment_videos.append(seg_video)
                    else:
                        logger.error(f"Video segment {i+1} failed, aborting multi-segment")
                        break

                if segment_videos and len(segment_videos) == len(segments):
                    concat_video = str(output_media / f"content_{content_id}_concat.mp4")
                    concat_ok = _concat_videos(segment_videos, concat_video)

                    if concat_ok:
                        merged = _merge_audio(concat_video, str(src_audio))
                        final = burn_subtitles(
                            merged, subtitle_text, self._video_size,
                            self._sub_config, tags, audio_duration,
                        )
                        if final:
                            src = Path(final)
                            dst = output_media / f"content_{content_id}_1.mp4"
                            shutil.copy2(src, dst)
                            rel_path = f"media/{dst.name}"
                            if placeholders:
                                processed = processed.replace(placeholders[0].group(0), f"\n\n[视频]({rel_path})\n", 1)
                            else:
                                processed += f"\n\n[视频]({rel_path})\n"
                            media_urls.append(str(dst))

                    try:
                        shutil.rmtree(seg_dir, ignore_errors=True)
                    except Exception:
                        pass
            else:
                audio_path_arg = str(src_audio) if src_audio else None
                video_path = self.video_provider.generate(
                    prompt=video_desc,
                    filename=filename,
                    audio_path=audio_path_arg,
                    subtitles=subtitle_text,
                    keywords=tags,
                    audio_duration=audio_duration,
                )
                if video_path:
                    src = Path(video_path)
                    dst = output_media / src.name
                    shutil.copy2(src, dst)
                    rel_path = f"media/{src.name}"
                    if placeholders:
                        processed = processed.replace(placeholders[0].group(0), f"\n\n[视频]({rel_path})\n", 1)
                    else:
                        processed += f"\n\n[视频]({rel_path})\n"
                    media_urls.append(str(dst))

        return processed, media_urls

    # ──────────────────────────────────────────────────────────────────────────
    # Public interface: generate_for_topic
    # ──────────────────────────────────────────────────────────────────────────

    def generate_for_topic(
        self,
        topic_id: int,
        topic_title: str,
        category: str = "dao",
        platforms: list[str] | None = None,
    ) -> list[Path]:
        """Generate content for a topic across specified platforms. Returns file paths."""
        platforms = platforms or get_enabled_platforms(self.config)
        file_paths = []

        for platform in platforms:
            result = self._generate_for_platform(topic_title, platform, category)
            if not result:
                continue

            title = result.get("title", "")
            body = result.get("body", result.get("script", ""))
            tags = result.get("tags", [])
            description = result.get("description", "")

            from modules.platforms import get_processor
            processor = get_processor(platform)
            if processor:
                title, body = processor(title, body, tags)

            content_id = topic_id * 100 + len(file_paths)
            body, media_urls = self._process_images(body, content_id, platform)

            if platform == "douyin":
                body, video_urls = self._process_videos(
                    body, content_id, platform, tags=tags, category=category,
                )
                media_urls.extend(video_urls)

            filepath = self.store.save_content(
                platform=platform,
                title=title,
                body=body,
                tags=tags,
                media_urls=media_urls,
                topic_id=topic_id,
                description=description,
            )
            file_paths.append(filepath)

        if file_paths:
            self.db.update_topic_status(topic_id, "processing")

        return file_paths

    # ──────────────────────────────────────────────────────────────────────────
    # Public interface: run (called from CLI)
    # ──────────────────────────────────────────────────────────────────────────

    def run(self, limit: int = 1, category: str | None = None) -> dict:
        """Generate content for all new topics. Returns summary.

        Args:
            limit: Max number of topics to process per category (default: 1).
            category: If set, only generate for this category ('dao' or 'shu').
        """
        if category:
            topics = self.db.get_topics(status="new", category=category, limit=limit)
        else:
            dao_topics = self.db.get_topics(status="new", category="dao", limit=limit)
            shu_topics = self.db.get_topics(status="new", category="shu", limit=limit)
            topics = dao_topics + shu_topics

        if not topics:
            logger.info("No new topics to generate content for")
            return {"topics_processed": 0, "contents_created": 0}

        total_contents = 0
        for topic in topics:
            paths = self.generate_for_topic(
                topic["id"], topic["title"], category=topic.get("category", "dao"),
            )
            total_contents += len(paths)

        summary = {
            "topics_processed": len(topics),
            "contents_created": total_contents,
        }
        logger.info(f"Generation complete: {summary}")
        return summary
