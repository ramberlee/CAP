"""Ark speech synthesis adapter.

Uses Ark's custom TTS HTTP chunked API with X-Api-Key auth.
"""

import base64
import json
import logging
from pathlib import Path

import requests

from .. import SpeechProvider
from ...config_model import ArkConfig

logger = logging.getLogger(__name__)

TTS_RESOURCE_ID = "seed-tts-2.0"


class ArkSpeechProvider(SpeechProvider):
    """Speech synthesis via Volcano Ark TTS (HTTP chunked JSON)."""

    def __init__(self, config: ArkConfig):
        self.api_key = config.api_key
        self.base_url = config.base_url.rstrip("/")
        self.tts_url = f"{self.base_url}/plan/tts/unidirectional"
        self.model = config.tts_model
        self.voice = config.tts_voice

        self.media_dir = Path(config.media_dir)
        self.media_dir.mkdir(parents=True, exist_ok=True)

    @property
    def _tts_headers(self) -> dict:
        return {
            "X-Api-Key": self.api_key,
            "X-Api-Resource-Id": TTS_RESOURCE_ID,
            "Content-Type": "application/json",
            "Connection": "keep-alive",
            "X-Control-Require-Usage-Tokens-Return": "*",
        }

    def synthesize(
        self,
        text: str,
        filename: str,
        voice: str | None = None,
        speed: float = 1.0,
        response_format: str = "wav",
    ) -> str | None:
        if not self.api_key:
            logger.warning("Ark API key not configured, skipping TTS")
            return None

        if not filename.endswith(f".{response_format}"):
            filename = filename.rsplit(".", 1)[0] + f".{response_format}"

        payload = {
            "req_params": {
                "text": text,
                "speaker": voice or self.voice,
                "audio_params": {"format": response_format, "sample_rate": 24000},
            }
        }
        if speed != 1.0:
            payload["req_params"]["speed_ratio"] = speed

        session = requests.Session()
        response = None
        try:
            logger.info(f"Ark TTS: speaker={voice or self.voice} | {text[:60]}...")
            response = session.post(self.tts_url, headers=self._tts_headers, json=payload, stream=True, timeout=120)

            if response.status_code != 200:
                logger.error(f"Ark TTS error: {response.status_code} - {response.text[:500]}")
                return None

            audio_data = bytearray()
            for line in response.iter_lines(decode_unicode=True):
                if not line:
                    continue
                try:
                    chunk = json.loads(line)
                except json.JSONDecodeError:
                    continue

                code = chunk.get("code", 0)
                if code == 20000000:
                    break
                if code > 0:
                    logger.error(f"Ark TTS error: code={code}, data={chunk}")
                    return None
                if code == 0 and "data" in chunk and chunk["data"]:
                    audio_data.extend(base64.b64decode(chunk["data"]))

            if not audio_data:
                logger.error("Ark TTS: no audio data received")
                return None

            filepath = self.media_dir / filename
            filepath.write_bytes(bytes(audio_data))
            logger.info(f"Ark TTS saved: {filepath} ({len(audio_data)} bytes)")
            return str(filepath)

        except Exception as e:
            logger.error(f"Ark TTS failed: {e}")
            return None
        finally:
            if response:
                response.close()
            session.close()
