"""Turn text into speech with the local Kokoro-82M model.

Input: a .txt file. Lines with only "---" split it into sections.
Output: one audio file (.wav, or .m4a/.mp3 through ffmpeg).
"""
import argparse
import os
import pathlib
import subprocess
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
os.environ.setdefault("HF_HOME", str(HERE / "models"))

import numpy as np  # noqa: E402
import soundfile as sf  # noqa: E402
from kokoro import KPipeline  # noqa: E402

RATE = 24000


def read_sections(path: pathlib.Path) -> list[str]:
    raw = path.read_text(encoding="utf-8")
    parts = [p.strip() for p in raw.split("\n---\n")]
    return [p for p in parts if p]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("input", type=pathlib.Path)
    ap.add_argument("output", type=pathlib.Path)
    ap.add_argument("--voice", default="af_heart", help="af_heart, af_bella, am_michael, am_fenrir, bf_emma, bm_george ...")
    ap.add_argument("--speed", type=float, default=1.0)
    ap.add_argument("--pause", type=float, default=1.2, help="seconds of silence between sections")
    ap.add_argument("--announce", default="", help='prefix per section, e.g. "Slide" -> "Slide 1."')
    args = ap.parse_args()

    sections = read_sections(args.input)
    lang = args.voice[0]  # a = American, b = British
    pipe = KPipeline(lang_code=lang, repo_id="hexgrad/Kokoro-82M")
    gap = np.zeros(int(RATE * args.pause), dtype=np.float32)
    chunks: list[np.ndarray] = []

    for i, text in enumerate(sections, 1):
        if args.announce:
            text = f"{args.announce} {i}. {text}"
        for _, _, audio in pipe(text, voice=args.voice, speed=args.speed, split_pattern=r"\n+"):
            chunks.append(np.asarray(audio, dtype=np.float32))
        chunks.append(gap)
        print(f"section {i}/{len(sections)}", file=sys.stderr)

    wav = np.concatenate(chunks)
    out = args.output
    if out.suffix.lower() == ".wav":
        sf.write(out, wav, RATE)
    else:
        with tempfile.NamedTemporaryFile(suffix=".wav") as tmp:
            sf.write(tmp.name, wav, RATE)
            subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", tmp.name, "-b:a", "128k", str(out)], check=True)
    print(f"{out} ({len(wav) / RATE / 60:.1f} min)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
