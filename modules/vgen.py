"""Video generation module with DashScope, Agnes and Remotion backends."""

import logging
import os
import re
import shutil
import subprocess
import time
from pathlib import Path
import requests
import dashscope
from dashscope import VideoSynthesis
from modules.agnes_client import AgnesClient
from modules.ark_client import ArkClient
from modules.remotion_client import RemotionClient
from modules.video_planner import AudioPlanner, VideoPlanner

logger = logging.getLogger(__name__)


def _find_ffmpeg() -> str:
    """Locate ffmpeg: system PATH first, then imageio_ffmpeg bundled binary."""
    found = shutil.which("ffmpeg")
    if found:
        return found
    try:
        import imageio_ffmpeg
        exe = imageio_ffmpeg.get_ffmpeg_exe()
        if exe and os.path.isfile(exe):
            return exe
    except Exception:
        pass
    return "ffmpeg"


class VideoGenerator:
    def __init__(self, config: dict):
        self.config = config
        # Determine provider: "dashscope" (default), "agnes", or "remotion"
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
        if self.provider == "agnes":
            self.agnes_client = AgnesClient(config)
            self.remotion_client = None
            logger.info(f"VideoGenerator using Agnes AI backend (model: {self.agnes_client.video_model})")
        elif self.provider == "ark":
            self.ark_client = ArkClient(config)
            self.remotion_client = None
            logger.info(f"VideoGenerator using Ark backend (model: {self.ark_client.video_model})")
        elif self.provider == "remotion":
            self.remotion_client = RemotionClient(config)
            logger.info(f"VideoGenerator using Remotion backend (project: {self.remotion_client.project_dir})")
        else:
            self.remotion_client = None

        # Video and audio planners (used by remotion provider)
        if self.provider == "remotion":
            self.audio_planner = AudioPlanner(config)
            self.planner = VideoPlanner(config)
        else:
            self.audio_planner = None
            self.planner = None

        gen_config = config.get("generation", {})
        self.video_subtitles = gen_config.get("video_subtitles", True)
        self.subtitle_font = gen_config.get("video_subtitle_font", "Microsoft YaHei")
        self.subtitle_fontsize = gen_config.get("video_subtitle_size", 48)
        self.subtitle_line_chars = gen_config.get("video_subtitle_line_chars", 16)
        self.subtitle_max_lines = gen_config.get("video_subtitle_max_lines", 1)

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

    def concat_videos(self, video_paths: list[str], output_path: str) -> str | None:
        """Concatenate multiple video files into one using ffmpeg.

        All videos must have the same resolution and codec.
        Uses concat demuxer for fast, re-encoding-free joining.

        Args:
            video_paths: List of video file paths to concatenate in order.
            output_path: Output video file path.

        Returns:
            Output path on success, None on failure.
        """
        # Delegate to RemotionClient if available (has ffmpeg path management)
        if self.remotion_client:
            return self.remotion_client.concat_videos(video_paths, output_path)

        if not video_paths:
            return None
        if len(video_paths) == 1:
            shutil.copy2(video_paths[0], output_path)
            return output_path

        # Write concat list file
        list_path = Path(output_path).with_suffix(".txt")
        with open(list_path, "w", encoding="utf-8") as f:
            for p in video_paths:
                safe_path = str(Path(p).resolve()).replace("\\", "/").replace("'", "'\\''")
                f.write(f"file '{safe_path}'\n")

        try:
            ffmpeg = _find_ffmpeg()
            subprocess.run(
                [ffmpeg, "-y",
                 "-f", "concat", "-safe", "0",
                 "-i", str(list_path),
                 "-c", "copy",
                 str(output_path)],
                check=True, capture_output=True, text=True, timeout=120,
            )
            list_path.unlink(missing_ok=True)
            logger.info(f"Videos concatenated: {len(video_paths)} segments → {output_path}")
            return output_path
        except Exception as e:
            logger.error(f"Video concatenation failed: {e}")
            list_path.unlink(missing_ok=True)
            return None

    def _merge_audio(self, video_path: str, audio_path: str, trim_duration: float | None = None) -> str | None:
        """Merge audio into a video file using ffmpeg.

        Delegates to RemotionClient if available, otherwise uses local ffmpeg.
        """
        if self.remotion_client:
            return self.remotion_client._merge_audio(video_path, audio_path, trim_duration)

        # Fallback: direct ffmpeg merge
        if not audio_path or not Path(audio_path).exists():
            return video_path

        ffmpeg = _find_ffmpeg()
        video_p = Path(video_path)
        temp_output = video_p.with_name(f"{video_p.stem}_with_audio.mp4")

        try:
            cmd = [
                ffmpeg, "-y",
                "-i", str(video_p),
                "-i", audio_path,
                "-c:v", "copy", "-c:a", "aac",
                "-map", "0:v:0", "-map", "1:a:0",
                "-shortest",
                str(temp_output),
            ]
            subprocess.run(cmd, check=True, capture_output=True, text=True, timeout=60)
            temp_output.replace(video_p)
            logger.info(f"Audio merged: {video_p}")
            return str(video_p)
        except Exception as e:
            logger.warning(f"Audio merge failed: {e}")
            return video_path

    @staticmethod
    def _pick_api_duration(audio_duration: float, supported: list[int] | None = None) -> int:
        """Pick the smallest supported API duration that covers the audio.

        DashScope/Agnes video APIs only accept fixed duration values.
        This ensures the video is at least as long as the audio.
        """
        if supported is None:
            supported = [5, 10, 15]
        for d in sorted(supported):
            if audio_duration <= d:
                return d
        return max(supported)

    def generate(self, prompt: str, filename: str, audio_url: str | None = None, subtitles: str | None = None, keywords: list[str] | None = None, audio_duration: float | None = None, plan: dict | None = None, scene_timings: list[dict] | None = None) -> str | None:
        """Generate a video from a text prompt, optionally with synced audio.

        Args:
            prompt: Text description for video generation.
            filename: Output filename.
            audio_url: Optional OSS URL of TTS audio (DashScope) or local path (Remotion).
            subtitles: Optional text to burn into the video as subtitles.
            keywords: Optional list of keywords to highlight in subtitles.
            audio_duration: Optional actual TTS audio duration in seconds for subtitle timing.
            plan: Optional pre-generated video composition plan (used by Remotion).
            scene_timings: Optional per-scene timing data for precise subtitle sync.
                          Each dict has keys: text, start, end (in seconds).

        Returns:
            Local file path of generated video, or None.
        """
        if self.provider == "remotion":
            return self._generate_remotion(
                script=prompt,
                filename=filename,
                audio_path=audio_url,
                keywords=keywords,
                audio_duration=audio_duration,
                plan=plan,
                scene_timings=scene_timings,
            )

        if self.provider == "agnes":
            return self._generate_agnes(prompt, filename, subtitles=subtitles, keywords=keywords, audio_duration=audio_duration, scene_timings=scene_timings)

        if self.provider == "ark":
            return self._generate_ark(prompt, filename, subtitles=subtitles, keywords=keywords, audio_duration=audio_duration, scene_timings=scene_timings)

        # DashScope backend
        if not self.api_key:
            logger.warning("DashScope API key not configured, skipping video generation")
            return None

        # Pick API duration: smallest supported value that covers the audio
        api_duration = self._pick_api_duration(audio_duration or self.duration)
        logger.info(f"API duration: {api_duration}s (audio: {audio_duration}s)")

        try:
            kwargs = dict(
                model=self.model,
                prompt=prompt,
                size=self.size,
                duration=api_duration,
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
                        return self._finalize_video(video_path, subtitles, keywords, audio_duration, scene_timings)
                    # Try alternative response format
                    results = result.output.get("results", [])
                    if results and results[0].get("url"):
                        video_path = self._download_video(results[0]["url"], filename)
                        return self._finalize_video(video_path, subtitles, keywords, audio_duration, scene_timings)
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

    def _finalize_video(self, video_path: str | None, subtitles: str | None, keywords: list[str] | None, audio_duration: float | None, scene_timings: list[dict] | None) -> str | None:
        """Finalize a generated video: burn subtitles using the video's actual duration.

        The video model may produce a video whose duration differs from the TTS audio.
        To keep subtitles in sync with the visual content, we probe the actual video
        duration and use it for subtitle timing instead of audio_duration.
        """
        if not video_path:
            return None

        # Use video's actual duration for subtitle timing (not audio_duration)
        # This ensures subtitles are synced to what's visually playing
        video_duration = self._probe_video_duration(video_path)
        subtitle_duration = video_duration or audio_duration

        if video_duration and audio_duration and abs(video_duration - audio_duration) > 1.0:
            logger.info(f"Video/Audio duration mismatch: video={video_duration:.1f}s, "
                       f"audio={audio_duration:.1f}s — using video duration for subtitles")

        return self._burn_subtitles(video_path, subtitles, keywords, subtitle_duration, scene_timings)

    def _generate_agnes(self, prompt: str, filename: str, subtitles: str | None = None, keywords: list[str] | None = None, audio_duration: float | None = None, scene_timings: list[dict] | None = None) -> str | None:
        """Generate video using Agnes AI API."""
        logger.info(f"Generating video via Agnes AI: {prompt[:80]}...")

        width, height = 1152, 768
        if "*" in self.size:
            parts = self.size.split("*")
            width, height = int(parts[0]), int(parts[1])
        elif "x" in self.size:
            parts = self.size.split("x")
            width, height = int(parts[0]), int(parts[1])

        fps = 24
        num_frames = min(441, int(self.duration * fps))
        num_frames = ((num_frames - 1) // 8) * 8 + 1

        video_path = self.agnes_client.generate_video(
            prompt=prompt,
            filename=filename,
            width=width,
            height=height,
            num_frames=num_frames,
            frame_rate=fps,
        )
        if video_path:
            return self._finalize_video(video_path, subtitles, keywords, audio_duration, scene_timings)
        return None

    def _generate_ark(self, prompt: str, filename: str, subtitles: str | None = None, keywords: list[str] | None = None, audio_duration: float | None = None, scene_timings: list[dict] | None = None) -> str | None:
        """Generate video using Volcano Ark API."""
        logger.info(f"Generating video via Ark: {prompt[:80]}...")

        # Pick API duration: smallest supported value that covers the audio
        api_duration = self._pick_api_duration(audio_duration or self.duration)
        logger.info(f"Ark API duration: {api_duration}s (audio: {audio_duration}s)")

        video_path = self.ark_client.generate_video(
            prompt=prompt,
            filename=filename,
            duration=api_duration,
        )
        if video_path:
            return self._finalize_video(video_path, subtitles, keywords, audio_duration, scene_timings)
        return None

    def _burn_subtitles(self, video_path: str | None, subtitle_text: str | None, keywords: list[str] | None = None, audio_duration: float | None = None, scene_timings: list[dict] | None = None) -> str | None:
        """Burn subtitles into video using ASS format (inspired by CapCut Mate).

        Supports: text color, border/outline, alignment, alpha,
        keyword highlighting, fade in/out animations, and position control.

        Args:
            video_path: Path to the video file.
            subtitle_text: Full subtitle text.
            keywords: Optional keywords to highlight.
            audio_duration: Total audio duration for fallback timing.
            scene_timings: Optional per-scene timing for precise sync.
                          Each dict: {text, start, end} in seconds.
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
            ass_content = self._build_ass(subtitle_text, duration, keywords, scene_timings)

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
                    _find_ffmpeg(),
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

    def _build_ass(self, text: str, duration: float, keywords: list[str] | None = None, scene_timings: list[dict] | None = None) -> str:
        """Build ASS subtitle content with CapCut Mate-inspired styling.

        Generates a complete .ass file including:
        - [Script Info] with resolution from self.size
        - [V4+ Styles] with text color, border, alignment, alpha, outline, shadow
        - [Events] with keyword highlighting and fade in/out animations

        Args:
            text: Full subtitle text.
            duration: Total duration in seconds.
            keywords: Optional keywords to highlight.
            scene_timings: Optional per-scene timing for precise sync.
        """
        lines = self._split_subtitle_lines(text)
        if not lines:
            return ""

        # Build subtitle groups and timing
        if scene_timings:
            # Scene-aware timing: map subtitle lines to scene time windows
            groups, group_durations = self._build_scene_subtitle_groups(lines, scene_timings, duration)
        else:
            # Fallback: proportional timing based on character count
            groups = [lines[i:i + self.subtitle_max_lines]
                      for i in range(0, len(lines), self.subtitle_max_lines)]
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

    def _build_scene_subtitle_groups(self, lines: list[str], scene_timings: list[dict], total_duration: float) -> tuple[list[list[str]], list[float]]:
        """Map subtitle lines to scene time windows for precise sync.

        Distributes subtitle lines across scenes proportionally by scene duration,
        ensuring each group's timing matches the actual speech window.

        Args:
            lines: Split subtitle lines.
            scene_timings: Per-scene timing [{text, start, end}, ...].
            total_duration: Total audio/video duration.

        Returns:
            (groups, durations) - same format as the fallback path.
        """
        # Build groups (same as fallback)
        groups = [lines[i:i + self.subtitle_max_lines]
                  for i in range(0, len(lines), self.subtitle_max_lines)]
        n_groups = len(groups)

        if not scene_timings or n_groups == 0:
            group_chars = [sum(len(line) for line in group) for group in groups]
            total_chars = sum(group_chars) or 1
            return groups, [max(1.5, total_duration * chars / total_chars) for chars in group_chars]

        # Map each subtitle group to a scene time window
        # Distribute groups across scenes by scene duration weight
        scene_durations = [max(0.1, s["end"] - s["start"]) for s in scene_timings]
        total_scene_dur = sum(scene_durations) or 1.0

        # Calculate how many groups each scene should get (proportional to duration)
        group_durations = []
        scene_idx = 0
        scene_remaining = scene_durations[0] if scene_durations else total_duration
        scene_start = scene_timings[0]["start"] if scene_timings else 0
        group_idx_in_scene = 0
        groups_in_scene = max(1, round(n_groups * scene_durations[0] / total_scene_dur)) if scene_durations else n_groups

        for g in range(n_groups):
            # Duration for this group within its scene
            if groups_in_scene > 0:
                group_dur = scene_remaining / groups_in_scene
            else:
                group_dur = total_duration / n_groups
            group_durations.append(max(1.0, round(group_dur, 2)))

            groups_in_scene -= 1
            scene_remaining -= group_dur

            # Move to next scene if this scene's groups are exhausted
            if groups_in_scene <= 0 and scene_idx < len(scene_durations) - 1:
                scene_idx += 1
                scene_remaining = scene_durations[scene_idx]
                groups_in_scene = max(1, round(n_groups * scene_durations[scene_idx] / total_scene_dur))
                group_idx_in_scene = 0

        return groups, group_durations

    def _split_subtitle_lines(self, text: str) -> list[str]:
        """Split subtitle text into balanced lines for ASS display.

        Rules:
        1. Split at natural punctuation boundaries (，。！？、；：)
        2. Never put punctuation at the start of a line
        3. Never leave a single orphan character on its own line
        4. Balance line lengths within each group (subtitle_max_lines)
        """
        cleaned = re.sub(r"\s+", " ", text.replace("\n", " ")).strip()
        if not cleaned:
            return []

        # Step 1: Split into segments at natural punctuation boundaries.
        # Keep punctuation attached to the preceding segment.
        # Split points: ，。！？、；：, and Chinese equivalents
        segments = []
        buf = ""
        for ch in cleaned:
            buf += ch
            if ch in "，。！？、；：,;!?":
                segments.append(buf)
                buf = ""
        if buf:
            segments.append(buf)

        # Step 2: Split oversized segments that exceed the line limit.
        split_segments = []
        for seg in segments:
            if len(seg) <= self.subtitle_line_chars:
                split_segments.append(seg)
            else:
                # Split long segment, preferring natural break points
                remaining = seg
                while len(remaining) > self.subtitle_line_chars:
                    cut = self.subtitle_line_chars
                    best_cut = None
                    # Priority 1: punctuation within limit
                    for j in range(min(cut, len(remaining)), 0, -1):
                        if remaining[j - 1] in "，。！？、；：,;!?":
                            best_cut = j
                            break
                    # Priority 2: space (word boundary for English)
                    if best_cut is None:
                        for j in range(min(cut, len(remaining)), 0, -1):
                            if remaining[j - 1] == " ":
                                best_cut = j
                                break
                    # Priority 3: hyphen/dot/paren (word boundary for mixed text)
                    if best_cut is None:
                        for j in range(min(cut, len(remaining)), 0, -1):
                            if remaining[j - 1] in "-—.（(）)":
                                best_cut = j
                                break
                    # Priority 4: boundary between Chinese and non-Chinese
                    if best_cut is None:
                        for j in range(min(cut, len(remaining)), 1, -1):
                            prev_cn = '一' <= remaining[j-1] <= '鿿'
                            curr_cn = '一' <= remaining[j] <= '鿿' if j < len(remaining) else False
                            if prev_cn != curr_cn:
                                best_cut = j
                                break
                    # Priority 5: split at limit (Chinese text is fine at any position)
                    if best_cut is None:
                        best_cut = cut
                    split_segments.append(remaining[:best_cut])
                    remaining = remaining[best_cut:]
                if remaining:
                    split_segments.append(remaining)
        segments = split_segments

        # Step 3: Merge orphan segments forward.
        # A segment with only 1 non-punctuation char is an orphan.
        # Pure punctuation segments are also orphans.
        # But don't merge if it would exceed the line limit.
        merged = []
        for seg in segments:
            stripped = seg.rstrip("，。！？、；：,;!?")
            is_orphan = len(stripped) <= 1
            if merged and is_orphan:
                # Only merge if the result won't exceed the limit
                if len(merged[-1]) + len(seg) <= self.subtitle_line_chars:
                    merged[-1] += seg
                else:
                    # Can't merge - keep as separate segment
                    merged.append(seg)
            else:
                merged.append(seg)
        segments = merged

        # Step 4: Build lines respecting subtitle_line_chars limit.
        # Try to pack segments into lines without exceeding the limit.
        # Ensure no line starts with punctuation.
        lines = []
        current_line = ""
        for seg in segments:
            if not current_line:
                current_line = seg
            elif len(current_line) + len(seg) <= self.subtitle_line_chars:
                current_line += seg
            else:
                # Current line is full, start a new one.
                # But if seg starts with punctuation, try to append it anyway
                # (punctuation should not start a line)
                seg_stripped = seg.lstrip()
                if seg_stripped and seg_stripped[0] in "，。！？、；：,;!?":
                    # Punctuation segment - force append to current line
                    # even if it slightly exceeds limit (better than punct at start)
                    current_line += seg
                else:
                    lines.append(current_line.rstrip())
                    current_line = seg
        if current_line:
            lines.append(current_line.rstrip())

        # Step 4: Balance adjacent line pairs for even display.
        # If two consecutive lines differ by more than 4 chars, try to rebalance.
        balanced = []
        i = 0
        while i < len(lines):
            if i + 1 < len(lines):
                a, b = lines[i], lines[i + 1]
                # Check if combining and re-splitting gives better balance
                combined = a + b
                if len(combined) <= self.subtitle_line_chars:
                    # Both fit on one line
                    balanced.append(combined)
                    i += 2
                    continue
                # Find the best split point (prefer punctuation boundaries)
                best_split = None
                best_diff = abs(len(a) - len(b))
                for j in range(1, len(combined)):
                    ch = combined[j - 1]
                    if ch in "，。！？、；：,;!?":
                        left = combined[:j]
                        right = combined[j:]
                        if right and len(left) <= self.subtitle_line_chars and len(right) <= self.subtitle_line_chars:
                            diff = abs(len(left) - len(right))
                            if diff < best_diff:
                                best_diff = diff
                                best_split = (left, right)
                if best_split:
                    balanced.extend(best_split)
                else:
                    balanced.append(a)
                    balanced.append(b)
                i += 2
            else:
                balanced.append(lines[i])
                i += 1

        return [re.sub(r"[，。！？、；：,;!?]", "", line).strip() for line in balanced]

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
        ffmpeg = _find_ffmpeg()
        return shutil.which(ffmpeg) is not None or os.path.isfile(ffmpeg)

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

    def _resolve_scene_images(self, plan: dict, filename: str) -> None:
        """Search and download images for any scene with an 'image_query' field.

        The LLM can assign image_query to ANY scene type (hook, highlight,
        data_card, ending, etc.) — not just image_text. Each scene with
        an image_query gets a background image downloaded and set as imagePath.
        """
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

        # Start an HTTP server to serve downloaded images to Remotion's Chromium.
        # This avoids Remotion's staticFile() which has intermittent 404 issues
        # with the public/ directory in render mode.
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
                # Start HTTP server on first successful image download
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

                # Use HTTP URL instead of file:// or staticFile()
                http_url = f"http://127.0.0.1:{http_port}/{path.name}"
                scene["imagePath"] = http_url
                logger.info(f"Image resolved for scene {i}: {http_url}")
            else:
                logger.warning(f"Failed to find image for scene {i} query '{query}'")
                # scene will use its normal background (no imagePath)

    def _generate_remotion(
        self,
        script: str,
        filename: str,
        audio_path: str | None = None,
        keywords: list[str] | None = None,
        audio_duration: float | None = None,
        plan: dict | None = None,
        scene_timings: list[dict] | None = None,
    ) -> str | None:
        """Generate video using Remotion (programmatic text-based video).

        If a pre-made plan is provided, uses it directly.
        Otherwise, the LLM generates a composition plan from the script.
        After rendering, audio is merged via ffmpeg.

        Args:
            script: The douyin oral script text.
            filename: Output filename.
            audio_path: Optional local path to TTS audio file to embed.
            keywords: Optional tags/keywords for content context.
            audio_duration: Target audio duration (used if plan not provided).
            plan: Optional pre-generated video composition plan.
            scene_timings: Unused for Remotion (kept for interface consistency).
        """

        # Step 1: Get or generate composition plan
        if plan:
            logger.info(f"Using pre-generated video plan: {len(plan.get('scenes', []))} scenes")
        else:
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

        # Calculate actual video duration from plan scenes
        plan_duration = sum(s.get("duration", 3) for s in plan.get("scenes", []))

        # Step 1.5: Resolve images for image_text scenes (skip if disabled)
        gen_config = self.config.get("generation", {})
        if gen_config.get("auto_image", False):
            self._resolve_scene_images(plan, filename)

        # Ensure video duration matches audio exactly.
        # With per-scene TTS, audio includes inter-scene gaps (~0.15s each)
        # that aren't part of any scene's duration. Extend last scene to cover.
        if audio_duration and plan_duration < audio_duration:
            gap = round(audio_duration - plan_duration, 2)
            if plan.get("scenes"):
                plan["scenes"][-1]["duration"] = round(plan["scenes"][-1]["duration"] + gap, 2)
                plan_duration = audio_duration
                logger.info(f"Extended last scene by {gap:.1f}s to match audio ({audio_duration:.1f}s)")

        # Step 2: Delegate rendering to RemotionClient
        return self.remotion_client.render(
            plan=plan,
            filename=filename,
            audio_path=audio_path,
            plan_duration=plan_duration,
        )
