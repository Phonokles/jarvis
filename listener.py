"""
JARVIS Listener
Wake word detection via Whisper + Speech-to-text
"""

import asyncio
import wave
import pyaudio
import whisper
import numpy as np
import os
from config import Config


class Listener:
    def __init__(self, config: Config):
        self.config = config
        self.audio = pyaudio.PyAudio()

        print("🔄 Loading Whisper model...")
        self.whisper_model = whisper.load_model(
            config.WHISPER_MODEL,
            device=config.WHISPER_DEVICE
        )
        print(f"✅ Whisper ({config.WHISPER_MODEL}) loaded on {config.WHISPER_DEVICE}")
        print(f"👂 Wake word: '{config.WAKE_WORD}'")

    def _record_chunk(self, seconds: float) -> tuple[list, float]:
        """Record a short audio chunk. Returns (frames, max_amplitude)."""
        chunk_size = 1024
        frames = []
        max_amplitude = 0.0

        stream = self.audio.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=self.config.SAMPLE_RATE,
            input=True,
            frames_per_buffer=chunk_size
        )

        num_chunks = int(self.config.SAMPLE_RATE / chunk_size * seconds)
        try:
            for _ in range(num_chunks):
                data = stream.read(chunk_size, exception_on_overflow=False)
                frames.append(data)
                amp = float(np.abs(np.frombuffer(data, dtype=np.int16)).mean())
                if amp > max_amplitude:
                    max_amplitude = amp
        finally:
            stream.stop_stream()
            stream.close()

        return frames, max_amplitude

    async def wait_for_wake_word(self) -> bool:
        """
        Records 1.5s chunks, checks for wake word.
        Only transcribes if audio is loud enough.
        Rejects if transcription is too long (background chatter).
        """
        SILENCE_THRESHOLD = 300
        CHUNK_SECONDS = 1.5          # shorter = snappier detection
        MAX_WORDS_IN_WAKE = 4        # "hey jarvis" = 2 words — reject long phrases

        while True:
            loop = asyncio.get_event_loop()
            frames, amplitude = await loop.run_in_executor(
                None, lambda: self._record_chunk(CHUNK_SECONDS)
            )

            # Skip quiet chunks
            if amplitude < SILENCE_THRESHOLD:
                await asyncio.sleep(0)
                continue

            # Save chunk
            tmp_path = "/tmp/jarvis_wake.wav"
            with wave.open(tmp_path, 'wb') as wf:
                wf.setnchannels(1)
                wf.setsampwidth(self.audio.get_sample_size(pyaudio.paInt16))
                wf.setframerate(self.config.SAMPLE_RATE)
                wf.writeframes(b''.join(frames))

            # Transcribe
            result = await loop.run_in_executor(
                None,
                lambda: self.whisper_model.transcribe(
                    tmp_path,
                    language="en",
                    fp16=(self.config.WHISPER_DEVICE == "cuda"),
                    condition_on_previous_text=False,
                    temperature=0.0,       # greedy, faster + more stable
                    no_speech_threshold=0.6,
                )
            )

            text = result["text"].lower().strip()

            # Skip if empty or too long (background conversation, not a wake word)
            word_count = len(text.split())
            if not text or word_count > MAX_WORDS_IN_WAKE:
                if text:
                    print(f"   [ignored: {text[:50]}]", end="\r")
                await asyncio.sleep(0)
                continue

            print(f"   [heard: {text}]", end="\r")

            # Check for wake word
            if self.config.WAKE_WORD.lower() in text:
                print("\n🟢 Wake word detected!")
                return True

            await asyncio.sleep(0)

    async def record_command(self) -> str | None:
        """Record audio until silence, return path to wav file."""
        chunk_size = 1024
        frames = []
        silence_threshold = 400
        silence_frames = 0
        max_silence_frames = int(self.config.SAMPLE_RATE / chunk_size * self.config.SILENCE_TIMEOUT)
        max_frames = int(self.config.SAMPLE_RATE / chunk_size * self.config.COMMAND_TIMEOUT)
        started = False

        stream = self.audio.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=self.config.SAMPLE_RATE,
            input=True,
            frames_per_buffer=chunk_size
        )

        print("🎙️  Recording... (speak now)")

        try:
            for _ in range(max_frames):
                data = stream.read(chunk_size, exception_on_overflow=False)
                frames.append(data)

                amplitude = float(np.abs(np.frombuffer(data, dtype=np.int16)).mean())

                if amplitude > silence_threshold:
                    started = True
                    silence_frames = 0
                elif started:
                    silence_frames += 1
                    if silence_frames >= max_silence_frames:
                        break

                await asyncio.sleep(0)
        finally:
            stream.stop_stream()
            stream.close()

        if not frames or not started:
            return None

        path = self.config.TEMP_AUDIO_PATH
        with wave.open(path, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(self.audio.get_sample_size(pyaudio.paInt16))
            wf.setframerate(self.config.SAMPLE_RATE)
            wf.writeframes(b''.join(frames))

        return path

    async def transcribe(self, audio_path: str) -> str:
        """Transcribe command audio to text."""
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            lambda: self.whisper_model.transcribe(
                audio_path,
                language="en",
                fp16=(self.config.WHISPER_DEVICE == "cuda"),
                temperature=0.0,
            )
        )
        return result["text"].strip()

    def cleanup(self):
        self.audio.terminate()
        for path in [self.config.TEMP_AUDIO_PATH, "/tmp/jarvis_wake.wav"]:
            if os.path.exists(path):
                os.remove(path)
