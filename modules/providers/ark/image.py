"""Ark image generation adapter.

Uses Ark's OpenAI-compatible /images/generations endpoint.
"""

import logging
from pathlib import Path

import requests

from .. import ImageProvider
from ...config_model import ArkConfig

logger = logging.getLogger(__name__)


class ArkImageProvider(ImageProvider):
    """Image generation via Volcano Ark (OpenAI-compatible API)."""

    def __init__(self, config: ArkConfig):
        self.api_key = config.api_key
        self.base_url = config.base_url.rstrip("/")
        self.model = config.image_model
        self.image_size = config.image_size
        self.media_dir = Path(config.media_dir)
        self.media_dir.mkdir(parents=True, exist_ok=True)

    @property
    def _headers(self) -> dict:
        return {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}

    def generate(self, prompt: str, filename: str, size: str | None = None) -> str | None:
        if not self.api_key:
            logger.warning("Ark API key not configured, skipping image generation")
            return None

        effective_size = (size or self.image_size).replace("*", "x")
        url = f"{self.base_url}/images/generations"
        data = {"model": self.model, "prompt": prompt, "n": 1, "size": effective_size, "response_format": "url"}

        try:
            logger.info(f"Ark image: {self.model} | {prompt[:50]}...")
            resp = requests.post(url, headers=self._headers, json=data, timeout=300)
            if resp.status_code != 200:
                logger.error(f"Ark image API error: {resp.status_code} - {resp.text}")
                return None

            result = resp.json()
            image_url = self._extract_image_url(result)
            if not image_url:
                logger.error(f"No image URL in Ark response: {result}")
                return None

            logger.info(f"Ark image generated, downloading...")
            return self._download_file(image_url, filename)

        except Exception as e:
            logger.error(f"Ark image generation failed: {e}")
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
            resp = requests.get(url, timeout=300, stream=True)
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
