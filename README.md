# video-factory

Free, faceless video pipeline for **What Why and How** (YouTube @WhatWhyandHow0009, Instagram whatwhyandhow0009).

## Make a short

```bash
pip install -r requirements.txt   # plus ffmpeg
scripts/get_voice.sh              # free Piper voice, once
python3 scripts/make_short.py videos/001-baby-memories
```

Each video lives in `videos/<number>-<slug>/`:

- `script.json`: title, description, and scenes (headline, sub line, colours, narration)
- `sources.md`: fact sources and proof the topic performs

The MP4 is written into that folder (not committed, since videos are large).
