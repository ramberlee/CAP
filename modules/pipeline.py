"""Topic-to-video pipeline: keyword → script → TTS → video plan → render.

Usage:
    from modules.pipeline import TopicToVideoPipeline
    pipeline = TopicToVideoPipeline.from_config(config)
    result = pipeline.run("Claude Code 使用技巧")
"""

import logging
import shutil
from pathlib import Path

from .config_model import AppConfig
from .video_planner import AudioPlanner, VideoPlanner
from .providers.remotion.video import RemotionVideoProvider

logger = logging.getLogger(__name__)


class TopicToVideoPipeline:
    """End-to-end pipeline: topic keyword → rendered video.

    Orchestrates: script generation → audio planning → TTS → video planning → render.
    """

    def __init__(
        self,
        config: AppConfig,
        *,
        llm_client=None,
        llm_model: str | None = None,
        speech_provider=None,
    ):
        self.config = config
        self.llm_client = llm_client
        self.llm_model = llm_model
        self.speech_provider = speech_provider

        # Planners
        self.audio_planner = AudioPlanner(config)
        self.video_planner = VideoPlanner(config)

        # Video provider
        self.video_provider = RemotionVideoProvider(config)

        # Output directory
        self.output_dir = Path(config.output_dir) / "douyin" / "media"
        self.output_dir.mkdir(parents=True, exist_ok=True)

    @classmethod
    def from_config(cls, config: AppConfig) -> "TopicToVideoPipeline":
        """Create pipeline from AppConfig, resolving providers automatically."""
        from .providers import ProviderFactory

        factory = ProviderFactory(config)
        llm_client, llm_model = factory.create_llm_client()
        speech_provider = factory.create_speech_provider() if config.generation.auto_video else None

        return cls(
            config,
            llm_client=llm_client,
            llm_model=llm_model,
            speech_provider=speech_provider,
        )

    def run(self, topic: str, content_id: int = 1) -> dict:
        """Run the full pipeline for a topic.

        Args:
            topic: Topic keyword or short description.
            content_id: Numeric ID for naming output files.

        Returns:
            dict with keys: video_path, audio_path, script, success, error.
        """
        result = {
            "video_path": None,
            "audio_path": None,
            "script": None,
            "success": False,
            "error": None,
        }

        try:
            # Step 1: Generate script from topic
            logger.info(f"[Pipeline] Step 1/4: Generating script for topic: {topic[:50]}")
            script_data = self._generate_script(topic)
            if not script_data:
                result["error"] = "Script generation failed"
                return result

            script_text = script_data.get("script", "")
            title = script_data.get("title", topic[:30])
            tags = script_data.get("tags", [])
            result["script"] = script_text
            logger.info(f"[Pipeline] Script generated: {title[:40]}... ({len(script_text)} chars)")

            # Step 2: Audio planning
            logger.info("[Pipeline] Step 2/4: Audio planning...")
            audio_plan = self.audio_planner.plan(
                script=script_text,
                title=title,
                tags=tags,
            )
            if audio_plan and audio_plan.get("narration"):
                script_text = audio_plan["narration"]
                result["script"] = script_text
                logger.info(f"[Pipeline] Audio plan: {len(audio_plan.get('segments', []))} segments")
            else:
                logger.warning("[Pipeline] Audio planner failed, using raw script")

            # Step 3: TTS
            logger.info("[Pipeline] Step 3/4: Generating TTS audio...")
            audio_result = self._generate_tts(
                script_text, audio_plan, content_id,
            )
            if not audio_result:
                result["error"] = "TTS generation failed"
                return result

            audio_path, audio_duration, scene_timings = audio_result
            result["audio_path"] = str(audio_path)
            logger.info(f"[Pipeline] TTS generated: {audio_duration:.1f}s")

            # Step 4: Video planning + render
            logger.info("[Pipeline] Step 4/4: Video planning + render...")
            video_plan = self.video_planner.plan(
                script=script_text,
                title=title,
                tags=tags,
                audio_timings=scene_timings,
            )
            if not video_plan:
                result["error"] = "Video planning failed"
                return result

            plan_dur = sum(s.get("duration", 0) for s in video_plan.get("scenes", []))
            logger.info(
                f"[Pipeline] Video plan: {len(video_plan.get('scenes', []))} scenes, "
                f"plan={plan_dur:.1f}s, audio={audio_duration:.1f}s"
            )

            filename = f"content_{content_id}_1.mp4"
            video_path = self.video_provider.generate(
                prompt=script_text,
                filename=filename,
                audio_path=str(audio_path),
                subtitles=script_text,
                keywords=tags,
                audio_duration=audio_duration,
                plan=video_plan,
                scene_timings=scene_timings if scene_timings else None,
            )

            if video_path:
                # Copy to output directory
                src = Path(video_path)
                dst = self.output_dir / src.name
                shutil.copy2(src, dst)
                result["video_path"] = str(dst)
                result["success"] = True
                logger.info(f"[Pipeline] Video rendered: {dst}")
            else:
                result["error"] = "Video rendering failed"

        except Exception as e:
            logger.error(f"[Pipeline] Pipeline failed: {e}", exc_info=True)
            result["error"] = str(e)

        return result

    def _generate_script(self, topic: str) -> dict | None:
        """Generate a douyin script from a topic keyword.

        Returns dict with keys: script, title, tags.
        """
        if not self.llm_client:
            logger.error("LLM client not available for script generation")
            return None

        system_prompt = (
            "你是一个短视频文案专家。根据给定话题，创作一段适合口播的抖音短视频文案。\n"
            "文案要求：\n"
            "1. 开头第一句要抓耳（黄金3秒）\n"
            "2. 中间部分有干货、有节奏感\n"
            "3. 结尾引导关注/评论\n"
            "4. 总字数 200-500 字\n"
            "5. 适合朗读，口语化\n\n"
            "输出纯 JSON：\n"
            '{"title": "15-20字标题", "script": "完整口播文案", "tags": ["#标签1", "#标签2", "#AI"]}'
        )

        try:
            response = self.llm_client.chat.completions.create(
                model=self.llm_model,
                max_tokens=2048,
                temperature=0.7,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"话题：{topic}"},
                ],
            )
            text = response.choices[0].message.content.strip()

            # Extract JSON
            json_start = text.find("{")
            json_end = text.rfind("}") + 1
            if json_start >= 0 and json_end > json_start:
                import json
                return json.loads(text[json_start:json_end])

            logger.warning(f"No JSON found in script generation response: {text[:200]}")
            return None
        except Exception as e:
            logger.error(f"Script generation failed: {e}")
            return None

    def _generate_tts(
        self,
        script_text: str,
        audio_plan: dict | None,
        content_id: int,
    ) -> tuple[Path, float, list[dict]] | None:
        """Generate TTS audio from script.

        Returns (audio_path, total_duration, scene_timings) or None.
        """
        if not self.speech_provider:
            logger.error("Speech provider not available for TTS")
            return None

        # Use audio plan segments if available
        if audio_plan and audio_plan.get("segments"):
            segments = audio_plan["segments"]
            voice_direction = audio_plan.get("voice_direction", "")

            audio_files = []
            scene_timings = []
            current_time = 0.0

            for i, seg in enumerate(segments):
                text = seg.get("text", "")
                pause_after = seg.get("pause_after", 0.2)
                if not text:
                    continue

                filename = f"content_{content_id}_seg{i}.wav"
                try:
                    result = self.speech_provider.synthesize(
                        text=text,
                        filename=filename,
                        voice=voice_direction if voice_direction else None,
                    )
                    if result:
                        audio_path = Path(result)
                        # Get audio duration
                        duration = self._get_audio_duration(audio_path)
                        if duration > 0:
                            scene_timings.append({
                                "text": text,
                                "start": current_time,
                                "end": current_time + duration,
                            })
                            current_time += duration + pause_after
                            audio_files.append(audio_path)
                except Exception as e:
                    logger.warning(f"TTS failed for segment {i}: {e}")
                    continue

            if not audio_files:
                return None

            # Concatenate audio files
            concat_path = self.output_dir / f"content_{content_id}_concat.wav"
            self._concat_audio(audio_files, concat_path)

            total_duration = current_time
            return concat_path, total_duration, scene_timings
        else:
            # Simple full-script TTS
            filename = f"content_{content_id}_tts.wav"
            try:
                result = self.speech_provider.synthesize(
                    text=script_text,
                    filename=filename,
                )
                if result:
                    audio_path = Path(result)
                    duration = self._get_audio_duration(audio_path)
                    return audio_path, duration, []
            except Exception as e:
                logger.error(f"TTS failed: {e}")

        return None

    def _get_audio_duration(self, path: Path) -> float:
        """Get audio file duration in seconds using ffprobe."""
        import subprocess
        try:
            result = subprocess.run(
                ["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
                 "-of", "csv=p=0", str(path)],
                capture_output=True, text=True, timeout=10,
            )
            return float(result.stdout.strip())
        except Exception:
            return 0.0

    def _concat_audio(self, files: list[Path], output: Path) -> None:
        """Concatenate audio files using ffmpeg."""
        import subprocess
        if not files:
            return

        # Create concat list file
        list_file = output.parent / ".concat_list.txt"
        with open(list_file, "w") as f:
            for p in files:
                f.write(f"file '{p.resolve()}'\n")

        try:
            result = subprocess.run(
                ["ffmpeg", "-y", "-f", "concat", "-safe", "0",
                 "-i", str(list_file), "-c", "copy", str(output)],
                capture_output=True, timeout=60,
            )
            if result.returncode != 0:
                logger.error(f"ffmpeg concat failed: {result.stderr.decode()[:200]}")
        except FileNotFoundError:
            logger.error("ffmpeg not found — cannot concatenate audio")
        finally:
            if list_file.exists():
                list_file.unlink()
