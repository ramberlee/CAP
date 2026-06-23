"""火山方舟 Ark API client for text-to-image, text-to-video, and TTS generation.

Volcano Ark provides a mix of OpenAI-compatible and custom APIs:
    Chat:      POST {base_url}/chat/completions
    Image:     POST {base_url}/images/generations
    TTS:       POST https://openspeech.bytedance.com/api/v3/plan/tts/unidirectional
               (HTTP chunked JSON + base64 audio, X-Api-Key auth)
    Video:     Uses the Volcengine unified API endpoint with Ark API Key.

Usage in config.yaml:
    ark:
      api_key: "your-ark-api-key"
      base_url: "https://ark.cn-beijing.volces.com/api/v3"
      model: "deepseek-r1-250528"
      image_model: "doubao-seedream-2.0-t2i-250529"
      video_model: "doubao-seedance-1.0-pro-250528"
      tts_model: "doubao-seed-tts-2.0"
      tts_voice: "zh_female_shuangkuaisisi_moon_bigtts"
"""

import base64
import json
import logging
import time
from pathlib import Path
from typing import Optional

import requests

logger = logging.getLogger(__name__)

# Volcengine unified API for video generation (requires Ark API Key via Authorization header)
VOLC_VIDEO_ENDPOINT = "https://api.volcengine.com/api/open/v1/video/generations"
# Video query endpoint
VOLC_VIDEO_QUERY_ENDPOINT = "https://api.volcengine.com/api/open/v1/video/query"


