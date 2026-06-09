"""Video generation module using DashScope VideoSynthesis (Wan2.7-T2V)."""

import logging
import time
from pathlib import Path
import requests
import dashscope
from dashscope import VideoSynthesis

logger = logging.getLogger(__name__)


class VideoGenerator:
    def __init__(self, config: dict):
        ds_config = config.get("dashscope", {})
        self.api_key = ds_config.get("api_key", "")
        self.model = ds_config.get("video_model", "wan2.7-t2v")
        self.size = ds_config.get("video_size", "1280*720")
        self.duration = ds_config.get("video_duration", 15)
        self.media_dir = Path(ds_config.get("media_dir", "media"))
        self.media_dir.mkdir(parents=True, exist_ok=True)

        # Polling config
        self.poll_interval = 5  # seconds
        self.max_poll_time = 600  # 10 minutes timeout

        dashscope.api_key = self.api_key

    def generate(self, prompt: str, filename: str, audio_url: str | None = None) -> str | None:
        """Generate a video from a text prompt, optionally with synced audio.

        Args:
            prompt: Text description for video generation.
            filename: Output filename.
            audio_url: Optional OSS URL of TTS audio for voice-synced video.

        Returns:
            Local file path of generated video, or None.
        """
        if not self.api_key:
            logger.warning("DashScope API key not configured, skipping video generation")
            return None

        try:
            kwargs = dict(
                model=self.model,
                prompt=prompt,
                size=self.size,
                duration=self.duration,
            )
            if audio_url:
                kwargs["audio_url"] = audio_url
                logger.info(f"Generating video with {self.model} (audio-synced): {prompt[:80]}...")
            else:
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

            # Poll for result
            elapsed = 0
            while elapsed < self.max_poll_time:
                time.sleep(self.poll_interval)
                elapsed += self.poll_interval

                result = VideoSynthesis.fetch(task_id)
                status = result.output.get("task_status", "")

                if status == "SUCCEEDED":
                    video_url = result.output.get("video_url")
                    if video_url:
                        return self._download_video(video_url, filename)
                    # Try alternative response format
                    results = result.output.get("results", [])
                    if results and results[0].get("url"):
                        return self._download_video(results[0]["url"], filename)
                    logger.error("No video URL in succeeded response")
                    return None

                if status == "FAILED":
                    logger.error(f"Video task failed: {result.output}")
                    return None

                # Still running, continue polling
                logger.debug(f"Video task {task_id} status: {status}, elapsed: {elapsed}s")

            logger.error(f"Video task timed out after {self.max_poll_time}s: {task_id}")
            return None

        except Exception as e:
            logger.error(f"Video generation failed: {e}")
            return None

    def _download_video(self, video_url: str, filename: str) -> str | None:
        """Download video from URL and save locally. Returns local path."""
        try:
            resp = requests.get(video_url, timeout=120, stream=True)
            resp.raise_for_status()

            # Ensure .mp4 extension
            if not filename.endswith(".mp4"):
                filename = filename.rsplit(".", 1)[0] + ".mp4"

            filepath = self.media_dir / filename
            total = 0
            with open(filepath, "wb") as f:
                for chunk in resp.iter_content(chunk_size=8192):
                    f.write(chunk)
                    total += len(chunk)

            logger.info(f"Video saved: {filepath} ({total} bytes)")
            return str(filepath)
        except Exception as e:
            logger.error(f"Video download failed: {e}")
            return None
