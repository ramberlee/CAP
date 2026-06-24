"""ASR (Automatic Speech Recognition) module using Volcano Ark WebSocket API.

Provides speech-to-text transcription via Volcano Ark's streaming ASR service.
Supports two modes:
  - Single-stream (nostream): sends all audio, returns high-accuracy result after completion
  - Dual-stream (async): real-time recognition, returns results while audio is being sent

Protocol: Custom binary WebSocket protocol with gzip-compressed JSON payloads.
Audio requirements: 16kHz, 16bit, mono WAV (ffmpeg auto-converts other formats).

Usage:
    from modules.asr import ASRTranscriber

    asr = ASRTranscriber(config)
    text = asr.transcribe("audio.wav")            # -> "识别出的文本"
    utterances = asr.transcribe_with_timestamps("audio.wav")  # -> [{text, start, end, confidence}, ...]
"""

import asyncio
import gzip
import json
import logging
import os
import shutil
import struct
import subprocess
import uuid
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

DEFAULT_SAMPLE_RATE = 16000

# ═══════════════════════════════════════════════════════════════════
# Binary Protocol Constants
# ═══════════════════════════════════════════════════════════════════


class _ProtocolVersion:
    V1 = 0b0001


class _MessageType:
    CLIENT_FULL_REQUEST = 0b0001
    CLIENT_AUDIO_ONLY_REQUEST = 0b0010
    SERVER_FULL_RESPONSE = 0b1001
    SERVER_ERROR_RESPONSE = 0b1111


class _MessageTypeSpecificFlags:
    NO_SEQUENCE = 0b0000
    POS_SEQUENCE = 0b0001
    NEG_SEQUENCE = 0b0010
    NEG_WITH_SEQUENCE = 0b0011


class _SerializationType:
    NO_SERIALIZATION = 0b0000
    JSON = 0b0001


class _CompressionType:
    GZIP = 0b0001


# ═══════════════════════════════════════════════════════════════════
# Binary Header Builder
# ═══════════════════════════════════════════════════════════════════


class _AsrRequestHeader:
    """Builds the 4-byte binary header for ASR WebSocket requests.

    Byte layout:
        [0] = (protocol_version << 4) | header_size
        [1] = (message_type << 4) | message_type_specific_flags
        [2] = (serialization_type << 4) | compression_type
        [3] = reserved
    """

    def __init__(self):
        self.message_type = _MessageType.CLIENT_FULL_REQUEST
        self.message_type_specific_flags = _MessageTypeSpecificFlags.POS_SEQUENCE
        self.serialization_type = _SerializationType.JSON
        self.compression_type = _CompressionType.GZIP
        self.reserved_data = bytes([0x00])

    def with_message_type(self, message_type: int) -> "_AsrRequestHeader":
        self.message_type = message_type
        return self

    def with_message_type_specific_flags(self, flags: int) -> "_AsrRequestHeader":
        self.message_type_specific_flags = flags
        return self

    def with_serialization_type(self, serialization_type: int) -> "_AsrRequestHeader":
        self.serialization_type = serialization_type
        return self

    def with_compression_type(self, compression_type: int) -> "_AsrRequestHeader":
        self.compression_type = compression_type
        return self

    def with_reserved_data(self, reserved_data: bytes) -> "_AsrRequestHeader":
        self.reserved_data = reserved_data
        return self

    def to_bytes(self) -> bytes:
        header = bytearray()
        header.append((_ProtocolVersion.V1 << 4) | 1)  # header_size = 1 (4 bytes)
        header.append((self.message_type << 4) | self.message_type_specific_flags)
        header.append((self.serialization_type << 4) | self.compression_type)
        header.extend(self.reserved_data)
        return bytes(header)

    @staticmethod
    def default_header() -> "_AsrRequestHeader":
        return _AsrRequestHeader()


# ═══════════════════════════════════════════════════════════════════
# Response Data Class
# ═══════════════════════════════════════════════════════════════════


