"""Provider factory — creates provider instances from AppConfig.

Providers are auto-discovered by scanning subdirectories under
modules/providers/.  Adding a new provider only requires creating
a new subdirectory with provider class(es) that inherit from the
appropriate base class — no factory code changes needed.
"""

import importlib
import inspect
import logging
from pathlib import Path
from typing import Optional
from openai import OpenAI

from modules.config_model import AppConfig
from modules import providers as providers_module
from modules.providers import ImageProvider, VideoProvider, SpeechProvider, TextProvider

logger = logging.getLogger(__name__)


# ── Auto-discovery registry ──────────────────────────────────────────────
# Populated at import time by scanning provider subdirectories.
# Structure: provider_name → {base_class: implementation_class}

_REGISTRY: dict[str, dict[type, type]] = {}

# Dynamically collect all ABCs defined in modules/providers/__init__.py
# (ImageProvider, VideoProvider, SpeechProvider, TextProvider, …).
# Any class defined in that file and inheriting from ABC is treated as a
# base type that concrete providers can implement.
_BASE_ABC = {
    cls
    for _, cls in inspect.getmembers(providers_module, inspect.isclass)
    if getattr(cls, "__module__", "") == providers_module.__name__
}


def _discover() -> None:
    """Scan modules/providers/ subdirectories and register provider classes."""
    root = Path(__file__).parent
    for entry in sorted(root.iterdir()):
        if not entry.is_dir() or entry.name.startswith("_") or entry.name == "__pycache__":
            continue

        name = entry.name
        found: dict[type, type] = {}

        for py_file in sorted(entry.glob("*.py")):
            if py_file.name == "__init__.py":
                continue

            try:
                mod = importlib.import_module(f"modules.providers.{name}.{py_file.stem}")
            except Exception as exc:
                logger.debug("Skipping %s/%s: %s", name, py_file.name, exc)
                continue

            for _, cls in inspect.getmembers(mod, inspect.isclass):
                if cls in _BASE_ABC:
                    continue  # skip the abstract base itself
                for base in cls.__mro__:
                    if base in _BASE_ABC:
                        found[base] = cls
                        break

        if found:
            _REGISTRY[name] = found
            logger.debug(
                "Discovered provider '%s': %s",
                name,
                {k.__name__: v.__name__ for k, v in found.items()},
            )


_discover()


class ProviderFactory:
    """Factory for creating provider instances from typed AppConfig.

    Provider classes are auto-discovered from subdirectories under
    ``modules/providers/``.  New backends can be added by simply creating
    a new subdirectory — no changes to this factory are needed.

    Usage::

        factory = ProviderFactory(config)
        image_provider = factory.create_image_provider()
        video_provider = factory.create_video_provider()
        speech_provider = factory.create_speech_provider()
        text_provider = factory.create_text_provider()
        client, model = text_provider.create_client()
    """

    def __init__(self, config: AppConfig):
        self.config = config

    # ── Generic provider builder ───────────────────────────────────────

    def _build(self, base: type, cfg_key: str) -> Optional:
        """Look up and instantiate a provider.

        Automatically inspects the class constructor signature to decide
        which arguments to pass:

        * ``__init__(self, config: AppConfig, ...)`` → pass ``self.config``
        * ``__init__(self, config: SubSectionConfig, ...)`` → pass the
          matching config subsection (e.g. ``self.config.ark``)

        Args:
            base: One of ``ImageProvider``, ``VideoProvider``, ``SpeechProvider``.
            cfg_key: Config field name (e.g. ``"image_provider"``).

        Returns:
            Provider instance or ``None`` if unknown / not implemented.
        """
        name = getattr(self.config.generation, cfg_key)
        mapping = _REGISTRY.get(name)
        if not mapping:
            logger.warning("Unknown provider '%s' for config.%s", name, cfg_key)
            return None

        cls = mapping.get(base)
        if not cls:
            logger.warning(
                "Provider '%s' does not implement %s", name, base.__name__
            )
            return None

        # Inspect __init__ signature to determine config passing strategy
        sig = inspect.signature(cls.__init__)
        params = list(sig.parameters.values())

        # param[0] is always 'self'; param[1] is the first real argument
        if len(params) >= 2:
            param_hint = params[1].annotation
            # If the first param hints at AppConfig, pass the full config
            if param_hint is AppConfig or (
                isinstance(param_hint, str) and "AppConfig" in param_hint
            ):
                return cls(self.config)

        # Default: pass the provider's config subsection
        subsection = getattr(self.config, name, None)
        if base is VideoProvider:
            return cls(subsection, generation=self.config.generation)
        return cls(subsection)

    # ── Image providers ────────────────────────────────────────────────

    def create_image_provider(self) -> Optional[ImageProvider]:
        """Select image provider by ``generation.image_provider``."""
        return self._build(ImageProvider, "image_provider")

    # ── Video providers ────────────────────────────────────────────────

    def create_video_provider(self) -> Optional[VideoProvider]:
        """Select video provider by ``generation.video_provider``."""
        return self._build(VideoProvider, "video_provider")

    # ── Speech providers ───────────────────────────────────────────────

    def create_speech_provider(self) -> Optional[SpeechProvider]:
        """Select speech provider by ``generation.text_provider``."""
        return self._build(SpeechProvider, "text_provider")

    # ── Video config resolution ────────────────────────────────────────

    def resolve_video_config(self) -> tuple[str, str, int]:
        """Resolve video model, size, and max duration from the active provider's config.

        Dynamically looks up the config subsection by provider name
        (``self.config.<provider_name>``).  Returns empty values when
        the subsection does not exist.

        Returns:
            Tuple of (video_model, video_size, video_max_duration).
        """
        provider = self.config.generation.video_provider
        cfg = getattr(self.config, provider, None)
        if cfg is None:
            logger.warning("No config subsection found for video provider '%s'", provider)
            return ("", "", 0)
        model = getattr(cfg, "video_model", provider)
        return (model, cfg.video_size, cfg.video_duration)

    # ── Text providers ──────────────────────────────────────────────────

    def create_text_provider(self) -> Optional[TextProvider]:
        """Select text provider by ``generation.text_provider``."""
        return self._build(TextProvider, "text_provider")

    def create_llm_client(self) -> tuple[Optional[OpenAI], Optional[str]]:
        """Backward-compat wrapper — delegates to ``create_text_provider()``.

        Returns:
            Tuple of (client, model_name). Either may be ``None`` if the
            provider's API key is not configured.
        """
        provider = self.create_text_provider()
        if provider is None:
            return None, None
        return provider.create_client()
