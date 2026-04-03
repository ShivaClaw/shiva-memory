#!/usr/bin/env bash
# Layer 0 Signal Router with Semantic Context Injection (Option D)
#
# This wrapper:
# 1. Reads latest Layer 0.5 staging file (semantic recall results)
# 2. Substitutes {LAYER_0_5_CONTEXT} placeholder in AGENT-PROMPT.md
# 3. Invokes Layer 0 agent via sessions_spawn with augmented prompt
#
# Called by: Layer 0 cron job (every 15 minutes)

set -euo pipefail

WORKSPACE="/data/.openclaw/workspace"
STAGING_DIR="$WORKSPACE/memory/layer0.5"
AGENT_PROMPT="$WORKSPACE/memory/layer0/AGENT-PROMPT.md"
TEMP_PROMPT="/tmp/layer0-agent-prompt-$$.md"

# Read latest staging file
latest_staging=$(find "$STAGING_DIR" -name 'context-injection-*.json' -type f | sort -r | head -1)

if [[ -z "$latest_staging" ]]; then
  echo "⚠️  No Layer 0.5 staging file found, proceeding without semantic context"
  semantic_context="(No recent semantic context available)"
else
  # Extract context_markdown from JSON
  semantic_context=$(jq -r '.context_markdown // "(Empty context)"' "$latest_staging")
  confidence=$(jq -r '.confidence // 0' "$latest_staging")
  
  # Add metadata header (multiply by 100 using awk instead of bc)
  confidence_pct=$(echo "$confidence" | awk '{printf "%.0f", $1 * 100}')
  semantic_context="**Confidence:** ${confidence_pct}%

$semantic_context"
fi

# Substitute into AGENT-PROMPT.md (using awk to handle multiline replacement)
awk -v context="$semantic_context" '{gsub(/\{LAYER_0_5_CONTEXT\}/, context); print}' "$AGENT_PROMPT" > "$TEMP_PROMPT"

# Invoke Layer 0 agent via OpenClaw (assumes openclaw CLI or sessions_spawn)
# For now, just output the augmented prompt to verify substitution works
cat "$TEMP_PROMPT"

# Clean up
rm -f "$TEMP_PROMPT"

exit 0
