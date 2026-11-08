#!/usr/bin/env bash
# Checks the local Kokoro TTS setup. Prints OK/MISSING per item; exit 1 if anything is missing.
dir="$HOME/tools/kokoro-tts"
missing=0
check() { if eval "$2" >/dev/null 2>&1; then echo "OK      $1"; else echo "MISSING $1"; missing=1; fi; }

check "python3.12 (brew install python@3.12)" "command -v python3.12"
check "espeak-ng (brew install espeak-ng)"     "command -v espeak-ng"
check "ffmpeg (brew install ffmpeg)"           "command -v ffmpeg"
check "venv at $dir/.venv"                     "test -x '$dir/.venv/bin/python'"
check "kokoro package in venv"                 "'$dir/.venv/bin/python' -c 'import kokoro, soundfile'"
check "speak.py at $dir"                       "test -f '$dir/speak.py'"
check "model cache (downloads ~330 MB on first run if missing)" "ls '$dir/models/hub' | grep -q Kokoro-82M"
exit $missing
