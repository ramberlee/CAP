"""Provider adapter interfaces for image, video, and speech generation.

Each provider backend (dashscope, agnes, ark, mimo, remotion) implements
the relevant interface(s) in its own package under modules/providers/.
"""

from abc import ABC, abstractmethod
from typing import Optional


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
        audio_url: Optional[str] = None,
        subtitles: Optional[str] = None,
        keywords: Optional[list[str]] = None,
        audio_duration: Optional[float] = None,
        scene_timings: Optional[list[dict]] = None,
    ) -> Optional[str]:
        """Generate a video. Returns local file path or None."""
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
