#!/usr/bin/env bash
# Final build once all 12 clips are in assets/voiceover/: re-time to the real voice, re-render at 60 fps, mix and encode.
set -euo pipefail
cd "$(dirname "$0")/.."
python3 scripts/vo_timing.py
python3 scripts/gen_frames.py
npx hyperframes check
npx hyperframes render --fps 60 --quality delivery --workers 4 --skill general-video --strict -o build/picture.mp4
python3 scripts/build.py
