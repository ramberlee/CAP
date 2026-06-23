"""Agnes AI API client for text-to-image and text-to-video generation.

Uses Agnes AI's OpenAI-compatible API:
    Image: POST https://apihub.agnes-ai.com/v1/images/generations
    Video: POST https://apihub.agnes-ai.com/v1/videos
"""

import logging
import time
from pathlib import Path
import requests

logger = logging.getLogger(__name__)

# Agnes AI API endpoints
AGNES_API_BASE = "https://apihub.agnes-ai.com"
AGNES_IMAGE_ENDPOINT = f"{AGNES_API_BASE}/v1/images/generations"
AGNES_VIDEO_ENDPOINT = f"{AGNES_API_BASE}/v1/videos"
AGNES_VIDEO_QUERY_ENDPOINT = f"{AGNES_API_BASE}/agnesapi"

# Default models
DEFAULT_IMAGE_MODEL = "agnes-image-2.1-flash"
DEFAULT_VIDEO_MODEL = "agnes-video-v2.0"


class AgnesClient:
    """Unified client for Agnes AI API."""

    def __init__(self, config: dict):
        agnes_config = config.get("agnes", {})
        self.api_key = agnes_config.get("api_key", "")
        self.image_model = agnes_config.get("image_model", DEFAULT_IMAGE_MODEL)
        self.video_model = agnes_config.get("video_model", DEFAULT_VIDEO_MODEL)
        self.media_dir = Path(agnes_config.get("media_dir", "media"))
        self.media_dir.mkdir(parents=True, exist_ok=True)

        # Video generation defaults
        self.video_width = agnes_config.get("video_width", 1152)
        self.video_height = agnes_config.get("video_height", 768)
        self.video_num_frames = agnes_config.get("video_num_frames", 121)
        self.video_frame_rate = agnes_config.get("video_frame_rate", 24)

        # Polling config
        self.poll_interval = 5  # seconds
        self.max_poll_time = 600  # 10 minutes timeout

    @property
    def headers(self) -> dict:
        """HTTP headers with authorization."""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def generate_image(
        self,
        prompt: str,
        filename: str,
        size: str = "1024x768",
        negative_prompt: str = "",
    ) -> str | None:
        """Generate an image from text prompt via Agnes AI API.

        Args:
            prompt: Text description for image generation.
            filename: Output filename (e.g. "content_1_1.png").
            size: Image resolution (e.g. "1024x768").
            negative_prompt: Negative prompt (not used by Agnes, kept for compatibility).

        Returns:
            Local file path of generated image, or None.
        """
        if not self.api_key:
            logger.warning("Agnes AI API key not configured, skipping image generation")
            return None

        data = {
            "model": self.image_model,
            "prompt": prompt,
            "size": size,
            "extra_body": {
                "response_format": "url"
            }
        }

        try:
            logger.info(f"Agnes AI image generation request: {prompt[:50]}...")
            resp = requests.post(
                AGNES_IMAGE_ENDPOINT,
                headers=self.headers,
                json=data,
                timeout=300,  # 5 min timeout for image generation
            )

            if resp.status_code != 200:
                logger.error(f"Agnes AI image API error: {resp.status_code} - {resp.text}")
                return None

            result = resp.json()

            # Extract image URL from response
            image_url = self._extract_image_url(result)
            if not image_url:
                logger.error(f"No image URL in Agnes AI response: {result}")
                return None

            logger.info(f"Agnes AI 图片 API 返回成功，image_url: {image_url[:80]}...")
            return self._download_file(image_url, filename)

        except requests.exceptions.Timeout:
            logger.error("Agnes AI image generation request timed out")
            return None
        except Exception as e:
            logger.error(f"Agnes AI image generation failed: {e}")
            return None

    def generate_video(
        self,
        prompt: str,
        filename: str,
        image_url: str | None = None,
        width: int | None = None,
        height: int | None = None,
        num_frames: int | None = None,
        frame_rate: int | None = None,
    ) -> str | None:
        """Generate a video from text prompt via Agnes AI API.

        Args:
            prompt: Text description for video generation.
            filename: Output filename (e.g. "content_1_1.mp4").
            image_url: Optional image URL for image-to-video generation.
            width: Video width (default from config).
            height: Video height (default from config).
            num_frames: Number of frames (default from config, must be 8n+1).
            frame_rate: Video FPS (default from config).

        Returns:
            Local file path of generated video, or None.
        """
        if not self.api_key:
            logger.warning("Agnes AI API key not configured, skipping video generation")
            return None

        data = {
            "model": self.video_model,
            "prompt": prompt,
            "width": width or self.video_width,
            "height": height or self.video_height,
            "num_frames": num_frames or self.video_num_frames,
            "frame_rate": frame_rate or self.video_frame_rate,
        }

        # Add image for image-to-video
        if image_url:
            data["image"] = image_url

        try:
            logger.info(f"Agnes AI video generation request: {prompt[:80]}...")
            resp = requests.post(
                AGNES_VIDEO_ENDPOINT,
                headers=self.headers,
                json=data,
                timeout=120,
            )

            if resp.status_code != 200:
                logger.error(f"Agnes AI video API error: {resp.status_code} - {resp.text}")
                return None

            result = resp.json()
            video_id = result.get("video_id")
            task_id = result.get("task_id")

            if not video_id and not task_id:
                logger.error(f"No video_id or task_id in Agnes AI response: {result}")
                return None

            # Use video_id (recommended) or task_id for polling
            poll_id = video_id or task_id
            logger.info(f"Agnes AI video task submitted: {poll_id}")

            # Poll for result
            return self._poll_video_result(poll_id, filename, use_video_id=bool(video_id))

        except requests.exceptions.Timeout:
            logger.error("Agnes AI video generation request timed out")
            return None
        except Exception as e:
            logger.error(f"Agnes AI video generation failed: {e}")
            return None

    def _poll_video_result(self, poll_id: str, filename: str, use_video_id: bool = True) -> str | None:
        """Poll video task until completion.

        Args:
            poll_id: video_id or task_id.
            filename: Output filename.
            use_video_id: If True, use video_id query method; otherwise use task_id.

        Returns:
            Local file path of generated video, or None.
        """
        elapsed = 0

        while elapsed < self.max_poll_time:
            time.sleep(self.poll_interval)
            elapsed += self.poll_interval

            try:
                if use_video_id:
                    url = f"{AGNES_VIDEO_QUERY_ENDPOINT}?video_id={poll_id}"
                else:
                    url = f"{AGNES_VIDEO_ENDPOINT}/{poll_id}"

                resp = requests.get(url, headers=self.headers, timeout=30)

                if resp.status_code != 200:
                    logger.warning(f"Agnes AI poll request failed: {resp.status_code}")
                    continue

                result = resp.json()
                status = result.get("status", "")

                if status == "completed":
                    # Video URL is in remixed_from_video_id field
                    video_url = result.get("remixed_from_video_id")
                    if video_url:
                        logger.info(f"Agnes AI video task {poll_id} completed")
                        return self._download_file(video_url, filename)
                    logger.error(f"No video URL in completed response: {result}")
                    return None

                if status == "failed":
                    logger.error(f"Agnes AI video task {poll_id} failed: {result}")
                    return None

                logger.debug(f"Agnes AI video task {poll_id} status: {status}, elapsed: {elapsed}s")

            except Exception as e:
                logger.warning(f"Agnes AI poll request error: {e}")

        logger.error(f"Agnes AI video task {poll_id} timed out after {self.max_poll_time}s")
        return None

    @staticmethod
    def _extract_image_url(result: dict) -> str | None:
        """Extract image URL from Agnes AI API response.

        Expected format: {"data": [{"url": "..."}]}
        """
        data = result.get("data", [])
        if data and isinstance(data, list):
            for item in data:
                if isinstance(item, dict) and item.get("url"):
                    return item["url"]
        return None

    def _download_file(self, url: str, filename: str) -> str | None:
        """Download file from URL and save locally.

        Args:
            url: Remote file URL.
            filename: Local filename to save as.

        Returns:
            Local file path on success, None on failure.
        """
        try:
            logger.info(f"Downloading file from Agnes AI: {url[:80]}...")
            resp = requests.get(url, timeout=120, stream=True)
            resp.raise_for_status()

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
