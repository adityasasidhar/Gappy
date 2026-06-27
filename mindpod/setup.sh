#!/usr/bin/env bash
set -euo pipefail

echo "🧠 MindPod setup"
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
echo "✅ Pod imported!"
echo ""

# Ask about seed data
read -r -p "Load demo seed data? (y/N): " load_seed
if [[ "$load_seed" =~ ^[Yy]$ ]]; then
  bash "$SCRIPT_DIR/seed/seed.sh"
fi

echo ""
echo "🚀 Opening MindPod..."
lemma apps open mindpod || echo "Run: lemma apps open mindpod"

echo ""
echo "Done! Upload files in the app, then describe your goal."
