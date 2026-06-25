"""Audio utility functions: duration, trimming, concatenation, splitting.

Standalone module-level functions — no class wrapper, no provider dependency.
Originally extracted from the former TTSSynthesizer class (now fully deleted).
"""

import logging
import os
import re
import subprocess
from pathlib import Path

logger = logging.getLogger(__name__)

# Script markers to strip before TTS
SCRIPT_MARKER_RE = re.compile(r"【[^】]+】")
SEPARATOR_RE = re.compile(r"\n*---\n*")


def clean_script(script: str) -> str:
    """Strip script markers and separators, return plain spoken text."""
    text = SCRIPT_MARKER_RE.sub("", script)
    text = SEPARATOR_RE.sub("，", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def get_audio_duration(filepath: str) -> float:
    """Get duration of a WAV file in seconds."""
    import wave
    try:
        with wave.open(filepath, "rb") as wf:
            frames = wf.getnframes()
            rate = wf.getframerate()
            return frames / rate if rate > 0 else 0
    except Exception:
        return 0


def trim_audio(filepath: str, max_seconds: float) -> str:
    """Trim WAV file to max_seconds. Returns the same filepath."""
    import wave
    try:
        with wave.open(filepath, "rb") as wf:
            rate = wf.getframerate()
            channels = wf.getnchannels()
            sampwidth = wf.getsampwidth()
            max_frames = int(rate * max_seconds)
            frames = wf.readframes(min(wf.getnframes(), max_frames))

        with wave.open(filepath, "wb") as out:
            out.setnchannels(channels)
            out.setsampwidth(sampwidth)
            out.setframerate(rate)
            out.writeframes(frames)
        return filepath
    except Exception as e:
        logger.warning(f"Audio trim failed: {e}")
        return filepath


def concat_wav_files(wav_paths: list[str], output_path: str, gap_seconds: float = 0.15) -> str:
    """Concatenate multiple WAV files into one, with small gaps between segments."""
    import wave
    if not wav_paths:
        raise ValueError("No WAV files to concatenate")

    with wave.open(wav_paths[0], "rb") as first:
        params = first.getparams()
        all_frames = [first.readframes(first.getnframes())]

    silence_frames = b"\x00" * int(
        params.framerate * params.nchannels * params.sampwidth * gap_seconds
    )

    for path in wav_paths[1:]:
        with wave.open(path, "rb") as wf:
            if (
                wf.getnchannels() != params.nchannels
                or wf.getsampwidth() != params.sampwidth
                or wf.getframerate() != params.framerate
            ):
                logger.warning(f"WAV format mismatch in {path}, skipping gap")
                all_frames.append(wf.readframes(wf.getnframes()))
            else:
                all_frames.append(silence_frames)
                all_frames.append(wf.readframes(wf.getnframes()))

    with wave.open(output_path, "wb") as out:
        out.setparams(params)
        for frames in all_frames:
            out.writeframes(frames)

    return output_path


def split_audio(
    audio_path: str,
    output_dir: str,
    max_segment_duration: float,
    filename_prefix: str = "seg",
) -> list[dict]:
    """Split audio into segments at silence boundaries."""
    import shutil as sh

    ffmpeg = sh.which("ffmpeg") or sh.which("ffmpeg.exe")
    if not ffmpeg:
        try:
            import imageio_ffmpeg

            exe = imageio_ffmpeg.get_ffmpeg_exe()
            if exe and os.path.isfile(exe):
                ffmpeg = exe
        except Exception:
            pass
    ffmpeg = ffmpeg or "ffmpeg"
    total_dur = get_audio_duration(audio_path)

    if total_dur <= max_segment_duration:
        return [
            {
                "path": audio_path,
                "start": 0.0,
                "end": total_dur,
                "duration": total_dur,
            }
        ]

    silence_points = []
    try:
        result = subprocess.run(
            [
                ffmpeg,
                "-i",
                audio_path,
                "-af",
                "silencedetect=noise=-30dB:d=0.3",
                "-f",
                "null",
                "-",
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )
        for match in re.finditer(r"silence_end: (\d+\.?\d*)", result.stderr):
            silence_points.append(float(match.group(1)))
    except Exception:
        pass

    segments = []
    current_start = 0.0
    while current_start < total_dur - 0.5:
        target_end = current_start + max_segment_duration
        if target_end >= total_dur - 0.5:
            segments.append((current_start, total_dur))
            break
        best_split = None
        for sp in silence_points:
            if current_start + 1.0 < sp < target_end + 0.5:
                best_split = sp
        if best_split and best_split > current_start + 1.0:
            segments.append((current_start, best_split))
            current_start = best_split
        else:
            segments.append((current_start, target_end))
            current_start = target_end

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    result_segments = []

    for i, (start, end) in enumerate(segments):
        seg_path = str(output_dir / f"{filename_prefix}_{i}.wav")
        seg_dur = end - start
        try:
            subprocess.run(
                [
                    ffmpeg,
                    "-y",
                    "-i",
                    audio_path,
                    "-ss",
                    f"{start:.2f}",
                    "-t",
                    f"{seg_dur:.2f}",
                    "-c",
                    "copy",
                    seg_path,
                ],
                check=True,
                capture_output=True,
                text=True,
                timeout=15,
            )
            result_segments.append(
                {
                    "path": seg_path,
                    "start": round(start, 2),
                    "end": round(end, 2),
                    "duration": round(seg_dur, 2),
                }
            )
        except Exception as e:
            logger.warning(f"Failed to cut segment {i}: {e}")

    logger.info(
        f"Audio split into {len(result_segments)} segments "
        f"(total {total_dur:.1f}s, max {max_segment_duration}s/seg)"
    )
    return result_segments
