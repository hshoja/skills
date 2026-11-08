---
name: local-tts
description: Use when the user wants text, a script, slide speaker notes, or a talk turned into a voice recording, audio file, narration or MP3/M4A, especially when macOS `say` sounds robotic or the user wants an open, local, natural-sounding voice instead of a cloud service.
---

# Local TTS (Kokoro-82M)

## Overview
Natural speech from a local open model (Kokoro-82M, Apache-2.0). No cloud, no API key. Do not use macOS `say`: it sounds robotic.

Setup lives in `~/tools/kokoro-tts/` (venv in `.venv`, model cache in `models/`, script `speak.py`).

## Workflow
1. **Check the setup:** run `bash <skill-dir>/check.sh`, where `<skill-dir>` is this skill's base directory. If any line says MISSING, tell the user what is missing and its download size, ask for an OK, then follow Setup below. Re-run the check until it exits 0.
2. **Ask the user for settings** in one AskUserQuestion call (skip any the user already gave; recommended option first):

   | Question | Options |
   |---|---|
   | Voice | `af_heart` US female (Recommended), `am_michael` US male, `bf_emma` UK female, `bm_george` UK male |
   | Speed | 1.0 normal (Recommended), 0.9 slower, 1.1 faster |
   | Sections | One section per slide with "Slide N" (Recommended for notes), sections without announce, one continuous text |
   | Output | `.m4a` (Recommended), `.mp3`, `.wav`; plus where to save (default: scratchpad) |

3. **Prepare input** (below), **run** `speak.py` with the chosen flags, then send the file to the user.

## Quick Reference

| Task | Command |
|---|---|
| Speak a text file | `~/tools/kokoro-tts/.venv/bin/python ~/tools/kokoro-tts/speak.py in.txt out.m4a` |
| Slides, one section each | split sections with a line `---`, add `--announce Slide` (says "Slide 1. ...") |
| Other voice | `--voice am_michael` (US male), `af_heart` (US female, default), `bf_emma` / `bm_george` (UK) |
| Faster / slower | `--speed 1.1` / `--speed 0.9` |
| Pause between sections | `--pause 1.5` (seconds) |

Output `.wav` directly, `.m4a`/`.mp3` through ffmpeg. Speed on Apple M4: about 15 s of audio per 4 s of compute; 17 min of audio took 4 min.

## Preparing input
- Strip HTML tags and stage directions such as `(Callback: ...)` first. Kokoro reads everything aloud.
- One section per slide, separated by a line that is only `---`.
- Write input and output to the scratchpad unless the user names a place.
- Over ~5 min of text: run in the background (compute is about a quarter of audio length).
- The printed length is in minutes; use `ffprobe` for seconds. A Hugging Face "unauthenticated" warning is harmless.

## Setup (only for items `check.sh` reports MISSING)
```bash
brew install python@3.12 espeak-ng ffmpeg
mkdir -p ~/tools/kokoro-tts && cd ~/tools/kokoro-tts
python3.12 -m venv .venv
.venv/bin/pip install "kokoro>=0.9.4" soundfile
```
Then copy `speak.py` from this skill folder into `~/tools/kokoro-tts/`. First run downloads the model (~330 MB, Hugging Face `hexgrad/Kokoro-82M`) and a spaCy model (~13 MB). Downloads need the user's OK.

## Common Mistakes
- Python 3.9 (system): kokoro needs 3.10-3.12. Use the venv.
- Missing `espeak-ng`: unknown words fail to pronounce.
- Voice prefix sets the accent: `a*` American, `b*` British.
