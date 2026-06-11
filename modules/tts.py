"""TTS (Text-to-Speech) module using MiMo TTS API (chat completions compatible).

MiMo TTS uses the /v1/chat/completions endpoint with a special message format:
- user: voice/tone description
- assistant: the text to speak
- audio parameter specifies format and voice
- Response contains base64-encoded audio in message.audio.data
"""

import base64
import io
import logging
import re
import struct
import wave
from pathlib import Path
from openai import OpenAI

logger = logging.getLogger(__name__)

# Script markers to strip before TTS
SCRIPT_MARKER_RE = re.compile(r"【[^】]+】")
SEPARATOR_RE = re.compile(r"\n*---\n*")

# Default voice design prompt for Chinese speech
DEFAULT_VOICE_PROMPT = "用自然、亲切、有感染力的中文语调朗读，像一位专业的短视频口播博主。"


class TTSSynthesizer:
    def __init__(self, config: dict):
        mimo_config = config.get("mimo", {})
        api_key = mimo_config.get("api_key", "")
        base_url = mimo_config.get("tts_base_url", mimo_config.get("base_url", "https://api.xiaomimimo.com/v1"))
        self.model = mimo_config.get("tts_model", "mimo-v2.5-tts")
        self.voice = mimo_config.get("tts_voice", "Chloe")
        self.voice_prompt = mimo_config.get("tts_voice_prompt", DEFAULT_VOICE_PROMPT)
        self.client = OpenAI(api_key=api_key, base_url=base_url)

        ds_config = config.get("dashscope", {})
        self.media_dir = Path(ds_config.get("media_dir", "media"))
        self.media_dir.mkdir(parents=True, exist_ok=True)

    def _clean_script(self, script: str) -> str:
        """Strip script markers and separators, return plain spoken text."""
        text = SCRIPT_MARKER_RE.sub("", script)
        text = SEPARATOR_RE.sub("，", text)
        text = re.sub(r"\s+", " ", text).strip()
        return text

    @staticmethod
    def get_audio_duration(filepath: str) -> float:
        """Get duration of a WAV file in seconds."""
        try:
            with wave.open(filepath, "rb") as wf:
                frames = wf.getnframes()
                rate = wf.getframerate()
                return frames / rate if rate > 0 else 0
        except Exception:
            return 0

    @staticmethod
    def trim_audio(filepath: str, max_seconds: float) -> str:
        """Trim WAV file to max_seconds. Returns the same filepath."""
        try:
            with wave.open(filepath, "rb") as wf:
                rate = wf.getframerate()
                channels = wf.getnchannels()
                sampwidth = wf.getsampwidth()
                max_frames = int(rate * max_seconds)
                frames = wf.readframes(min(wf.getnframes(), max_frames))

            with wave.open(filepath, "wb") as out:
                out.setnchannels(channels)
                out.setsampwidth(sampwidth)
                out.setframerate(rate)
                out.writeframes(frames)
            return filepath
        except Exception as e:
            logger.warning(f"Audio trim failed: {e}")
            return filepath

    def synthesize(self, script: str, filename: str, max_duration: float = 28) -> tuple[str, float, float] | None:
        """Generate audio from script text. Returns (file_path, duration_seconds) or None.

        Args:
            script: The oral script text (may contain markers like 【钩子】).
            filename: Output filename (e.g. "content_100_1.wav").
            max_duration: Maximum audio duration in seconds.
        """
        if not self.client.api_key:
            logger.warning("MiMo API key not configured, skipping TTS")
            return None

        text = self._clean_script(script)
        if not text:
            logger.warning("Empty script after cleaning, skipping TTS")
            return None

        # Ensure .wav extension (MiMo TTS returns wav by default)
        if not filename.endswith(".wav"):
            filename = filename.rsplit(".", 1)[0] + ".wav"

        filepath = self.media_dir / filename

        try:
            logger.info(f"Generating TTS with {self.model}: {text[:60]}...")

            completion = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": self.voice_prompt,
                    },
                    {
                        "role": "assistant",
                        "content": text,
                    },
                ],
                audio={
                    "format": "wav",
                    "voice": self.voice,
                },
            )

            message = completion.choices[0].message
            if not hasattr(message, "audio") or message.audio is None:
                logger.error("No audio data in TTS response")
                return None

            audio_bytes = base64.b64decode(message.audio.data)
            filepath.write_bytes(audio_bytes)

            # Check and trim audio duration to fit video model limit
            duration = self.get_audio_duration(str(filepath))
            original_duration = duration
            if duration > max_duration:
                logger.info(f"TTS audio {duration:.1f}s exceeds {max_duration}s limit, trimming...")
                self.trim_audio(str(filepath), max_duration)
                duration = self.get_audio_duration(str(filepath))

            logger.info(f"TTS saved: {filepath} ({len(audio_bytes)} bytes, {duration:.1f}s)")
            return str(filepath), duration, original_duration

        except Exception as e:
            logger.warning(f"TTS generation failed (video will have no voice): {e}")
            return None
