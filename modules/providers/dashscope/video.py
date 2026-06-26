"""DashScope video generation adapter.

Extracted from modules/vgen.py — uses VideoSynthesis SDK with async polling.
"""

import logging
import time
from pathlib import Path

import dashscope
import requests
from dashscope import VideoSynthesis

from .. import VideoProvider
from .._subtitle_builder import SubtitleConfig, finalize_video
from .._ffmpeg_utils import download_video
from ...config_model import DashScopeConfig, GenerationConfig

logger = logging.getLogger(__name__)


class DashScopeVideoProvider(VideoProvider):
    """Video generation via DashScope (Alibaba Cloud) VideoSynthesis API."""

    def __init__(self, config: DashScopeConfig, generation: "GenerationConfig | None" = None):
        self.api_key = config.api_key
        self.model = config.video_model
        self.size = config.video_size
        self.duration = config.video_duration
        self.media_dir = Path(config.media_dir)
        self.media_dir.mkdir(parents=True, exist_ok=True)
        self.sub_config = SubtitleConfig.from_config(generation) if generation else SubtitleConfig()
        self.poll_interval = 5
        self.max_poll_time = 600
        dashscope.api_key = self.api_key

    @staticmethod
    def _pick_api_duration(audio_duration: float, supported: list[int] | None = None) -> int:
        """Pick the smallest supported API duration that covers the audio."""
        if supported is None:
            supported = [5, 10, 15]
        for d in sorted(supported):
            if audio_duration <= d:
                return d
        return max(supported)

    def _upload_to_oss(self, file_path: str, model_name: str) -> str | None:
        """Upload a local audio file to DashScope OSS and return oss:// URL."""
        if not self.api_key:
            logger.warning("DashScope API key not configured, skipping upload")
            return None

        try:
            policy_url = "https://dashscope.aliyuncs.com/api/v1/uploads"
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }
            params = {"action": "getPolicy", "model": model_name}
            resp = requests.get(policy_url, headers=headers, params=params, timeout=10)
            if resp.status_code != 200:
                logger.error(f"Get upload policy failed: {resp.text}")
                return None

            policy_data = resp.json().get("data", {})

            file_name = Path(file_path).name
            key = f"{policy_data['upload_dir']}/{file_name}"

            with open(file_path, "rb") as f:
                files = {
                    "OSSAccessKeyId": (None, policy_data["oss_access_key_id"]),
                    "Signature": (None, policy_data["signature"]),
                    "policy": (None, policy_data["policy"]),
                    "x-oss-object-acl": (None, policy_data.get("x_oss_object_acl", "private")),
                    "x-oss-forbid-overwrite": (None, policy_data.get("x_oss_forbid_overwrite", "true")),
                    "key": (None, key),
                    "success_action_status": (None, "200"),
                    "file": (file_name, f),
                }
                resp = requests.post(policy_data["upload_host"], files=files, timeout=60)

            if resp.status_code != 200:
                logger.error(f"Upload file to OSS failed: {resp.text}")
                return None

            oss_url = f"oss://{key}"
            logger.info(f"File uploaded to OSS: {oss_url}")
            return oss_url

        except Exception as e:
            logger.error(f"Upload to OSS failed: {e}")
            return None

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
            logger.warning("DashScope API key not configured, skipping video generation")
            return None

        api_duration = self._pick_api_duration(audio_duration or self.duration)
        logger.info(f"API duration: {api_duration}s (audio: {audio_duration}s)")

        try:
            kwargs = dict(model=self.model, prompt=prompt, size=self.size, duration=api_duration)
            if audio_path:
                audio_url = self._upload_to_oss(audio_path, self.model)
                if audio_url:
                    kwargs["audio_url"] = audio_url

            logger.info(f"Generating video with {self.model}: {prompt[:80]}...")
            response = VideoSynthesis.async_call(**kwargs)

            if response.status_code != 200:
                logger.error(f"Video task submission failed: {response.code} - {response.message}")
                return None

            task_id = response.output.get("task_id")
            if not task_id:
                logger.error("No task_id in video response")
                return None

            logger.info(f"Video task submitted: {task_id}")

            elapsed = 0
            while elapsed < self.max_poll_time:
                time.sleep(self.poll_interval)
                elapsed += self.poll_interval

                result = VideoSynthesis.fetch(task_id)
                status = result.output.get("task_status", "")

                if status == "SUCCEEDED":
                    video_url = result.output.get("video_url")
                    if video_url:
                        video_path = download_video(video_url, filename, self.media_dir)
                        return finalize_video(video_path, subtitles, self.size, self.sub_config,
                                              keywords, audio_duration, scene_timings)

                    results = result.output.get("results", [])
                    if results and results[0].get("url"):
                        video_path = download_video(results[0]["url"], filename, self.media_dir)
                        return finalize_video(video_path, subtitles, self.size, self.sub_config,
                                              keywords, audio_duration, scene_timings)

                    logger.error("No video URL in succeeded response")
                    return None

                if status == "FAILED":
                    logger.error(f"Video task failed: {result.output}")
                    return None

                logger.debug(f"Video task {task_id} status: {status}, elapsed: {elapsed}s")

            logger.error(f"Video task timed out after {self.max_poll_time}s: {task_id}")
            return None

        except Exception as e:
            logger.error(f"Video generation failed: {e}")
            return None
