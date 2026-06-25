"""Remotion client for programmatic video rendering.

Renders videos using the Remotion framework (React-based).
Handles npx/ffmpeg discovery, rendering via CLI, and audio merging.

Internal implementation detail of RemotionVideoProvider — do not import
from outside modules/providers/remotion/.
"""

import json
import logging
import os
import shutil
import subprocess
from pathlib import Path

from ...config_model import AppConfig

logger = logging.getLogger(__name__)


class RemotionClient:
    """Client for rendering videos via Remotion CLI."""

    def __init__(self, config: AppConfig):
        self.project_dir = Path(config.remotion.project_dir)
        self.fps = config.remotion.fps
        self.browser_executable = config.remotion.browser_executable
        # Resolve relative paths to absolute (paths in config are relative to project root)
        if self.browser_executable and not os.path.isabs(self.browser_executable):
            self.browser_executable = os.path.abspath(self.browser_executable)
        self.chrome_flags = config.remotion.chrome_flags

        # Media output directory
        self.media_dir = Path(config.dashscope.media_dir)
        self.media_dir.mkdir(parents=True, exist_ok=True)

        # Locate external tools
        self._npx_path = self._find_npx()
        self._ffmpeg_path = self._find_ffmpeg()

    def _find_ffmpeg(self) -> str:
        """Locate the ffmpeg executable for audio merging."""
        found = shutil.which("ffmpeg")
        if found:
            return found
        found = shutil.which("ffmpeg.exe")
        if found:
            return found
        for path_dir in os.environ.get("PATH", "").split(os.pathsep):
            for name in ("ffmpeg.exe", "ffmpeg"):
                p = os.path.join(path_dir, name)
                if os.path.isfile(p):
                    return p
        candidates = [
            os.path.expanduser("~/bin/ffmpeg.exe"),
            os.path.expanduser("~/bin/ffmpeg"),
            r"C:\ffmpeg\bin\ffmpeg.exe",
            r"C:\Program Files\ffmpeg\bin\ffmpeg.exe",
            r"C:\tools\ffmpeg\bin\ffmpeg.exe",
        ]
        for p in candidates:
            if os.path.isfile(p):
                return p
        # Fallback: use imageio_ffmpeg's bundled binary
        try:
            import imageio_ffmpeg
            ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
            if ffmpeg_exe and os.path.isfile(ffmpeg_exe):
                logger.info(f"Using bundled ffmpeg: {ffmpeg_exe}")
                return ffmpeg_exe
        except ImportError:
            pass
        logger.warning("ffmpeg not found in PATH or common locations. "
                       "Install ffmpeg from https://ffmpeg.org/download.html")
        return "ffmpeg"

    def _find_npx(self) -> str:
        """Locate the npx executable for running Remotion CLI."""
        # First try shutil.which which checks PATH properly
        found = shutil.which("npx") or shutil.which("npx.cmd")
        if found:
            logger.debug(f"Found npx via shutil.which: {found}")
            return found

        candidates = [
            r"C:\Program Files\nodejs\npx.cmd",
            r"C:\Program Files (x86)\nodejs\npx.cmd",
            os.path.expanduser(r"~\AppData\Roaming\npm\npx.cmd"),
            os.path.expanduser(r"~\AppData\Local\npm\npx.cmd"),
            r"D:\nvm4w\nodejs\npx.cmd",
            os.path.expanduser(r"~\AppData\Local\nvm\npx.cmd"),
        ]
        for candidate in candidates:
            if os.path.isfile(candidate):
                logger.debug(f"Found npx at: {candidate}")
                return candidate
            try:
                result = subprocess.run([candidate, "--version"], capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    logger.debug(f"Found npx: {candidate}")
                    return candidate
            except (FileNotFoundError, subprocess.TimeoutExpired):
                continue

        # Last resort: search PATH directories manually
        for path_dir in os.environ.get("PATH", "").split(os.pathsep):
            for name in ("npx.cmd", "npx"):
                p = os.path.join(path_dir, name)
                if os.path.isfile(p):
                    logger.debug(f"Found npx in PATH: {p}")
                    return p

        logger.warning("npx not found. Install Node.js from https://nodejs.org")
        return "npx"

    def render(
        self,
        plan: dict,
        filename: str,
        audio_path: str | None = None,
        plan_duration: float | None = None,
    ) -> str | None:
        """Render a video from a composition plan using Remotion CLI.

        Args:
            plan: Composition plan dict with title, theme, scenes.
            filename: Output filename (e.g. "content_1_1.mp4").
            audio_path: Optional local path to TTS audio file to embed.
            plan_duration: Total plan duration in seconds (used for audio trimming).

        Returns:
            Local file path of rendered video, or None on failure.
        """
        if not self.project_dir.exists():
            logger.error(f"Remotion project directory not found: {self.project_dir}")
            return None

        # Write plan to input.json for Remotion
        # Calculate total duration from scenes for the composition
        scenes = plan.get("scenes", [])
        total_plan_duration = sum(s.get("duration", 3) for s in scenes)
        # Use plan_duration if provided (includes audio extension), otherwise use plan total
        effective_duration = plan_duration if plan_duration else total_plan_duration
        # Add 1s buffer for transitions
        total_frames = max(90, round((effective_duration + 1) * self.fps))

        input_json_path = self.project_dir / "input.json"
        try:
            input_data = {
                "plan": plan,
                "durationInFrames": total_frames,
            }
            input_json_path.write_text(
                json.dumps(input_data, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            logger.info(f"Composition plan written to {input_json_path} ({total_frames} frames, {effective_duration:.1f}s)")
        except Exception as e:
            logger.error(f"Failed to write input.json: {e}")
            return None

        # Build output path
        output_path = self.media_dir.resolve() / filename
        output_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            logger.info("Rendering video with Remotion...")

            # Generate a temporary Root.tsx with the correct duration
            root_tsx_path = self.project_dir / "src" / "Root.tsx"
            root_tsx_backup = self.project_dir / "src" / "Root.tsx.bak"
            custom_root = False

            if root_tsx_path.exists() and total_frames > 90:
                # Write a custom Root.tsx with the exact frame count
                root_tsx_backup.write_text(
                    root_tsx_path.read_text(encoding="utf-8"),
                    encoding="utf-8",
                )
                custom_root_content = f'''import React from "react";
import {{ Composition, registerRoot }} from "remotion";
import VideoComposition from "./VideoComposition";

const defaultPlan: Record<string, unknown> = {{}} as Record<string, unknown>;

const RemotionRoot: React.FC = () => {{
  return (
    <>
      <Composition
        id="CAPVideo"
        component={{VideoComposition}}
        durationInFrames={{{total_frames}}}
        fps={{{self.fps}}}
        width={{1080}}
        height={{1920}}
        defaultProps={{defaultPlan}}
      />
    </>
  );
}};

registerRoot(RemotionRoot);
'''
                root_tsx_path.write_text(custom_root_content, encoding="utf-8")
                custom_root = True
                logger.info(f"Custom Root.tsx: {total_frames} frames ({effective_duration:.1f}s)")

            cmd = [
                self._npx_path,
                "remotion",
                "render",
                "src/Root.tsx",
                "CAPVideo",
                str(output_path),
                "--props=./input.json",
                "--overwrite",
                "--codec", "h264",
                "--crf", "18",
                "--pixel-format", "yuv420p",
            ]

            if self.browser_executable:
                cmd.extend(["--browser-executable", self.browser_executable])

            if self.chrome_flags:
                cmd.extend(["--chrome-flags", self.chrome_flags])

            result = subprocess.run(
                cmd,
                cwd=str(self.project_dir),
                capture_output=True,
                encoding="utf-8",
                errors="replace",
                timeout=300,
            )

            # Restore original Root.tsx
            if custom_root and root_tsx_backup.exists():
                root_tsx_path.write_text(
                    root_tsx_backup.read_text(encoding="utf-8"),
                    encoding="utf-8",
                )
                root_tsx_backup.unlink(missing_ok=True)

            if result.returncode != 0:
                logger.error(f"Remotion render failed:\n{result.stderr}")
                return None

            # Remotion CLI auto-adds .mp4 when no extension is specified
            output_with_ext = output_path.with_suffix(".mp4")
            if output_with_ext.exists():
                logger.info(f"Video rendered: {output_with_ext}")
                return self._merge_audio(output_with_ext, audio_path, plan_duration)

            # Try alternative output path in remotion project directory
            alt_path = (self.project_dir.resolve() / "out" / filename).with_suffix(".mp4")
            if alt_path.exists():
                logger.info(f"Video rendered (alt path): {alt_path}")
                shutil.copy2(str(alt_path), str(output_with_ext))
                return self._merge_audio(output_with_ext, audio_path, plan_duration)

            logger.error("Remotion render completed but output not found")
            return None

        except subprocess.TimeoutExpired:
            logger.error("Remotion render timed out (5 min)")
            return None
        except FileNotFoundError:
            logger.error(
                "npx/remotion not found. Ensure Node.js is installed "
                "and 'npm install' has been run in the remotion/ directory."
            )
            return None
        except Exception as e:
            logger.error(f"Remotion render failed: {e}")
            return None
        finally:
            # Always restore original Root.tsx if we modified it
            if custom_root and root_tsx_backup.exists():
                try:
                    root_tsx_path.write_text(
                        root_tsx_backup.read_text(encoding="utf-8"),
                        encoding="utf-8",
                    )
                    root_tsx_backup.unlink(missing_ok=True)
                except Exception:
                    pass

    def _merge_audio(
        self,
        video_path: str | Path,
        audio_path: str | None,
        trim_duration: float | None = None,
    ) -> str | None:
        """Merge audio into a video file using ffmpeg.

        If no audio path is provided, returns the video path unchanged.
        The original video file is replaced by the audio-merged version.

        Args:
            video_path: Path to the rendered video file.
            audio_path: Optional local path to audio file to embed.
            trim_duration: If set, trim video to this exact duration (seconds)
                           before merging audio, to remove excess frames from
                           Remotion's fixed-duration composition.
        """
        if not audio_path or not Path(audio_path).exists():
            logger.info(f"No audio to merge: path={audio_path}, "
                        f"exists={Path(audio_path).exists() if audio_path else 'N/A'}")
            return str(video_path)

        if not shutil.which(self._ffmpeg_path) and not os.path.isfile(self._ffmpeg_path):
            logger.warning(f"ffmpeg not found at '{self._ffmpeg_path}', skipping audio merge")
            return str(video_path)

        video_path = Path(video_path)
        temp_output = video_path.with_name(f"{video_path.stem}_with_audio.mp4")

        try:
            # Step 1: Trim video to exact duration if needed
            working_video = video_path
            if trim_duration and trim_duration > 0:
                trimmed = video_path.with_name(f"{video_path.stem}_trimmed.mp4")
                subprocess.run(
                    [self._ffmpeg_path, "-y",
                     "-i", str(video_path),
                     "-t", f"{trim_duration:.2f}",
                     "-c", "copy",
                     str(trimmed)],
                    check=True, capture_output=True, text=True, timeout=30,
                )
                working_video = trimmed

            # Probe audio duration
            audio_dur = 0
            try:
                probe = subprocess.run(
                    [self._ffmpeg_path, "-i", str(audio_path), "-f", "null", "-"],
                    capture_output=True, text=True, timeout=10
                )
                for line in probe.stderr.split('\n'):
                    if 'Duration' in line:
                        parts = line.strip().split(',')[0].split('Duration:')[1].strip()
                        h, m, s = parts.split(':')
                        audio_dur = int(h) * 3600 + int(m) * 60 + float(s)
            except Exception:
                pass

            cmd = [
                self._ffmpeg_path,
                "-y",
                "-i", str(working_video),
                "-i", str(audio_path),
                "-c:v", "copy",
                "-c:a", "aac",
                "-b:a", "192k",
                "-map", "0:v:0",
                "-map", "1:a:0",
            ]

            # If audio is shorter than video, pad with silence so audio isn't cut
            if audio_dur > 0:
                video_dur = 0
                try:
                    probe_v = subprocess.run(
                        [self._ffmpeg_path, "-i", str(working_video), "-f", "null", "-"],
                        capture_output=True, text=True, timeout=10
                    )
                    for line in probe_v.stderr.split('\n'):
                        if 'Duration' in line:
                            parts = line.strip().split(',')[0].split('Duration:')[1].strip()
                            h, m, s = parts.split(':')
                            video_dur = int(h) * 3600 + int(m) * 60 + float(s)
                except Exception:
                    pass

                if video_dur > audio_dur + 0.5:
                    pad_dur = video_dur - audio_dur
                    cmd.extend(["-af", f"apad=pad_dur={pad_dur:.1f}"])
                else:
                    cmd.append("-shortest")
            else:
                cmd.append("-shortest")

            cmd.append(str(temp_output))

            subprocess.run(
                cmd,
                check=True,
                capture_output=True,
                text=True,
                timeout=60,
            )
            temp_output.replace(video_path)
            # Clean up trimmed temp file
            if working_video != video_path:
                working_video.unlink(missing_ok=True)
            logger.info(f"Audio merged: {video_path}")
            return str(video_path)
        except subprocess.TimeoutExpired:
            logger.warning("Audio merge timed out, returning video without audio")
            return str(video_path)
        except FileNotFoundError as e:
            logger.warning(f"Audio merge: file not found ({e}). "
                           f"ffmpeg={self._ffmpeg_path}, "
                           f"video={working_video}, audio={audio_path}")
            return str(video_path)
        except Exception as e:
            logger.warning(f"Audio merge failed: {e}, returning video without audio")
            return str(video_path)

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
                [self._ffmpeg_path, "-y",
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
