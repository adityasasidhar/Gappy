#!/usr/bin/env bash
# ──────────────────────────────────────────────────────────────────────────────
# Point the self-hosted Lemma stack at your LOCAL Ollama for all agent inference.
#
# Ollama exposes an OpenAI-compatible API at /v1, so we register it as the
# stack's default `openai_compat` provider. Every agent that uses the default
# runtime (none of the MindPod agents pin a custom one) then runs on Ollama —
# the pod files need NO changes and stay portable.
#
# Prereqs:
#   • Ollama running and reachable from Docker (see "OLLAMA NETWORKING" below)
#   • lemma-stack installed and started:
#       curl -fsSL https://raw.githubusercontent.com/lemma-work/lemma-platform/main/install.sh | bash
#       lemma-stack start
#
# Usage:
#   bash use-ollama.sh                       # uses nemotron-3-nano:30b-cloud
#   OLLAMA_MODEL=qwen3.5:4b bash use-ollama.sh
#   OLLAMA_URL=http://172.17.0.1:11434/v1 bash use-ollama.sh   # Linux bridge fallback
# ──────────────────────────────────────────────────────────────────────────────
set -euo pipefail

# Docker→host hostname. host.docker.internal works on Docker Desktop and on
# Linux when the container is given host-gateway. If the stack can't reach
# Ollama, re-run with OLLAMA_URL=http://172.17.0.1:11434/v1 (docker bridge IP).
OLLAMA_URL="${OLLAMA_URL:-http://host.docker.internal:11434/v1}"
OLLAMA_MODEL="${OLLAMA_MODEL:-nemotron-3-nano:30b-cloud}"

if ! command -v lemma-stack >/dev/null 2>&1; then
  echo "❌ lemma-stack not found. Install it first:"
  echo "   curl -fsSL https://raw.githubusercontent.com/lemma-work/lemma-platform/main/install.sh | bash"
  exit 1
fi

echo "🦙 Configuring Lemma stack → Ollama"
echo "   endpoint: $OLLAMA_URL"
echo "   model:    $OLLAMA_MODEL"
echo ""

lemma-stack config set LEMMA_DEFAULT_MODEL_TYPE      openai_compat
lemma-stack config set LEMMA_OPENAI_API_KEY          ollama          # Ollama ignores the key but one must be present
lemma-stack config set LEMMA_OPENAI_BASE_URL         "$OLLAMA_URL"
lemma-stack config set LEMMA_OPENAI_DEFAULT_MODEL    "$OLLAMA_MODEL"
lemma-stack config set LEMMA_OPENAI_MODEL_NAMES      "$OLLAMA_MODEL"
lemma-stack config set LEMMA_OPENAI_VISION_MODEL_NAMES "$OLLAMA_MODEL"  # only used for optional image reads

echo ""
echo "🔄 Restarting stack to apply..."
lemma-stack restart

echo ""
echo "✅ Done. The default runtime now routes through your local Ollama ($OLLAMA_MODEL)."
echo "   Re-import the pod into the local stack:  lemma pods import ./ "
