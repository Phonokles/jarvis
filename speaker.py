"""
JARVIS Speaker
Text-to-Speech using pyttsx3 (offline) or edge-tts (online, better quality)
"""

import pyttsx3
import asyncio
import subprocess
import tempfile
import os
from config import Config


class Speaker:
    def __init__(self, config: Config):
        self.config = config
        self.engine_type = config.TTS_ENGINE

        if self.engine_type == "pyttsx3":
            self.engine = pyttsx3.init()
            self.engine.setProperty("rate", config.TTS_VOICE_RATE)
            self.engine.setProperty("volume", config.TTS_VOICE_VOLUME)

            # Try to set a good English voice
            voices = self.engine.getProperty("voices")
            for voice in voices:
                if "english" in voice.name.lower() or "en" in voice.id.lower():
                    self.engine.setProperty("voice", voice.id)
                    break

            print(f"✅ TTS engine: pyttsx3 (offline)")

        elif self.engine_type == "edge-tts":
            # edge-tts is online but free and sounds much better
            print(f"✅ TTS engine: edge-tts (online) - Voice: {config.EDGE_TTS_VOICE}")

    def speak(self, text: str):
        """Convert text to speech and play it."""
        print(f"🔊 Speaking: {text}")

        if self.engine_type == "pyttsx3":
            self.engine.say(text)
            self.engine.runAndWait()

        elif self.engine_type == "edge-tts":
            asyncio.run(self._speak_edge(text))

    async def _speak_edge(self, text: str):
        """Async edge-tts speech."""
        try:
            import edge_tts
            voice = self.config.EDGE_TTS_VOICE
            tmp = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
            tmp.close()

            communicate = edge_tts.Communicate(text, voice)
            await communicate.save(tmp.name)

            # Play with mpg123 or ffplay (install with: sudo apt install mpg123)
            subprocess.run(["mpg123", "-q", tmp.name], check=True)
            os.unlink(tmp.name)
        except Exception as e:
            print(f"⚠️  edge-tts failed ({e}), falling back to pyttsx3")
            fallback = pyttsx3.init()
            fallback.say(text)
            fallback.runAndWait()
