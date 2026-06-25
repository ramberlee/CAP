"""ASS subtitle building and burning for video processing.

Provides SubtitleConfig dataclass, ASS subtitle generation, and subtitle
burn-in via ffmpeg. Extracted from the former _subtitle_utils.py for
focused reuse — all ffmpeg utility functions live in _ffmpeg_utils.
"""

import logging
import re
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

from ._ffmpeg_utils import find_ffmpeg, ffmpeg_available, probe_video_duration

logger = logging.getLogger(__name__)


# ─── Subtitle Configuration ─────────────────────────────────────────

@dataclass
class SubtitleConfig:
    """CapCut Mate-inspired subtitle styling options."""
    enabled: bool = True
    font: str = "Microsoft YaHei"
    fontsize: int = 48
    line_chars: int = 16
    max_lines: int = 1
    text_color: str = "#FFFFFF"
    border_color: str = "#000000"
    alignment: int = 1       # 0-5, 1=bottom-center
    alpha: float = 1.0       # 0.0-1.0
    keyword_color: str = "#FFD700"
    keyword_fontsize: int | None = None
    fade_in: float = 0.15    # seconds
    fade_out: float = 0.15   # seconds
    margin_v: int = 50       # vertical margin (pixels)
    outline: int = 2
    shadow: int = 1

    @classmethod
    def from_config(cls, config: "GenerationConfig | dict") -> "SubtitleConfig":
        if hasattr(config, "video_subtitles"):
            # Typed GenerationConfig
            return cls(
                enabled=config.video_subtitles,
                font=config.video_subtitle_font,
                fontsize=config.video_subtitle_size,
                line_chars=config.video_subtitle_line_chars,
                max_lines=config.video_subtitle_max_lines,
                text_color=config.video_subtitle_text_color,
                border_color=config.video_subtitle_border_color,
                alignment=config.video_subtitle_alignment,
                alpha=config.video_subtitle_alpha,
                keyword_color=config.video_subtitle_keyword_color,
                keyword_fontsize=config.video_subtitle_keyword_size,
                fade_in=config.video_subtitle_fade_in,
                fade_out=config.video_subtitle_fade_out,
                margin_v=config.video_subtitle_margin_v,
                outline=config.video_subtitle_outline,
                shadow=config.video_subtitle_shadow,
            )
        gen = config.get("generation", {})
        return cls(
            enabled=gen.get("video_subtitles", True),
            font=gen.get("video_subtitle_font", "Microsoft YaHei"),
            fontsize=gen.get("video_subtitle_size", 48),
            line_chars=gen.get("video_subtitle_line_chars", 16),
            max_lines=gen.get("video_subtitle_max_lines", 1),
            text_color=gen.get("video_subtitle_text_color", "#FFFFFF"),
            border_color=gen.get("video_subtitle_border_color", "#000000"),
            alignment=gen.get("video_subtitle_alignment", 1),
            alpha=gen.get("video_subtitle_alpha", 1.0),
            keyword_color=gen.get("video_subtitle_keyword_color", "#FFD700"),
            keyword_fontsize=gen.get("video_subtitle_keyword_size", None),
            fade_in=gen.get("video_subtitle_fade_in", 0.15),
            fade_out=gen.get("video_subtitle_fade_out", 0.15),
            margin_v=gen.get("video_subtitle_margin_v", 50),
            outline=gen.get("video_subtitle_outline", 2),
            shadow=gen.get("video_subtitle_shadow", 1),
        )


# ─── Subtitle Burning ───────────────────────────────────────────────

def finalize_video(video_path: str | None, subtitle_text: str | None,
                   video_size: str, sub_config: SubtitleConfig,
                   keywords: list[str] | None = None,
                   audio_duration: float | None = None,
                   scene_timings: list[dict] | None = None) -> str | None:
    """Download and burn subtitles into a generated video.

    Probes actual video duration for subtitle timing (more accurate than
    audio_duration, since the video model may produce a different length).
    """
    if not video_path:
        return None

    video_dur = probe_video_duration(video_path)
    subtitle_duration = video_dur or audio_duration

    if video_dur and audio_duration and abs(video_dur - audio_duration) > 1.0:
        logger.info(f"Video/Audio duration mismatch: video={video_dur:.1f}s, "
                    f"audio={audio_duration:.1f}s — using video duration for subtitles")

    return burn_subtitles(video_path, subtitle_text, video_size, sub_config,
                          keywords, subtitle_duration, scene_timings)


