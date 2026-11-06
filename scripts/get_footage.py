"""Download one free vertical HD clip per scene from Pexels (needs PEXELS_API_KEY).

Usage: PEXELS_API_KEY=... python3 scripts/get_footage.py videos/001-baby-memories remotion/public
Adds "media" to build/timeline.json for each scene that got a clip.
"""
import json
import os
import sys
import urllib.parse
import urllib.request
from pathlib import Path

KEY = os.environ["PEXELS_API_KEY"]


def get(url):
    req = urllib.request.Request(url, headers={"Authorization": KEY, "User-Agent": "video-factory"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def best_file(video):
    files = [f for f in video["video_files"] if f.get("height") and f["file_type"] == "video/mp4"]
    portrait = [f for f in files if f["height"] >= f["width"] and f["height"] <= 2000]
    pool = portrait or files
    return max(pool, key=lambda f: f["height"]) if pool else None


def main(folder, public):
    folder, public = Path(folder), Path(public)
    tl_path = folder / "build" / "timeline.json"
    tl = json.loads(tl_path.read_text())
    used = set()
    for i, sc in enumerate(tl["scenes"]):
        q = sc.get("footage")
        if not q:
            continue
        for orient in ("portrait", "landscape"):
            res = get("https://api.pexels.com/videos/search?" + urllib.parse.urlencode(
                {"query": q, "orientation": orient, "per_page": 10, "size": "medium"}))
            vids = [v for v in res.get("videos", []) if v["id"] not in used and v["duration"] >= 4]
            if vids:
                break
        if not vids:
            print("no clip for", q)
            continue
        v = vids[0]
        f = best_file(v)
        name = f"clip_{i}.mp4"
        req = urllib.request.Request(f["link"], headers={"User-Agent": "video-factory"})
        with urllib.request.urlopen(req, timeout=120) as r, open(public / name, "wb") as out:
            out.write(r.read())
        used.add(v["id"])
        sc["media"], sc["mediaType"] = name, "video"
        sc["credit"] = f'{v["user"]["name"]} on Pexels ({v["url"]})'
        print(f"scene {i}: {q} -> {v['url']}")
    tl_path.write_text(json.dumps(tl, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
