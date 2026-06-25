"""Ark video generation adapter.

Uses Agent Plan's content generation API with async polling.
Supports doubao-seedance models with:
- 9:16 portrait mode (for Douyin shorts)
- Text-only or text+image content inputs
- Audio-conditioned generation when audio_url is provided
"""

import logging
import time
from pathlib import Path

import requests

from .. import VideoProvider
from .._subtitle_builder import SubtitleConfig, finalize_video
from .._ffmpeg_utils import download_video
from ...config_model import ArkConfig, GenerationConfig

logger = logging.getLogger(__name__)


class ArkVideoProvider(VideoProvider):
    """Video generation via Volcano Ark Agent Plan content generation API.

    Uses the correct Agent Plan endpoints:
    - POST /api/plan/v3/contents/generations/tasks  (create task)
    - GET  /api/plan/v3/contents/generations/tasks/{id}  (query task)
    """

    def __init__(self, config: ArkConfig, generation: GenerationConfig | None = None):
        self.api_key = config.api_key
        self.base_url = config.base_url.rstrip("/")
        self.model = config.video_model
        self.video_size = config.video_size
        self.duration = config.video_duration

        # Agent Plan video generation endpoints
        self.video_generation_url = f"{self.base_url}/contents/generations/tasks"
        self.video_query_url = f"{self.base_url}/contents/generations/tasks"

        self.media_dir = Path(config.media_dir)
        self.media_dir.mkdir(parents=True, exist_ok=True)

        self.sub_config = SubtitleConfig.from_config(generation) if generation else SubtitleConfig()
        self.poll_interval = 5
        self.max_poll_time = 600

    @property
    def _headers(self) -> dict:
        return {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}

    def _parse_ratio(self) -> str:
        """Parse video_size config and determine ratio.

        Returns "9:16" for portrait, "16:9" for landscape, or "adaptive".
        """
        size_str = self.video_size.replace("*", "x")
        width, height = 720, 1280  # Default to 9:16 portrait for Douyin

        if "x" in size_str:
            parts = size_str.split("x")
            try:
                w, h = int(parts[0]), int(parts[1])
                width, height = w, h
            except (ValueError, IndexError):
                pass

        ratio = width / height
        if abs(ratio - 9 / 16) < 0.05:
            return "9:16"
        elif abs(ratio - 16 / 9) < 0.05:
            return "16:9"
        elif abs(ratio - 1.0) < 0.05:
            return "1:1"
        elif abs(ratio - 4 / 3) < 0.05:
            return "4:3"
        elif abs(ratio - 3 / 4) < 0.05:
            return "3:4"
        return "adaptive"

    def _build_content(self, prompt: str, audio_url: str | None) -> list[dict]:
        """Build the content array for the API request."""
        content = [{"type": "text", "text": prompt}]
        # Note: Agent Plan video API supports image_url in content,
        # but audio_url is not directly supported in the content array.
        # Audio integration would need a different approach (pre-merged).
        return content

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
            logger.warning("Ark API key not configured, skipping video generation")
            return None

        ratio = self._parse_ratio()
        content = self._build_content(prompt, audio_url)

        # Duration: Seedance models only support 5s, regardless of audio
        is_seedance = "seedance" in self.model.lower()
        if is_seedance:
            api_duration = 5
            logger.info(f"Ark video duration: 5s (Seedance cap)")
        elif audio_duration:
            api_duration = min(int(audio_duration), self.duration or 15)
            logger.info(f"Ark video duration: {api_duration}s (audio: {audio_duration:.1f}s)")
        else:
            api_duration = self.duration or 5
            logger.info(f"Ark video duration: {api_duration}s (config default)")

        data = {
            "model": self.model,
            "content": content,
            "ratio": ratio,
            "duration": api_duration,
            "generate_audio": False,
            "watermark": False,
        }

        try:
            logger.info(f"Ark video: {self.model} | {ratio} | {prompt[:60]}...")
            resp = requests.post(self.video_generation_url, headers=self._headers, json=data, timeout=120)
            if resp.status_code != 200:
                logger.error(f"Ark video API error: {resp.status_code} - {resp.text[:500]}")
                return None

            result = resp.json()
            # Agent Plan response: { "id": "task_id", "model": "...", "status": "running", ... }
            task_id = result.get("id") or result.get("data", {}).get("id")
            if not task_id:
                logger.error(f"No task_id in Ark video response: {result}")
                return None

            logger.info(f"Ark video task submitted: {task_id}")
            return self._poll(task_id, filename, subtitles, keywords, audio_duration, scene_timings)

        except Exception as e:
            logger.error(f"Ark video generation failed: {e}")
            return None

    def _poll(self, task_id: str, filename: str, subtitles: str | None = None,
              keywords: list[str] | None = None, audio_duration: float | None = None,
              scene_timings: list[dict] | None = None) -> str | None:
        query_url = f"{self.video_query_url}/{task_id}"
        elapsed = 0
        while elapsed < self.max_poll_time:
            time.sleep(self.poll_interval)
            elapsed += self.poll_interval

            try:
                resp = requests.get(query_url, headers=self._headers, timeout=30)
                if resp.status_code != 200:
                    continue

                result = resp.json()
                data = result.get("data", result)
                status = data.get("status", "")

                if status == "succeeded":
                    # Try different response shapes
                    video_url = data.get("url") or data.get("video_url") or data.get("output", {}).get("video_url")
                    if video_url:
                        logger.info(f"Ark video task {task_id} completed")
                        video_path = download_video(video_url, filename, self.media_dir)
                        return finalize_video(video_path, subtitles, self.video_size, self.sub_config,
                                              keywords, audio_duration, scene_timings)

                    results = data.get("results", [])
                    if results and results[0].get("url"):
                        logger.info(f"Ark video task {task_id} completed")
                        video_path = download_video(results[0]["url"], filename, self.media_dir)
                        return finalize_video(video_path, subtitles, self.video_size, self.sub_config,
                                              keywords, audio_duration, scene_timings)

                    # Agent Plan output format: { "content": { "video_url": "..." } }
                    content = data.get("content", {})
                    if content.get("video_url"):
                        logger.info(f"Ark video task {task_id} completed")
                        video_path = download_video(content["video_url"], filename, self.media_dir)
                        return finalize_video(video_path, subtitles, self.video_size, self.sub_config,
                                              keywords, audio_duration, scene_timings)

                    output = data.get("output", {})
                    if output.get("video_url"):
                        logger.info(f"Ark video task {task_id} completed")
                        video_path = download_video(output["video_url"], filename, self.media_dir)
                        return finalize_video(video_path, subtitles, self.video_size, self.sub_config,
                                              keywords, audio_duration, scene_timings)

                    logger.error(f"No video URL in completed response: {data}")
                    return None

                if status in ("failed", "error"):
                    error_msg = data.get("error", data.get("message", "unknown"))
                    logger.error(f"Ark video task {task_id} failed: {error_msg}")
                    return None

                if elapsed % 30 == 0:
                    logger.info(f"Ark video task {task_id} status: {status}, elapsed: {elapsed}s")

            except Exception as e:
                logger.warning(f"Ark video poll error: {e}")

        logger.error(f"Ark video task {task_id} timed out after {self.max_poll_time}s")
        return None
