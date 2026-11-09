#!/usr/bin/env python3
"""Look at a vertical video before placing captions.

  python3 inspect.py sheet <video> <out.jpg> [t1 t2 ...]
      Frames at the given times (default: every 1s) with a 10%-height grid, so you can read
      where the face, on-screen overlays and the hook sit as fractions of the frame height.

  python3 inspect.py window <video> <x> <y> <w> <h> [--bright 200 | --dark 40]
      When is an overlay on screen? Averages a small region per frame and prints the time
      range where it is brighter (white card) or darker (black card) than the threshold.
      Coordinates are in output pixels (1080x1920).
"""
import subprocess, sys
import numpy as np
from PIL import Image, ImageDraw

def dur(v):
    return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", v],
                                capture_output=True, text=True).stdout)

def frame(v, t, w=216):
    png = subprocess.run(["ffmpeg", "-v", "error", "-ss", str(t), "-i", v, "-frames:v", "1",
                          "-vf", f"scale={w}:-2", "-f", "image2pipe", "-vcodec", "png", "-"],
                         capture_output=True, check=True).stdout
    import io; return Image.open(io.BytesIO(png)).convert("RGB")

if sys.argv[1] == "sheet":
    v, out = sys.argv[2], sys.argv[3]
    ts = [float(x) for x in sys.argv[4:]] or [float(i) for i in range(int(dur(v)) + 1)]
    ims = []
    for t in ts:
        im = frame(v, t); d = ImageDraw.Draw(im); W, H = im.size
        for k in range(1, 10):
            d.line([(0, H * k / 10), (W, H * k / 10)], fill=(255, 230, 0), width=1)
            d.text((2, H * k / 10 - 11), f".{k}", fill=(255, 230, 0))
        d.text((4, 4), f"{t:.1f}s", fill=(255, 255, 0))
        ims.append(im)
    cols = min(8, len(ims)); rows = (len(ims) + cols - 1) // cols; W, H = ims[0].size
    s = Image.new("RGB", (cols * (W + 4), rows * (H + 4)))
    for i, im in enumerate(ims): s.paste(im, ((i % cols) * (W + 4), (i // cols) * (H + 4)))
    s.save(out); print(out)

elif sys.argv[1] == "window":
    v = sys.argv[2]; x, y, w, h = map(int, sys.argv[3:7])
    mode, thr = ("bright", 200.0)
    if "--dark" in sys.argv: mode, thr = "dark", float(sys.argv[sys.argv.index("--dark") + 1])
    if "--bright" in sys.argv: thr = float(sys.argv[sys.argv.index("--bright") + 1])
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", v, "-vf",
                          f"fps=30,scale=1080:1920,crop={w}:{h}:{x}:{y},scale=32:8,format=gray",
                          "-f", "rawvideo", "-"], capture_output=True, check=True).stdout
    m = np.frombuffer(raw, np.uint8).reshape(-1, 256).mean(1)
    hit = m > thr if mode == "bright" else m < thr
    idx = np.flatnonzero(hit)
    if not len(idx): print("not found"); sys.exit(0)
    # report contiguous runs
    runs, s0 = [], idx[0]
    for a, b in zip(idx, idx[1:]):
        if b != a + 1: runs.append((s0, a)); s0 = b
    runs.append((s0, idx[-1]))
    for a, b in runs:
        if b - a >= 3: print(f"on screen {a / 30:.2f}s - {(b + 1) / 30:.2f}s")
