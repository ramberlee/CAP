"""Tests for fake provider implementations."""

import sys
sys.path.insert(0, ".")

import json
import tempfile
from pathlib import Path

import pytest

from test_support.fakes import (
    FakeImageProvider,
    FakeVideoProvider,
    FakeSpeechProvider,
    FakeContentStore,
)


class TestFakeImageProvider:
    def test_generate_returns_path(self):
        provider = FakeImageProvider()
        result = provider.generate("a test image", "test.png")
        assert result is not None
        path = Path(result)
        assert path.exists()
        assert path.suffix == ".png"
        assert len(provider.generated) == 1
        assert provider.generated[0][0] == "a test image"

    def test_generate_tracks_calls(self):
        provider = FakeImageProvider()
        provider.generate("image 1", "a.png", size="1024x1024")
        provider.generate("image 2", "b.png")
        assert len(provider.generated) == 2
        assert provider.generated[0][2] == "1024x1024"


class TestFakeVideoProvider:
    def test_generate_returns_path(self):
        provider = FakeVideoProvider()
        result = provider.generate("a test video", "test.mp4")
        assert result is not None
        path = Path(result)
        assert path.exists()
        assert len(provider.generated) == 1

    def test_generate_with_audio_params(self):
        provider = FakeVideoProvider()
        result = provider.generate(
            "video with audio",
            "audio_vid.mp4",
            audio_url="/path/to/audio.wav",
            subtitles="Hello world",
            keywords=["AI", "tech"],
            audio_duration=30.0,
            scene_timings=[{"text": "hello", "start": 0, "end": 2}],
        )
        assert result is not None
        call = provider.generated[0]
        assert call["audio_url"] == "/path/to/audio.wav"
        assert call["subtitles"] == "Hello world"
        assert call["keywords"] == ["AI", "tech"]
        assert call["audio_duration"] == 30.0
        assert len(call["scene_timings"]) == 1


class TestFakeSpeechProvider:
    def test_synthesize_returns_wav(self):
        provider = FakeSpeechProvider()
        result = provider.synthesize("Hello world", "test.wav")
        assert result is not None
        path = Path(result)
        assert path.exists()
        assert path.suffix == ".wav"
        assert len(provider.generated) == 1

    def test_synthesize_adds_wav_extension(self):
        provider = FakeSpeechProvider()
        result = provider.synthesize("Hello", "test")
        assert result is not None
        assert result.endswith(".wav")

    def test_duration_proportional_to_text_length(self):
        import wave
        provider = FakeSpeechProvider()
        long_text = "Hello world " * 100
        result = provider.synthesize(long_text, "long.wav")
        with wave.open(result, "rb") as wf:
            frames = wf.getnframes()
            rate = wf.getframerate()
            duration = frames / rate
        # Should be at least ~0.5s for 1100 chars * 0.05s
        assert duration >= 0.5


class TestFakeContentStore:
    def test_save_and_load_content(self):
        store = FakeContentStore()
        path = store.save_content(
            platform="wechat",
            title="Test Article",
            body="This is a test body.",
            tags=["AI", "test"],
            topic_id=42,
        )
        assert path.name.endswith(".md")

        loaded = store.load_content(path)
        assert loaded is not None
        assert loaded["title"] == "Test Article"
        assert loaded["platform"] == "wechat"
        assert loaded["tags"] == ["AI", "test"]
        assert loaded["topic_id"] == 42

    def test_load_contents_with_filters(self):
        store = FakeContentStore()
        store.save_content(platform="wechat", title="A", body="")
        store.save_content(platform="douyin", title="B", body="")

        all_items = store.load_contents()
        assert len(all_items) == 2

        wechat = store.load_contents(platform="wechat")
        assert len(wechat) == 1
        assert wechat[0]["platform"] == "wechat"

    def test_update_status(self):
        store = FakeContentStore()
        path = store.save_content(platform="wechat", title="Test", body="")
        store.update_status(str(path), "published")
        loaded = store.load_content(path)
        assert loaded["status"] == "published"

    def test_get_stats(self):
        store = FakeContentStore()
        store.save_content(platform="wechat", title="A", body="")
        store.save_content(platform="douyin", title="B", body="")
        stats = store.get_stats()
        assert stats["total"] == 2
        assert stats["approved"] == 2
