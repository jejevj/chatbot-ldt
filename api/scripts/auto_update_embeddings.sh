#!/bin/bash
# Auto update embeddings script

set -e

echo "[$(date)] Starting embedding update..."

# Run embedding generation script
cd /app
python scripts/generate_embeddings.py

echo "[$(date)] Embedding update completed"