def burn_subtitles(video_path: str | None, subtitle_text: str | None,
                   video_size: str, sub_config: SubtitleConfig,
                   keywords: list[str] | None = None,
                   duration: float | None = None,
                   scene_timings: list[dict] | None = None) -> str | None:
    """Burn subtitles into video using ASS format (CapCut Mate-inspired).

    Args:
        video_path: Path to the video file.
        subtitle_text: Full subtitle text.
        video_size: Video resolution string (e.g. "1280*720").
        sub_config: Subtitle styling configuration.
        keywords: Optional keywords to highlight.
        duration: Total duration for subtitle timing (seconds).
        scene_timings: Optional per-scene timing for precise sync.

    Returns:
        Video path on success, original video_path on failure.
    """
    if not video_path or not subtitle_text or not sub_config.enabled:
        return video_path

    if not ffmpeg_available():
        logger.warning("ffmpeg not found, skipping subtitle burn-in")
        return video_path

    effective_duration = duration or probe_video_duration(video_path) or 15.0

    try:
        ass_content = _build_ass(subtitle_text, effective_duration, video_size,
                                 sub_config, keywords, scene_timings)
        if not ass_content:
            return video_path

        output_path = Path(video_path).with_name(f"{Path(video_path).stem}.sub.mp4")
        ass_name = f"_tmp_{Path(video_path).stem}.ass"
        ass_path = Path(ass_name)
        ass_path.write_text(ass_content, encoding="utf-8")

        video_filter_path = str(video_path).replace("\\", "/")
        output_filter_path = str(output_path).replace("\\", "/")

        subprocess.run(
            [find_ffmpeg(), "-y", "-i", video_filter_path,
             "-vf", f"ass={ass_name}",
             "-c:v", "libx264", "-crf", "18", "-preset", "fast",
             "-c:a", "copy", output_filter_path],
            check=True, capture_output=True, text=True,
        )

        ass_path.unlink(missing_ok=True)
        output_path.replace(video_path)
        logger.info(f"Subtitles (ASS) burned in: {video_path}")
        return str(video_path)
    except Exception as e:
        logger.warning(f"Failed to burn subtitles into video: {e}")
        return video_path


# ─── ASS Building ───────────────────────────────────────────────────

def _build_ass(text: str, duration: float, video_size: str,
               sub_config: SubtitleConfig,
               keywords: list[str] | None = None,
               scene_timings: list[dict] | None = None) -> str:
    """Build ASS subtitle content with CapCut Mate-inspired styling."""
    lines = _split_subtitle_lines(text, sub_config.line_chars)
    if not lines:
        return ""

    if scene_timings:
        groups, group_durations = _build_scene_subtitle_groups(
            lines, scene_timings, duration, sub_config.max_lines)
    else:
        groups = [lines[i:i + sub_config.max_lines]
                  for i in range(0, len(lines), sub_config.max_lines)]
        group_chars = [sum(len(line) for line in g) for g in groups]
        total_chars = sum(group_chars) or 1
        group_durations = [max(1.5, duration * chars / total_chars) for chars in group_chars]

    width, height = video_size.split('*')
    kw_list = keywords or []
    kw_color_hex = sub_config.keyword_color
    kw_fs = sub_config.keyword_fontsize or sub_config.fontsize
    default_fs = sub_config.fontsize
    fade_in_cs = int(sub_config.fade_in * 100)
    fade_out_cs = int(sub_config.fade_out * 100)
    align_ass = _capcut_align_to_ass(sub_config.alignment)

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

    primary_color = _ass_color_with_alpha(sub_config.text_color, sub_config.alpha)
    outline_color_ass = _ass_color_with_alpha(sub_config.border_color, 1.0)

    ass_parts.append(
        f"Style: Default,{sub_config.font},{sub_config.fontsize},"
        f"{primary_color},{primary_color},{outline_color_ass},&H80000000,"
        f"0,0,0,0,100,100,0,0,1,"
        f"{sub_config.outline},{sub_config.shadow},"
        f"{align_ass},10,10,{sub_config.margin_v},1"
    )
    ass_parts.append("")
    ass_parts.append("[Events]")
    ass_parts.append(
        "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"
    )

    elapsed = 0.0
    for index, group in enumerate(groups):
        start_ts = _format_ass_timestamp(elapsed)
        elapsed += group_durations[index]
        end_ts = _format_ass_timestamp(elapsed)

        highlighted_lines = []
        for line in group:
            hl_line = _highlight_keywords(line, kw_list, kw_color_hex, kw_fs, default_fs)
            highlighted_lines.append(hl_line)

        group_text = "\\N".join(highlighted_lines)
        if fade_in_cs > 0 or fade_out_cs > 0:
            group_text = f"{{\\fad({fade_in_cs},{fade_out_cs})}}{group_text}"

        ass_parts.append(f"Dialogue: 0,{start_ts},{end_ts},Default,,0,0,0,,{group_text}")

    return "\n".join(ass_parts) + "\n"


