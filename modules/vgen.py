"""Video generation module with DashScope and ModelScope backends."""

import logging
import re
import shutil
import subprocess
import tempfile
import time
from pathlib import Path
import requests
import dashscope
from dashscope import VideoSynthesis
from modules.modelscope_client import ModelScopeClient

logger = logging.getLogger(__name__)


class VideoGenerator:
    def __init__(self, config: dict):
        # Determine provider: "dashscope" (default) or "modelscope"
        gen_config = config.get("generation", {})
        self.provider = gen_config.get("video_provider", "dashscope")

        ds_config = config.get("dashscope", {})
        self.api_key = ds_config.get("api_key", "")
        self.model = ds_config.get("video_model", "wan2.7-t2v")
        self.size = ds_config.get("video_size", "1280*720")
        self.duration = ds_config.get("video_duration", 15)
        self.media_dir = Path(ds_config.get("media_dir", "media"))
        self.media_dir.mkdir(parents=True, exist_ok=True)

        # Initialize provider-specific client
        if self.provider == "modelscope":
            self.ms_client = ModelScopeClient(config)
            logger.info(f"VideoGenerator using ModelScope backend (model: {self.ms_client.video_model})")
        else:
            self.ms_client = None

        gen_config = config.get("generation", {})
        self.video_subtitles = gen_config.get("video_subtitles", True)
        self.subtitle_font = gen_config.get("video_subtitle_font", "Microsoft YaHei")
        self.subtitle_fontsize = gen_config.get("video_subtitle_size", 48)
        self.subtitle_line_chars = gen_config.get("video_subtitle_line_chars", 16)
        self.subtitle_max_lines = gen_config.get("video_subtitle_max_lines", 2)

        # CapCut Mate-inspired subtitle style options
        self.subtitle_text_color = gen_config.get("video_subtitle_text_color", "#FFFFFF")
        self.subtitle_border_color = gen_config.get("video_subtitle_border_color", "#000000")
        self.subtitle_alignment = gen_config.get("video_subtitle_alignment", 1)  # 0-5, 1=bottom-center
        self.subtitle_alpha = gen_config.get("video_subtitle_alpha", 1.0)  # 0.0-1.0
        self.subtitle_keyword_color = gen_config.get("video_subtitle_keyword_color", "#FFD700")
        self.subtitle_keyword_fontsize = gen_config.get("video_subtitle_keyword_size", None)
        self.subtitle_fade_in = gen_config.get("video_subtitle_fade_in", 0.15)  # seconds
        self.subtitle_fade_out = gen_config.get("video_subtitle_fade_out", 0.15)  # seconds
        self.subtitle_margin_v = gen_config.get("video_subtitle_margin_v", 50)  # vertical margin (pixels)
        self.subtitle_outline = gen_config.get("video_subtitle_outline", 2)  # outline width
        self.subtitle_shadow = gen_config.get("video_subtitle_shadow", 1)  # shadow depth

        # Polling config
        self.poll_interval = 5  # seconds
        self.max_poll_time = 600  # 10 minutes timeout

        dashscope.api_key = self.api_key

    def generate(self, prompt: str, filename: str, audio_url: str | None = None, subtitles: str | None = None, keywords: list[str] | None = None, audio_duration: float | None = None) -> str | None:
        """Generate a video from a text prompt, optionally with synced audio.

        Args:
            prompt: Text description for video generation.
            filename: Output filename.
            audio_url: Optional OSS URL of TTS audio for voice-synced video.
            subtitles: Optional text to burn into the video as subtitles.
            keywords: Optional list of keywords to highlight in subtitles.
            audio_duration: Optional actual TTS audio duration in seconds for subtitle timing.

        Returns:
            Local file path of generated video, or None.
        """
        if self.provider == "modelscope":
            return self._generate_modelscope(prompt, filename, subtitles=subtitles, keywords=keywords, audio_duration=audio_duration)

        # DashScope backend
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
                        video_path = self._download_video(video_url, filename)
                        return self._burn_subtitles(video_path, subtitles, keywords, audio_duration)
                    # Try alternative response format
                    results = result.output.get("results", [])
                    if results and results[0].get("url"):
                        video_path = self._download_video(results[0]["url"], filename)
                        return self._burn_subtitles(video_path, subtitles, keywords, audio_duration)
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

    def _generate_modelscope(self, prompt: str, filename: str, subtitles: str | None = None, keywords: list[str] | None = None, audio_duration: float | None = None) -> str | None:
        """Generate video using ModelScope API.

        Args:
            prompt: Text description for video generation.
            filename: Output filename.
            subtitles: Optional text to burn into the video as subtitles.
            keywords: Optional list of keywords to highlight in subtitles.
            audio_duration: Optional actual TTS audio duration in seconds for subtitle timing.

        Returns:
            Local file path of generated video, or None.
        """
        logger.info(f"Generating video via ModelScope: {prompt[:80]}...")
        video_path = self.ms_client.generate_video(
            prompt=prompt,
            filename=filename,
            size=self.size,
            duration=self.duration,
        )
        if video_path:
            return self._burn_subtitles(video_path, subtitles, keywords, audio_duration)
        return None

    def _burn_subtitles(self, video_path: str | None, subtitle_text: str | None, keywords: list[str] | None = None, audio_duration: float | None = None) -> str | None:
        """Burn subtitles into video using ASS format (inspired by CapCut Mate).

        Supports: text color, border/outline, alignment, alpha,
        keyword highlighting, fade in/out animations, and position control.
        """
        if not video_path or not subtitle_text or not self.video_subtitles:
            return video_path

        if not self._ffmpeg_available():
            logger.warning("ffmpeg not found, skipping subtitle burn-in")
            return video_path

        # Use TTS audio duration for subtitle timing (matches spoken words),
        # fall back to probed video duration, then config duration.
        duration = audio_duration or self._probe_video_duration(video_path) or float(self.duration)
        try:
            # Generate ASS subtitle content (richer than SRT, supports CapCut Mate-style styling)
            ass_content = self._build_ass(subtitle_text, duration, keywords)

            output_path = Path(video_path).with_name(f"{Path(video_path).stem}.sub.mp4")

            # Write ASS to CWD (relative path, avoids Windows drive-letter colon issues in ffmpeg filter)
            ass_name = f"_tmp_{Path(video_path).stem}.ass"
            ass_path = Path(ass_name)
            ass_path.write_text(ass_content, encoding="utf-8")

            # Use POSIX-style paths to avoid backslash issues in ffmpeg
            video_filter_path = str(video_path).replace("\\", "/")
            output_filter_path = str(output_path).replace("\\", "/")

            subprocess.run(
                [
                    "ffmpeg",
                    "-y",
                    "-i",
                    video_filter_path,
                    "-vf",
                    f"ass={ass_name}",
                    "-c:v",
                    "libx264",
                    "-crf",
                    "18",
                    "-preset",
                    "fast",
                    "-c:a",
                    "copy",
                    output_filter_path,
                ],
                check=True,
                capture_output=True,
                text=True,
            )

            ass_path.unlink(missing_ok=True)
            output_path.replace(video_path)
            logger.info(f"Subtitles (ASS) burned in: {video_path}")
            return str(video_path)
        except Exception as e:
            logger.warning(f"Failed to burn subtitles into video: {e}")
            return video_path

    def _build_ass(self, text: str, duration: float, keywords: list[str] | None = None) -> str:
        """Build ASS subtitle content with CapCut Mate-inspired styling.

        Generates a complete .ass file including:
        - [Script Info] with resolution from self.size
        - [V4+ Styles] with text color, border, alignment, alpha, outline, shadow
        - [Events] with keyword highlighting and fade in/out animations
        """
        lines = self._split_subtitle_lines(text)
        if not lines:
            return ""

        groups = [lines[i:i + self.subtitle_max_lines]
                  for i in range(0, len(lines), self.subtitle_max_lines)]

        # Proportional timing: each group's duration is based on its character count
        group_chars = [sum(len(line) for line in group) for group in groups]
        total_chars = sum(group_chars) or 1
        group_durations = [max(1.5, duration * chars / total_chars) for chars in group_chars]

        width, height = self.size.split('*')
        kw_list = keywords or []
        kw_color_hex = self.subtitle_keyword_color
        kw_fs = self.subtitle_keyword_fontsize or self.subtitle_fontsize
        default_fs = self.subtitle_fontsize
        fade_in_cs = int(self.subtitle_fade_in * 100)
        fade_out_cs = int(self.subtitle_fade_out * 100)
        align_ass = self._capcut_align_to_ass(self.subtitle_alignment)

        ass_parts = [
            "[Script Info]",
            "Title: CAP Subtitles (CapCut Mate style)",
            "ScriptType: v4.00+",
            "Collisions: Normal",
            f"PlayResX: {width}",
            f"PlayResY: {height}",
            "WrapStyle: 2",
            "",
            "[V4+ Styles]",
            "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, "
            "OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, "
            "ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, "
            "Alignment, MarginL, MarginR, MarginV, Encoding",
        ]

        # Build style line
        primary_color = self._ass_color_with_alpha(self.subtitle_text_color, self.subtitle_alpha)
        outline_color_ass = self._ass_color_with_alpha(self.subtitle_border_color, 1.0)

        ass_parts.append(
            f"Style: Default,{self.subtitle_font},{self.subtitle_fontsize},"
            f"{primary_color},{primary_color},{outline_color_ass},&H80000000,"
            f"0,0,0,0,100,100,0,0,1,"
            f"{self.subtitle_outline},{self.subtitle_shadow},"
            f"{align_ass},10,10,{self.subtitle_margin_v},1"
        )
        ass_parts.append("")
        ass_parts.append("[Events]")
        ass_parts.append(
            "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"
        )

        elapsed = 0.0
        for index, group in enumerate(groups):
            start_ts = self._format_ass_timestamp(elapsed)
            elapsed += group_durations[index]
            end_ts = self._format_ass_timestamp(elapsed)

            # Keyword highlighting (CapCut Mate-style)
            highlighted_lines = []
            for line in group:
                hl_line = self._highlight_keywords(line, kw_list, kw_color_hex, kw_fs, default_fs)
                highlighted_lines.append(hl_line)

            group_text = "\\N".join(highlighted_lines)

            # Fade animation (CapCut Mate in_animation / out_animation)
            if fade_in_cs > 0 or fade_out_cs > 0:
                group_text = f"{{\\fad({fade_in_cs},{fade_out_cs})}}{group_text}"

            ass_parts.append(f"Dialogue: 0,{start_ts},{end_ts},Default,,0,0,0,,{group_text}")

        return "\n".join(ass_parts) + "\n"

    def _split_subtitle_lines(self, text: str) -> list[str]:
        cleaned = re.sub(r"\s+", " ", text.replace("\n", " ")).strip()
        if not cleaned:
            return []

        parts = re.split(r"([。！？!?])", cleaned)
        sentences = []
        for i in range(0, len(parts) - 1, 2):
            sentence = (parts[i].strip() + parts[i + 1]).strip()
            if sentence:
                sentences.append(sentence)
        if len(parts) % 2 == 1 and parts[-1].strip():
            sentences.append(parts[-1].strip())

        lines = []
        for sentence in sentences:
            for i in range(0, len(sentence), self.subtitle_line_chars):
                lines.append(sentence[i : i + self.subtitle_line_chars].strip())

        return lines

    @staticmethod
    def _format_ass_timestamp(seconds: float) -> str:
        """ASS timestamp format: H:MM:SS.cc (centiseconds)."""
        total_cs = int(seconds * 100)
        hours = total_cs // 360_000
        minutes = (total_cs // 6000) % 60
        secs = (total_cs // 100) % 60
        cs = total_cs % 100
        return f"{hours}:{minutes:02d}:{secs:02d}.{cs:02d}"

    @staticmethod
    def _html_to_ass_color(html_color: str) -> tuple[str, str, str]:
        """Parse #RRGGBB into (rr, gg, bb) hex strings."""
        c = html_color.lstrip('#')
        if len(c) >= 6:
            return c[0:2], c[2:4], c[4:6]
        return "FF", "FF", "FF"

    @staticmethod
    def _ass_color_with_alpha(html_color: str, alpha: float) -> str:
        """Build ASS color value &HAABBGGRR from HTML #RRGGBB and alpha (0.0-1.0)."""
        r, g, b = VideoGenerator._html_to_ass_color(html_color)
        alpha_hex = f"{max(0, min(255, int((1.0 - alpha) * 255))):02X}"
        return f"&H{alpha_hex}{b}{g}{r}"

    @staticmethod
    def _ass_inline_color(html_color: str) -> str:
        """Build ASS inline color tag value &HBBGGRR& from HTML #RRGGBB (no alpha)."""
        r, g, b = VideoGenerator._html_to_ass_color(html_color)
        return f"&H{b}{g}{r}&"

    @staticmethod
    def _capcut_align_to_ass(align: int) -> int:
        """Map CapCut Mate alignment (0-5) to ASS alignment (1-9 numpad style).

        CapCut: 0=bottom-left, 1=bottom-center, 2=bottom-right,
                3=mid-left,    4=mid-center,    5=mid-right
        ASS:    1=bottom-left, 2=bottom-center, 3=bottom-right,
                4=mid-left,    5=mid-center,    6=mid-right
                7=top-left,    8=top-center,    9=top-right
        """
        mapping = {0: 1, 1: 2, 2: 3, 3: 4, 4: 5, 5: 6}
        return mapping.get(align, 2)

    @staticmethod
    def _highlight_keywords(text: str, keywords: list[str], kw_color_hex: str, kw_fs: int, default_fs: int) -> str:
        """Wrap keywords found in text with ASS color/size override tags.

        Uses \\c and \\fs tags like CapCut Mate's keyword_color and keyword_font_size.
        """
        if not keywords:
            return text
        kw_color_ass = VideoGenerator._ass_inline_color(kw_color_hex)
        result = text
        for kw in keywords:
            if kw and kw in result:
                result = result.replace(
                    kw,
                    f"{{\\c{kw_color_ass}\\fs{kw_fs}}}{kw}{{\\c\\fs{default_fs}}}"
                )
        return result

    def _ffmpeg_available(self) -> bool:
        return shutil.which("ffmpeg") is not None

    def _probe_video_duration(self, video_path: str) -> float | None:
        if shutil.which("ffprobe") is None:
            return None
        try:
            result = subprocess.run(
                [
                    "ffprobe",
                    "-v",
                    "error",
                    "-show_entries",
                    "format=duration",
                    "-of",
                    "default=noprint_wrappers=1:nokey=1",
                    str(video_path),
                ],
                capture_output=True,
                text=True,
                check=True,
            )
            return float(result.stdout.strip())
        except Exception:
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
