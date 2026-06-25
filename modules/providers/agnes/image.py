"""Agnes image generation adapter.

Uses Agnes AI's OpenAI-compatible /v1/images/generations endpoint.
"""

import logging
from pathlib import Path

import requests

from .. import ImageProvider
from ...config_model import AgnesConfig

logger = logging.getLogger(__name__)

AGNES_API_BASE = "https://apihub.agnes-ai.com"
AGNES_IMAGE_ENDPOINT = f"{AGNES_API_BASE}/v1/images/generations"
DEFAULT_IMAGE_MODEL = "agnes-image-2.1-flash"


class AgnesImageProvider(ImageProvider):
    """Image generation via Agnes AI API."""

    def __init__(self, config: AgnesConfig):
        self.api_key = config.api_key
        self.model = config.image_model
        self.media_dir = Path(config.media_dir)
        self.media_dir.mkdir(parents=True, exist_ok=True)

    @property
    def _headers(self) -> dict:
        return {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}

    def generate(self, prompt: str, filename: str, size: str | None = None) -> str | None:
        if not self.api_key:
            logger.warning("Agnes API key not configured, skipping image generation")
            return None

        effective_size = size or "1024x768"

        data = {"model": self.model, "prompt": prompt, "size": effective_size,
                "extra_body": {"response_format": "url"}}

        try:
            logger.info(f"Agnes image: {prompt[:50]}...")
            resp = requests.post(AGNES_IMAGE_ENDPOINT, headers=self._headers, json=data, timeout=300)
            if resp.status_code != 200:
                logger.error(f"Agnes image API error: {resp.status_code} - {resp.text}")
                return None

            result = resp.json()
            image_url = self._extract_image_url(result)
            if not image_url:
                logger.error(f"No image URL in Agnes response: {result}")
                return None

            return self._download_file(image_url, filename)

        except Exception as e:
            logger.error(f"Agnes image generation failed: {e}")
            return None

    @staticmethod
    def _extract_image_url(result: dict) -> str | None:
        data = result.get("data", [])
        if data and isinstance(data, list):
            for item in data:
                if isinstance(item, dict) and item.get("url"):
                    return item["url"]
        return None

    def _download_file(self, url: str, filename: str) -> str | None:
        try:
            resp = requests.get(url, timeout=120, stream=True)
            resp.raise_for_status()
            if not filename.endswith((".png", ".jpg", ".jpeg")):
                filename = filename.rsplit(".", 1)[0] + ".png"
            filepath = self.media_dir / filename
            with open(filepath, "wb") as f:
                for chunk in resp.iter_content(chunk_size=8192):
                    f.write(chunk)
            logger.info(f"Image saved: {filepath}")
            return str(filepath)
        except Exception as e:
            logger.error(f"File download failed: {e}")
            return None