def _build_scene_subtitle_groups(lines: list[str], scene_timings: list[dict],
                                  total_duration: float, max_lines: int
                                  ) -> tuple[list[list[str]], list[float]]:
    """Map subtitle lines to scene time windows for precise sync."""
    groups = [lines[i:i + max_lines] for i in range(0, len(lines), max_lines)]
    n_groups = len(groups)

    if not scene_timings or n_groups == 0:
        group_chars = [sum(len(line) for line in g) for g in groups]
        total_chars = sum(group_chars) or 1
        return groups, [max(1.5, total_duration * chars / total_chars) for chars in group_chars]

    scene_durations = [max(0.1, s["end"] - s["start"]) for s in scene_timings]
    total_scene_dur = sum(scene_durations) or 1.0

    group_durations = []
    scene_idx = 0
    scene_remaining = scene_durations[0] if scene_durations else total_duration
    groups_in_scene = max(1, round(n_groups * scene_durations[0] / total_scene_dur)) if scene_durations else n_groups

    for g in range(n_groups):
        group_dur = scene_remaining / groups_in_scene if groups_in_scene > 0 else total_duration / n_groups
        group_durations.append(max(1.0, round(group_dur, 2)))
        groups_in_scene -= 1
        scene_remaining -= group_dur

        if groups_in_scene <= 0 and scene_idx < len(scene_durations) - 1:
            scene_idx += 1
            scene_remaining = scene_durations[scene_idx]
            groups_in_scene = max(1, round(n_groups * scene_durations[scene_idx] / total_scene_dur))

    return groups, group_durations


def _split_subtitle_lines(text: str, line_chars: int) -> list[str]:
    """Split subtitle text into balanced lines for ASS display."""
    cleaned = re.sub(r"\s+", " ", text.replace("\n", " ")).strip()
    if not cleaned:
        return []

    # Step 1: Split at natural punctuation boundaries
    segments = []
    buf = ""
    for ch in cleaned:
        buf += ch
        if ch in "，。！？、；：,;!?":
            segments.append(buf)
            buf = ""
    if buf:
        segments.append(buf)

    # Step 2: Split oversized segments
    split_segments = []
    for seg in segments:
        if len(seg) <= line_chars:
            split_segments.append(seg)
        else:
            remaining = seg
            while len(remaining) > line_chars:
                cut = _find_best_split(remaining, line_chars)
                split_segments.append(remaining[:cut])
                remaining = remaining[cut:]
            if remaining:
                split_segments.append(remaining)
    segments = split_segments

    # Step 3: Merge orphan segments forward
    merged = []
    for seg in segments:
        stripped = seg.rstrip("，。！？、；：,;!?")
        is_orphan = len(stripped) <= 1
        if merged and is_orphan:
            if len(merged[-1]) + len(seg) <= line_chars:
                merged[-1] += seg
            else:
                merged.append(seg)
        else:
            merged.append(seg)
    segments = merged

    # Step 4: Build lines respecting line_chars limit
    lines = []
    current_line = ""
    for seg in segments:
        if not current_line:
            current_line = seg
        elif len(current_line) + len(seg) <= line_chars:
            current_line += seg
        else:
            seg_stripped = seg.lstrip()
            if seg_stripped and seg_stripped[0] in "，。！？、；：,;!?":
                current_line += seg
            else:
                lines.append(current_line.rstrip())
                current_line = seg
    if current_line:
        lines.append(current_line.rstrip())

    # Step 5: Balance adjacent line pairs
    balanced = []
    i = 0
    while i < len(lines):
        if i + 1 < len(lines):
            a, b = lines[i], lines[i + 1]
            combined = a + b
            if len(combined) <= line_chars:
                balanced.append(combined)
                i += 2
                continue
            best_split = None
            best_diff = abs(len(a) - len(b))
            for j in range(1, len(combined)):
                if combined[j - 1] in "，。！？、；：,;!?":
                    left, right = combined[:j], combined[j:]
                    if right and len(left) <= line_chars and len(right) <= line_chars:
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


