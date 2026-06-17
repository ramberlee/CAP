"""Image generation module with DashScope and Agnes backends."""

import logging
import time
from pathlib import Path
import requests
import dashscope
from dashscope import ImageSynthesis, MultiModalConversation
from modules.agnes_client import AgnesClient

logger = logging.getLogger(__name__)

# qwen-image-2.0 / qwen-image-2.0-pro use multimodal-generation endpoint (sync)
# qwen-image / qwen-image-plus / qwen-image-max use text2image endpoint (async)
QWEN_V2_MODELS = {
    "qwen-image-2.0", "qwen-image-2.0-pro",
    "qwen-image-2.0-2026-03-03", "qwen-image-2.0-pro-2026-04-22",
    "qwen-image-2.0-pro-2026-03-03",
}


class ImageGenerator:
    def __init__(self, config: dict):
        # Determine provider: "dashscope" (default) or "agnes"
        gen_config = config.get("generation", {})
        self.provider = gen_config.get("image_provider", "dashscope")

        ds_config = config.get("dashscope", {})
        self.api_key = ds_config.get("api_key", "")
        self.model = ds_config.get("model", "qwen-image")
        self.size = ds_config.get("size", "1472*1104")
        self.media_dir = Path(ds_config.get("media_dir", "media"))
        self.media_dir.mkdir(parents=True, exist_ok=True)

        # Initialize provider-specific client
        if self.provider == "agnes":
            self.agnes_client = AgnesClient(config)
            logger.info(f"ImageGenerator using Agnes AI backend (model: {self.agnes_client.image_model})")
        else:
            # Configure DashScope SDK
            dashscope.api_key = self.api_key

    def generate(self, prompt: str, filename: str) -> str | None:
        """Generate an image from a text prompt. Returns local file path or None."""
        if self.provider == "agnes":
            return self._generate_agnes(prompt, filename)

        # DashScope backend
        if not self.api_key:
            logger.warning("DashScope API key not configured, skipping image generation")
            return None

        if self.model in QWEN_V2_MODELS or "2.0" in self.model:
            return self._generate_v2(prompt, filename)
        else:
            return self._generate_v1(prompt, filename)

    def _generate_agnes(self, prompt: str, filename: str) -> str | None:
        """Generate using Agnes AI API."""
        logger.info(f"Generating image via Agnes AI: {prompt[:50]}...")
        # Convert size format from "1472*1104" to "1472x1104" for Agnes API
        agnes_size = self.size.replace("*", "x")
        return self.agnes_client.generate_image(
            prompt=prompt,
            filename=filename,
            size=agnes_size,
        )

    def _generate_v2(self, prompt: str, filename: str) -> str | None:
        """Generate using MultiModalConversation SDK (sync, qwen-image-2.0*)."""
        messages = [
            {
                "role": "user",
                "content": [{"text": prompt}],
            }
        ]

        try:
            logger.info(f"Generating image with {self.model}: {prompt[:50]}...")
            response = MultiModalConversation.call(
                model=self.model,
                messages=messages,
                api_key=self.api_key,
                result_format="message",
                size=self.size,
                prompt_extend=True,
                watermark=False,
                negative_prompt="低分辨率，低画质，肢体畸形，手指畸形，画面过饱和，蜡像感，画面具有AI感，构图混乱，文字模糊，扭曲",
            )

            if response.status_code != 200:
                logger.error(f"Image generation failed: {response.code} - {response.message}")
                return None

            # Extract image URL from response
            choices = response.output.get("choices", [])
            if choices:
                content = choices[0].get("message", {}).get("content", [])
                for item in content:
                    if item.get("image"):
                        return self._download_image(item["image"], filename)
            logger.error(f"No image in response")
            return None

        except Exception as e:
            logger.error(f"Image generation failed: {e}")
            return None

    def _generate_v1(self, prompt: str, filename: str) -> str | None:
        """Generate using ImageSynthesis SDK (async, older models)."""
        try:
            logger.info(f"Generating image with {self.model}: {prompt[:50]}...")
            response = ImageSynthesis.call(
                model=self.model,
                prompt=prompt,
                n=1,
                size=self.size,
                api_key=self.api_key,
            )

            if response.status_code != 200:
                logger.error(f"Image generation failed: {response.code} - {response.message}")
                return None

            task_id = response.output.get("task_id")
            if not task_id:
                logger.error(f"No task_id in response")
                return None

            logger.info(f"Image task submitted: {task_id}")
            result = ImageSynthesis.wait(task_id, api_key=self.api_key)

            if result.status_code != 200 or result.output.get("task_status") != "SUCCEEDED":
                logger.error(f"Image task failed: {result.output}")
                return None

            results = result.output.get("results", [])
            if results:
                return self._download_image(results[0]["url"], filename)
            logger.error(f"No image in succeeded response")
            return None

        except Exception as e:
            logger.error(f"Image generation failed: {e}")
            return None

    def _download_image(self, image_url: str, filename: str) -> str | None:
        """Download image from URL and save locally. Returns local path."""
        try:
            resp = requests.get(image_url, timeout=30)
            resp.raise_for_status()

            filepath = self.media_dir / filename
            filepath.write_bytes(resp.content)
            logger.info(f"Image saved: {filepath} ({len(resp.content)} bytes)")
            return str(filepath)
        except Exception as e:
            logger.error(f"Image download failed: {e}")
            return None

    def generate_for_content(self, content_id: int, image_prompt: str) -> str | None:
        """Generate image for a content item. Returns local path."""
        filename = f"content_{content_id}_{int(time.time())}.png"
        return self.generate(image_prompt, filename)
