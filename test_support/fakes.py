"""In-memory fake provider implementations for unit testing.

Each fake implements the corresponding provider ABC with deterministic,
configurable behavior — no network access, no API keys, no filesystem I/O.

Usage:
    from test_support.fakes import FakeImageProvider, FakeVideoProvider, FakeSpeechProvider

    generator = ContentGenerator(
        db=db,
        config={},
        image_provider=FakeImageProvider(),
        video_provider=FakeVideoProvider(),
        speech_provider=FakeSpeechProvider(),
        store=FakeContentStore(),
    )
"""

import logging
import wave
import struct
import io
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class FakeImageProvider:
    """In-memory image provider that writes a minimal valid PNG to disk.

    Deterministic: returns a valid file path for any prompt.
    Configure latency with `simulated_delay` (seconds, default 0).
    """

    def __init__(self, simulated_delay: float = 0.0):
        self.simulated_delay = simulated_delay
        self.generated: list[tuple[str, str, str | None]] = []  # (prompt, filename, size)

    def generate(self, prompt: str, filename: str, size: Optional[str] = None) -> Optional[str]:
        import time
        time.sleep(self.simulated_delay)
        self.generated.append((prompt, filename, size))

        output_path = Path("output") / "test" / "media" / filename
        output_path.parent.mkdir(parents=True, exist_ok=True)
        # Write a minimal valid 1x1 PNG
        # PNG header + IHDR + IDAT (single pixel) + IEND ≈ 67 bytes
        _write_minimal_png(output_path)
        logger.debug(f"FakeImageProvider: wrote {output_path} ({prompt[:40]})")
        return str(output_path)


class FakeVideoProvider:
    """In-memory video provider that writes a minimal valid MP4 to disk.

    Deterministic: returns a valid file path for any prompt.
    Configure latency with `simulated_delay` (seconds, default 0).
    """

    def __init__(self, simulated_delay: float = 0.0):
        self.simulated_delay = simulated_delay
        self.generated: list[dict] = []

    def generate(
        self,
        prompt: str,
        filename: str,
        audio_url: Optional[str] = None,
        subtitles: Optional[str] = None,
        keywords: Optional[list[str]] = None,
        audio_duration: Optional[float] = None,
        scene_timings: Optional[list[dict]] = None,
    ) -> Optional[str]:
        import time
        time.sleep(self.simulated_delay)
        call = {
            "prompt": prompt,
            "filename": filename,
            "audio_url": audio_url,
            "subtitles": subtitles,
            "keywords": keywords,
            "audio_duration": audio_duration,
            "scene_timings": scene_timings,
        }
        self.generated.append(call)

        output_path = Path("output") / "test" / "media" / filename
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(b"\x00\x00\x00\x1cftypmp42")  # minimal mp4 stub
        logger.debug(f"FakeVideoProvider: wrote {output_path} ({prompt[:40]})")
        return str(output_path)


class FakeSpeechProvider:
    """In-memory speech provider that writes a minimal valid WAV to disk.

    Deterministic: returns a valid file path for any text.
    The generated WAV contains silence of duration proportional to text length
    (~0.05s per character), so get_audio_duration returns a meaningful value.
    Configure latency with `simulated_delay` (seconds, default 0).
    """

    def __init__(self, simulated_delay: float = 0.0):
        self.simulated_delay = simulated_delay
        self.generated: list[tuple[str, str, str | None, float, str]] = []

    def synthesize(
        self,
        text: str,
        filename: str,
        voice: Optional[str] = None,
        speed: float = 1.0,
        response_format: str = "wav",
    ) -> Optional[str]:
        import time
        time.sleep(self.simulated_delay)
        self.generated.append((text, filename, voice, speed, response_format))

        if not filename.endswith(".wav"):
            filename = filename.rsplit(".", 1)[0] + ".wav"

        output_path = Path("output") / "test" / "media" / filename
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Generate silence WAV: ~0.05s per char, at 16000 Hz, mono, 16-bit
        sample_rate = 16000
        duration = max(0.5, len(text) * 0.05)
        num_samples = int(sample_rate * duration)

        with wave.open(str(output_path), "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)  # 16-bit
            wf.setframerate(sample_rate)
            wf.writeframes(b"\x00\x00" * num_samples)

        logger.debug(f"FakeSpeechProvider: wrote {output_path} ({duration:.1f}s, {text[:40]})")
        return str(output_path)


class FakeContentStore:
    """In-memory content store — no filesystem writes.

    Mirrors the ContentStore API for use in unit tests.
    All data is kept in a list of dicts.
    """

    def __init__(self):
        self.contents: list[dict] = []
        self._seq = 0

    def save_content(
        self,
        platform: str,
        title: str,
        body: str,
        tags: Optional[list[str]] = None,
        media_urls: Optional[list[str]] = None,
        topic_id: Optional[int] = None,
        description: str = "",
    ) -> Path:
        self._seq += 1
        filepath = Path(f"test/{platform}/{self._seq:03d}_{title[:20]}.md")
        item = {
            "filepath": str(filepath),
            "filename": filepath.name,
            "platform": platform,
            "status": "approved",
            "title": title,
            "body": body,
            "description": description,
            "tags": tags or [],
            "media_urls": media_urls or [],
            "created_at": "2026-01-01T00:00:00",
            "topic_id": topic_id,
        }
        self.contents.append(item)
        return filepath

    def load_content(self, filepath: Path) -> Optional[dict]:
        for c in self.contents:
            if c["filepath"] == str(filepath):
                return dict(c)
        return None

    def load_contents(self, platform: Optional[str] = None, status: Optional[str] = None) -> list[dict]:
        results = []
        for c in self.contents:
            if platform and c["platform"] != platform:
                continue
            if status and c["status"] != status:
                continue
            results.append(dict(c))
        return results

    def update_status(self, filepath: str | Path, new_status: str):
        fp = str(filepath)
        for c in self.contents:
            if c["filepath"] == fp:
                c["status"] = new_status
                return

    def get_stats(self) -> dict:
        stats = {"total": len(self.contents), "approved": 0, "published": 0}
        for c in self.contents:
            s = c.get("status", "approved")
            stats[s] = stats.get(s, 0) + 1
        return stats


# ── Helpers ──

def _write_minimal_png(path: Path) -> None:
    """Write a minimal valid 1x1 RGB PNG to the given path."""
    import zlib

    # PNG signature
    signature = b"\x89PNG\r\n\x1a\n"

    # IHDR chunk: width=1, height=1, bit_depth=8, color_type=2 (RGB)
    ihdr_data = struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0)
    ihdr_crc = zlib.crc32(b"IHDR" + ihdr_data) & 0xFFFFFFFF
    ihdr = struct.pack(">I", 13) + b"IHDR" + ihdr_data + struct.pack(">I", ihdr_crc)

    # IDAT chunk: one row filter byte (0) + one RGB pixel (red)
    raw_data = b"\x00\xff\x00\x00"
    compressed = zlib.compress(raw_data)
    idat_crc = zlib.crc32(b"IDAT" + compressed) & 0xFFFFFFFF
    idat = struct.pack(">I", len(compressed)) + b"IDAT" + compressed + struct.pack(">I", idat_crc)

    # IEND chunk
    iend_crc = zlib.crc32(b"IEND") & 0xFFFFFFFF
    iend = struct.pack(">I", 0) + b"IEND" + struct.pack(">I", iend_crc)

    path.write_bytes(signature + ihdr + idat + iend)
