#!/usr/bin/env bash
set -euo pipefail

echo "🏛️ PANCHAI Setup"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Check lemma CLI
if ! command -v lemma &> /dev/null; then
  echo "❌ Lemma CLI not found. Install with: npm install -g @lemma/cli"
  exit 1
fi

# Import the pod
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
echo "📦 Importing pod from $SCRIPT_DIR..."
lemma pods import "$SCRIPT_DIR"

echo ""
echo "✅ Pod imported successfully!"
echo ""

# Ask about seed data
read -r -p "Load demo seed data (YesMadam & Binocs scenarios)? (y/N): " load_seed
if [[ "$load_seed" =~ ^[Yy]$ ]]; then
  echo "🌱 Loading seed data..."
  bash "$SCRIPT_DIR/seed/seed.sh"
fi

echo ""
echo "🚀 Opening PANCHAI App..."
lemma apps open panchai || echo "Run: lemma apps open panchai"

echo ""
echo "Setup complete! The PANCHAI multi-agent deliberation engine is ready."
