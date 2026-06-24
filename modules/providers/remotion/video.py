"""Remotion video generation adapter.

Renders videos using the Remotion framework (React-based).
Delegates to modules/remotion_client.py for CLI rendering, ffmpeg audio merging,
and image serving. Handles LLM-based composition planning internally.
"""

import logging
from pathlib import Path

from modules.remotion_client import RemotionClient
from modules.video_planner import AudioPlanner, VideoPlanner

from .. import VideoProvider
from .._subtitle_utils import SubtitleConfig, concat_videos, merge_audio

logger = logging.getLogger(__name__)


class RemotionVideoProvider(VideoProvider):
    """Video generation via Remotion (programmatic text-based video).

    Remotion's composition plan and scene timing are internal implementation
    details — not exposed through the VideoProvider interface.
    """

    def __init__(self, config: dict):
        self.config = config
        self.remotion_client = RemotionClient(config)
        self.audio_planner = AudioPlanner(config)
        self.planner = VideoPlanner(config)
        self.sub_config = SubtitleConfig.from_config(config)

        ds_config = config.get("dashscope", {})
        self.media_dir = Path(ds_config.get("media_dir", "media"))
        self.media_dir.mkdir(parents=True, exist_ok=True)

        gen_config = config.get("generation", {})
        self.duration = gen_config.get("video_duration", 15)

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
        """Generate a Remotion video. `prompt` is the oral script text."""
        return self._generate_remotion(
            script=prompt,
            filename=filename,
            audio_path=audio_url,
            keywords=keywords,
            audio_duration=audio_duration,
            scene_timings=scene_timings,
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

        http_server = None
        http_port = None
        base_name = Path(filename).stem

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
                scene["imagePath"] = http_url
                logger.info(f"Image resolved for scene {i}: {http_url}")
            else:
                logger.warning(f"Failed to find image for scene {i} query '{query}'")

    def _generate_remotion(
        self,
        script: str,
        filename: str,
        audio_path: str | None = None,
        keywords: list[str] | None = None,
        audio_duration: float | None = None,
        scene_timings: list[dict] | None = None,
    ) -> str | None:
        """Internal Remotion rendering logic. `scene_timings` kept for interface consistency."""

        duration = audio_duration or self.duration
        plan = self.planner.plan(
            script=script,
            title=filename.replace(".mp4", "").replace("_", " ").title(),
            tags=keywords,
            total_duration=duration,
        )
        if not plan:
            logger.error("Failed to generate video composition plan")
            return None

        plan_duration = sum(s.get("duration", 3) for s in plan.get("scenes", []))

        gen_config = self.config.get("generation", {})
        if gen_config.get("auto_image", False):
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
