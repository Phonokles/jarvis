#!/usr/bin/env python3
"""
JARVIS - Personal AI Assistant
"""

import asyncio
import signal
import sys
import time
from listener import Listener
from speaker import Speaker
from brain import Brain
from actions import Actions
from config import Config

class Jarvis:
    def __init__(self):
        self.config = Config()
        self.speaker = Speaker(self.config)
        self.listener = Listener(self.config)
        self.actions = Actions(self.config)
        self.brain = Brain(self.config)
        self.running = False
        self.active = False
        self.last_interaction = 0.0

    async def start(self):
        self.running = True
        print("\n🤖 JARVIS is online. Say 'Jarvis' to wake me up.\n")
        self.speaker.speak("JARVIS online. How can I assist you?")

        while self.running:
            try:
                if not self.active:
                    print("💤 Sleeping... say 'Jarvis' to wake me up.")
                    await self.listener.wait_for_wake_word()
                    self.active = True
                    self.last_interaction = time.time()
                    self.speaker.speak("Yes?")
                    print("✅ Active — listening for commands (sleeps after 60s of silence)\n")

                print("👂 Listening...")
                audio = await self.listener.record_command()

                # Check inactivity timeout
                if time.time() - self.last_interaction > self.config.INACTIVITY_TIMEOUT:
                    self.active = False
                    print("⏰ Timeout — going back to sleep.")
                    self.speaker.speak("Going to sleep. Say Jarvis to wake me.")
                    continue

                if not audio:
                    continue

                print("🔄 Transcribing...")
                text = await self.listener.transcribe(audio)
                if not text or len(text.strip()) < 2:
                    continue

                print(f"📝 You: {text}")
                self.last_interaction = time.time()

                # Actions (setups, volume, etc.)
                action_result = self.actions.handle(text)
                if action_result == "__RESET_MEMORY__":
                    self.brain.reset_memory()
                    self.speaker.speak("Memory cleared.")
                    continue
                if action_result:
                    self.speaker.speak(action_result)
                    continue

                # AI brain (with access to actions for sudo)
                print("🧠 Thinking...")
                response = await self.brain.think(text, actions=self.actions)
                print(f"💬 JARVIS: {response}")
                self.speaker.speak(response)

            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"⚠️  Error: {e}")
                continue

        self.shutdown()

    def shutdown(self):
        self.running = False
        print("\n🔴 JARVIS shutting down...")
        self.speaker.speak("Goodbye.")
        sys.exit(0)


def main():
    jarvis = Jarvis()

    def signal_handler(sig, frame):
        jarvis.shutdown()

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    asyncio.run(jarvis.start())


if __name__ == "__main__":
    main()
