"""Ark video generation adapter.

Uses Ark's custom Volcengine video generation API with async polling.
"""

import logging
import time
from pathlib import Path

import requests

from .. import VideoProvider
from .._subtitle_utils import SubtitleConfig, download_video, finalize_video

logger = logging.getLogger(__name__)


class ArkVideoProvider(VideoProvider):
    """Video generation via Volcano Ark (Volcengine video API)."""

    def __init__(self, config: dict):
        ark_config = config.get("ark", {})
        self.api_key = ark_config.get("api_key", "")
        self.base_url = ark_config.get("base_url", "https://ark.cn-beijing.volces.com/api/v3").rstrip("/")
        self.model = ark_config.get("video_model", "doubao-seedance-1.0-pro-250528")
        self.video_size = ark_config.get("video_size", "1280*720")
        self.duration = ark_config.get("video_duration", 15)
        self.video_generation_url = f"{self.base_url}/video/generations"
        self.video_query_url = f"{self.base_url}/video/query"

        ds_config = config.get("dashscope", {})
        self.media_dir = Path(ark_config.get("media_dir") or ds_config.get("media_dir", "media"))
        self.media_dir.mkdir(parents=True, exist_ok=True)

        self.sub_config = SubtitleConfig.from_config(config)
        self.poll_interval = 5
        self.max_poll_time = 600

    @property
    def _headers(self) -> dict:
        return {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}

    @staticmethod
    def _pick_api_duration(audio_duration: float, supported: list[int] | None = None) -> int:
        if supported is None:
            supported = [5, 10, 15]
        for d in sorted(supported):
            if audio_duration <= d:
                return d
        return max(supported)

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

        api_duration = self._pick_api_duration(audio_duration or self.duration)
        logger.info(f"Ark API duration: {api_duration}s (audio: {audio_duration}s)")

        width, height = 1280, 720
        size_str = self.video_size.replace("*", "x")
        if "x" in size_str:
            parts = size_str.split("x")
            try:
                width, height = int(parts[0]), int(parts[1])
            except (ValueError, IndexError):
                pass

        data = {"model": self.model, "prompt": prompt, "duration": api_duration, "width": width, "height": height}

        try:
            logger.info(f"Ark video: {self.model} | {prompt[:60]}...")
            resp = requests.post(self.video_generation_url, headers=self._headers, json=data, timeout=120)
            if resp.status_code != 200:
                logger.error(f"Ark video API error: {resp.status_code} - {resp.text}")
                return None

            result = resp.json()
            task_id = result.get("data", {}).get("task_id") or result.get("task_id")
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
        elapsed = 0
        while elapsed < self.max_poll_time:
            time.sleep(self.poll_interval)
            elapsed += self.poll_interval

            try:
                resp = requests.get(self.video_query_url, headers=self._headers,
                                    params={"task_id": task_id}, timeout=30)
                if resp.status_code != 200:
                    continue

                result = resp.json()
                data = result.get("data", result)
                status = data.get("status", "")

                if status == "succeeded":
                    video_url = data.get("video_url") or data.get("url")
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

                    logger.error(f"No video URL in completed response: {data}")
                    return None

                if status in ("failed", "error"):
                    logger.error(f"Ark video task {task_id} failed: {data.get('error', data.get('message', 'unknown'))}")
                    return None

                logger.debug(f"Ark video task {task_id} status: {status}, elapsed: {elapsed}s")

            except Exception as e:
                logger.warning(f"Ark video poll error: {e}")

        logger.error(f"Ark video task {task_id} timed out")
        return None