class _AsrResponse:
    """Parsed ASR WebSocket response."""

    def __init__(self):
        self.code = 0
        self.event = 0
        self.is_last_package = False
        self.payload_sequence = 0
        self.payload_size = 0
        self.payload_msg: Optional[dict] = None

    def to_dict(self) -> dict:
        return {
            "code": self.code,
            "event": self.event,
            "is_last_package": self.is_last_package,
            "payload_sequence": self.payload_sequence,
            "payload_size": self.payload_size,
            "payload_msg": self.payload_msg,
        }


# ═══════════════════════════════════════════════════════════════════
# Response Parser
# ═══════════════════════════════════════════════════════════════════


class _ResponseParser:
    """Parses binary WebSocket frames into _AsrResponse objects."""

    @staticmethod
    def parse_response(msg: bytes) -> _AsrResponse:
        response = _AsrResponse()

        header_size = msg[0] & 0x0F
        message_type = msg[1] >> 4
        message_type_specific_flags = msg[1] & 0x0F
        serialization_method = msg[2] >> 4
        message_compression = msg[2] & 0x0F

        payload = msg[header_size * 4 :]

        # Parse message_type_specific_flags
        if message_type_specific_flags & 0x01:
            if len(payload) >= 4:
                response.payload_sequence = struct.unpack(">i", payload[:4])[0]
                payload = payload[4:]
        if message_type_specific_flags & 0x02:
            response.is_last_package = True
        if message_type_specific_flags & 0x04:
            if len(payload) >= 4:
                response.event = struct.unpack(">i", payload[:4])[0]
                payload = payload[4:]

        # Parse message_type
        if message_type == _MessageType.SERVER_FULL_RESPONSE:
            if len(payload) >= 4:
                response.payload_size = struct.unpack(">I", payload[:4])[0]
                payload = payload[4:]
        elif message_type == _MessageType.SERVER_ERROR_RESPONSE:
            if len(payload) >= 8:
                response.code = struct.unpack(">i", payload[:4])[0]
                response.payload_size = struct.unpack(">I", payload[4:8])[0]
                payload = payload[8:]

        if not payload:
            return response

        # Decompress
        if message_compression == _CompressionType.GZIP:
            try:
                payload = gzip.decompress(payload)
            except Exception as e:
                logger.error(f"Failed to decompress ASR response payload: {e}")
                return response

        # Parse payload
        try:
            if serialization_method == _SerializationType.JSON:
                response.payload_msg = json.loads(payload.decode("utf-8"))
        except Exception as e:
            logger.error(f"Failed to parse ASR response payload: {e}")

        return response


# ═══════════════════════════════════════════════════════════════════
# Request Builder
# ═══════════════════════════════════════════════════════════════════


