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

logger = logging.getLogger(__name__)

PLATFORMS = ["xiaohongshu", "wechat", "douyin"]
IMAGE_PLACEHOLDER_RE = re.compile(r"\[IMAGE:(.*?)]")


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
        self.store = ContentStore(
            output_dir=config.get("output_dir", "output"),
            media_dir=config.get("dashscope", {}).get("media_dir", "media"),
        )
        self._templates = {}

    def _load_template(self, platform: str) -> str:
        if platform not in self._templates:
            template_path = Path(f"templates/{platform}.md")
            if not template_path.exists():
                raise FileNotFoundError(f"Template not found: {template_path}")
            self._templates[platform] = template_path.read_text(encoding="utf-8")
        return self._templates[platform]

    def _generate_for_platform(self, topic: str, platform: str) -> Optional[dict]:
        """Generate content for a specific platform."""
        template = self._load_template(platform)
        prompt = template.replace("{topic}", topic)

        logger.info(f"Generating {platform} content for: {topic[:50]}...")

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                max_tokens=self.gen_config.get("max_tokens", 4096),
                temperature=self.gen_config.get("temperature", 0.7),
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "你是MiMo，是小米公司研发的AI智能助手。"
                            "你正在为一个AI领域的内容账号创作内容，账号定位是：「AI时代必备心法。在这里，看懂AI的道与术。」"
                            "所有内容都需要从AI视角切入，提供AI时代的洞察、工具、方法论。"
                            "请严格按照要求的JSON格式输出。"
                        ),
                    },
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

    def generate_for_topic(self, topic_id: int, topic_title: str, platforms: list[str] | None = None) -> list[Path]:
        """Generate content for a topic across specified platforms. Returns file paths."""
        platforms = platforms or self.config.get("generation", {}).get("platforms", PLATFORMS)
        file_paths = []

        for platform in platforms:
            result = self._generate_for_platform(topic_title, platform)
            if not result:
                continue

            title = result.get("title", "")
            body = result.get("body", result.get("script", ""))
            tags = result.get("tags", [])

            # Process inline images
            content_id = topic_id * 100 + len(file_paths)
            body, media_urls = self._process_images(body, content_id, platform)

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

    def run(self, limit: int = 5) -> dict:
        """Generate content for all new topics. Returns summary."""
        topics = self.db.get_topics(status="new", limit=limit)
        if not topics:
            logger.info("No new topics to generate content for")
            return {"topics_processed": 0, "contents_created": 0}

        total_contents = 0
        for topic in topics:
            paths = self.generate_for_topic(topic["id"], topic["title"])
            total_contents += len(paths)

        summary = {
            "topics_processed": len(topics),
            "contents_created": total_contents,
        }
        logger.info(f"Generation complete: {summary}")
        return summary
