"""Provider adapter interfaces for image, video, and speech generation.

Each provider backend (dashscope, agnes, ark, mimo, remotion) implements
the relevant interface(s) in its own package under modules/providers/.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from openai import OpenAI


class ImageProvider(ABC):
    """Generate images from text prompts."""

    @abstractmethod
    def generate(self, prompt: str, filename: str, size: Optional[str] = None) -> Optional[str]:
        """Generate an image. Returns local file path or None."""
        ...


class VideoProvider(ABC):
    """Generate videos from text prompts, optionally with audio and subtitles."""

    @abstractmethod
    def generate(
        self,
        prompt: str,
        filename: str,
        audio_path: Optional[str] = None,
        subtitles: Optional[str] = None,
        keywords: Optional[list[str]] = None,
        audio_duration: Optional[float] = None,
        scene_timings: Optional[list[dict]] = None,
        plan: Optional[dict] = None,
    ) -> Optional[str]:
        """Generate a video. Returns local file path or None.

        Args:
            prompt: Video description prompt.
            filename: Output filename.
            audio_path: Local path to audio file. Each provider decides
                how to handle it (upload to OSS, use locally, etc.).
            subtitles: Subtitle text to burn in.
            keywords: Keywords to highlight in subtitles.
            audio_duration: Duration of the audio in seconds.
            scene_timings: Per-scene timing for subtitle sync.
            plan: Pre-generated composition plan (used by Remotion).
        """
        ...


class SpeechProvider(ABC):
    """Synthesize speech from text."""

    @abstractmethod
    def synthesize(
        self,
        text: str,
        filename: str,
        voice: Optional[str] = None,
        speed: float = 1.0,
        response_format: str = "wav",
    ) -> Optional[str]:
        """Synthesize speech audio. Returns local file path or None."""
        ...


class TextProvider(ABC):
    """Create an OpenAI-compatible LLM client from config.

    Each text provider implementation wraps a config subsection
    (e.g. ``ArkConfig`` / ``MiMoConfig``) and exposes an OpenAI-compatible
    client and default model name.
    """

    @abstractmethod
    def create_client(self) -> tuple[Optional["OpenAI"], Optional[str]]:
        """Return (client, model_name).

        ``client`` is ``None`` when the API key is not configured.
        """
        ...

    @property
    @abstractmethod
    def model(self) -> Optional[str]:
        """The default model name for this provider."""
        ...
