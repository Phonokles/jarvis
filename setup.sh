#!/bin/bash
# JARVIS Setup Script for Arch Linux
# Run with: bash setup.sh

set -e

echo "╔══════════════════════════════════════╗"
echo "║        JARVIS SETUP (ARCH)           ║"
echo "╚══════════════════════════════════════╝"
echo ""

# --- System dependencies via yay ---
echo "📦 Installing system dependencies..."
yay -S --noconfirm --needed \
    python \
    python-pip \
    portaudio \
    ffmpeg \
    mpg123 \
    python-virtualenv \
    base-devel

# --- Python virtual environment ---
echo ""
echo "🐍 Creating Python virtual environment..."
# --system-site-packages lets the venv see system PyTorch later
python -m venv --system-site-packages venv
source venv/bin/activate

# --- CUDA / PyTorch ---
echo ""
echo "🔍 Checking for NVIDIA GPU..."
if command -v nvidia-smi &> /dev/null; then
    echo "✅ NVIDIA GPU detected:"
    nvidia-smi --query-gpu=name,memory.total --format=csv,noheader
    echo ""
    echo "📦 Installing PyTorch with CUDA via yay (Arch repos — correct for your Python version)..."
    # Install system-wide; venv inherits it via --system-site-packages
    yay -S --noconfirm --needed python-pytorch-cuda python-torchvision python-torchaudio
else
    echo "⚠️  No NVIDIA GPU found. Installing CPU-only PyTorch via yay..."
    yay -S --noconfirm --needed python-pytorch python-torchvision python-torchaudio
fi

# Quick sanity check
python -c "import torch; print(f'✅ PyTorch {torch.__version__} — CUDA: {torch.cuda.is_available()}')"

# --- Python packages ---
echo ""
echo "📦 Installing Python packages..."
pip install -r requirements.txt

# --- Ollama ---
echo ""
echo "🦙 Checking Ollama..."
if ! command -v ollama &> /dev/null; then
    echo "📦 Installing Ollama via yay..."
    yay -S --noconfirm ollama
else
    echo "✅ Ollama already installed."
fi

echo ""
echo "🔄 Pulling Llama 3.1 8B model (~5GB, grab a coffee)..."
ollama pull llama3.1:8b

# --- Whisper predownload ---
echo ""
echo "🔄 Pre-downloading Whisper base.en model..."
python -c "import whisper; whisper.load_model('base.en')"

# --- Fish shell config ---
echo ""
echo "🐟 Setting up Fish shell aliases..."
FISH_CONFIG="$HOME/.config/fish/config.fish"
mkdir -p "$HOME/.config/fish"
JARVIS_DIR="$(pwd)"

if ! grep -q "jarvis" "$FISH_CONFIG" 2>/dev/null; then
    cat >> "$FISH_CONFIG" << EOF

# JARVIS aliases
abbr --add jarvis "cd $JARVIS_DIR && source venv/bin/activate.fish && python main.py"
abbr --add jarvis-serve "ollama serve"
EOF
    echo "✅ Fish aliases added to $FISH_CONFIG"
else
    echo "ℹ️  Fish aliases already present, skipping."
fi

echo ""
echo "╔══════════════════════════════════════╗"
echo "║           SETUP COMPLETE! ✅          ║"
echo "╚══════════════════════════════════════╝"
echo ""
echo "To start JARVIS:"
echo ""
echo "  Terminal 1 — start Ollama:"
echo "    ollama serve"
echo ""
echo "  Terminal 2 — start JARVIS:"
echo "    source venv/bin/activate.fish"
echo "    python main.py"
echo ""
echo "  Or just use the Fish alias:"
echo "    jarvis"
echo ""
echo "Say 'Hey Jarvis' to wake it up! 🤖"
