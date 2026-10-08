#!/bin/bash
# Double-click to start the Group Poster UI (opens in your browser).
cd "$(dirname "$0")"
PY=$(command -v python3.11 || command -v python3)
"$PY" app.py
echo; read -n 1 -s -r -p "Stopped. Press any key to close this window."
