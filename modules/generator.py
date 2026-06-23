"""AI content generation module using MiMo API (OpenAI compatible)."""

import json
import logging
import re
import shutil
from pathlib import Path
from typing import Optional
from openai import OpenAI
from modules.database import Database
from modules.content_store import ContentStore
from modules.imager import ImageGenerator
from modules.vgen import VideoGenerator
from modules.tts import TTSSynthesizer
import requests

logger = logging.getLogger(__name__)

PLATFORMS = ["xiaohongshu", "wechat", "douyin"]
IMAGE_PLACEHOLDER_RE = re.compile(r"\[IMAGE:(.*?)]")
VIDEO_PLACEHOLDER_RE = re.compile(r"\[VIDEO:(.*?)]")

CATEGORY_SYSTEM_PROMPTS = {
    "dao": (
        "你是MiMo，是小米公司研发的AI智能助手。"
        "你正在为一个AI领域的内容账号创作「道」系列内容，账号定位是：「AI时代必备心法。在这里，看懂AI的道与术。」"
        "「道」系列关注社会趋势、人性洞察、时代变迁，用AI思维提供独特的观察视角。"
        "内容要求：从宏观视角解读社会热点，提供认知升级的洞察，而非就事论事。"
        "请严格按照要求的JSON格式输出。"
    ),
    "shu": (
        "你是MiMo，是小米公司研发的AI智能助手。"
        "你正在为一个AI领域的内容账号创作「术」系列内容，账号定位是：「AI时代必备心法。在这里，看懂AI的道与术。」"
        "「术」系列关注AI技术本身，解读技术原理、应用场景、实操方法。"
        "内容要求：有具体的技术细节、工具名称、使用方法，提供实操价值，而非泛泛而谈。"
        "请严格按照要求的JSON格式输出。"
    ),
}


def get_enabled_platforms(config: dict) -> list[str]:
    """Return the list of platforms that have enabled: true in config.platforms."""
    platforms_config = config.get("platforms", {})
    enabled = []
    for name in PLATFORMS:
        if platforms_config.get(name, {}).get("enabled", False):
            enabled.append(name)
    return enabled


