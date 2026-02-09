#!/usr/bin/env bash
# ============================================
# News Summary Bot - Quick Setup Script
# ============================================
set -e

echo "=========================================="
echo "  NEWS SUMMARY BOT - Setup"
echo "=========================================="

# Check Python
if ! command -v python3 &>/dev/null; then
    echo "[ERROR] Python 3.11+ is required. Install it first."
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
echo "[OK] Python $PYTHON_VERSION detected"

# Create virtual environment
if [ ! -d "venv" ]; then
    echo "[...] Creating virtual environment..."
    python3 -m venv venv
    echo "[OK] Virtual environment created"
else
    echo "[OK] Virtual environment already exists"
fi

# Activate
source venv/bin/activate
echo "[OK] Virtual environment activated"

# Install dependencies
echo "[...] Installing dependencies..."
pip install --upgrade pip -q
pip install -r requirements.txt -q
echo "[OK] Dependencies installed"

# Create .env if not exists
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo ""
    echo "=========================================="
    echo "  .env file created! Please configure:"
    echo "=========================================="
    echo ""
    echo "  1. TELEGRAM_BOT_TOKEN  (required)"
    echo "  2. TELEGRAM_CHAT_ID    (required)"
    echo "  3. ANTHROPIC_API_KEY   (required)"
    echo "  4. TWITTER_BEARER_TOKEN (optional)"
    echo ""
    echo "  Edit with: nano .env"
    echo "=========================================="
else
    echo "[OK] .env already exists"
fi

echo ""
echo "Setup complete! To run:"
echo "  source venv/bin/activate"
echo "  python -m news_bot.main"
echo ""