class _RequestBuilder:
    """Builds binary WebSocket request frames for ASR."""

    @staticmethod
    def new_auth_headers(api_key: str, resource_id: str) -> dict:
        """Build authentication headers for WebSocket connection."""
        reqid = str(uuid.uuid4())
        return {
            "X-Api-Key": api_key,
            "X-Api-Resource-Id": resource_id,
            "X-Api-Request-Id": reqid,
            "X-Api-Connect-Id": reqid,
            "X-Api-Sequence": "-1",
        }

    @staticmethod
    def new_full_client_request(
        seq: int,
        enable_nonstream: bool = True,
    ) -> bytes:
        """Build the initial CLIENT_FULL_REQUEST binary frame with audio config.

        Args:
            seq: Sequence number (usually 1).
            enable_nonstream: True for single-stream (high accuracy) mode,
                              False for dual-stream (real-time) mode.
        """
        header = _AsrRequestHeader.default_header().with_message_type_specific_flags(
            _MessageTypeSpecificFlags.POS_SEQUENCE
        )

        payload = {
            "user": {"uid": "demo_uid"},
            "audio": {
                "format": "wav",
                "codec": "raw",
                "rate": 16000,
                "bits": 16,
                "channel": 1,
            },
            "request": {
                "model_name": "bigmodel",
                "enable_itn": True,
                "enable_punc": True,
                "enable_ddc": True,
                "show_utterances": True,
                "enable_nonstream": enable_nonstream,
            },
        }

        payload_bytes = json.dumps(payload).encode("utf-8")
        compressed_payload = gzip.compress(payload_bytes)
        payload_size = len(compressed_payload)

        request = bytearray()
        request.extend(header.to_bytes())
        request.extend(struct.pack(">i", seq))
        request.extend(struct.pack(">I", payload_size))
        request.extend(compressed_payload)

        return bytes(request)

    @staticmethod
    def new_audio_only_request(
        seq: int, segment: bytes, is_last: bool = False
    ) -> bytes:
        """Build a CLIENT_AUDIO_ONLY_REQUEST binary frame.

        Args:
            seq: Sequence number.
            segment: Raw PCM audio bytes for this segment.
            is_last: True if this is the final audio segment.
                     Negates the sequence number to signal end-of-stream.
        """
        header = _AsrRequestHeader.default_header()
        if is_last:
            header.with_message_type_specific_flags(
                _MessageTypeSpecificFlags.NEG_WITH_SEQUENCE
            )
            seq = -seq
        else:
            header.with_message_type_specific_flags(
                _MessageTypeSpecificFlags.POS_SEQUENCE
            )
        header.with_message_type(_MessageType.CLIENT_AUDIO_ONLY_REQUEST)

        compressed_segment = gzip.compress(segment)

        request = bytearray()
        request.extend(header.to_bytes())
        request.extend(struct.pack(">i", seq))
        request.extend(struct.pack(">I", len(compressed_segment)))
        request.extend(compressed_segment)

        return bytes(request)


# ═══════════════════════════════════════════════════════════════════
# Audio Utilities
# ═══════════════════════════════════════════════════════════════════


class _CommonUtils:
    """Audio and compression utilities for ASR pipeline."""

    @staticmethod
    def gzip_compress(data: bytes) -> bytes:
        return gzip.compress(data)

    @staticmethod
    def gzip_decompress(data: bytes) -> bytes:
        return gzip.decompress(data)

    @staticmethod
    def judge_wav(data: bytes) -> bool:
        """Check if raw bytes represent a valid WAV file."""
        if len(data) < 44:
            return False
        return data[:4] == b"RIFF" and data[8:12] == b"WAVE"

    @staticmethod
    def _find_ffmpeg() -> str:
        """Locate ffmpeg executable. Returns path or 'ffmpeg' fallback."""
        ffmpeg = shutil.which("ffmpeg") or shutil.which("ffmpeg.exe")
        if not ffmpeg:
            try:
                import imageio_ffmpeg

                exe = imageio_ffmpeg.get_ffmpeg_exe()
                if exe and os.path.isfile(exe):
                    ffmpeg = exe
            except Exception:
                pass
        return ffmpeg or "ffmpeg"

    @staticmethod
    def convert_to_wav(
        audio_path: str, sample_rate: int = DEFAULT_SAMPLE_RATE
    ) -> bytes:
        """Convert any audio file to 16kHz mono WAV bytes via ffmpeg.

        Args:
            audio_path: Path to the audio file.
            sample_rate: Target sample rate in Hz.

        Returns:
            WAV file bytes (16kHz, 16bit, mono PCM).

        Raises:
            RuntimeError: If ffmpeg conversion fails.
        """
        ffmpeg = _CommonUtils._find_ffmpeg()
        try:
            cmd = [
                ffmpeg,
                "-v", "quiet", "-y",
                "-i", audio_path,
                "-acodec", "pcm_s16le",
                "-ac", "1",
                "-ar", str(sample_rate),
                "-f", "wav",
                "-",
            ]
            result = subprocess.run(
                cmd,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=60,
            )
            return result.stdout
        except subprocess.CalledProcessError as e:
            error_msg = e.stderr.decode(errors="replace") if e.stderr else str(e)
            logger.error(f"ffmpeg audio conversion failed: {error_msg}")
            raise RuntimeError(f"Audio conversion failed: {error_msg}")

    @staticmethod
    def read_wav_info(data: bytes) -> tuple:
        """Parse WAV header and return audio metadata.

        Args:
            data: Raw WAV file bytes.

        Returns:
            (num_channels, sample_width_bytes, sample_rate, num_frames, raw_audio_data)

        Raises:
            ValueError: If the data is not a valid WAV file.
        """
        if len(data) < 44:
            raise ValueError("Invalid WAV file: too short")

        if data[:4] != b"RIFF" or data[8:12] != b"WAVE":
            raise ValueError("Invalid WAV file: not RIFF/WAVE format")

        # Parse fmt sub-chunk
        audio_format = struct.unpack("<H", data[20:22])[0]
        num_channels = struct.unpack("<H", data[22:24])[0]
        sample_rate = struct.unpack("<I", data[24:28])[0]
        bits_per_sample = struct.unpack("<H", data[34:36])[0]

        # Find data sub-chunk (may have extra chunks between fmt and data)
        pos = 36
        while pos < len(data) - 8:
            subchunk_id = data[pos : pos + 4]
            subchunk_size = struct.unpack("<I", data[pos + 4 : pos + 8])[0]
            if subchunk_id == b"data":
                wave_data = data[pos + 8 : pos + 8 + subchunk_size]
                return (
                    num_channels,
                    bits_per_sample // 8,
                    sample_rate,
                    subchunk_size // (num_channels * (bits_per_sample // 8)),
                    wave_data,
                )
            pos += 8 + subchunk_size

        raise ValueError("Invalid WAV file: no data sub-chunk found")


