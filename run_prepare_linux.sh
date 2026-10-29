#!/usr/bin/env bash
set -euo pipefail
if [[ $# -lt 3 ]]; then
  echo "Usage: $0 <HyP3_root> <plan_dir> <output_dir> [extra hyp3lics prepare options...]"
  echo "Example:"
  echo "  $0 /data/MGX /data/MGX_plan /data/MGX_LiCSBAS --extent-mode intersection"
  exit 2
fi
INPUT="$1"; PLAN="$2"; OUTPUT="$3"; shift 3
python "$(dirname "$0")/hyp3lics.py" prepare \
  -i "$INPUT" \
  -o "$OUTPUT" \
  --plan-dir "$PLAN" \
  --extent-mode intersection \
  --plot-backend auto \
  "$@"
