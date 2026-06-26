"""Agnes video generation adapter.

Uses Agnes AI's /v1/videos API with async polling.
Supports agnes-video-v2.0 with:
- Text-to-video (ti2vid)
- Image-to-video (single image URL)
- Multi-image video (extra_body.image array)
- Keyframe animation (extra_body.mode="keyframes")
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

# Standard frame counts following 8n+1 rule, mapped to approximate duration at 24fps
STANDARD_FRAME_CONFIGS: list[tuple[int, int, float]] = [
    (81,  24, 3.4),   # ~3s
    (121, 24, 5.0),   # ~5s
    (161, 24, 6.7),   # ~7s
    (241, 24, 10.0),  # ~10s
    (441, 24, 18.4),  # ~18s
]


class AgnesVideoProvider(VideoProvider):
    """Video generation via Agnes AI API (agnes-video-v2.0)."""

    def __init__(self, config: AgnesConfig, generation: GenerationConfig | None = None):
        self.api_key = config.api_key
        self.model = config.video_model or DEFAULT_VIDEO_MODEL
        self.width = config.video_width
        self.height = config.video_height
        self.default_num_frames = config.video_num_frames
        self.default_frame_rate = config.video_frame_rate
        self.media_dir = Path(config.media_dir)
        self.media_dir.mkdir(parents=True, exist_ok=True)
        self.sub_config = SubtitleConfig.from_config(generation) if generation else SubtitleConfig()
        self.poll_interval = 5
        self.max_poll_time = 600

    @property
    def _headers(self) -> dict:
        return {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}

    @staticmethod
    def _pick_frame_config(duration: float | None) -> tuple[int, int, float]:
        """Pick the best standard frame/fps combo to cover the target duration.

        Uses the standard configs recommended by the API docs.
        Picks the first config whose estimated duration >= target.
        Falls back to max frames (441) if duration exceeds the longest standard.
        """
        if not duration or duration <= 0:
            return 121, 24, 5.0

        for frames, fps, est_seconds in STANDARD_FRAME_CONFIGS:
            if duration <= est_seconds + 1.0:
                return frames, fps, est_seconds

        return 441, 24, 18.4

    def generate(
        self,
        prompt: str,
        filename: str,
        audio_path: str | None = None,
        subtitles: str | None = None,
        keywords: list[str] | None = None,
        audio_duration: float | None = None,
        scene_timings: list[dict] | None = None,
    ) -> str | None:
        if not self.api_key:
            logger.warning("Agnes API key not configured, skipping video generation")
            return None

        num_frames, frame_rate, _ = self._pick_frame_config(audio_duration)

        data: dict = {
            "model": self.model,
            "prompt": prompt,
            "width": self.width,
            "height": self.height,
            "num_frames": num_frames,
            "frame_rate": frame_rate,
        }

        try:
            logger.info(
                f"Agnes video: {prompt[:60]}... | "
                f"{self.width}x{self.height} | {num_frames}frames @{frame_rate}fps"
            )
            resp = requests.post(
                AGNES_VIDEO_ENDPOINT,
                headers=self._headers,
                json=data,
                timeout=300,
            )
            if resp.status_code != 200:
                logger.error(f"Agnes video API error: {resp.status_code} - {resp.text[:500]}")
                return None

            result = resp.json()
            video_id = result.get("video_id")
            task_id = result.get("task_id") or result.get("id")

            if not video_id and not task_id:
                logger.error(f"No video_id/task_id in Agnes response: {result}")
                return None

            logger.info(
                f"Agnes video task submitted: {task_id} "
                f"(video_id: {video_id})"
            )
            return self._poll(
                video_id=video_id,
                task_id=task_id,
                filename=filename,
                subtitles=subtitles,
                keywords=keywords,
                audio_duration=audio_duration,
                scene_timings=scene_timings,
            )

        except Exception as e:
            logger.error(f"Agnes video generation failed: {e}")
            return None

    def _poll(
        self,
        video_id: str | None,
        task_id: str | None,
        filename: str,
        subtitles: str | None = None,
        keywords: list[str] | None = None,
        audio_duration: float | None = None,
        scene_timings: list[dict] | None = None,
    ) -> str | None:
        elapsed = 0
        while elapsed < self.max_poll_time:
            time.sleep(self.poll_interval)
            elapsed += self.poll_interval

            try:
                # Use video_id endpoint (recommended by API docs) if available
                if video_id:
                    url = f"{AGNES_VIDEO_QUERY_ENDPOINT}?video_id={video_id}"
                elif task_id:
                    url = f"{AGNES_VIDEO_ENDPOINT}/{task_id}"
                else:
                    return None

                resp = requests.get(url, headers=self._headers, timeout=30)
                if resp.status_code != 200:
                    continue

                result = resp.json()
                status = result.get("status", "")

                if status == "completed":
                    video_url = self._extract_video_url(result)
                    if video_url:
                        logger.info(f"Agnes video task completed: {video_id or task_id}")
                        video_path = download_video(video_url, filename, self.media_dir)
                        return finalize_video(
                            video_path, subtitles, f"{self.width}*{self.height}",
                            self.sub_config, keywords, audio_duration, scene_timings,
                        )
                    logger.error(f"No video URL in completed response: {result}")
                    return None

                if status == "failed":
                    error_msg = result.get("error", result.get("message", "unknown"))
                    logger.error(f"Agnes video task failed: {error_msg}")
                    return None

                if elapsed % 30 == 0:
                    seconds = result.get("seconds", "?")
                    logger.info(
                        f"Agnes video {video_id or task_id}: {status} "
                        f"({result.get('progress', 0)}%), "
                        f"elapsed: {elapsed}s, duration: {seconds}s"
                    )

            except Exception as e:
                logger.warning(f"Agnes video poll error: {e}")

        logger.error(f"Agnes video task timed out after {self.max_poll_time}s")
        return None

    @staticmethod
    def _extract_video_url(result: dict) -> str | None:
        """Extract video URL from various possible response fields."""
        # Primary: remixed_from_video_id (this field contains the actual URL)
        url = result.get("remixed_from_video_id")
        if url and isinstance(url, str) and url.startswith("http"):
            return url
        # Fallback: video_url
        url = result.get("video_url")
        if url and isinstance(url, str) and url.startswith("http"):
            return url
        # Fallback: output.video_url
        output = result.get("output", {})
        if isinstance(output, dict):
            url = output.get("video_url")
            if url and isinstance(url, str) and url.startswith("http"):
                return url
        # Fallback: results array
        results = result.get("results", [])
        if isinstance(results, list):
            for item in results:
                if isinstance(item, dict):
                    url = item.get("url") or item.get("video_url")
                    if url and isinstance(url, str) and url.startswith("http"):
                        return url
        return None