# ═══════════════════════════════════════════════════════════════════
# Async WebSocket Client
# ═══════════════════════════════════════════════════════════════════


class _AsrWsClient:
    """Async WebSocket client for Volcano Ark ASR streaming.

    Handles the full lifecycle: connect → send config → stream audio → collect results.
    Uses aiohttp for WebSocket communication with custom binary protocol.

    Usage:
        async with _AsrWsClient(api_key, resource_id, url) as client:
            responses = await client.execute("audio.wav")
    """

    def __init__(
        self,
        api_key: str,
        resource_id: str,
        url: str,
        segment_duration: int = 200,
        enable_nonstream: bool = True,
    ):
        self.seq = 1
        self.api_key = api_key
        self.resource_id = resource_id
        self.url = url
        self.segment_duration = segment_duration  # ms per audio chunk
        self.enable_nonstream = enable_nonstream
        self.session: Optional["aiohttp.ClientSession"] = None
        self.ws: Optional["aiohttp.ClientWebSocketResponse"] = None

    async def __aenter__(self):
        import aiohttp

        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        if self.ws and not self.ws.closed:
            await self.ws.close()
        if self.session and not self.session.closed:
            await self.session.close()

    async def execute(self, audio_path: str) -> list[_AsrResponse]:
        """Full ASR pipeline: read audio → connect → stream → collect.

        Args:
            audio_path: Path to the audio file to transcribe.

        Returns:
            List of _AsrResponse objects from the server.
        """
        if not audio_path:
            raise ValueError("Audio file path is empty")

        self.seq = 1

        try:
            # 1. Read and prepare audio
            content = await self._read_audio_data(audio_path)

            # 2. Calculate segment size
            segment_size = self._get_segment_size(content)

            # 3. Connect to WebSocket
            await self._create_connection()

            # 4. Send full client request (config)
            await self._send_full_client_request()

            # 5. Stream audio and collect responses
            responses = []
            async for response in self._start_audio_stream(segment_size, content):
                responses.append(response)

            return responses

        except Exception as e:
            logger.error(f"ASR WebSocket execution failed: {e}")
            raise
        finally:
            if self.ws and not self.ws.closed:
                await self.ws.close()

    async def _read_audio_data(self, file_path: str) -> bytes:
        """Read audio file and convert to 16kHz mono WAV if needed."""
        with open(file_path, "rb") as f:
            content = f.read()

        if not _CommonUtils.judge_wav(content):
            logger.info("Converting audio to 16kHz mono WAV for ASR...")
            content = _CommonUtils.convert_to_wav(file_path, DEFAULT_SAMPLE_RATE)

        return content

    def _get_segment_size(self, content: bytes) -> int:
        """Calculate segment size in bytes from WAV header.

        segment_size = sample_rate * channels * sample_width * segment_duration_ms / 1000
        """
        channel_num, samp_width, frame_rate, _, _ = _CommonUtils.read_wav_info(
            content
        )
        size_per_sec = channel_num * samp_width * frame_rate
        segment_size = size_per_sec * self.segment_duration // 1000
        return max(segment_size, 1)  # ensure at least 1 byte

    async def _create_connection(self) -> None:
        """Establish WebSocket connection with auth headers."""
        import aiohttp

        headers = _RequestBuilder.new_auth_headers(self.api_key, self.resource_id)
        try:
            self.ws = await self.session.ws_connect(
                self.url,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=300),
            )
            logger.info(f"ASR WebSocket connected to {self.url}")
        except Exception as e:
            logger.error(f"ASR WebSocket connection failed: {e}")
            raise

    async def _send_full_client_request(self) -> None:
        """Send the initial CLIENT_FULL_REQUEST with audio config."""
        import aiohttp

        request = _RequestBuilder.new_full_client_request(
            self.seq, enable_nonstream=self.enable_nonstream
        )
        self.seq += 1

        await self.ws.send_bytes(request)
        logger.info(f"Sent ASR full client request (seq={self.seq - 1})")

        # Receive initial response
        msg = await self.ws.receive()
        if msg.type == aiohttp.WSMsgType.BINARY:
            response = _ResponseParser.parse_response(msg.data)
            logger.debug(f"ASR initial response: code={response.code}")
        else:
            logger.error(f"Unexpected initial response type: {msg.type}")

    async def _start_audio_stream(
        self, segment_size: int, content: bytes
    ) -> list[_AsrResponse]:
        """Stream audio segments and receive recognition results concurrently.

        Runs sender and receiver as concurrent tasks:
        - Sender: splits audio into segments, sends with simulated real-time pacing
        - Receiver: collects parsed responses until end-of-stream
        """
        responses: list[_AsrResponse] = []

        async def sender():
            """Send audio segments with pacing."""
            audio_segments = self._split_audio(content, segment_size)
            total_segments = len(audio_segments)

            for i, segment in enumerate(audio_segments):
                is_last = i == total_segments - 1
                request = _RequestBuilder.new_audio_only_request(
                    self.seq, segment, is_last=is_last
                )
                await self.ws.send_bytes(request)
                logger.debug(
                    f"Sent ASR audio segment seq={self.seq} (last={is_last})"
                )

                if not is_last:
                    self.seq += 1

                # Simulate real-time streaming pace
                await asyncio.sleep(self.segment_duration / 1000)

        async def receiver():
            """Receive and parse ASR responses."""
            import aiohttp

            try:
                async for msg in self.ws:
                    if msg.type == aiohttp.WSMsgType.BINARY:
                        response = _ResponseParser.parse_response(msg.data)
                        responses.append(response)

                        if response.is_last_package or response.code != 0:
                            if response.code != 0:
                                logger.error(
                                    f"ASR error response: code={response.code}, "
                                    f"msg={response.payload_msg}"
                                )
                            break
                    elif msg.type == aiohttp.WSMsgType.ERROR:
                        logger.error(f"ASR WebSocket error: {self.ws.exception()}")
                        break
                    elif msg.type == aiohttp.WSMsgType.CLOSED:
                        logger.info("ASR WebSocket connection closed by server")
                        break
            except Exception as e:
                logger.error(f"ASR receiver error: {e}")

        # Run sender and receiver concurrently
        sender_task = asyncio.create_task(sender())
        receiver_task = asyncio.create_task(receiver())

        try:
            await asyncio.gather(sender_task, receiver_task)
        except Exception:
            sender_task.cancel()
            receiver_task.cancel()
            try:
                await asyncio.gather(sender_task, receiver_task)
            except (asyncio.CancelledError, Exception):
                pass

        return responses

    @staticmethod
    def _split_audio(data: bytes, segment_size: int) -> list[bytes]:
        """Split raw audio data into fixed-size segments."""
        if segment_size <= 0:
            return []

        segments = []
        for i in range(0, len(data), segment_size):
            end = min(i + segment_size, len(data))
            segments.append(data[i:end])
        return segments