class ArkClient:
    """Unified client for Volcano Ark AI APIs."""

    def __init__(self, config: dict):
        ark_config = config.get("ark", {})
        self.api_key = ark_config.get("api_key", "")
        self.base_url = ark_config.get("base_url", "https://ark.cn-beijing.volces.com/api/v3")
        # Normalize: remove trailing slash
        self.base_url = self.base_url.rstrip("/")

        # Models
        self.chat_model = ark_config.get("model") or "deepseek-r1-250528"
        self.image_model = ark_config.get("image_model") or "doubao-seedream-2.0-t2i-250529"
        self.video_model = ark_config.get("video_model") or "doubao-seedance-1.0-pro-250528"
        self.tts_model = ark_config.get("tts_model") or "doubao-tts-1.0"
        self.tts_voice = ark_config.get("tts_voice", "zh_female_shuangkuaisisi_moon_bigtts")
        self.planner_model = ark_config.get("planner_model") or self.chat_model

        # Media settings (shared fallback)
        ds_config = config.get("dashscope", {})
        self.media_dir = Path(ark_config.get("media_dir") or ds_config.get("media_dir", "media"))
        self.media_dir.mkdir(parents=True, exist_ok=True)

        # Image settings
        self.image_size = ark_config.get("image_size", "1472*1104")

        # Video settings
        self.video_size = ark_config.get("video_size", "1280*720")
        self.poll_interval = 5  # seconds
        self.max_poll_time = 600  # 10 minutes timeout

    @property
    def headers(self) -> dict:
        """HTTP headers with Ark API Key authorization."""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    # ─── IMAGE GENERATION ────────────────────────────────────────

    def generate_image(
        self,
        prompt: str,
        filename: str,
        size: Optional[str] = None,
        negative_prompt: str = "",
    ) -> Optional[str]:
        """Generate an image via Ark's OpenAI-compatible /images/generations endpoint.

        Args:
            prompt: Text description for image generation.
            filename: Output filename (e.g. "content_1_1.png").
            size: Image resolution (e.g. "1472*1104"). Uses config default if None.
            negative_prompt: Negative prompt (not universally supported, sent as extra).

        Returns:
            Local file path of generated image, or None on failure.
        """
        if not self.api_key:
            logger.warning("Ark API key not configured, skipping image generation")
            return None

        url = f"{self.base_url}/images/generations"
        effective_size = (size or self.image_size).replace("*", "x")

        data = {
            "model": self.image_model,
            "prompt": prompt,
            "n": 1,
            "size": effective_size,
            "response_format": "url",
        }

        try:
            logger.info(f"Ark image generation: {self.image_model} | {prompt[:50]}...")
            resp = requests.post(url, headers=self.headers, json=data, timeout=300)

            if resp.status_code != 200:
                logger.error(f"Ark image API error: {resp.status_code} - {resp.text}")
                return None

            result = resp.json()
            image_url = self._extract_image_url(result)
            if not image_url:
                logger.error(f"No image URL in Ark response: {result}")
                return None

            logger.info(f"Ark image generated, downloading from: {image_url[:80]}...")
            return self._download_file(image_url, filename)

        except requests.exceptions.Timeout:
            logger.error("Ark image generation request timed out")
            return None
        except Exception as e:
            logger.error(f"Ark image generation failed: {e}")
            return None

    @staticmethod
    def _extract_image_url(result: dict) -> Optional[str]:
        """Extract image URL from OpenAI-compatible image response.

        Expected format:
            {"data": [{"url": "..."}]}
            or {"data": [{"b64_json": "..."}]}
        """
        data = result.get("data", [])
        if data and isinstance(data, list):
            for item in data:
                if isinstance(item, dict):
                    # URL format
                    if item.get("url"):
                        return item["url"]
                    # b64_json format (not common for Ark, but handle gracefully)
                    if item.get("b64_json"):
                        import base64
                        img_data = base64.b64decode(item["b64_json"])
                        logger.info(f"Received base64 image ({len(img_data)} bytes)")
                        return img_data  # Will be handled differently
        return None

    # ─── VIDEO GENERATION ───────────────────────────────────────

    def generate_video(
        self,
        prompt: str,
        filename: str,
        duration: int = 5,
        image_url: Optional[str] = None,
    ) -> Optional[str]:
        """Generate a video via Ark's Volcengine video generation API.

        Uses the unified Volcengine API endpoint for video generation.
        The API is asynchronous: submits a task and polls for the result.

        Args:
            prompt: Text description for video generation.
            filename: Output filename.
            duration: Video duration in seconds (5 or 10 for most models).
            image_url: Optional image URL for image-to-video generation.

        Returns:
            Local file path of generated video, or None on failure.
        """
        if not self.api_key:
            logger.warning("Ark API key not configured, skipping video generation")
            return None

        # Parse size
        width, height = 1280, 720
        size_str = self.video_size.replace("*", "x")
        if "x" in size_str:
            parts = size_str.split("x")
            try:
                width, height = int(parts[0]), int(parts[1])
            except (ValueError, IndexError):
                pass

        data = {
            "model": self.video_model,
            "prompt": prompt,
            "duration": duration,
            "width": width,
            "height": height,
        }
        if image_url:
            data["image_url"] = image_url

        try:
            logger.info(f"Ark video generation request: {self.video_model} | {prompt[:60]}...")
            resp = requests.post(
                VOLC_VIDEO_ENDPOINT,
                headers=self.headers,
                json=data,
                timeout=120,
            )

            if resp.status_code != 200:
                logger.error(f"Ark video API error: {resp.status_code} - {resp.text}")
                return None

            result = resp.json()
            task_id = result.get("data", {}).get("task_id") or result.get("task_id")
            if not task_id:
                logger.error(f"No task_id in Ark video response: {result}")
                return None

            logger.info(f"Ark video task submitted: {task_id}")

            # Poll for result
            return self._poll_video_result(task_id, filename)

        except requests.exceptions.Timeout:
            logger.error("Ark video generation request timed out")
            return None
        except Exception as e:
            logger.error(f"Ark video generation failed: {e}")
            return None

    def _poll_video_result(self, task_id: str, filename: str) -> Optional[str]:
        """Poll video task until completion."""
        elapsed = 0

        while elapsed < self.max_poll_time:
            time.sleep(self.poll_interval)
            elapsed += self.poll_interval

            try:
                resp = requests.get(
                    VOLC_VIDEO_QUERY_ENDPOINT,
                    headers=self.headers,
                    params={"task_id": task_id},
                    timeout=30,
                )

                if resp.status_code != 200:
                    logger.warning(f"Ark video poll request failed: {resp.status_code}")
                    continue

                result = resp.json()
                data = result.get("data", result)
                status = data.get("status", "")

                if status == "succeeded":
                    video_url = data.get("video_url") or data.get("url")
                    if video_url:
                        logger.info(f"Ark video task {task_id} completed")
                        return self._download_file(video_url, filename)
                    # Check results array
                    results = data.get("results", [])
                    if results and results[0].get("url"):
                        logger.info(f"Ark video task {task_id} completed")
                        return self._download_file(results[0]["url"], filename)

                    logger.error(f"No video URL in completed response: {data}")
                    return None

                if status in ("failed", "error"):
                    error_msg = data.get("error", data.get("message", "unknown"))
                    logger.error(f"Ark video task {task_id} failed: {error_msg}")
                    return None

                logger.debug(f"Ark video task {task_id} status: {status}, elapsed: {elapsed}s")

            except Exception as e:
                logger.warning(f"Ark video poll request error: {e}")

        logger.error(f"Ark video task {task_id} timed out after {self.max_poll_time}s")
        return None

    # ─── TTS (TEXT-TO-SPEECH) ───────────────────────────────────

    # Ark TTS uses the openspeech HTTP endpoint (not the standard Ark base_url)
    TTS_URL = "https://openspeech.bytedance.com/api/v3/plan/tts/unidirectional"
    TTS_RESOURCE_ID = "seed-tts-2.0"

    @property
    def _tts_headers(self) -> dict:
        """HTTP headers for TTS requests (X-Api-Key auth, not Bearer)."""
        return {
            "X-Api-Key": self.api_key,
            "X-Api-Resource-Id": self.TTS_RESOURCE_ID,
            "Content-Type": "application/json",
            "Connection": "keep-alive",
            "X-Control-Require-Usage-Tokens-Return": "*",
        }

    def synthesize_speech(
        self,
        text: str,
        filename: str,
        voice: Optional[str] = None,
        response_format: str = "mp3",
        speed: float = 1.0,
        sample_rate: int = 24000,
    ) -> Optional[str]:
        """Generate speech audio from text via Ark TTS HTTP chunked API.

        Uses the openspeech HTTP endpoint with chunked JSON + base64 audio
        (as documented in 接入语音模型.md).

        Args:
            text: The text to convert to speech.
            filename: Output filename (e.g. "tts_output.mp3").
            voice: Speaker name (default from config).
            response_format: Audio format: "mp3", "wav", "ogg", etc.
            speed: Speech speed multiplier (0.5-2.0). NOTE: Ark API may not
                   support speed; sent as an extra field but may be ignored.
            sample_rate: Audio sample rate in Hz (default 24000).

        Returns:
            Local file path of audio file, or None on failure.
        """
        if not self.api_key:
            logger.warning("Ark API key not configured, skipping TTS")
            return None

        # Ensure proper extension
        if not filename.endswith(f".{response_format}"):
            filename = filename.rsplit(".", 1)[0] + f".{response_format}"

        payload = {
            "req_params": {
                "text": text,
                "speaker": voice or self.tts_voice,
                "audio_params": {
                    "format": response_format,
                    "sample_rate": sample_rate,
                },
            }
        }
        # Speed is not a standard field in Ark's API; include if ≠ 1.0
        if speed != 1.0:
            payload["req_params"]["speed_ratio"] = speed

        session = requests.Session()
        response = None

        try:
            logger.info(f"Ark TTS (HTTP chunked): speaker={voice or self.tts_voice} | {text[:60]}...")
            response = session.post(
                self.TTS_URL,
                headers=self._tts_headers,
                json=payload,
                stream=True,
                timeout=120,
            )

            if response.status_code != 200:
                logger.error(f"Ark TTS API error: {response.status_code} - {response.text[:500]}")
                return None

            audio_data = bytearray()
            for line in response.iter_lines(decode_unicode=True):
                if not line:
                    continue
                try:
                    chunk = json.loads(line)
                except json.JSONDecodeError:
                    logger.warning(f"Ark TTS: non-JSON line in response: {line[:100]}")
                    continue

                code = chunk.get("code", 0)
                if code == 20000000:
                    # End-of-stream marker
                    break
                if code > 0:
                    logger.error(f"Ark TTS error response: code={code}, data={chunk}")
                    return None
                if code == 0 and "data" in chunk and chunk["data"]:
                    chunk_audio = base64.b64decode(chunk["data"])
                    audio_data.extend(chunk_audio)

            if not audio_data:
                logger.error("Ark TTS: no audio data received in response")
                return None

            filepath = self.media_dir / filename
            filepath.write_bytes(bytes(audio_data))
            logger.info(f"Ark TTS saved: {filepath} ({len(audio_data)} bytes)")
            return str(filepath)

        except requests.exceptions.Timeout:
            logger.error("Ark TTS request timed out")
            return None
        except Exception as e:
            logger.error(f"Ark TTS failed: {e}")
            return None
        finally:
            if response:
                response.close()
            session.close()

    # ─── HELPERS ─────────────────────────────────────────────────

    def _download_file(self, url: str, filename: str) -> Optional[str]:
        """Download file from URL and save locally."""
        try:
            logger.info(f"Downloading from Ark: {url[:80]}...")
            resp = requests.get(url, timeout=300, stream=True)
            resp.raise_for_status()

            # Ensure proper extension
            if not filename.endswith((".mp4", ".png", ".jpg", ".jpeg", ".wav", ".mp3")):
                # Try to infer from Content-Type
                content_type = resp.headers.get("Content-Type", "")
                if "video" in content_type:
                    filename = filename.rsplit(".", 1)[0] + ".mp4"
                elif "image" in content_type:
                    filename = filename.rsplit(".", 1)[0] + ".png"
                elif "audio" in content_type:
                    filename = filename.rsplit(".", 1)[0] + ".wav"
                else:
                    filename = filename.rsplit(".", 1)[0] + ".mp4"

            filepath = self.media_dir / filename
            total = 0
            with open(filepath, "wb") as f:
                for chunk in resp.iter_content(chunk_size=8192):
                    f.write(chunk)
                    total += len(chunk)

            logger.info(f"File saved: {filepath} ({total} bytes)")
            return str(filepath)

        except Exception as e:
            logger.error(f"File download failed: {e}")
            return None
