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
            return IMAGE_PLACEHOLDER_RE.sub("", body), []

        placeholders = list(IMAGE_PLACEHOLDER_RE.finditer(body))
        if not placeholders:
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
            else:
                # Remove placeholder if generation failed
                processed = processed.replace(match.group(0), "", 1)

        return processed, media_urls

    def _process_videos(self, body: str, content_id: int, platform: str) -> tuple[str, list[str]]:
        """Replace [VIDEO:description] placeholders with generated videos.

        For douyin: generates TTS audio from the script, uploads to DashScope OSS,
        then passes audio_url to the video model for voice-synced video.

        Returns (processed_body, list_of_local_video_paths).
        """
        if not self.vgen:
            # No video generator, just strip placeholders
            return VIDEO_PLACEHOLDER_RE.sub("", body), []

        placeholders = list(VIDEO_PLACEHOLDER_RE.finditer(body))

        # Prepare output media dir for this platform
        output_media = Path("output") / platform / "media"
        output_media.mkdir(parents=True, exist_ok=True)

        # Generate TTS audio from script text (strip video placeholders first)
        audio_oss_url = None
        if self.tts:
            script_text = VIDEO_PLACEHOLDER_RE.sub("", body).strip()
            audio_filename = f"content_{content_id}_tts.wav"
            # Video model max duration is 30s, leave 2s margin
            max_audio_duration = min(self.vgen.duration, 28) if self.vgen else 28
            logger.info("Generating TTS audio for script...")
            audio_path = self.tts.synthesize(script_text, audio_filename, max_duration=max_audio_duration)
            if audio_path:
                # Copy audio to output dir
                src_audio = Path(audio_path)
                dst_audio = output_media / src_audio.name
                shutil.copy2(src_audio, dst_audio)

                # Upload to DashScope OSS for video model
                audio_oss_url = self._upload_to_oss(str(src_audio), self.vgen.model)

        media_urls = []
        processed = body

        # If no [VIDEO:...] placeholder found, generate one from script text
        if not placeholders:
            script_for_video = VIDEO_PLACEHOLDER_RE.sub("", body).strip()
            desc = f"总时长15秒。{script_for_video[:200]}"
            logger.info(f"No [VIDEO:...] placeholder found, auto-generating video description...")
            placeholders_desc = [desc]
        else:
            placeholders_desc = [m.group(1).strip() for m in placeholders]

        for i, desc in enumerate(placeholders_desc):
            filename = f"content_{content_id}_{i+1}.mp4"
            logger.info(f"Generating video {i+1}/{len(placeholders_desc)}: {desc[:50]}...")

            video_path = self.vgen.generate(desc, filename, audio_url=audio_oss_url)
            if video_path:
                # Copy to output dir
                src = Path(video_path)
                dst = output_media / src.name
                shutil.copy2(src, dst)

                rel_path = f"media/{src.name}"
                if placeholders:
                    # Replace existing placeholder
                    processed = processed.replace(placeholders[i].group(0), f"\n\n[视频]({rel_path})\n", 1)
                else:
                    # Auto-generated: append video reference
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
                body, video_urls = self._process_videos(body, content_id, platform)
                media_urls.extend(video_urls)

            filepath = self.store.save_content(
                platform=platform,
                title=title,
                body=body,
                tags=tags,
                media_urls=media_urls,
                topic_id=topic_id,
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
