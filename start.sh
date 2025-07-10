#!/usr/bin/env bash

set -eo pipefail

# Load environment variables from .env file
if [ -f .env ]; then
    set -o allexport
    source .env
    set +o allexport
fi

# Default values (used if not set in .env)
MODEL=${MLX_MODEL:-"mlx-community/DeepSeek-Coder-V2-Lite-Instruct-4bit-mlx"}
PORT_MLX=${MLX_PORT:-8080}
PORT_CHAINLIT=${PORT_CHAINLIT:-7860}
VENV_PATH=${VENV_PATH:-.venv}
LOG_FILE=${LOG_FILE:-server.log}
LOG_LEVEL=${LOG_LEVEL:-DEBUG}

# MLX OpenAI Server
#uv venv --python 3.12
# Start the mlx_lm server in the background with the specified model
#uv run --with mlx-lm python -m mlx_lm.server --model "${MODEL}" --log-level "${LOG_LEVEL}" --port "${PORT_MLX}" > "$LOG_FILE" 2>&1 &

# Activate the virtual environment
source "$VENV_PATH/bin/activate"
# Run the Chainlit application
$VENV_PATH/bin/chainlit run app.py