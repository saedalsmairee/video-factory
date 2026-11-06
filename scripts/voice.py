"""Voice every scene with a free Microsoft neural voice (edge-tts) and save exact word timings.

Usage: python3 scripts/voice.py videos/001-baby-memories
Writes build/voice.mp3 and build/timeline.json.
"""
import asyncio
import json
import os
import subprocess
import sys
from pathlib import Path

import edge_tts

GAP = 0.18  # seconds of silence after each scene
PROXY = os.environ.get("HTTPS_PROXY") or None


async def voice_scene(text, voice, rate, out):
    comm = edge_tts.Communicate(text, voice, rate=rate, boundary="WordBoundary", proxy=PROXY)
    words = []
    with open(out, "wb") as f:
        async for chunk in comm.stream():
            if chunk["type"] == "audio":
                f.write(chunk["data"])
            elif chunk["type"] == "WordBoundary":
                s = chunk["offset"] / 1e7
                words.append({"w": chunk["text"], "s": s, "e": s + chunk["duration"] / 1e7})
    return words


def duration(path):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                        "-of", "csv=p=0", str(path)], capture_output=True, text=True)
    return float(r.stdout.strip())


async def main(folder):
    folder = Path(folder)
    spec = json.loads((folder / "script.json").read_text())
    build = folder / "build"
    build.mkdir(exist_ok=True)
    t, timeline, parts = 0.0, [], []
    for i, sc in enumerate(spec["scenes"]):
        mp3 = build / f"vo_{i}.mp3"
        words = await voice_scene(sc["text"], spec["voice"], spec.get("rate", "+0%"), mp3)
        wav = build / f"vo_{i}.wav"
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(mp3), "-af",
                        f"apad=pad_dur={GAP}", "-ar", "48000", "-ac", "1", str(wav)], check=True)
        d = duration(wav)
        timeline.append({**sc, "start": t, "dur": d,
                         "words": [{**w, "s": w["s"] + t, "e": w["e"] + t} for w in words]})
        parts.append(wav)
        t += d
    lst = build / "parts.txt"
    lst.write_text("".join(f"file '{p.name}'\n" for p in parts))
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(lst),
                    "-c:a", "pcm_s16le", str(build / "voice.wav")], check=True)
    (build / "timeline.json").write_text(json.dumps({"title": spec["title"], "total": t,
                                                     "scenes": timeline}, indent=1, ensure_ascii=False))
    print(f"voiced {len(timeline)} scenes, {t:.1f}s")


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1]))
