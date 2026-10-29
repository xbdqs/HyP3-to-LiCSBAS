#!/usr/bin/env bash
set -euo pipefail
if [[ $# -ne 2 ]]; then
  echo "Usage: $0 <HyP3_root> <plan_output>"
  exit 2
fi
python "$(dirname "$0")/hyp3lics.py" plan -i "$1" -o "$2"
