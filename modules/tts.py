"""TTS (Text-to-Speech) module using MiMo TTS API (chat completions compatible).

MiMo TTS uses the /v1/chat/completions endpoint with a special message format:
- user: voice/tone description (generated dynamically by LLM)
- assistant: the text to speak
- audio parameter specifies format and voice
- Response contains base64-encoded audio in message.audio.data
"""

import base64
import io
import logging
import os
import re
import struct
import wave
from pathlib import Path
from openai import OpenAI

logger = logging.getLogger(__name__)

# Script markers to strip before TTS
SCRIPT_MARKER_RE = re.compile(r"【[^】]+】")
SEPARATOR_RE = re.compile(r"\n*---\n*")


class TTSSynthesizer:
    def __init__(self, config: dict):
        gen_config = config.get("generation", {})
        self.text_provider = gen_config.get("text_provider", "mimo")
        ds_config = config.get("dashscope", {})
        self.media_dir = Path(ds_config.get("media_dir", "media"))
        self.media_dir.mkdir(parents=True, exist_ok=True)

        if self.text_provider == "ark":
            ark_config = config.get("ark", {})
            from modules.ark_client import ArkClient
            self.ark_client = ArkClient(config)
            self.model = ark_config.get("tts_model") or self.ark_client.tts_model
            self.voice = ark_config.get("tts_voice", "zh_female_shuangkuaisisi_moon_bigtts")
            self.client = None  # Ark uses ArkClient for TTS, not OpenAI client
        else:
            mimo_config = config.get("mimo", {})
            api_key = mimo_config.get("api_key", "")
            base_url = mimo_config.get("tts_base_url", mimo_config.get("base_url", "https://api.xiaomimimo.com/v1"))
            self.model = mimo_config.get("tts_model", "mimo-v2.5-tts")
            self.voice = mimo_config.get("tts_voice", "Chloe")
            self.client = OpenAI(api_key=api_key, base_url=base_url) if api_key else None

    def _clean_script(self, script: str) -> str:
        """Strip script markers and separators, return plain spoken text."""
        text = SCRIPT_MARKER_RE.sub("", script)
        text = SEPARATOR_RE.sub("，", text)
        text = re.sub(r"\s+", " ", text).strip()
        return text

    @staticmethod
    def get_audio_duration(filepath: str) -> float:
        """Get duration of a WAV file in seconds."""
        try:
            with wave.open(filepath, "rb") as wf:
                frames = wf.getnframes()
                rate = wf.getframerate()
                return frames / rate if rate > 0 else 0
        except Exception:
            return 0

    @staticmethod
    def trim_audio(filepath: str, max_seconds: float) -> str:
        """Trim WAV file to max_seconds. Returns the same filepath."""
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

    @staticmethod
    def concat_wav_files(wav_paths: list[str], output_path: str, gap_seconds: float = 0.15) -> str:
        """Concatenate multiple WAV files into one, with small gaps between segments.

        Args:
            wav_paths: List of WAV file paths to concatenate in order.
            output_path: Output WAV file path.
            gap_seconds: Silence gap between segments (default 0.15s for natural pauses).

        Returns:
            Output file path.
        """
        if not wav_paths:
            raise ValueError("No WAV files to concatenate")

        # Read first file to get format
        with wave.open(wav_paths[0], "rb") as first:
            params = first.getparams()
            all_frames = [first.readframes(first.getnframes())]

        # Silence gap
        silence_frames = b"\x00" * int(params.framerate * params.nchannels * params.sampwidth * gap_seconds)

        # Read remaining files
        for path in wav_paths[1:]:
            with wave.open(path, "rb") as wf:
                if wf.getnchannels() != params.nchannels or wf.getsampwidth() != params.sampwidth or wf.getframerate() != params.framerate:
                    logger.warning(f"WAV format mismatch in {path}, skipping gap")
                    all_frames.append(wf.readframes(wf.getnframes()))
                else:
                    all_frames.append(silence_frames)
                    all_frames.append(wf.readframes(wf.getnframes()))

        # Write concatenated output
        with wave.open(output_path, "wb") as out:
            out.setparams(params)
            for frames in all_frames:
                out.writeframes(frames)

        return output_path

    @staticmethod
    def split_audio(audio_path: str, output_dir: str, max_segment_duration: float, filename_prefix: str = "seg") -> list[dict]:
        """Split audio into segments at silence boundaries.

        Each segment is ≤ max_segment_duration. Uses ffmpeg silencedetect
        to find natural pause points for clean splits.

        Args:
            audio_path: Path to the WAV file to split.
            output_dir: Directory for segment files.
            max_segment_duration: Maximum duration per segment in seconds.
            filename_prefix: Prefix for segment filenames.

        Returns:
            List of dicts: [{path, start, end, duration}, ...]
        """
        import subprocess
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
        total_dur = TTSSynthesizer.get_audio_duration(audio_path)

        if total_dur <= max_segment_duration:
            return [{
                "path": audio_path,
                "start": 0.0,
                "end": total_dur,
                "duration": total_dur,
            }]

        # Find silence points for clean split locations
        silence_points = []
        try:
            result = subprocess.run(
                [ffmpeg, "-i", audio_path, "-af",
                 f"silencedetect=noise=-30dB:d=0.3",
                 "-f", "null", "-"],
                capture_output=True, text=True, timeout=30,
            )
            import re
            for match in re.finditer(r"silence_end: (\d+\.?\d*)", result.stderr):
                silence_points.append(float(match.group(1)))
        except Exception:
            pass

        # Build segment boundaries
        segments = []
        current_start = 0.0

        while current_start < total_dur - 0.5:
            target_end = current_start + max_segment_duration

            if target_end >= total_dur - 0.5:
                # Last segment
                segments.append((current_start, total_dur))
                break

            # Find nearest silence point before target_end
            best_split = None
            for sp in silence_points:
                if current_start + 1.0 < sp < target_end + 0.5:
                    best_split = sp

            if best_split and best_split > current_start + 1.0:
                segments.append((current_start, best_split))
                current_start = best_split
            else:
                # No silence point found, hard split
                segments.append((current_start, target_end))
                current_start = target_end

        # Cut segments with ffmpeg
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        result_segments = []

        for i, (start, end) in enumerate(segments):
            seg_path = str(output_dir / f"{filename_prefix}_{i}.wav")
            seg_dur = end - start
            try:
                subprocess.run(
                    [ffmpeg, "-y",
                     "-i", audio_path,
                     "-ss", f"{start:.2f}",
                     "-t", f"{seg_dur:.2f}",
                     "-c", "copy",
                     seg_path],
                    check=True, capture_output=True, text=True, timeout=15,
                )
                result_segments.append({
                    "path": seg_path,
                    "start": round(start, 2),
                    "end": round(end, 2),
                    "duration": round(seg_dur, 2),
                })
            except Exception as e:
                logger.warning(f"Failed to cut segment {i}: {e}")

        logger.info(f"Audio split into {len(result_segments)} segments "
                    f"(total {total_dur:.1f}s, max {max_segment_duration}s/seg)")
        return result_segments

    def synthesize(self, script: str, filename: str, max_duration: float | None = 28, voice_prompt: str | None = None) -> tuple[str, float, float] | None:
        """Generate audio from script text. Returns (file_path, duration_seconds, original_duration) or None.

        Args:
            script: The oral script text (may contain markers like 【钩子】).
            filename: Output filename (e.g. "content_100_1.wav").
            max_duration: Maximum audio duration in seconds. None = no limit.
            voice_prompt: Tone/style instruction for TTS (generated by LLM).
                         If None, uses a minimal default.
        """
        text = self._clean_script(script)
        if not text:
            logger.warning("Empty script after cleaning, skipping TTS")
            return None

        if self.text_provider == "ark":
            return self._synthesize_ark(text, filename, max_duration)

        # ── MiMo TTS (chat completions with audio param) ──
        if not self.client or not self.client.api_key:
            logger.warning("MiMo API key not configured, skipping TTS")
            return None

        # Ensure .wav extension (MiMo TTS returns wav by default)
        if not filename.endswith(".wav"):
            filename = filename.rsplit(".", 1)[0] + ".wav"

        filepath = self.media_dir / filename

        # Use provided voice_prompt or minimal default
        effective_prompt = voice_prompt or "用自然、有感染力的中文语调朗读。"

        try:
            logger.info(f"Generating TTS with {self.model}: {text[:60]}...")
            logger.debug(f"Voice prompt: {effective_prompt}")

            completion = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": effective_prompt,
                    },
                    {
                        "role": "assistant",
                        "content": text,
                    },
                ],
                audio={
                    "format": "wav",
                    "voice": self.voice,
                },
            )

            message = completion.choices[0].message
            if not hasattr(message, "audio") or message.audio is None:
                logger.error("No audio data in TTS response")
                return None

            audio_bytes = base64.b64decode(message.audio.data)
            filepath.write_bytes(audio_bytes)

            # Check and trim audio duration if max_duration is set
            duration = self.get_audio_duration(str(filepath))
            original_duration = duration
            if max_duration and duration > max_duration:
                logger.info(f"TTS audio {duration:.1f}s exceeds {max_duration}s limit, trimming...")
                self.trim_audio(str(filepath), max_duration)
                duration = self.get_audio_duration(str(filepath))

            logger.info(f"TTS saved: {filepath} ({len(audio_bytes)} bytes, {duration:.1f}s)")
            return str(filepath), duration, original_duration

        except Exception as e:
            logger.warning(f"TTS generation failed (video will have no voice): {e}")
            return None

    def _synthesize_ark(self, text: str, filename: str, max_duration: float | None = None) -> tuple[str, float, float] | None:
        """Generate audio using Volcano Ark TTS (HTTP chunked, not OpenAI-compatible).

        Uses the openspeech HTTP endpoint: POST with chunked JSON + base64 audio.
        """
        if not self.ark_client or not self.ark_client.api_key:
            logger.warning("Ark API key not configured, skipping TTS")
            return None

        # Ark returns binary audio; use wav format for compatibility with existing pipeline
        ar_filename = filename
        if not ar_filename.endswith(".wav"):
            ar_filename = ar_filename.rsplit(".", 1)[0] + ".wav"

        try:
            logger.info(f"Generating TTS via Ark ({self.model}): {text[:60]}...")
            audio_path = self.ark_client.synthesize_speech(
                text=text,
                filename=ar_filename,
                voice=self.voice,
                response_format="wav",
            )

            if not audio_path:
                logger.error("Ark TTS generation failed")
                return None

            # Check and trim audio duration if max_duration is set
            duration = self.get_audio_duration(audio_path)
            original_duration = duration
            if max_duration and duration > max_duration:
                logger.info(f"Ark TTS audio {duration:.1f}s exceeds {max_duration}s limit, trimming...")
                self.trim_audio(audio_path, max_duration)
                duration = self.get_audio_duration(audio_path)

            logger.info(f"Ark TTS saved: {audio_path} ({duration:.1f}s)")
            return audio_path, duration, original_duration

        except Exception as e:
            logger.warning(f"Ark TTS generation failed: {e}")
            return None
