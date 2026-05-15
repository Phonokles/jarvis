# 🤖 JARVIS — Local AI Assistant

A fully local, private AI assistant for Linux with voice control, PC automation, and Smart Home support.

## Tech Stack

| Component | Technology |
|-----------|-----------|
| AI Brain | Ollama + Llama 3.1 8B (local, free, unlimited) |
| Speech Recognition | OpenAI Whisper (local) |
| Wake Word | Pvporcupine ("Hey Jarvis") |
| Text to Speech | pyttsx3 (offline) or edge-tts (online) |
| PC Control | subprocess + pyaudio |
| Smart Home | Home Assistant API |

## Quick Start

```bash
# 1. Clone / download the project
cd jarvis

# 2. Run setup (installs everything)
bash setup.sh

# 3. Start Ollama in a separate terminal
ollama serve

# 4. Activate venv and run JARVIS
source venv/bin/activate
python main.py
```

## Voice Commands

| Say | Action |
|-----|--------|
| "Hey Jarvis" | Wake up |
| "What time is it?" | Current time |
| "Open Firefox" | Launch app |
| "Go to youtube.com" | Open website |
| "Volume up / down" | Adjust volume |
| "Take a screenshot" | Save screenshot |
| "Lock the screen" | Lock |
| "Turn on living room light" | Smart Home (if configured) |
| "Clear memory" | Reset conversation |
| Anything else | AI response from Llama 3.1 |

## Configuration

Edit `config.py`:

```python
OLLAMA_MODEL = "llama3.1:8b"      # Change AI model
WHISPER_MODEL = "base.en"          # tiny/base/small/medium
TTS_ENGINE = "edge-tts"            # Better quality (online)
WAKE_WORD_SENSITIVITY = 0.6        # Adjust sensitivity
```

## Changing the AI Model

```bash
# Pull a different model
ollama pull mistral:7b
ollama pull gemma3:12b

# Then update config.py:
OLLAMA_MODEL = "mistral:7b"
```

## Better TTS (Optional)

Switch to `edge-tts` in `config.py` for much better voice quality:
```python
TTS_ENGINE = "edge-tts"
EDGE_TTS_VOICE = "en-GB-RyanNeural"  # British accent
# or
EDGE_TTS_VOICE = "en-US-GuyNeural"   # American accent
```

## Project Structure

```
jarvis/
├── main.py         # Main loop
├── listener.py     # Wake word + Whisper STT
├── speaker.py      # Text-to-Speech
├── brain.py        # Ollama LLM connection
├── actions.py      # PC & Smart Home control
├── config.py       # All settings
├── requirements.txt
└── setup.sh        # Automated setup
```

## Roadmap

- [ ] Beautiful Electron/Tauri GUI
- [ ] Memory / notes skill
- [ ] Weather skill
- [ ] Music playback control
- [ ] Timer / alarm skill
- [ ] Custom wake word training
