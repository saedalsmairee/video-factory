"""Make a vertical short (1080x1920) from a script.json.

Usage: python3 scripts/make_short.py videos/001-baby-memories

Needs: piper-tts, pillow, numpy, ffmpeg. Everything is free and runs offline.
"""
import json
import math
import random
import subprocess
import sys
import wave
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
from piper import PiperVoice, SynthesisConfig

W, H, FPS = 1080, 1920, 30
ROOT = Path(__file__).resolve().parent.parent
VOICE = ROOT / "voices" / "en-us-ryan-high.onnx"
FONT_BLACK = "/usr/share/fonts/opentype/inter/InterDisplay-Black.otf"
FONT_BOLD = "/usr/share/fonts/opentype/inter/Inter-ExtraBold.otf"
GAP = 0.25  # silence between scenes, seconds
HIGHLIGHT = (255, 230, 0)


def hex_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def synth(scenes, workdir):
    """Voice each scene, return list of durations and the joined wav path."""
    voice = PiperVoice.load(str(VOICE))
    cfg = SynthesisConfig(length_scale=1.0)
    durations, chunks, rate = [], [], 22050
    for i, s in enumerate(scenes):
        p = workdir / f"vo_{i}.wav"
        with wave.open(str(p), "wb") as w:
            voice.synthesize_wav(s["text"], w, syn_config=cfg)
        with wave.open(str(p), "rb") as r:
            rate = r.getframerate()
            data = np.frombuffer(r.readframes(r.getnframes()), dtype=np.int16)
        chunks.append(data)
        chunks.append(np.zeros(int(GAP * rate), dtype=np.int16))
        durations.append(len(data) / rate + GAP)
    out = workdir / "voice.wav"
    with wave.open(str(out), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(np.concatenate(chunks).tobytes())
    return durations, out


def word_times(text, start, dur):
    """Spread words over the spoken part of a scene, weighted by length."""
    words = text.split()
    speak = dur - GAP
    weights = [len(w) + 2 + (4 if w[-1] in ".,?!:" else 0) for w in words]
    total = sum(weights)
    t, out = start, []
    for w, wt in zip(words, weights):
        d = speak * wt / total
        out.append((w, t, t + d))
        t += d
    return out


def gradient(c1, c2, h=H + 600):
    a, b = np.array(hex_rgb(c1), float), np.array(hex_rgb(c2), float)
    y = np.linspace(0, 1, h)[:, None]
    y = (np.sin(y * math.pi * 2) + 1) / 2  # loops so it can scroll
    col = a * (1 - y) + b * y
    img = np.repeat(col[:, None, :], W, axis=1)
    return img.astype(np.uint8)


def blob_sprite(r, color):
    s = Image.new("RGBA", (r * 4, r * 4), (0, 0, 0, 0))
    d = ImageDraw.Draw(s)
    d.ellipse((r, r, r * 3, r * 3), fill=color + (110,))
    return s.filter(ImageFilter.GaussianBlur(r * 0.45))


def text_img(text, font, fill, stroke=10):
    box = font.getbbox(text, stroke_width=stroke)
    im = Image.new("RGBA", (box[2] - box[0] + 20, box[3] - box[1] + 20), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((10 - box[0], 10 - box[1]), text, font=font, fill=fill,
                            stroke_width=stroke, stroke_fill=(20, 10, 40))
    return im


def fit_font(text, path, size, max_w):
    while size > 40:
        f = ImageFont.truetype(path, size)
        if f.getbbox(text)[2] <= max_w:
            return f
        size -= 8
    return ImageFont.truetype(path, size)


def ease_pop(t):
    """0 -> 1 with a little overshoot, over ~0.35 s."""
    if t >= 0.35:
        return 1.0
    x = t / 0.35
    return 1 + 2.2 * (x - 1) ** 3 + 1.2 * (x - 1) ** 2 if x < 1 else 1.0


def main(folder):
    folder = Path(folder)
    spec = json.loads((folder / "script.json").read_text())
    scenes = spec["scenes"]
    work = folder / "build"
    work.mkdir(exist_ok=True)

    durations, voice_wav = synth(scenes, work)
    total = sum(durations)
    starts = np.cumsum([0] + durations[:-1])

    # Prepare per-scene assets
    cap_font = ImageFont.truetype(FONT_BLACK, 92)
    brand_font = ImageFont.truetype(FONT_BOLD, 34)
    assets = []
    rnd = random.Random(7)
    for s, st, du in zip(scenes, starts, durations):
        c1, c2 = s["colors"]
        head = text_img(s["headline"], fit_font(s["headline"], FONT_BLACK, 230, W - 140), (255, 255, 255), 14)
        sub = text_img(s["sub"].upper(), fit_font(s["sub"].upper(), FONT_BOLD, 64, W - 160), (255, 255, 255), 8)
        blobs = []
        for _ in range(6):
            r = rnd.randint(90, 220)
            col = hex_rgb(rnd.choice([c1, c2, "#ffffff"]))
            blobs.append((blob_sprite(r, col), rnd.random() * W, rnd.random() * H,
                          rnd.uniform(-60, 60), rnd.uniform(-90, 90), rnd.random() * 6))
        words = word_times(s["text"], st, du)
        # group words into caption chunks of up to 3
        chunks = [words[i:i + 3] for i in range(0, len(words), 3)]
        assets.append(dict(bg=gradient(c1, c2), head=head, sub=sub, blobs=blobs,
                           chunks=chunks, start=st, dur=du))

    out_mp4 = folder / f"{folder.name}.mp4"
    music = work / "music.wav"
    # Soft synth pad + gentle pulse, made by ffmpeg (no licence worries)
    subprocess.run([
        "ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i",
        f"aevalsrc='0.05*(sin(2*PI*220*t)+0.7*sin(2*PI*277.18*t)+0.6*sin(2*PI*329.63*t)+0.4*sin(2*PI*110*t))"
        f"*(0.6+0.4*sin(2*PI*0.25*t))+0.04*sin(2*PI*55*t)*exp(-8*mod(t,0.5))':s=44100:d={total + 1:.2f}",
        "-af", "lowpass=f=1800,afade=t=in:d=1,afade=t=out:st=" + f"{total - 1.5:.2f}:d=1.5",
        str(music)], check=True)

    ff = subprocess.Popen([
        "ffmpeg", "-y", "-loglevel", "error",
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
        "-i", str(voice_wav), "-i", str(music),
        "-filter_complex", "[1:a]volume=1.6[v];[2:a]volume=0.55[m];[v][m]amix=inputs=2:duration=first:normalize=0,alimiter=limit=0.89[a]",
        "-map", "0:v", "-map", "[a]", "-c:v", "libx264", "-preset", "medium", "-crf", "20",
        "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k", "-shortest", str(out_mp4)],
        stdin=subprocess.PIPE)

    n_frames = int(total * FPS)
    for f in range(n_frames):
        t = f / FPS
        idx = max(i for i, a in enumerate(assets) if a["start"] <= t)
        a = assets[idx]
        lt = t - a["start"]

        off = int((t * 120) % 600)
        frame = Image.fromarray(a["bg"][off:off + H]).convert("RGBA")
        for spr, x, y, vx, vy, ph in a["blobs"]:
            px = (x + vx * t + 40 * math.sin(t + ph)) % (W + 300) - 300
            py = (y + vy * t + 40 * math.cos(t * 0.8 + ph)) % (H + 300) - 300
            frame.alpha_composite(spr, (int(px), int(py)))

        # Headline pops in, then breathes
        k = ease_pop(lt) * (1 + 0.025 * math.sin(lt * 4))
        hw, hh = a["head"].size
        head = a["head"].resize((max(1, int(hw * k)), max(1, int(hh * k))))
        hy = 560 - head.size[1] // 2
        frame.alpha_composite(head, ((W - head.size[0]) // 2, hy))
        if lt > 0.25:
            sub = a["sub"]
            frame.alpha_composite(sub, ((W - sub.size[0]) // 2, 560 + hh // 2 + 30))

        # Word-by-word caption: current 3-word chunk, spoken word highlighted
        chunk = next((c for c in a["chunks"] if c[0][1] <= t < c[-1][2] + 0.05), None)
        if chunk:
            d = ImageDraw.Draw(frame)
            texts = [w for w, _, _ in chunk]
            line = " ".join(texts)
            fnt = cap_font if cap_font.getlength(line) < W - 140 else fit_font(line, FONT_BLACK, 92, W - 140)
            x = (W - fnt.getlength(line)) / 2
            for w, s0, s1 in chunk:
                on = s0 <= t
                cur = s0 <= t < s1
                col = HIGHLIGHT if cur else (255, 255, 255) if on else (255, 255, 255, 150)
                yy = 1250 - (14 if cur else 0)
                d.text((x, yy), w, font=fnt, fill=col, stroke_width=9, stroke_fill=(20, 10, 40))
                x += fnt.getlength(w + " ")

        # Progress bar + brand
        d = ImageDraw.Draw(frame)
        d.rounded_rectangle((60, 120, 60 + (W - 120) * t / total, 136), 8, fill=(255, 255, 255))
        d.text((W // 2, 1560), "WHAT · WHY · HOW", font=brand_font, fill=(255, 255, 255, 200), anchor="mm")

        ff.stdin.write(frame.convert("RGB").tobytes())
        if f % 300 == 0:
            print(f"frame {f}/{n_frames}", flush=True)

    ff.stdin.close()
    ff.wait()
    print("done:", out_mp4, f"{total:.1f}s")


if __name__ == "__main__":
    main(sys.argv[1])
