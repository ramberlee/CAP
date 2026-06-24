"""Video generation module — delegates to the appropriate VideoProvider adapter.

Preserves the VideoGenerator class API for existing consumers (generator.py).
"""

import logging
import os
import shutil
from pathlib import Path

from modules.providers.dashscope.video import DashScopeVideoProvider
from modules.providers.agnes.video import AgnesVideoProvider
from modules.providers.ark.video import ArkVideoProvider
from modules.providers.remotion.video import RemotionVideoProvider
from modules.providers._subtitle_utils import (
    SubtitleConfig,
    burn_subtitles,
    concat_videos as _concat_videos,
    find_ffmpeg,
    merge_audio as _merge_audio,
    probe_video_duration,
)
from modules.video_planner import AudioPlanner, VideoPlanner

logger = logging.getLogger(__name__)


class VideoGenerator:
    """Video generation facade — routes to the configured provider adapter.

    Provider is selected by generation.video_provider in config:
      "dashscope" (default), "agnes", "ark", or "remotion".

    Preserves all public methods and attributes for existing consumers.
    """

    def __init__(self, config: dict):
        self.config = config
        gen_config = config.get("generation", {})
        self.provider = gen_config.get("video_provider", "dashscope")

        ds_config = config.get("dashscope", {})
        self.api_key = ds_config.get("api_key", "")
        self.model = ds_config.get("video_model", "wan2.7-t2v")
        self.size = ds_config.get("video_size", "1280*720")
        self.duration = ds_config.get("video_duration", 15)
        self.media_dir = Path(ds_config.get("media_dir", "media"))
        self.media_dir.mkdir(parents=True, exist_ok=True)

        # Subtitle config (preserved for _burn_subtitles compat)
        self.sub_config = SubtitleConfig.from_config(config)
        self.video_subtitles = gen_config.get("video_subtitles", True)

        # Instantiate the correct adapter
        if self.provider == "agnes":
            self._provider = AgnesVideoProvider(config)
            self.remotion_client = None
            self.audio_planner = None
            self.planner = None
        elif self.provider == "ark":
            self._provider = ArkVideoProvider(config)
            self.remotion_client = None
            self.audio_planner = None
            self.planner = None
        elif self.provider == "remotion":
            self._provider = RemotionVideoProvider(config)
            self.remotion_client = self._provider.remotion_client
            self.audio_planner = self._provider.audio_planner
            self.planner = self._provider.planner
        else:
            self._provider = DashScopeVideoProvider(config)
            self.remotion_client = None
            self.audio_planner = None
            self.planner = None

        logger.info(f"VideoGenerator using {self.provider} backend")

    def generate(
        self,
        prompt: str,
        filename: str,
        audio_url: str | None = None,
        subtitles: str | None = None,
        keywords: list[str] | None = None,
        audio_duration: float | None = None,
        plan: dict | None = None,
        scene_timings: list[dict] | None = None,
    ) -> str | None:
        """Generate a video. For Remotion, `plan` is forwarded as internal detail."""
        if self.provider == "remotion":
            return self._provider.generate(
                prompt=prompt,
                filename=filename,
                audio_url=audio_url,
                subtitles=subtitles,
                keywords=keywords,
                audio_duration=audio_duration,
                scene_timings=scene_timings,
            )
        return self._provider.generate(
            prompt=prompt,
            filename=filename,
            audio_url=audio_url,
            subtitles=subtitles,
            keywords=keywords,
            audio_duration=audio_duration,
            scene_timings=scene_timings,
        )

    def concat_videos(self, video_paths: list[str], output_path: str) -> str | None:
        """Concatenate multiple video files into one."""
        if self.remotion_client:
            return self.remotion_client.concat_videos(video_paths, output_path)
        return _concat_videos(video_paths, output_path)

    def _merge_audio(self, video_path: str, audio_path: str | None, trim_duration: float | None = None) -> str | None:
        """Merge audio into a video file. Returns video path."""
        if self.remotion_client:
            return self.remotion_client._merge_audio(video_path, audio_path, trim_duration)
        result = _merge_audio(video_path, audio_path, trim_duration)
        return result

    def _burn_subtitles(
        self,
        video_path: str | None,
        subtitle_text: str | None,
        keywords: list[str] | None = None,
        audio_duration: float | None = None,
        scene_timings: list[dict] | None = None,
    ) -> str | None:
        """Burn subtitles into video using ASS format."""
        if not video_path or not subtitle_text or not self.video_subtitles:
            return video_path
        return burn_subtitles(
            video_path, subtitle_text, self.size, self.sub_config,
            keywords, audio_duration, scene_timings,
        )

    @staticmethod
    def _pick_api_duration(audio_duration: float, supported: list[int] | None = None) -> int:
        if supported is None:
            supported = [5, 10, 15]
        for d in sorted(supported):
            if audio_duration <= d:
                return d
        return max(supported)

    def _probe_video_duration(self, video_path: str) -> float | None:
        return probe_video_duration(video_path)
