#!/bin/bash
set -e

echo "=== Archon Setup Script ==="

# 1. Create utils package
mkdir -p utils
touch utils/__init__.py
echo "✔ Created utils/__init__.py"

# 2. Create data directories
mkdir -p data/chroma data/sessions
echo "✔ Created data/chroma and data/sessions"

# 3. Copy env example if no .env exists
if [ ! -f .env ]; then
  cp .env.example .env
  echo "✔ Copied .env.example → .env (fill in your API keys!)"
else
  echo "ℹ .env already exists, skipping"
fi

# 4. Install dependencies
pip install -r requirements.txt
echo "✔ Dependencies installed"

echo ""
echo "=== Setup complete! Run: python app.py ==="
