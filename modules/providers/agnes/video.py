"""Agnes video generation adapter.

Uses Agnes AI's /v1/videos API with async polling.
"""

import logging
import time
from pathlib import Path

import requests

from .. import VideoProvider
from .._subtitle_builder import SubtitleConfig, finalize_video
from .._ffmpeg_utils import download_video
from ...config_model import AgnesConfig, GenerationConfig

logger = logging.getLogger(__name__)

AGNES_API_BASE = "https://apihub.agnes-ai.com"
AGNES_VIDEO_ENDPOINT = f"{AGNES_API_BASE}/v1/videos"
AGNES_VIDEO_QUERY_ENDPOINT = f"{AGNES_API_BASE}/agnesapi"
DEFAULT_VIDEO_MODEL = "agnes-video-v2.0"


class AgnesVideoProvider(VideoProvider):
    """Video generation via Agnes AI API."""

    def __init__(self, config: AgnesConfig, generation: GenerationConfig | None = None):
        self.api_key = config.api_key
        self.model = config.video_model
        self.size = f"{config.video_width}*{config.video_height}"
        self.duration = config.video_num_frames // config.video_frame_rate
        self.media_dir = Path(config.media_dir)
        self.media_dir.mkdir(parents=True, exist_ok=True)
        self.sub_config = SubtitleConfig.from_config(generation) if generation else SubtitleConfig()
        self.poll_interval = 5
        self.max_poll_time = 600

    @property
    def _headers(self) -> dict:
        return {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}

    def _parse_size(self) -> tuple[int, int]:
        width, height = 1152, 768
        s = self.size.replace("*", "x")
        if "x" in s:
            parts = s.split("x")
            try:
                return int(parts[0]), int(parts[1])
            except (ValueError, IndexError):
                pass
        return width, height

    def generate(
        self,
        prompt: str,
        filename: str,
        audio_url: str | None = None,
        subtitles: str | None = None,
        keywords: list[str] | None = None,
        audio_duration: float | None = None,
        scene_timings: list[dict] | None = None,
    ) -> str | None:
        if not self.api_key:
            logger.warning("Agnes API key not configured, skipping video generation")
            return None

        width, height = self._parse_size()
        fps = 24
        num_frames = min(441, int((audio_duration or self.duration) * fps))
        num_frames = ((num_frames - 1) // 8) * 8 + 1

        data = {
            "model": self.model, "prompt": prompt,
            "width": width, "height": height,
            "num_frames": num_frames, "frame_rate": fps,
        }

        try:
            logger.info(f"Agnes video: {prompt[:80]}...")
            resp = requests.post(AGNES_VIDEO_ENDPOINT, headers=self._headers, json=data, timeout=120)
            if resp.status_code != 200:
                logger.error(f"Agnes video API error: {resp.status_code} - {resp.text}")
                return None

            result = resp.json()
            video_id = result.get("video_id")
            task_id = result.get("task_id")
            poll_id = video_id or task_id
            if not poll_id:
                logger.error(f"No video_id/task_id in Agnes response: {result}")
                return None

            logger.info(f"Agnes video task submitted: {poll_id}")
            return self._poll(poll_id, filename, bool(video_id), subtitles, keywords, audio_duration, scene_timings)

        except Exception as e:
            logger.error(f"Agnes video generation failed: {e}")
            return None

    def _poll(self, poll_id: str, filename: str, use_video_id: bool,
              subtitles: str | None = None, keywords: list[str] | None = None,
              audio_duration: float | None = None, scene_timings: list[dict] | None = None) -> str | None:
        elapsed = 0
        while elapsed < self.max_poll_time:
            time.sleep(self.poll_interval)
            elapsed += self.poll_interval

            try:
                url = f"{AGNES_VIDEO_QUERY_ENDPOINT}?video_id={poll_id}" if use_video_id else f"{AGNES_VIDEO_ENDPOINT}/{poll_id}"
                resp = requests.get(url, headers=self._headers, timeout=30)
                if resp.status_code != 200:
                    continue

                result = resp.json()
                status = result.get("status", "")

                if status == "completed":
                    video_url = result.get("remixed_from_video_id")
                    if video_url:
                        logger.info(f"Agnes video task {poll_id} completed")
                        video_path = download_video(video_url, filename, self.media_dir)
                        return finalize_video(video_path, subtitles, self.size, self.sub_config,
                                              keywords, audio_duration, scene_timings)
                    logger.error(f"No video URL in completed response: {result}")
                    return None

                if status == "failed":
                    logger.error(f"Agnes video task {poll_id} failed: {result}")
                    return None

                logger.debug(f"Agnes video task {poll_id} status: {status}, elapsed: {elapsed}s")

            except Exception as e:
                logger.warning(f"Agnes video poll error: {e}")

        logger.error(f"Agnes video task {poll_id} timed out")
        return None
