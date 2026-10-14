#!/usr/bin/env bash
# Publish this as a Release asset only after reviewing its source and manifest.
set -euo pipefail
if [ "$#" -ne 1 ]; then printf 'usage: bash install-addon.sh <add-on-name>\n' >&2; exit 2; fi
command -v binux >/dev/null || { printf 'binux CLI must be installed first\n' >&2; exit 1; }
printf 'BlecaStudio add-on installer. External shell scripts execute with your user permissions.\n'
printf 'Review this script before running it. Package assets are checked using SHA-256 and a configured signature key.\n'
binux addon install "$1"
