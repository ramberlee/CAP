"""FFmpeg utility functions for video processing.

Provides ffmpeg discovery, video/audio probing, concatenation, and merging.
Extracted from the former _subtitle_utils.py for focused, independent reuse.
"""

import logging
import os
import shutil
import subprocess
from pathlib import Path

import requests

logger = logging.getLogger(__name__)


# ─── FFmpeg Discovery ───────────────────────────────────────────────

def find_ffmpeg() -> str:
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


def ffmpeg_available() -> bool:
    ffmpeg = find_ffmpeg()
    return shutil.which(ffmpeg) is not None or os.path.isfile(ffmpeg)


def probe_video_duration(video_path: str) -> float | None:
    """Probe video file duration using ffprobe."""
    ffprobe = shutil.which("ffprobe")
    if ffprobe is None:
        return None
    try:
        result = subprocess.run(
            [ffprobe, "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", str(video_path)],
            capture_output=True, text=True, check=True,
        )
        return float(result.stdout.strip())
    except Exception:
        return None


# ─── Download Helpers ───────────────────────────────────────────────

def download_video(video_url: str, filename: str, media_dir: Path,
                   max_retries: int = 3) -> str | None:
    """Download video from URL and save locally. Returns local path.

    Retries on connection errors / incomplete reads up to `max_retries` times.
    """
    import time
    for attempt in range(1, max_retries + 1):
        try:
            resp = requests.get(video_url, timeout=120, stream=True)
            resp.raise_for_status()

            if not filename.endswith(".mp4"):
                filename = filename.rsplit(".", 1)[0] + ".mp4"

            filepath = media_dir / filename
            total = 0
            with open(filepath, "wb") as f:
                for chunk in resp.iter_content(chunk_size=65536):
                    f.write(chunk)
                    total += len(chunk)

            logger.info(f"Video saved: {filepath} ({total} bytes)")
            return str(filepath)
        except Exception as e:
            logger.warning(f"Video download failed (attempt {attempt}/{max_retries}): {e}")
            if attempt < max_retries:
                wait = 2 ** attempt
                logger.info(f"Retrying in {wait}s...")
                time.sleep(wait)
            else:
                logger.error(f"Video download failed after {max_retries} attempts: {e}")
                return None


# ─── Video Concatenation ────────────────────────────────────────────

def concat_videos(video_paths: list[str], output_path: str, ffmpeg_path: str | None = None) -> str | None:
    """Concatenate multiple video files into one using ffmpeg concat demuxer."""
    ffmpeg = ffmpeg_path or find_ffmpeg()
    if not video_paths:
        return None
    if len(video_paths) == 1:
        shutil.copy2(video_paths[0], output_path)
        return output_path

    list_path = Path(output_path).with_suffix(".txt")
    with open(list_path, "w", encoding="utf-8") as f:
        for p in video_paths:
            safe_path = str(Path(p).resolve()).replace("\\", "/").replace("'", "'\\''")
            f.write(f"file '{safe_path}'\n")

    try:
        subprocess.run(
            [ffmpeg, "-y", "-f", "concat", "-safe", "0",
             "-i", str(list_path), "-c", "copy", str(output_path)],
            check=True, capture_output=True, text=True, timeout=120,
        )
        list_path.unlink(missing_ok=True)
        logger.info(f"Videos concatenated: {len(video_paths)} segments → {output_path}")
        return output_path
    except Exception as e:
        logger.error(f"Video concatenation failed: {e}")
        list_path.unlink(missing_ok=True)
        return None


# ─── Audio Merging ──────────────────────────────────────────────────

def merge_audio(video_path: str, audio_path: str | None, trim_duration: float | None = None,
                ffmpeg_path: str | None = None) -> str:
    """Merge audio into a video file using ffmpeg. Returns video path."""
    ffmpeg = ffmpeg_path or find_ffmpeg()
    if not audio_path or not Path(audio_path).exists():
        return video_path

    video_p = Path(video_path)
    temp_output = video_p.with_name(f"{video_p.stem}_with_audio.mp4")

    try:
        working_video = video_p
        if trim_duration and trim_duration > 0:
            trimmed = video_p.with_name(f"{video_p.stem}_trimmed.mp4")
            subprocess.run(
                [ffmpeg, "-y", "-i", str(video_p), "-t", f"{trim_duration:.2f}", "-c", "copy", str(trimmed)],
                check=True, capture_output=True, text=True, timeout=30,
            )
            working_video = trimmed

        audio_dur = _probe_ffmpeg_duration(ffmpeg, audio_path)
        video_dur = _probe_ffmpeg_duration(ffmpeg, str(working_video)) if audio_dur else 0

        cmd = [
            ffmpeg, "-y",
            "-i", str(working_video), "-i", str(audio_path),
            "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
            "-map", "0:v:0", "-map", "1:a:0",
        ]

        if audio_dur > 0 and video_dur > audio_dur + 0.5:
            cmd.extend(["-af", f"apad=pad_dur={video_dur - audio_dur:.1f}"])
        else:
            cmd.append("-shortest")

        cmd.append(str(temp_output))
        subprocess.run(cmd, check=True, capture_output=True, text=True, timeout=60)
        temp_output.replace(video_p)
        if working_video != video_p:
            working_video.unlink(missing_ok=True)
        logger.info(f"Audio merged: {video_p}")
        return str(video_p)
    except Exception as e:
        logger.warning(f"Audio merge failed: {e}")
        return video_path


def _probe_ffmpeg_duration(ffmpeg: str, path: str) -> float:
    """Probe media duration via ffmpeg stderr parsing."""
    try:
        probe = subprocess.run(
            [ffmpeg, "-i", str(path), "-f", "null", "-"],
            capture_output=True, text=True, timeout=10,
        )
        for line in probe.stderr.split('\n'):
            if 'Duration' in line:
                parts = line.strip().split(',')[0].split('Duration:')[1].strip()
                h, m, s = parts.split(':')
                return int(h) * 3600 + int(m) * 60 + float(s)
    except Exception:
        pass
    return 0
