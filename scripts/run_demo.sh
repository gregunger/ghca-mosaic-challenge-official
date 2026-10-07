#!/usr/bin/env bash
# SPDX-License-Identifier: LicenseRef-MOSAIC-Evaluation
# Generate the offline reference with the checkout's virtual environment when available.
set -euo pipefail

project_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
python_executable="python3"
if [[ -x "$project_root/.venv/bin/python" ]]; then
  python_executable="$project_root/.venv/bin/python"
fi

output_directory="${1:-$project_root/demo-output/SYN-001}"
export PYTHONPATH="$project_root/src"
cd "$project_root"
exec "$python_executable" -m mosaic.cli --output "$output_directory"
