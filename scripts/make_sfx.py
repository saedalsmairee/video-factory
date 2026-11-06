"""Make royalty-free sound effects and a simple upbeat music bed with numpy.

Usage: python3 scripts/make_sfx.py remotion/public [seconds]
"""
import sys
import wave
from pathlib import Path

import numpy as np

SR = 48000
rng = np.random.default_rng(3)


def save(path, x):
    x = np.clip(x / (np.max(np.abs(x)) + 1e-9) * 0.9, -1, 1)
    st = np.stack([x, x], axis=1) if x.ndim == 1 else x
    with wave.open(str(path), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((st * 32767).astype(np.int16).tobytes())


def lowpass(x, a):
    y = np.zeros_like(x)
    acc = 0.0
    for i, v in enumerate(x):
        acc += a[i] * (v - acc) if hasattr(a, "__len__") else a * (v - acc)
        y[i] = acc
    return y


def whoosh(d=0.6):
    n = int(SR * d)
    t = np.linspace(0, 1, n)
    noise = rng.standard_normal(n)
    sweep = 0.02 + 0.5 * np.sin(np.pi * t) ** 2
    y = lowpass(noise, sweep) - lowpass(noise, sweep * 0.15)
    return y * np.sin(np.pi * t) ** 1.5


def pop(d=0.18):
    t = np.arange(int(SR * d)) / SR
    f = 900 * np.exp(-t * 25) + 250
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 28)


def music(seconds, bpm=104):
    n = int(SR * seconds)
    t = np.arange(n) / SR
    beat = 60 / bpm
    out = np.zeros(n)
    # chords: Am - F - C - G (one bar each)
    chords = [[220, 261.63, 329.63], [174.61, 220, 261.63], [196, 261.63, 329.63], [196, 246.94, 293.66]]
    bar = beat * 4
    for b in range(int(seconds / bar) + 1):
        s, e = int(b * bar * SR), min(n, int((b + 1) * bar * SR))
        if s >= n:
            break
        tt = t[s:e] - b * bar
        env = np.minimum(1, tt * 6) * np.exp(-tt * 0.5)
        for f in chords[b % 4]:
            # pluck-ish pad with a little detune for width
            out[s:e] += 0.12 * env * (np.sin(2 * np.pi * f * tt) + 0.5 * np.sin(2 * np.pi * f * 2.003 * tt))
        # bass on each beat
        for k in range(4):
            bs = s + int(k * beat * SR)
            be = min(n, bs + int(beat * SR))
            if bs >= n:
                break
            bt = np.arange(be - bs) / SR
            out[bs:be] += 0.25 * np.sin(2 * np.pi * chords[b % 4][0] / 2 * bt) * np.exp(-bt * 5)
    for k in range(int(seconds / beat)):
        s = int(k * beat * SR)
        kt = np.arange(min(int(0.25 * SR), n - s)) / SR
        out[s:s + len(kt)] += 0.7 * np.sin(2 * np.pi * (50 + 100 * np.exp(-kt * 30)) * kt) * np.exp(-kt * 12)
        h = s + int(beat / 2 * SR)
        if h < n:
            ht = np.arange(min(int(0.05 * SR), n - h)) / SR
            out[h:h + len(ht)] += 0.12 * rng.standard_normal(len(ht)) * np.exp(-ht * 90)
        if k % 2 == 1:  # clap on 2 and 4
            ct = np.arange(min(int(0.15 * SR), n - s)) / SR
            out[s:s + len(ct)] += 0.25 * rng.standard_normal(len(ct)) * np.exp(-ct * 30)
    fade = np.minimum(1, np.minimum(t / 1.0, (seconds - t) / 2.0))
    return out * fade


if __name__ == "__main__":
    out = Path(sys.argv[1])
    secs = float(sys.argv[2]) if len(sys.argv) > 2 else 60
    save(out / "whoosh.wav", whoosh())
    save(out / "pop.wav", pop())
    save(out / "music.wav", music(secs))
    print("sfx ready")
