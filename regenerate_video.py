"""Regenerate Remotion videos for specific content items.

Uses the new AudioPlanner → TTS → VideoPlanner pipeline:
  1. AudioPlanner generates narration + voice direction
  2. TTS synthesizes per-segment, yielding precise timestamps
  3. VideoPlanner generates visual composition around those timestamps
  4. Remotion renders the final video
"""
import re
import shutil
import sys
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

VIDEO_PLACEHOLDER_RE = re.compile(r'\[视频\]\(.*?\)|\[VIDEO:.*?\]', re.DOTALL)

from modules.config import load_config
from modules.video_planner import AudioPlanner, VideoPlanner
from modules.tts import TTSSynthesizer
from modules.vgen import VideoGenerator


def _generate_tts_from_audio_segments(
    segments: list[dict],
    content_id: str,
    output_media: Path,
    tts: TTSSynthesizer,
    voice_prompt: str,
) -> tuple[str | None, float | None, list[dict]]:
    """Generate per-segment TTS from AudioPlanner output. Returns (path, dur, timings)."""
    seg_audio_paths = []
    seg_durations = []
    seg_texts = []
    pauses = []

    for i, seg in enumerate(segments):
        seg_text = seg.get("text", "").strip()
        pause = seg.get("pause_after", 0.2)
        if not seg_text:
            seg_durations.append(0.0)
            seg_texts.append("")
            pauses.append(0.0)
            continue

        audio_filename = f"content_{content_id}_seg_{i}.wav"
        logger.info(f"  TTS seg {i}: {seg_text[:40]}...")
        result = tts.synthesize(seg_text, audio_filename, max_duration=30, voice_prompt=voice_prompt)
        if result:
            audio_path, duration, _ = result
            seg_audio_paths.append(audio_path)
            seg_durations.append(duration)
        else:
            seg_durations.append(0.0)
        seg_texts.append(seg_text)
        pauses.append(pause)

    if not seg_audio_paths:
        return None, None, []

    concat_filename = f"content_{content_id}_tts.wav"
    concat_path = str(output_media / concat_filename)
    TTSSynthesizer.concat_wav_files(seg_audio_paths, concat_path, gap_seconds=0.0)

    segment_timings = []
    current_time = 0.0
    for i, (dur, text) in enumerate(zip(seg_durations, seg_texts)):
        if dur > 0:
            start = current_time
            end = current_time + dur
            segment_timings.append({"text": text, "start": round(start, 2), "end": round(end, 2)})
            current_time = end + pauses[i]
        else:
            segment_timings.append({"text": text, "start": round(current_time, 2), "end": round(current_time, 2)})

    total_duration = TTSSynthesizer.get_audio_duration(concat_path)
    logger.info(f"  TTS done: {len(seg_audio_paths)} segments, {total_duration:.1f}s")
    return concat_path, total_duration, segment_timings


def regenerate_video(seq: str, config: dict) -> bool:
    """Regenerate Remotion video for content seq."""

    files = list(Path('output/douyin').glob(f'{seq}_*.md'))
    if not files:
        logger.error(f"Content {seq} not found")
        return False

    filepath = files[0]
    raw = filepath.read_text(encoding='utf-8')

    parts = raw.split('---', 2)
    body = parts[-1] if len(parts) > 2 else raw

    script = VIDEO_PLACEHOLDER_RE.sub('', body).strip()
    script = re.sub(r'【[^】]+】', '', script)
    script = re.sub(r'\n*---\n*', '，', script).strip()
    script = re.sub(r'[，。]{2,}', '，', script)

    lines = script.split('\n')
    title = lines[0].strip()[:50] if lines else 'AI资讯'

    logger.info(f"[{seq}] {title}")

    # ── Step 1: Audio plan ──
    audio_planner = AudioPlanner(config)
    audio_plan = audio_planner.plan(script=script, title=title)
    if not audio_plan:
        logger.error(f"[{seq}] Audio plan failed")
        return False

    narration = audio_plan.get("narration", "")
    voice_direction = audio_plan.get("voice_direction", "用沉稳有力的声音朗读")
    segments = audio_plan.get("segments", [])
    logger.info(f"[{seq}] Audio: {len(segments)} segments, voice='{voice_direction[:30]}'")

    # ── Step 2: TTS from audio segments ──
    output_media = Path('output/douyin/media')
    output_media.mkdir(parents=True, exist_ok=True)

    tts = TTSSynthesizer(config)
    audio_path, total_dur, scene_timings = _generate_tts_from_audio_segments(
        segments, seq, output_media, tts, voice_direction,
    )
    if not audio_path or not total_dur:
        logger.error(f"[{seq}] TTS failed")
        return False

    # Copy audio
    src_audio = Path(audio_path)
    dst_audio = output_media / f"content_{seq}_remotion_tts.wav"
    if dst_audio.exists():
        dst_audio.unlink()
    shutil.copy2(src_audio, dst_audio)

    # ── Step 3: Video plan with audio timings ──
    video_planner = VideoPlanner(config)
    plan = video_planner.plan(
        script=narration,
        title=title,
        tags=None,
        audio_timings=scene_timings,
    )
    if not plan:
        logger.error(f"[{seq}] Video plan failed")
        return False

    logger.info(f"[{seq}] Video: {len(plan['scenes'])} scenes, "
                f"theme={plan.get('theme', '?')}")
    for i, s in enumerate(plan['scenes']):
        logger.info(f"  {i}: type={s['type']} icon={s.get('icon','-')} "
                    f"dur={s.get('duration','?')}s anim={s.get('animation','?')}")

    # ── Step 4: Remotion render ──
    vgen = VideoGenerator(config)
    vgen.planner = video_planner
    vgen.tts = tts

    filename = f"content_{seq}_remotion"
    logger.info(f"[{seq}] Rendering Remotion video ({total_dur:.1f}s)...")

    video_path = vgen.generate(
        narration, filename,
        audio_url=str(dst_audio),
        subtitles=narration,
        keywords=None,
        audio_duration=total_dur,
        plan=plan,
        scene_timings=scene_timings,
    )

    if not video_path:
        logger.error(f"[{seq}] Video render failed")
        return False

    # Copy video
    src_video = Path(video_path)
    dst_video = output_media / f"content_{seq}_remotion.mp4"
    if dst_video.exists():
        dst_video.unlink()
    shutil.copy2(src_video, dst_video)
    logger.info(f"[{seq}] Video: {dst_video.name} ({dst_video.stat().st_size/1024/1024:.1f}MB)")

    # ── Step 5: Update content ──
    new_body = VIDEO_PLACEHOLDER_RE.sub('', body).strip()
    new_body += f"\n\n[视频](media/{dst_video.name})\n"
    new_content = f"---{parts[1]}---\n{new_body}" if len(parts) > 2 else new_body
    filepath.write_text(new_content, encoding='utf-8')

    logger.info(f"[{seq}] ✅ Done!")
    return True


if __name__ == '__main__':
    config = load_config()
    for seq in sys.argv[1:] if len(sys.argv) > 1 else ['035', '036']:
        try:
            ok = regenerate_video(seq, config)
        except Exception as e:
            logger.exception(f"[{seq}] Error: {e}")
            ok = False
        if not ok:
            logger.error(f"[{seq}] ❌ Failed")
