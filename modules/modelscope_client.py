"""ModelScope API client for text-to-image and text-to-video generation.

Uses ModelScope's HTTP API inference endpoint:
    POST https://api-inference.modelscope.cn/v1/models/{model_id}
"""

import logging
import time
from pathlib import Path
import requests

logger = logging.getLogger(__name__)

# ModelScope API endpoints
MODELSCOPE_API_BASE = "https://api-inference.modelscope.cn/v1/models"

# Default models
DEFAULT_IMAGE_MODEL = "wanx-community/wanx-v1"
DEFAULT_VIDEO_MODEL = "Wan-AI/Wan2.1-T2V-14B"


class ModelScopeClient:
    """Unified client for ModelScope API inference."""

    def __init__(self, config: dict):
        ms_config = config.get("modelscope", {})
        self.api_token = ms_config.get("api_token", "")
        self.image_model = ms_config.get("image_model", DEFAULT_IMAGE_MODEL)
        self.video_model = ms_config.get("video_model", DEFAULT_VIDEO_MODEL)
        self.media_dir = Path(ms_config.get("media_dir", "media"))
        self.media_dir.mkdir(parents=True, exist_ok=True)

        # Polling config
        self.poll_interval = 5  # seconds
        self.max_poll_time = 600  # 10 minutes timeout

    @property
    def headers(self) -> dict:
        """HTTP headers with authorization."""
        return {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json",
        }

    def _request(self, model_id: str, data: dict) -> dict | None:
        """Send inference request to ModelScope API.

        Handles async task submission and polling for results.

        Args:
            model_id: Model identifier (e.g. "wanx-community/wanx-v1").
            data: Request payload with 'input' field.

        Returns:
            Response data dict on success, None on failure.
        """
        url = f"{MODELSCOPE_API_BASE}/{model_id}"
        try:
            logger.info(f"ModelScope API request to {model_id}...")
            resp = requests.post(url, headers=self.headers, json=data, timeout=30)

            if resp.status_code != 200:
                logger.error(f"ModelScope API error: {resp.status_code} - {resp.text}")
                return None

            result = resp.json()

            # Check if this is an async task
            task_id = result.get("request_id") or result.get("task_id")
            task_status = result.get("status", "")

            # If task is already complete (synchronous response)
            if task_status == "SUCCEEDED" or "output" in result:
                output = result.get("output", result)
                # Check for direct results
                if output.get("results") or output.get("result_urls") or output.get("url"):
                    return output
                # Some models return results at top level
                if result.get("results") or result.get("result_urls"):
                    return result

            # If async task, poll for result
            if task_id:
                return self._poll_task(model_id, task_id)

            # If response has result directly
            if result.get("results") or result.get("result_urls") or result.get("url"):
                return result

            logger.error(f"Unexpected ModelScope API response format: {result}")
            return None

        except requests.exceptions.Timeout:
            logger.error(f"ModelScope API request timed out for {model_id}")
            return None
        except Exception as e:
            logger.error(f"ModelScope API request failed: {e}")
            return None

    def _poll_task(self, model_id: str, task_id: str) -> dict | None:
        """Poll async task until completion.

        Args:
            model_id: Model identifier.
            task_id: Task ID from initial request.

        Returns:
            Result data on success, None on failure/timeout.
        """
        url = f"{MODELSCOPE_API_BASE}/{model_id}"
        elapsed = 0

        while elapsed < self.max_poll_time:
            time.sleep(self.poll_interval)
            elapsed += self.poll_interval

            try:
                # Try fetching task status
                poll_url = f"{url}?request_id={task_id}"
                resp = requests.get(poll_url, headers=self.headers, timeout=30)

                if resp.status_code != 200:
                    logger.warning(f"Poll request failed: {resp.status_code}")
                    continue

                result = resp.json()
                status = result.get("status", "")

                if status == "SUCCEEDED":
                    output = result.get("output", result)
                    logger.info(f"ModelScope task {task_id} succeeded")
                    return output

                if status == "FAILED":
                    logger.error(f"ModelScope task {task_id} failed: {result}")
                    return None

                logger.debug(f"Task {task_id} status: {status}, elapsed: {elapsed}s")

            except Exception as e:
                logger.warning(f"Poll request error: {e}")

        logger.error(f"ModelScope task {task_id} timed out after {self.max_poll_time}s")
        return None

    def generate_image(
        self,
        prompt: str,
        filename: str,
        negative_prompt: str = "",
        size: str = "1024*1024",
    ) -> str | None:
        """Generate an image from text prompt via ModelScope API.

        Args:
            prompt: Text description for image generation.
            filename: Output filename (e.g. "content_1_1.png").
            negative_prompt: Negative prompt to avoid certain features.
            size: Image resolution (e.g. "1024*1024").

        Returns:
            Local file path of generated image, or None.
        """
        if not self.api_token:
            logger.warning("ModelScope API token not configured, skipping image generation")
            return None

        # Parse size
        width, height = 1024, 1024
        if "*" in size:
            parts = size.split("*")
            width, height = int(parts[0]), int(parts[1])

        data = {
            "input": {
                "prompt": prompt,
            },
            "parameters": {
                "n": 1,
                "size": f"{width}*{height}",
            },
        }
        if negative_prompt:
            data["input"]["negative_prompt"] = negative_prompt

        result = self._request(self.image_model, data)
        if not result:
            return None

        # Extract image URL from response
        image_url = self._extract_image_url(result)
        if not image_url:
            logger.error(f"No image URL in ModelScope response: {result}")
            return None

        return self._download_file(image_url, filename)

    def generate_video(
        self,
        prompt: str,
        filename: str,
        size: str = "1280*720",
        duration: int = 5,
    ) -> str | None:
        """Generate a video from text prompt via ModelScope API.

        Args:
            prompt: Text description for video generation.
            filename: Output filename (e.g. "content_1_1.mp4").
            size: Video resolution (e.g. "1280*720").
            duration: Video duration in seconds.

        Returns:
            Local file path of generated video, or None.
        """
        if not self.api_token:
            logger.warning("ModelScope API token not configured, skipping video generation")
            return None

        # Parse size
        width, height = 1280, 720
        if "*" in size:
            parts = size.split("*")
            width, height = int(parts[0]), int(parts[1])

        data = {
            "input": {
                "prompt": prompt,
            },
            "parameters": {
                "size": f"{width}*{height}",
                "duration": duration,
            },
        }

        result = self._request(self.video_model, data)
        if not result:
            return None

        # Extract video URL from response
        video_url = self._extract_video_url(result)
        if not video_url:
            logger.error(f"No video URL in ModelScope response: {result}")
            return None

        return self._download_file(video_url, filename)

    @staticmethod
    def _extract_image_url(result: dict) -> str | None:
        """Extract image URL from ModelScope API response.

        Supports multiple response formats:
        - {"results": [{"url": "..."}]}
        - {"result_urls": ["..."]}
        - {"url": "..."}
        - {"output": {"results": [{"url": "..."}]}}
        """
        # Format 1: results list
        results = result.get("results", [])
        if results and isinstance(results, list):
            for item in results:
                if isinstance(item, dict) and item.get("url"):
                    return item["url"]
                if isinstance(item, str):
                    return item

        # Format 2: result_urls list
        result_urls = result.get("result_urls", [])
        if result_urls and isinstance(result_urls, list):
            return result_urls[0]

        # Format 3: direct url
        if result.get("url"):
            return result["url"]

        # Format 4: output nested
        output = result.get("output", {})
        if isinstance(output, dict):
            out_results = output.get("results", [])
            if out_results:
                for item in out_results:
                    if isinstance(item, dict) and item.get("url"):
                        return item["url"]
            out_urls = output.get("result_urls", [])
            if out_urls:
                return out_urls[0]

        return None

    @staticmethod
    def _extract_video_url(result: dict) -> str | None:
        """Extract video URL from ModelScope API response.

        Same format variations as image, plus:
        - {"video_url": "..."}
        - {"output": {"video_url": "..."}}
        """
        # Try video-specific fields first
        if result.get("video_url"):
            return result["video_url"]

        output = result.get("output", {})
        if isinstance(output, dict) and output.get("video_url"):
            return output["video_url"]

        # Fall back to generic URL extraction
        return ModelScopeClient._extract_image_url(result)

    def _download_file(self, url: str, filename: str) -> str | None:
        """Download file from URL and save locally.

        Args:
            url: Remote file URL.
            filename: Local filename to save as.

        Returns:
            Local file path on success, None on failure.
        """
        try:
            logger.info(f"Downloading file from ModelScope: {url[:80]}...")
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