class ContentGenerator:
    def __init__(self, db: Database, config: dict):
        self.db = db
        self.config = config
        mimo_config = config.get("mimo", {})
        api_key = mimo_config.get("api_key", "")
        base_url = mimo_config.get("base_url", "https://api.xiaomimimo.com/v1")
        self.model = mimo_config.get("model", "mimo-v2.5-pro")
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.gen_config = config.get("generation", {})
        self.auto_image = self.gen_config.get("auto_image", False)
        self.imager = ImageGenerator(config) if self.auto_image else None
        self.auto_video = self.gen_config.get("auto_video", False)
        self.vgen = VideoGenerator(config) if self.auto_video else None
        self.tts = TTSSynthesizer(config) if self.auto_video else None
        self.ds_api_key = config.get("dashscope", {}).get("api_key", "")
        self.store = ContentStore(
            output_dir=config.get("output_dir", "output"),
            media_dir=config.get("dashscope", {}).get("media_dir", "media"),
        )
        self._templates = {}

    def _load_template(self, platform: str, category: str = "dao") -> str:
        cache_key = f"{platform}_{category}"
        if cache_key not in self._templates:
            # Try category-specific template first, fall back to generic
            category_path = Path(f"templates/{platform}_{category}.md")
            generic_path = Path(f"templates/{platform}.md")

            if category_path.exists():
                self._templates[cache_key] = category_path.read_text(encoding="utf-8")
            elif generic_path.exists():
                self._templates[cache_key] = generic_path.read_text(encoding="utf-8")
            else:
                raise FileNotFoundError(f"Template not found: {category_path} or {generic_path}")
        return self._templates[cache_key]

    def _ensure_tags(self, result: dict, category: str) -> None:
        """Ensure result has valid tags. Auto-generate from title if empty."""
        tags = result.get("tags", [])
        if tags:
            # Limit to 5 max (Douyin constraint, safe for all platforms)
            result["tags"] = tags[:5]
            return

        title = result.get("title", "")
        # Generate basic tags from title keywords
        fallback_tags = ["#AI"]
        if category == "dao":
            fallback_tags.append("#AI时代")
        else:
            fallback_tags.append("#AI技术")

        # Extract potential keywords from title (simple split by common delimiters)
        import re
        # Remove punctuation and split into chunks
        chunks = re.split(r'[，。！？、：；“”‘’（）\s]+', title)
        stopwords = {"的", "了", "是", "在", "和", "有", "不", "这", "那", "人", "我", "你", "他", "她", "它", "们", "被", "把", "将", "从", "到", "又", "就", "也", "都", "而", "且", "但", "或", "如果"}
        for chunk in chunks:
            chunk = chunk.strip()
            if len(chunk) >= 2 and chunk not in stopwords:
                tag = f"#{chunk}"
                if tag not in fallback_tags and len(fallback_tags) < 5:
                    fallback_tags.append(tag)

        # Ensure at least 3 tags
        while len(fallback_tags) < 3:
            fallback_tags.append(f"#热点{len(fallback_tags)}")

        result["tags"] = fallback_tags[:5]
        logger.info(f"Auto-generated tags: {result['tags']}")

    def _validate_douyin_script(self, result: dict) -> None:
        """Validate douyin script quality and log warnings for issues.

        Non-blocking: logs warnings but does not discard the content.
        """
        script = result.get("script", result.get("body", ""))
        tags = result.get("tags", [])
        warnings = []

        # Check three-part structure
        has_hook = "【钩子】" in script
        has_value = "【价值】" in script
        has_ending = "【收尾】" in script
        if not (has_hook and has_value and has_ending):
            missing = []
            if not has_hook:
                missing.append("【钩子】")
            if not has_value:
                missing.append("【价值】")
            if not has_ending:
                missing.append("【收尾】")
            warnings.append(f"缺少三段结构: {', '.join(missing)}")

        # Check separator
        if "---" not in script:
            warnings.append("缺少 --- 分隔符")

        # Check word count (200-800 chars for Chinese scripts)
        char_count = len(script)
        if char_count < 200:
            warnings.append(f"脚本过短 ({char_count}字)，建议200-800字")
        elif char_count > 800:
            warnings.append(f"脚本过长 ({char_count}字)，建议200-800字")

        # Check tags
        if len(tags) < 3:
            warnings.append(f"标签不足 ({len(tags)}个)，建议3-5个")
        elif len(tags) > 5:
            warnings.append(f"标签过多 ({len(tags)}个)，建议3-5个")

        ai_tag_found = any("AI" in t.upper() or "人工智能" in t for t in tags)
        if not ai_tag_found:
            warnings.append("缺少 #AI 相关标签")

        # Log warnings
        if warnings:
            for w in warnings:
                logger.warning(f"[抖音质量校验] {w}")
        else:
            logger.info("[抖音质量校验] 脚本质量合格")

    def _generate_for_platform(self, topic: str, platform: str, category: str = "dao") -> Optional[dict]:
        """Generate content for a specific platform."""
        template = self._load_template(platform, category)
        prompt = template.replace("{topic}", topic)

        system_prompt = CATEGORY_SYSTEM_PROMPTS.get(category, CATEGORY_SYSTEM_PROMPTS["dao"])
        logger.info(f"Generating {platform}/{category} content for: {topic[:50]}...")

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                max_tokens=self.gen_config.get("max_tokens", 4096),
                temperature=self.gen_config.get("temperature", 0.7),
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt},
                ],
            )

            text = response.choices[0].message.content

            # Extract JSON from response
            json_start = text.find("{")
            json_end = text.rfind("}") + 1
            if json_start == -1 or json_end == 0:
                logger.error(f"No JSON found in response for {platform}")
                return None

            result = json.loads(text[json_start:json_end])
            logger.info(f"Generated {platform} content: {result.get('title', 'N/A')[:30]}")

            # Ensure tags exist (auto-generate if empty)
            if not result.get("tags"):
                self._ensure_tags(result, category)

            # Validate douyin script quality
            if platform == "douyin":
                self._validate_douyin_script(result)

            return result

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON for {platform}: {e}")
            return None
        except Exception as e:
            logger.error(f"Generation failed for {platform}: {e}")
            return None

    def _upload_to_oss(self, file_path: str, model_name: str) -> str | None:
        """Upload a local file to DashScope OSS and return oss:// URL.

        Uses the temporary file upload API:
        1. GET /api/v1/uploads?action=getPolicy&model=xxx
        2. POST file to upload_host with policy data
        3. Return oss:// URL
        """
        if not self.ds_api_key:
            logger.warning("DashScope API key not configured, skipping upload")
            return None

        try:
            # Step 1: Get upload policy
            policy_url = "https://dashscope.aliyuncs.com/api/v1/uploads"
            headers = {
                "Authorization": f"Bearer {self.ds_api_key}",
                "Content-Type": "application/json",
            }
            params = {
                "action": "getPolicy",
                "model": model_name,
            }
            resp = requests.get(policy_url, headers=headers, params=params, timeout=10)
            if resp.status_code != 200:
                logger.error(f"Get upload policy failed: {resp.text}")
                return None

            policy_data = resp.json().get("data", {})

            # Step 2: Upload file to OSS
            file_name = Path(file_path).name
            key = f"{policy_data['upload_dir']}/{file_name}"

            with open(file_path, "rb") as f:
                files = {
                    "OSSAccessKeyId": (None, policy_data["oss_access_key_id"]),
                    "Signature": (None, policy_data["signature"]),
                    "policy": (None, policy_data["policy"]),
                    "x-oss-object-acl": (None, policy_data.get("x_oss_object_acl", "private")),
                    "x-oss-forbid-overwrite": (None, policy_data.get("x_oss_forbid_overwrite", "true")),
                    "key": (None, key),
                    "success_action_status": (None, "200"),
                    "file": (file_name, f),
                }
                resp = requests.post(policy_data["upload_host"], files=files, timeout=60)

            if resp.status_code != 200:
                logger.error(f"Upload file to OSS failed: {resp.text}")
                return None

            oss_url = f"oss://{key}"
            logger.info(f"File uploaded to OSS: {oss_url}")
            return oss_url

        except Exception as e:
            logger.error(f"OSS upload failed: {e}")
            return None

    def _process_images(self, body: str, content_id: int, platform: str) -> tuple[str, list[str]]:
        """Replace [IMAGE:description] placeholders with generated images.

        Returns (processed_body, list_of_local_image_paths).
        """
        if not self.imager:
            # No imager, just strip placeholders
            placeholder_count = len(list(IMAGE_PLACEHOLDER_RE.finditer(body)))
            if placeholder_count > 0:
                logger.info(f"auto_image 未启用，已移除 {placeholder_count} 个 [IMAGE:...] 占位符")
            return IMAGE_PLACEHOLDER_RE.sub("", body), []

        placeholders = list(IMAGE_PLACEHOLDER_RE.finditer(body))
        if not placeholders:
            logger.info("正文中无 [IMAGE:...] 占位符，跳过配图")
            return body, []

        # Prepare output media dir for this platform
        output_media = Path("output") / platform / "media"
        output_media.mkdir(parents=True, exist_ok=True)

        media_urls = []
        processed = body

        for i, match in enumerate(placeholders):
            desc = match.group(1).strip()
            filename = f"content_{content_id}_{i+1}.png"
            logger.info(f"Generating image {i+1}/{len(placeholders)}: {desc[:50]}...")

            image_path = self.imager.generate(desc, filename)
            if image_path:
                # Copy to output dir
                src = Path(image_path)
                dst = output_media / src.name
                shutil.copy2(src, dst)

                # Replace placeholder with markdown image
                rel_path = f"media/{src.name}"
                processed = processed.replace(match.group(0), f"\n\n![配图]({rel_path})\n", 1)
                media_urls.append(str(dst))
                logger.info(f"图片生成成功 [{i+1}/{len(placeholders)}]: {dst}")
            else:
                # Remove placeholder if generation failed
                processed = processed.replace(match.group(0), "", 1)
                logger.warning(f"图片生成失败 [{i+1}/{len(placeholders)}]: {desc[:50]}...，已移除占位符")

        total = len(placeholders)
        success = len(media_urls)
        failed = total - success
        logger.info(f"配图处理完成: 成功 {success}/{total}，失败 {failed}/{total}")
        return processed, media_urls

    def _generate_voice_prompt(self, script_text: str, category: str = "dao") -> str | None:
        """Generate a TTS voice prompt dynamically based on script content.

        Uses LLM to analyze the script's tone, emotion, and style, then generates
        an appropriate voice instruction for the TTS engine.

        Args:
            script_text: The cleaned script text.
            category: Content category ('dao' or 'shu').

        Returns:
            Voice prompt string, or None on failure.
        """
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
            # Clean up: remove quotes, markdown, etc.
            prompt = prompt.strip('"\'`').strip()
            if prompt:
                logger.info(f"Generated voice prompt: {prompt}")
                return prompt
            return None
        except Exception as e:
            logger.warning(f"Voice prompt generation failed: {e}")
            return None

    def _generate_tts_from_audio_plan(
        self,
        audio_plan: dict,
        content_id: int,
        output_media: Path,
        voice_prompt: str | None = None,
    ) -> tuple[str | None, float | None, list[dict]]:
        """Generate TTS audio from AudioPlanner segments for precise sync.

        Each segment in the audio plan is synthesized individually, then all
        WAVs are concatenated. Returns precise timing data keyed to segments.

        Returns:
            (concat_audio_path, total_duration, segment_timings)
            where segment_timings is [{text, start, end}, ...]
        """
        if not self.tts or not audio_plan.get("segments"):
            return None, None, []

        segments = audio_plan["segments"]
        seg_audio_paths = []
        seg_durations = []
        seg_texts = []
        pauses = []  # pause_after per segment

        for i, seg in enumerate(segments):
            seg_text = seg.get("text", "").strip()
            pause = seg.get("pause_after", 0.2)
            if not seg_text:
                seg_durations.append(0.0)
                seg_texts.append("")
                pauses.append(0.0)
                continue

            audio_filename = f"content_{content_id}_audio_seg_{i}.wav"
            tts_result = self.tts.synthesize(
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

        # Concatenate with the pauses specified by AudioPlanner
        concat_filename = f"content_{content_id}_tts.wav"
        concat_path = str(output_media / concat_filename)
        from modules.tts import TTSSynthesizer
        # Use per-segment pauses (AudioPlanner-specified) instead of fixed 0.15s
        TTSSynthesizer.concat_wav_files(
            seg_audio_paths, concat_path,
            gap_seconds=0.0,  # pauses are baked into segment texts or handled below
        )

        # Build timing data with specified pauses
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

        total_duration = TTSSynthesizer.get_audio_duration(concat_path)
        logger.info(f"Audio-plan TTS: {len(seg_audio_paths)} segments, {total_duration:.1f}s total")
        return concat_path, total_duration, segment_timings

    def _generate_tts_per_scene(self, plan: dict, content_id: int, output_media: Path, max_total_duration: float = 60, voice_prompt: str | None = None) -> tuple[str | None, float | None, list[dict]]:
        """[DEPRECATED] Legacy per-scene TTS from plan scenes.

        Kept as fallback when AudioPlanner is unavailable.
        """
        if not self.tts or not plan.get("scenes"):
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
            tts_result = self.tts.synthesize(scene_text, audio_filename, max_duration=max_total_duration, voice_prompt=voice_prompt)
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
        from modules.tts import TTSSynthesizer
        TTSSynthesizer.concat_wav_files(scene_audio_paths, concat_path, gap_seconds=0.15)

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

        total_duration = TTSSynthesizer.get_audio_duration(concat_path)
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

    def _generate_video_description(self, script_text: str, title: str, category: str = "dao") -> str | None:
        """Generate a text-to-video prompt from an oral script using the video template.

        Uses a dedicated video prompt template (douyin_video.md / douyin_video_dao.md / douyin_video_shu.md)
        to create a cinematic description optimized for AI video generation models.

        Args:
            script_text: The oral script text (cleaned, no markers).
            title: The content title.
            category: Content category ('dao' or 'shu').

        Returns:
            Video description string, or None on failure.
        """
        # Load video-specific template
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
                max_tokens=1024,
                temperature=0.7,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt},
                ],
            )
            text = response.choices[0].message.content.strip()

            # Extract JSON and parse video_prompt
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
                    pass  # Fall through to regex extraction

            # Fallback: extract video_prompt value directly via regex
            # Handles truncated JSON where the string is never closed
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

    def _process_videos(self, body: str, content_id: int, platform: str, tags: list[str] | None = None, category: str = "dao") -> tuple[str, list[str]]:
        """Generate videos for douyin content.

        Two paths based on video provider:
        - Remotion: uses script text directly with video_planner → text-based animation
        - Text-to-video (DashScope/Agnes): generates cinematic video description
          via dedicated video template, then calls the video generation API

        Returns (processed_body, list_of_local_video_paths).
        """
        if not self.vgen:
            return body, []

        # Prepare output media dir for this platform
        output_media = Path("output") / platform / "media"
        output_media.mkdir(parents=True, exist_ok=True)

        # Extract clean script text (strip markers and separators)
        script_text = VIDEO_PLACEHOLDER_RE.sub("", body).strip()
        script_text = re.sub(r"【[^】]+】", "", script_text)
        script_text = re.sub(r"\n*---\n*", "，", script_text).strip()
        script_text = re.sub(r"[，。]{2,}", "，", script_text)
        subtitle_text = script_text
        video_plan = None  # For remotion: pre-generated plan

        # Extract title from body
        topic_title = re.sub(r"【[^】]+】", "", body).strip()
        topic_title = topic_title.split("\n")[0].strip()[:50]
        if not topic_title:
            topic_title = "AI 资讯"

        is_remotion = getattr(self.vgen, 'provider', 'dashscope') == 'remotion'

        # ── Remotion flow: Audio plan first → TTS → Video plan ──
        audio_plan = None    # AudioPlanner output
        audio_segments = []  # raw segments from audio plan
        if is_remotion and self.vgen and self.vgen.audio_planner:
            logger.info("Step 1/3: Generating audio narration plan (AudioPlanner)...")
            audio_plan = self.vgen.audio_planner.plan(
                script=script_text,
                title=topic_title,
                tags=tags,
            )
            if audio_plan:
                narration = audio_plan.get("narration", "")
                voice_direction = audio_plan.get("voice_direction", "")
                audio_segments = audio_plan.get("segments", [])
                logger.info(f"Audio plan: {len(audio_segments)} segments, "
                           f"voice_direction={voice_direction[:40] if voice_direction else 'N/A'}")
                if narration:
                    script_text = narration
                    subtitle_text = narration
            else:
                logger.warning("AudioPlan failed, falling back to raw script TTS")

        # --- TTS audio generation ---
        audio_oss_url = None
        src_audio = None
        audio_duration = None
        scene_timings = []  # Per-scene timing for precise sync
        use_audio_sync = self.tts is not None

        if use_audio_sync:
            # Voice prompt: use AudioPlanner direction for Remotion, LLM-generated otherwise
            if is_remotion and audio_plan:
                voice_prompt = audio_plan.get("voice_direction")
            else:
                voice_prompt = self._generate_voice_prompt(script_text, category)

            if is_remotion and audio_plan and audio_plan.get("segments"):
                # ── Remotion: per-segment TTS from AudioPlanner ──
                logger.info("Step 2/3: Generating per-segment TTS from audio plan...")
                concat_path, total_duration, scene_timings = self._generate_tts_from_audio_plan(
                    audio_plan, content_id, output_media, voice_prompt=voice_prompt
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
                    video_plan = self.vgen.planner.plan(
                        script=script_text,
                        title=topic_title,
                        tags=tags,
                        audio_timings=scene_timings,
                    )
                    if video_plan:
                        plan_dur = sum(s.get("duration", 0) for s in video_plan["scenes"])
                        logger.info(f"Video plan with audio sync: {len(video_plan['scenes'])} scenes, "
                                   f"plan={plan_dur:.1f}s, audio={audio_duration:.1f}s")
                    else:
                        logger.warning("VideoPlanner failed after TTS, plan will be None")

            elif is_remotion and video_plan and video_plan.get("scenes"):
                # ── Legacy fallback: per-scene TTS from old plan ──
                logger.info("Generating per-scene TTS for precise audio/video sync (legacy)...")
                concat_path, total_duration, scene_timings = self._generate_tts_per_scene(
                    video_plan, content_id, output_media, max_total_duration=60, voice_prompt=voice_prompt
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
                    logger.info(f"Plan durations from TTS (legacy): {plan_dur:.1f}s (audio: {audio_duration:.1f}s, "
                               f"gap from {len(scene_timings)} scene pauses)")
            else:
                # --- Text-to-video: full TTS (audio is source of truth) ---
                audio_filename = f"content_{content_id}_tts.wav"
                logger.info("Generating TTS audio for script (no duration limit)...")
                tts_result = self.tts.synthesize(script_text, audio_filename, max_duration=None, voice_prompt=voice_prompt)
                if tts_result:
                    audio_path, audio_duration, _ = tts_result
                    src_audio = Path(audio_path)
                    dst_audio = output_media / src_audio.name
                    shutil.copy2(src_audio, dst_audio)

        # --- Video generation ---
        media_urls = []
        processed = body

        # Check for existing [VIDEO:...] placeholders (legacy support)
        placeholders = list(VIDEO_PLACEHOLDER_RE.finditer(body))

        if is_remotion:
            # Remotion: no [VIDEO:...] needed, generate directly from plan
            video_desc = script_text  # not used by Remotion, just for logging
        elif placeholders:
            # Legacy: body contains [VIDEO:...] placeholders
            video_desc = placeholders[0].group(1).strip()
        else:
            # New flow: generate video description from script via video template
            video_desc = self._generate_video_description(script_text, topic_title, category)
            if not video_desc:
                # Fallback: use raw script as description
                video_desc = f"总时长15秒。{script_text[:200]}"
                logger.warning("Video description generation failed, using fallback")

        filename = f"content_{content_id}_1.mp4"
        logger.info(f"Generating video: {video_desc[:60]}...")

        if is_remotion:
            # Remotion: single video from plan, audio already local
            audio_url_arg = str(src_audio) if src_audio else None
            video_path = self.vgen.generate(
                video_desc, filename,
                audio_url=audio_url_arg,
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
            api_max = getattr(self.vgen, 'duration', 15) or 15
            needs_split = audio_duration and audio_duration > api_max + 1

            if needs_split and src_audio:
                # Split audio into segments ≤ API max duration
                seg_dir = output_media / f"segs_{content_id}"
                segments = TTSSynthesizer.split_audio(
                    str(src_audio), str(seg_dir), max_segment_duration=float(api_max)
                )
                logger.info(f"Audio split into {len(segments)} segments for multi-segment video")

                # Generate video per segment
                segment_videos = []
                for i, seg in enumerate(segments):
                    seg_oss = self._upload_to_oss(seg["path"], self.vgen.model)
                    seg_filename = f"content_{content_id}_seg{i}.mp4"
                    logger.info(f"Generating video segment {i+1}/{len(segments)} ({seg['duration']:.1f}s)...")
                    seg_video = self.vgen.generate(
                        video_desc, seg_filename,
                        audio_url=seg_oss,
                        audio_duration=seg["duration"],
                    )
                    if seg_video:
                        segment_videos.append(seg_video)
                    else:
                        logger.error(f"Video segment {i+1} failed, aborting multi-segment")
                        break

                if segment_videos and len(segment_videos) == len(segments):
                    # Concatenate video segments
                    concat_video = str(output_media / f"content_{content_id}_concat.mp4")
                    concat_ok = self.vgen.concat_videos(segment_videos, concat_video)

                    if concat_ok:
                        # Merge full TTS audio into concatenated video
                        merged = self.vgen._merge_audio(concat_video, str(src_audio))
                        # Burn subtitles using audio duration for timing
                        final = self.vgen._burn_subtitles(
                            merged, subtitle_text, tags, audio_duration,
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

                    # Clean up segment files
                    try:
                        shutil.rmtree(seg_dir, ignore_errors=True)
                    except Exception:
                        pass
            else:
                # Single segment: upload full audio, generate one video
                if src_audio and not audio_oss_url:
                    audio_oss_url = self._upload_to_oss(str(src_audio), self.vgen.model)
                video_path = self.vgen.generate(
                    video_desc, filename,
                    audio_url=audio_oss_url,
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

    def generate_for_topic(self, topic_id: int, topic_title: str, category: str = "dao", platforms: list[str] | None = None) -> list[Path]:
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

            # Enforce Xiaohongshu limits
            if platform == "xiaohongshu":
                if len(title) > 20:
                    logger.info(f"  Title truncated: {len(title)} -> 20 chars")
                    title = title[:20]
                # Body limit: 1000 chars minus tags space
                tags_text = " ".join(tags) if tags else ""
                max_body = 950 - len(tags_text) - 2 if tags_text else 950
                if len(body) > max_body:
                    logger.info(f"  Body truncated: {len(body)} -> {max_body} chars")
                    body = body[:max_body].rsplit("。", 1)[0] + "。"

            # Process inline images
            content_id = topic_id * 100 + len(file_paths)
            body, media_urls = self._process_images(body, content_id, platform)

            # Process inline videos (for douyin and other video-first platforms)
            if platform == "douyin":
                body, video_urls = self._process_videos(body, content_id, platform, tags=tags, category=category)
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

        # Mark topic as processing
        if file_paths:
            self.db.update_topic_status(topic_id, "processing")

        return file_paths

    def run(self, limit: int = 1, category: str | None = None) -> dict:
        """Generate content for all new topics. Returns summary.

        Args:
            limit: Max number of topics to process per category (default: 1).
            category: If set, only generate for this category ('dao' or 'shu').
        """
        if category:
            # 单类别模式：只处理指定类别
            topics = self.db.get_topics(status="new", category=category, limit=limit)
        else:
            # 双类别模式：分别处理"道"和"术"，每类各limit篇
            dao_topics = self.db.get_topics(status="new", category="dao", limit=limit)
            shu_topics = self.db.get_topics(status="new", category="shu", limit=limit)
            topics = dao_topics + shu_topics

        if not topics:
            logger.info("No new topics to generate content for")
            return {"topics_processed": 0, "contents_created": 0}

        total_contents = 0
        for topic in topics:
            paths = self.generate_for_topic(
                topic["id"], topic["title"], category=topic.get("category", "dao")
            )
            total_contents += len(paths)

        summary = {
            "topics_processed": len(topics),
            "contents_created": total_contents,
        }
        logger.info(f"Generation complete: {summary}")
        return summary