def _find_best_split(text: str, limit: int) -> int:
    """Find the best split position in text within the first `limit` chars."""
    cut = limit
    best_cut = None

    # Priority 1: punctuation
    for j in range(min(cut, len(text)), 0, -1):
        if text[j - 1] in "，。！？、；：,;!?":
            return j
    # Priority 2: space
    for j in range(min(cut, len(text)), 0, -1):
        if text[j - 1] == " ":
            best_cut = j
            break
    # Priority 3: CJK/non-CJK boundary
    if best_cut is None:
        for j in range(min(cut, len(text)), 1, -1):
            prev_cn = '一' <= text[j - 1] <= '鿿'
            curr_cn = '一' <= text[j] <= '鿿' if j < len(text) else False
            if prev_cn != curr_cn:
                return j
    # Priority 4: hyphen/paren
    if best_cut is None:
        for j in range(min(cut, len(text)), 0, -1):
            if text[j - 1] in "-—.（(）)":
                return j
    return best_cut or cut


def _format_ass_timestamp(seconds: float) -> str:
    """ASS timestamp format: H:MM:SS.cc (centiseconds)."""
    total_cs = int(seconds * 100)
    hours = total_cs // 360_000
    minutes = (total_cs // 6000) % 60
    secs = (total_cs // 100) % 60
    cs = total_cs % 100
    return f"{hours}:{minutes:02d}:{secs:02d}.{cs:02d}"


def _html_to_ass_color(html_color: str) -> tuple[str, str, str]:
    """Parse #RRGGBB into (rr, gg, bb) hex strings."""
    c = html_color.lstrip('#')
    if len(c) >= 6:
        return c[0:2], c[2:4], c[4:6]
    return "FF", "FF", "FF"


def _ass_color_with_alpha(html_color: str, alpha: float) -> str:
    """Build ASS color value &HAABBGGRR from HTML #RRGGBB and alpha (0.0-1.0)."""
    r, g, b = _html_to_ass_color(html_color)
    alpha_hex = f"{max(0, min(255, int((1.0 - alpha) * 255))):02X}"
    return f"&H{alpha_hex}{b}{g}{r}"


def _ass_inline_color(html_color: str) -> str:
    """Build ASS inline color tag value &HBBGGRR& from HTML #RRGGBB."""
    r, g, b = _html_to_ass_color(html_color)
    return f"&H{b}{g}{r}&"


def _capcut_align_to_ass(align: int) -> int:
    """Map CapCut Mate alignment (0-5) to ASS alignment (1-9 numpad style)."""
    mapping = {0: 1, 1: 2, 2: 3, 3: 4, 4: 5, 5: 6}
    return mapping.get(align, 2)


def _highlight_keywords(text: str, keywords: list[str], kw_color_hex: str,
                         kw_fs: int, default_fs: int) -> str:
    """Wrap keywords with ASS color/size override tags."""
    if not keywords:
        return text
    kw_color_ass = _ass_inline_color(kw_color_hex)
    result = text
    for kw in keywords:
        if kw and kw in result:
            result = result.replace(
                kw,
                f"{{\\c{kw_color_ass}\\fs{kw_fs}}}{kw}{{\\c\\fs{default_fs}}}"
            )
    return result
