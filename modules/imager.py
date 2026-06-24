"""Image generation module — delegates to the appropriate ImageProvider adapter.

Existing consumers (generator.py) import ImageGenerator from this module.
"""

import logging
import time
from pathlib import Path

from modules.providers import ImageProvider
from modules.providers.dashscope.image import DashScopeImageProvider
from modules.providers.agnes.image import AgnesImageProvider
from modules.providers.ark.image import ArkImageProvider

logger = logging.getLogger(__name__)


class ImageGenerator:
    """Image generation facade — routes to the configured provider adapter.

    Provider is selected by generation.image_provider in config:
      "dashscope" (default), "agnes", or "ark".
    """

    def __init__(self, config: dict):
        gen_config = config.get("generation", {})
        provider_name = gen_config.get("image_provider", "dashscope")
        self.media_dir = Path(config.get("dashscope", {}).get("media_dir", "media"))
        self.media_dir.mkdir(parents=True, exist_ok=True)

        # Instantiate the correct adapter
        if provider_name == "agnes":
            self._provider: ImageProvider = AgnesImageProvider(config)
        elif provider_name == "ark":
            self._provider: ImageProvider = ArkImageProvider(config)
        else:
            self._provider: ImageProvider = DashScopeImageProvider(config)

        logger.info(f"ImageGenerator using {provider_name} backend")

    def generate(self, prompt: str, filename: str) -> str | None:
        """Generate an image from a text prompt. Returns local file path or None."""
        return self._provider.generate(prompt, filename)

    def generate_for_content(self, content_id: int, image_prompt: str) -> str | None:
        """Generate image for a content item. Returns local path."""
        filename = f"content_{content_id}_{int(time.time())}.png"
        return self.generate(image_prompt, filename)
