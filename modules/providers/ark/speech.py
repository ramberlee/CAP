"""Ark speech synthesis adapter.

Uses Ark's custom TTS HTTP chunked API with X-Api-Key auth.
"""

import base64
import json
import logging
import struct
from pathlib import Path

import requests

from .. import SpeechProvider
from ...config_model import ArkConfig

logger = logging.getLogger(__name__)

class ArkSpeechProvider(SpeechProvider):
    """Speech synthesis via Volcano Ark TTS (HTTP chunked JSON)."""

    def __init__(self, config: ArkConfig):
        self.api_key = config.api_key
        self.base_url = config.base_url.rstrip("/")
        # Agent Plan TTS uses openspeech domain, not the chat base_url
        self.tts_url = "https://openspeech.bytedance.com/api/v3/plan/tts/unidirectional"
        self.model = config.tts_model
        self.voice = config.tts_voice
        self.resource_id = config.tts_resource_id

        self.media_dir = Path(config.media_dir)
        self.media_dir.mkdir(parents=True, exist_ok=True)

    @property
    def _tts_headers(self) -> dict:
        return {
            "X-Api-Key": self.api_key,
            "X-Api-Resource-Id": self.resource_id,
            "Content-Type": "application/json",
            "Connection": "keep-alive",
            "X-Control-Require-Usage-Tokens-Return": "*",
        }

    @staticmethod
    def _fix_wav_header(audio_data: bytearray | bytes) -> bytes:
        """Fix WAV header data chunk size if it's incorrect.

        The Ark TTS API sometimes returns a WAV with data chunk size set to
        2147483647 (max int32), which causes get_audio_duration() to return
        a bogus value (~89478s for an 80s clip). This function detects that
        and recalculates the correct size from the actual bytes.
        """
        data = bytes(audio_data)
        if data[:4] != b'RIFF' or data[8:12] != b'WAVE':
            return data  # Not a WAV, return as-is

        pos = 12
        while pos < len(data) - 8:
            chunk_id = data[pos:pos + 4]
            chunk_size = struct.unpack('<I', data[pos + 4:pos + 8])[0]
            if chunk_id == b'data':
                actual_data_size = len(data) - pos - 8
                if chunk_size != actual_data_size:
                    # Fix data chunk size
                    data_arr = bytearray(data)
                    struct.pack_into('<I', data_arr, pos + 4, actual_data_size)
                    # Fix RIFF total size
                    struct.pack_into('<I', data_arr, 4, len(data_arr) - 8)
                    logger.info(f"Fixed WAV header: data chunk size {chunk_size} → {actual_data_size}")
                    return bytes(data_arr)
                break
            pos += 8 + chunk_size
        return data

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

            # Fix WAV header: the TTS API may write incorrect data chunk size
            audio_data = self._fix_wav_header(audio_data)

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
