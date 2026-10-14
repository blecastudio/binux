#!/usr/bin/env bash
set -euo pipefail
project_dir="$(cd "$(dirname "$0")/.." && pwd)"
cd "$project_dir"
PYTHONPATH="$project_dir/core${PYTHONPATH:+:$PYTHONPATH}" python3 -m unittest discover -s tests -v
