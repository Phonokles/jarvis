"""
JARVIS Brain
Handles conversation with local Ollama LLM (Gemma 4)
"""

import aiohttp
import json
import re
from config import Config


class Brain:
    def __init__(self, config: Config):
        self.config = config
        self.ollama_url = f"{config.OLLAMA_URL}/api/chat"
        self.conversation_history = []
        self.system_prompt = config.SYSTEM_PROMPT
        print(f"✅ Brain connected to Ollama ({config.OLLAMA_MODEL})")

    async def think(self, user_input: str, actions=None) -> str:
        """Send message to Ollama and get a response."""
        self.conversation_history.append({
            "role": "user",
            "content": user_input
        })

        payload = {
            "model": self.config.OLLAMA_MODEL,
            "messages": [
                {"role": "system", "content": self.system_prompt},
                *self.conversation_history
            ],
            "stream": False,
            "options": {
                "temperature": 0.7,
                "num_predict": 300,
            }
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.ollama_url,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=60)
                ) as resp:
                    if resp.status != 200:
                        return "Sorry, I couldn't connect to my brain. Is Ollama running?"

                    data = await resp.json()
                    response = data["message"]["content"].strip()

                    # Check if response contains a sudo command
                    if actions and response.startswith("SUDO:"):
                        command = response[5:].strip()
                        result = actions.run_sudo(command)
                        response = result

                    self.conversation_history.append({
                        "role": "assistant",
                        "content": response
                    })

                    # Keep history from getting too long
                    if len(self.conversation_history) > 20:
                        self.conversation_history = self.conversation_history[-20:]

                    return response

        except aiohttp.ClientConnectorError:
            return "I can't reach Ollama. Please make sure it's running with: ollama serve"
        except Exception as e:
            return f"Brain error: {str(e)}"

    def reset_memory(self):
        self.conversation_history = []
        print("🧹 Memory cleared.")
