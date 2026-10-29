#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
PYTHON="${PYTHON:-python3}"

echo "============================================================"
echo "HyP3-to-LiCSBAS v1.0.1 - Linux setup"
echo "Core installation does NOT require Matplotlib."
echo "============================================================"

"$PYTHON" -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip wheel
python -m pip install -e .

echo
echo "Optional prettier network plot:"
echo "  python -m pip install -e '.[plot]'"
echo "Not required; auto mode falls back to stdlib PNG."
echo
python check_env.py
