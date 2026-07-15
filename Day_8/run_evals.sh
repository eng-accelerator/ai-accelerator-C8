#!/usr/bin/env bash
set -euo pipefail

# All models via OpenRouter
MODELS=(
    "openai/openai/gpt-5.4"
    "openai/anthropic/claude-sonnet-4-6"
    "openai/google/gemini-3.1-pro"
    "openai/x-ai/grok-3"
)

SANDBOX="${1:-docker}"  # docker or modal
TASK="${2:-all}"        # all, landing_page, or code_critique

echo "=== EduTech LLM Evals ==="
echo "Sandbox: $SANDBOX"
echo "Models:  ${MODELS[*]}"
echo ""

for model in "${MODELS[@]}"; do
    model_short="${model##*/}"
    echo "--- Running: $model_short ---"

    if [[ "$TASK" == "all" || "$TASK" == "landing_page" ]]; then
        echo "[Task 1] Landing Page — $model_short"
        inspect eval task_landing_page.py \
            --model "$model" \
            -T sandbox_type="$SANDBOX" \
            --max-samples 1 \
            2>&1 | tail -5
        echo ""
    fi

    if [[ "$TASK" == "all" || "$TASK" == "code_critique" ]]; then
        echo "[Task 2] Code Critique — $model_short"
        inspect eval task_code_critique.py \
            --model "$model" \
            --max-samples 1 \
            2>&1 | tail -5
        echo ""
    fi
done

echo "=== Done. View results: inspect view ==="
