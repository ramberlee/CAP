"""Remotion video generation adapter.

Renders videos using the Remotion framework (React-based).
Uses .client.RemotionClient for CLI rendering, ffmpeg audio merging,
and image serving. Handles LLM-based composition planning internally.
"""

import logging
from pathlib import Path

from .client import RemotionClient
from modules.video_planner import VideoPlanner

from .. import VideoProvider
from .._subtitle_builder import SubtitleConfig
from .._ffmpeg_utils import concat_videos, merge_audio
from ...config_model import AppConfig

logger = logging.getLogger(__name__)


class RemotionVideoProvider(VideoProvider):
    """Video generation via Remotion (programmatic text-based video).

    Remotion's composition plan and scene timing are internal implementation
    details — not exposed through the VideoProvider interface.
    """

    def __init__(self, config: AppConfig):
        self.config = config
        self.remotion_client = RemotionClient(config)
        self.planner = VideoPlanner(config)
        self.sub_config = SubtitleConfig.from_config(config.generation)

        self.media_dir = Path(config.dashscope.media_dir)
        self.media_dir.mkdir(parents=True, exist_ok=True)

        self.video_size = config.remotion.video_size
        self.duration = config.remotion.video_duration or 30

    def generate(
        self,
        prompt: str,
        filename: str,
        audio_path: str | None = None,
        subtitles: str | None = None,
        keywords: list[str] | None = None,
        audio_duration: float | None = None,
        scene_timings: list[dict] | None = None,
        plan: dict | None = None,
    ) -> str | None:
        """Generate a Remotion video. `prompt` is the oral script text."""
        return self._generate_remotion(
            script=prompt,
            filename=filename,
            audio_path=audio_path,
            keywords=keywords,
            audio_duration=audio_duration,
            scene_timings=scene_timings,
            plan=plan,
        )

    def _resolve_scene_images(self, plan: dict, filename: str) -> None:
        """Search and download images for any scene with an 'image_query' field."""
        scenes = plan.get("scenes", [])
        image_scenes = [
            (i, s) for i, s in enumerate(scenes)
            if s.get("image_query") and isinstance(s.get("image_query"), str) and s["image_query"].strip()
        ]
        if not image_scenes:
            return

        try:
            from modules.image_search import get_searcher
            searcher = get_searcher(self.config)
        except Exception as e:
            logger.warning(f"Image search module not available: {e}")
            return

        image_dir = searcher.download_dir.resolve()
        import threading
        from http.server import HTTPServer, SimpleHTTPRequestHandler

        class _ImageHandler(SimpleHTTPRequestHandler):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, directory=str(image_dir), **kwargs)

        http_server: HTTPServer | None = None
        http_port: int | None = None
        base_name = Path(filename).stem

        try:
            for i, scene in image_scenes:
                query = scene["image_query"].strip()
                logger.info(f"Searching image for scene {i} ({scene.get('type')}): '{query}'")
                img_filename = f"{base_name}_scene_{i}"
                path = searcher.search_and_download(query, img_filename)
                if path:
                    if http_server is None:
                        for port in range(9876, 9900):
                            try:
                                http_server = HTTPServer(("127.0.0.1", port), _ImageHandler)
                                http_port = port
                                thread = threading.Thread(target=http_server.serve_forever, daemon=True)
                                thread.start()
                                logger.info(f"Started image HTTP server on port {http_port}")
                                break
                            except OSError:
                                continue
                    http_url = f"http://127.0.0.1:{http_port}/{path.name}"
                    scene["imageUrl"] = http_url
                    logger.info(f"Image resolved for scene {i}: {http_url}")
                else:
                    logger.warning(f"Failed to find image for scene {i} query '{query}'")
        finally:
            if http_server is not None:
                http_server.shutdown()
                logger.info("Image HTTP server shut down")

    def _generate_remotion(
        self,
        script: str,
        filename: str,
        audio_path: str | None = None,
        keywords: list[str] | None = None,
        audio_duration: float | None = None,
        scene_timings: list[dict] | None = None,
        plan: dict | None = None,
    ) -> str | None:
        """Internal Remotion rendering logic.

        When `plan` is provided (pre-generated with audio timings), uses it directly.
        Otherwise generates a new plan internally (legacy path for backward compat).
        """

        duration = audio_duration or self.duration

        # Use external plan if provided (avoids double LLM call)
        if plan is None:
            plan = self.planner.plan(
                script=script,
                title=filename.replace(".mp4", "").replace("_", " ").title(),
                tags=keywords,
                total_duration=duration,
            )
            if not plan:
                logger.error("Failed to generate video composition plan")
                return None
        else:
            logger.info("Using externally-provided composition plan (with audio timings)")

        plan_duration = sum(s.get("duration", 3) for s in plan.get("scenes", []))

        if self.config.generation.auto_image:
            self._resolve_scene_images(plan, filename)

        if audio_duration and plan_duration < audio_duration:
            gap = round(audio_duration - plan_duration, 2)
            if plan.get("scenes"):
                plan["scenes"][-1]["duration"] = round(plan["scenes"][-1]["duration"] + gap, 2)
                plan_duration = audio_duration
                logger.info(f"Extended last scene by {gap:.1f}s to match audio ({audio_duration:.1f}s)")

        return self.remotion_client.render(
            plan=plan,
            filename=filename,
            audio_path=audio_path,
            plan_duration=plan_duration,
        )
