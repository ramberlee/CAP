"""MiMo speech synthesis adapter.

Uses MiMo TTS via OpenAI-compatible /v1/chat/completions endpoint with audio parameter.
"""

import base64
import logging
from pathlib import Path

from openai import OpenAI

from .. import SpeechProvider
from ...config_model import MiMoConfig

logger = logging.getLogger(__name__)

DEFAULT_VOICE = "Chloe"
DEFAULT_MODEL = "mimo-v2.5-tts"
DEFAULT_BASE_URL = "https://api.xiaomimimo.com/v1"


class MiMoSpeechProvider(SpeechProvider):
    """Speech synthesis via MiMo TTS (OpenAI-compatible chat completions with audio param)."""

    def __init__(self, config: MiMoConfig):
        api_key = config.api_key
        base_url = config.base_url
        self.model = config.tts_model
        self.voice = config.tts_voice

        self.media_dir = Path("media")
        self.media_dir.mkdir(parents=True, exist_ok=True)

        self.client = OpenAI(api_key=api_key, base_url=base_url) if api_key else None

    def synthesize(
        self,
        text: str,
        filename: str,
        voice: str | None = None,
        speed: float = 1.0,
        response_format: str = "wav",
    ) -> str | None:
        if not self.client or not self.client.api_key:
            logger.warning("MiMo API key not configured, skipping TTS")
            return None

        if not filename.endswith(".wav"):
            filename = filename.rsplit(".", 1)[0] + ".wav"

        filepath = self.media_dir / filename

        try:
            logger.info(f"MiMo TTS ({self.model}): {text[:60]}...")

            completion = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "user", "content": "用自然、有感染力的中文语调朗读。"},
                    {"role": "assistant", "content": text},
                ],
                audio={"format": response_format, "voice": voice or self.voice},
            )

            message = completion.choices[0].message
            if not hasattr(message, "audio") or message.audio is None:
                logger.error("No audio data in TTS response")
                return None

            audio_bytes = base64.b64decode(message.audio.data)
            filepath.write_bytes(audio_bytes)

            logger.info(f"MiMo TTS saved: {filepath} ({len(audio_bytes)} bytes)")
            return str(filepath)

        except Exception as e:
            logger.warning(f"MiMo TTS failed: {e}")
            return None