# ═══════════════════════════════════════════════════════════════════
# Public API
# ═══════════════════════════════════════════════════════════════════


class ASRTranscriber:
    """Synchronous ASR (speech-to-text) interface for Volcano Ark.

    Wraps the async WebSocket client with asyncio.run() to provide
    a synchronous API matching the project's existing patterns.

    Usage:
        asr = ASRTranscriber(config)
        text = asr.transcribe("audio.wav")
        utterances = asr.transcribe_with_timestamps("audio.wav")
    """

    def __init__(self, config: dict):
        ark_config = config.get("ark", {})
        self.api_key = ark_config.get("api_key", "")
        self.base_url = ark_config.get("base_url", "https://ark.cn-beijing.volces.com/api/v3").rstrip("/")
        self.resource_id = ark_config.get(
            "asr_resource_id", "volc.seedasr.sauc.duration"
        )
        self.mode = ark_config.get("asr_mode", "nostream")
        self.segment_duration = ark_config.get("asr_segment_duration", 200)
        self.sample_rate = ark_config.get("asr_sample_rate", 16000)
        self.enabled = ark_config.get("asr_enabled", False)

        ws_base_url = self.base_url.replace("https://", "wss://", 1).replace("http://", "ws://", 1)
        if self.mode == "async":
            self.ws_url = f"{ws_base_url}/plan/sauc/bigmodel_async"
            self._enable_nonstream = False
        else:
            self.ws_url = f"{ws_base_url}/plan/sauc/bigmodel_nostream"
            self._enable_nonstream = True

    def transcribe(self, audio_path: str, timeout: float = 300.0) -> Optional[str]:
        """Transcribe audio file to text.

        Converts audio to 16kHz mono WAV (via ffmpeg if needed),
        streams it to Ark ASR WebSocket, and returns the recognized text.

        Args:
            audio_path: Path to audio file (.wav, .mp3, .m4a, etc.).
            timeout: Maximum wait time in seconds (default 300s).

        Returns:
            Full recognized text string, or None on failure.
        """
        if not self.enabled:
            logger.warning("ASR is disabled (asr_enabled=false), skipping transcription")
            return None
        if not self.api_key:
            logger.warning("Ark API key not configured, skipping ASR transcription")
            return None

        try:
            responses = asyncio.wait_for(
                self._transcribe_async(audio_path), timeout=timeout
            )
            return self._extract_text(responses)
        except asyncio.TimeoutError:
            logger.error(f"ASR transcription timed out after {timeout}s")
            return None
        except Exception as e:
            logger.error(f"ASR transcription failed: {e}")
            return None

    def transcribe_with_timestamps(
        self, audio_path: str, timeout: float = 300.0
    ) -> Optional[list[dict]]:
        """Transcribe audio and return utterances with timing information.

        Args:
            audio_path: Path to audio file.
            timeout: Maximum wait time in seconds (default 300s).

        Returns:
            List of dicts with timing info:
                [{"text": "...", "start": 0.0, "end": 2.5, "confidence": 0.95}, ...]
            or None on failure.

            Timestamps are in seconds (converted from the API's millisecond values).
            The format is compatible with scene_timings used in generator.py.
        """
        if not self.enabled:
            logger.warning("ASR is disabled (asr_enabled=false), skipping transcription")
            return None
        if not self.api_key:
            logger.warning("Ark API key not configured, skipping ASR transcription")
            return None

        try:
            responses = asyncio.wait_for(
                self._transcribe_async(audio_path), timeout=timeout
            )
            return self._extract_utterances(responses)
        except asyncio.TimeoutError:
            logger.error(f"ASR transcription timed out after {timeout}s")
            return None
        except Exception as e:
            logger.error(f"ASR transcription with timestamps failed: {e}")
            return None

    async def _transcribe_async(self, audio_path: str) -> list[_AsrResponse]:
        """Internal async transcription pipeline."""
        async with _AsrWsClient(
            api_key=self.api_key,
            resource_id=self.resource_id,
            url=self.ws_url,
            segment_duration=self.segment_duration,
            enable_nonstream=self._enable_nonstream,
        ) as client:
            return await client.execute(audio_path)

    @staticmethod
    def _extract_text(responses: list[_AsrResponse]) -> Optional[str]:
        """Concatenate all recognized text from ASR responses.

        Handles various response shapes from the Ark ASR API:
        - result as a single dict: {"text": "..."}
        - result as a list of dicts: [{"text": "..."}, ...]
        - utterances array with text fields
        """
        if not responses:
            return None

        texts = []
        for r in responses:
            if not r.payload_msg:
                continue

            msg = r.payload_msg

            # Try utterances array first (most common for nostream mode)
            utterances = msg.get("utterances", [])
            if utterances:
                for u in utterances:
                    text = u.get("text", "")
                    if text.strip():
                        texts.append(text)
                continue

            # Try result field
            result = msg.get("result", "")
            if result:
                if isinstance(result, str):
                    if result.strip():
                        texts.append(result)
                elif isinstance(result, list):
                    for item in result:
                        if isinstance(item, dict):
                            t = item.get("text", "")
                            if t.strip():
                                texts.append(t)
                        elif isinstance(item, str) and item.strip():
                            texts.append(item)
                elif isinstance(result, dict):
                    t = result.get("text", "")
                    if t.strip():
                        texts.append(t)

        full_text = "".join(texts)
        return full_text if full_text.strip() else None

    @staticmethod
    def _extract_utterances(responses: list[_AsrResponse]) -> Optional[list[dict]]:
        """Extract utterance-level data with timing from ASR responses.

        Converts millisecond timestamps from the API to seconds for
        compatibility with the project's scene_timings format.
        """
        if not responses:
            return None

        utterances = []
        for r in responses:
            if not r.payload_msg:
                continue

            msg = r.payload_msg

            # Try utterances array first
            raw_utterances = msg.get("utterances", [])
            if raw_utterances:
                for u in raw_utterances:
                    text = u.get("text", "")
                    if text.strip():
                        utterances.append(
                            {
                                "text": text,
                                "start": u.get("start_time", 0) / 1000.0,
                                "end": u.get("end_time", 0) / 1000.0,
                                "confidence": u.get("confidence", 1.0),
                            }
                        )
                continue

            # Try result as list of segments
            result = msg.get("result", "")
            if isinstance(result, list):
                for item in result:
                    if not isinstance(item, dict):
                        continue
                    text = item.get("text", "")
                    if text.strip():
                        utterances.append(
                            {
                                "text": text,
                                "start": item.get("start_time", 0) / 1000.0,
                                "end": item.get("end_time", 0) / 1000.0,
                                "confidence": item.get("confidence", 1.0),
                            }
                        )
            elif isinstance(result, dict):
                text = result.get("text", "")
                if text.strip():
                    utterances.append(
                        {
                            "text": text,
                            "start": result.get("start_time", 0) / 1000.0,
                            "end": result.get("end_time", 0) / 1000.0,
                            "confidence": result.get("confidence", 1.0),
                        }
                    )

        return utterances if utterances else None
