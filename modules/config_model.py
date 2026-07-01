"""Typed configuration models for CAP content pipeline.

Provides Pydantic models for the full config.yaml structure.
DictCompatMixin provides .get() and __getitem__() for backward compatibility
during migration — old code like config.get("generation", {}).get("max_tokens", 4096)
continues to work on the typed model.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

from pydantic import BaseModel, Field


class DictCompatMixin(BaseModel):
    """Mixin providing dict-like .get() for backward compatibility during migration."""

    model_config = {"extra": "forbid", "frozen": False}

    def get(self, key: str, default: Any = None) -> Any:
        """Dict-like get() for backward compatibility during migration."""
        try:
            val = getattr(self, key)
            if isinstance(val, DictCompatMixin):
                return val
            return val
        except AttributeError:
            return default

    def __getitem__(self, key: str) -> Any:
        """Dict-like __getitem__ for backward compatibility."""
        return getattr(self, key)

    def __contains__(self, key: str) -> bool:
        """Dict-like __contains__ for backward compatibility."""
        return hasattr(self, key)

    def to_dict(self) -> dict[str, Any]:
        """Return a plain dict for consumers not yet migrated to typed access."""
        return self.model_dump()


# ── Provider configs ───────────────────────────────────────────────


class MiMoConfig(DictCompatMixin):
    api_key: str = ""
    base_url: str = "https://api.xiaomimimo.com/v1"
    model: str = "mimo-v2.5-pro"
    tts_model: str = "mimo-v2.5-tts"
    tts_voice: str = "Chloe"
    planner_model: Optional[str] = None
    media_dir: str = "media"

    @property
    def effective_planner_model(self) -> str:
        return self.planner_model or self.model

    @property
    def tts_base_url(self) -> str:
        """TTS may use a different base URL; falls back to base_url."""
        return self.base_url


class DashScopeConfig(DictCompatMixin):
    api_key: str = ""
    model: str = "qwen-image"
    size: str = "1472*1104"
    media_dir: str = "media"
    video_model: str = "wan2.7-t2v"
    video_size: str = "1280*720"
    video_duration: int = 15


class RemotionConfig(DictCompatMixin):
    project_dir: str = "remotion"
    fps: int = 24
    video_size: str = "1920*1080"
    video_duration: int = 30
    browser_executable: Optional[str] = None
    chrome_flags: str = ""


class AgnesConfig(DictCompatMixin):
    api_key: str = ""
    image_model: str = "ag-elite-v2"
    video_model: str = "agnes-video-v2.0"
    media_dir: str = "media"
    # Video generation parameters
    video_size: str = "1152*768"
    video_duration: int = 5


class ArkConfig(DictCompatMixin):
    api_key: str = ""
    base_url: str = "https://ark.cn-beijing.volces.com/api/v3"
    model: str = "deepseek-r1-250528"
    image_model: str = "doubao-seedream-2.0-t2i-250529"
    image_size: str = "1472*1104"
    video_model: str = "doubao-seedance-1.5-pro-250611"
    video_size: str = "1920*1080"
    video_duration: int = 12
    tts_model: str = "doubao-seed-tts-2.0"
    tts_resource_id: str = "seed-tts-2.0"
    tts_voice: str = "zh_female_gaolengyujie_uranus_bigtts"
    planner_model: Optional[str] = None
    media_dir: str = "media"
    asr_enabled: bool = False
    asr_mode: str = "short"
    asr_segment_duration: int = 200
    asr_sample_rate: int = 16000
    asr_resource_id: str = ""

    @property
    def effective_planner_model(self) -> str:
        return self.planner_model or self.model


# ── Generation config ──────────────────────────────────────────────


class GenerationConfig(DictCompatMixin):
    max_tokens: int = 4096
    temperature: float = 0.7
    default_limit: int = 1
    auto_image: bool = False
    auto_video: bool = False
    text_provider: str = "mimo"
    image_provider: str = "dashscope"
    video_provider: str = "dashscope"
    # Subtitle settings (flat in YAML, flat here to match structure)
    video_subtitles: bool = True
    video_subtitle_font: str = "Microsoft YaHei"
    video_subtitle_size: int = 48
    video_subtitle_line_chars: int = 16
    video_subtitle_max_lines: int = 1
    video_subtitle_text_color: str = "#FFFFFF"
    video_subtitle_border_color: str = "#000000"
    video_subtitle_alignment: int = 1
    video_subtitle_alpha: float = 1.0
    video_subtitle_keyword_color: str = "#FFD700"
    video_subtitle_keyword_size: Optional[int] = None
    video_subtitle_fade_in: float = 0.15
    video_subtitle_fade_out: float = 0.15
    video_subtitle_margin_v: int = 50
    video_subtitle_outline: int = 2
    video_subtitle_shadow: int = 1


# ── Platform configs ───────────────────────────────────────────────


class WeChatPlatformConfig(DictCompatMixin):
    enabled: bool = False
    app_id: str = ""
    app_secret: str = ""
    author: str = ""
    mode: str = "draft"
    theme: str = "claude"
    validate_content: bool = False
    max_repair: int = 1
    # Long-form articles (1500-2500字 + image prompts) easily exceed the
    # global 4096 limit, truncating the JSON. Override with a larger value.
    max_tokens: int = 8192


class XiaohongshuPlatformConfig(DictCompatMixin):
    enabled: bool = False
    cookie_file: str = "db/xhs_cookies.json"
    headless: bool = False
    channel: str = "chrome"


class DouyinPlatformConfig(DictCompatMixin):
    enabled: bool = False
    cookie_file: str = "db/douyin_cookies.json"
    headless: bool = False
    channel: str = "chrome"
    post_publish_wait: int = 30


class PlatformsConfig(DictCompatMixin):
    wechat: WeChatPlatformConfig = Field(default_factory=WeChatPlatformConfig)
    xiaohongshu: XiaohongshuPlatformConfig = Field(default_factory=XiaohongshuPlatformConfig)
    douyin: DouyinPlatformConfig = Field(default_factory=DouyinPlatformConfig)


# ── Other configs ──────────────────────────────────────────────────


class ImageSearchConfig(DictCompatMixin):
    provider: str = "placeholder"
    pexels_api_key: str = ""
    unsplash_access_key: str = ""
    download_dir: str = "data/images"
    orientation: str = "portrait"


class MonitorConfig(DictCompatMixin):
    max_topics: int = 10
    sources: dict[str, list[str]] = Field(default_factory=lambda: {"dao": [], "shu": []})


class DatabaseConfig(DictCompatMixin):
    path: str = "db/pipeline.db"


class LoggingConfig(DictCompatMixin):
    level: str = "INFO"


# ── Top-level app config ───────────────────────────────────────────


class AppConfig(DictCompatMixin):
    """Top-level application configuration matching config.yaml structure."""

    output_dir: str = "output"
    mimo: MiMoConfig = Field(default_factory=MiMoConfig)
    generation: GenerationConfig = Field(default_factory=GenerationConfig)
    dashscope: DashScopeConfig = Field(default_factory=DashScopeConfig)
    remotion: RemotionConfig = Field(default_factory=RemotionConfig)
    agnes: AgnesConfig = Field(default_factory=AgnesConfig)
    ark: ArkConfig = Field(default_factory=ArkConfig)
    platforms: PlatformsConfig = Field(default_factory=PlatformsConfig)
    image_search: ImageSearchConfig = Field(default_factory=ImageSearchConfig)
    monitor: MonitorConfig = Field(default_factory=MonitorConfig)
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
