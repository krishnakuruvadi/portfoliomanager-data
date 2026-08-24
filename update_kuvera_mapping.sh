#!/bin/bash
set -euo pipefail

if [ $# -eq 0 ]; then
    echo "Usage: $0 <kuvera fund name>" >&2
    exit 1
fi

script_dir=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)

cd "$script_dir"
source venv/bin/activate
cd India/code
python update_kuvera_name.py "$1"
