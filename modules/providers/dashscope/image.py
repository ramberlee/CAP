"""DashScope image generation adapter.

Extracted from modules/imager.py — qwen-image-2.0* uses MultiModalConversation (sync),
older models use ImageSynthesis (async polling).
"""

import logging
from pathlib import Path

import dashscope
from dashscope import ImageSynthesis, MultiModalConversation

from .. import ImageProvider

logger = logging.getLogger(__name__)

QWEN_V2_MODELS = {
    "qwen-image-2.0", "qwen-image-2.0-pro",
    "qwen-image-2.0-2026-03-03", "qwen-image-2.0-pro-2026-04-22",
    "qwen-image-2.0-pro-2026-03-03",
}

DEFAULT_NEGATIVE_PROMPT = "低分辨率，低画质，肢体畸形，手指畸形，画面过饱和，蜡像感，画面具有AI感，构图混乱，文字模糊，扭曲"


class DashScopeImageProvider(ImageProvider):
    """Image generation via DashScope (Alibaba Cloud)."""

    def __init__(self, config: dict):
        ds_config = config.get("dashscope", {})
        self.api_key = ds_config.get("api_key", "")
        self.model = ds_config.get("model", "qwen-image")
        self.size = ds_config.get("size", "1472*1104")
        self.media_dir = Path(ds_config.get("media_dir", "media"))
        self.media_dir.mkdir(parents=True, exist_ok=True)
        dashscope.api_key = self.api_key

    def generate(self, prompt: str, filename: str, size: str | None = None) -> str | None:
        if not self.api_key:
            logger.warning("DashScope API key not configured, skipping image generation")
            return None

        effective_size = size or self.size
        is_v2 = self.model in QWEN_V2_MODELS or "2.0" in self.model

        if is_v2:
            return self._generate_v2(prompt, filename, effective_size)
        else:
            return self._generate_v1(prompt, filename, effective_size)

    def _generate_v2(self, prompt: str, filename: str, size: str) -> str | None:
        """Generate using MultiModalConversation SDK (sync, qwen-image-2.0*)."""
        messages = [{"role": "user", "content": [{"text": prompt}]}]
        try:
            logger.info(f"Generating image with {self.model}: {prompt[:50]}...")
            response = MultiModalConversation.call(
                model=self.model, messages=messages,
                api_key=self.api_key, result_format="message",
                size=size, prompt_extend=True, watermark=False,
                negative_prompt=DEFAULT_NEGATIVE_PROMPT,
            )
            if response.status_code != 200:
                logger.error(f"Image generation failed: {response.code} - {response.message}")
                return None

            choices = response.output.get("choices", [])
            if choices:
                content = choices[0].get("message", {}).get("content", [])
                for item in content:
                    if item.get("image"):
                        return self._download_image(item["image"], filename)
            logger.error("No image in response")
            return None
        except Exception as e:
            logger.error(f"Image generation failed: {e}")
            return None

    def _generate_v1(self, prompt: str, filename: str, size: str) -> str | None:
        """Generate using ImageSynthesis SDK (async, older models)."""
        try:
            logger.info(f"Generating image with {self.model}: {prompt[:50]}...")
            response = ImageSynthesis.call(model=self.model, prompt=prompt, n=1, size=size, api_key=self.api_key)
            if response.status_code != 200:
                logger.error(f"Image generation failed: {response.code} - {response.message}")
                return None

            task_id = response.output.get("task_id")
            if not task_id:
                logger.error("No task_id in response")
                return None

            logger.info(f"Image task submitted: {task_id}")
            result = ImageSynthesis.wait(task_id, api_key=self.api_key)
            if result.status_code != 200 or result.output.get("task_status") != "SUCCEEDED":
                logger.error(f"Image task failed: {result.output}")
                return None

            results = result.output.get("results", [])
            if results:
                return self._download_image(results[0]["url"], filename)
            logger.error("No image in succeeded response")
            return None
        except Exception as e:
            logger.error(f"Image generation failed: {e}")
            return None

    def _download_image(self, image_url: str, filename: str) -> str | None:
        """Download image from URL and save locally."""
        import requests
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
