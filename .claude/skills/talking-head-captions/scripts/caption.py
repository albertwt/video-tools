#!/usr/bin/env python3
"""Burn phrase captions (2-4 words) into a vertical talking-head video from a word transcript.

  python3 caption.py <video> <transcript.json> <config.json> <out.mp4>

config.json (every key optional):
{
  "y": 0.73,                      # default caption centre, as a fraction of frame height
  "size": 70,                     # font px at 1080 wide
  "max_words": 4, "max_chars": 24,
  "pause": 0.15,                  # a gap longer than this (s) starts a new chunk
  "fixes": {"500": ".500", "strength schedule": "strength of schedule"},  # whole-word fixes ("6 -0"/"38 .5" are auto-joined)
  "starts": [0, 4, 6],            # optional hand-set chunk start word indices (overrides auto chunking)
  "avoid": [{"from": 8.83, "to": 11.53, "y": 0.78}],               # move captions while an overlay is up
  "highlight_numbers": true,      # numbers in yellow
  "box_opacity": 200
}
Captions run back to back: each one stays up until the next chunk's first word.
"""
import json, os, re, subprocess, sys
from PIL import Image, ImageDraw, ImageFont

VIDEO, TRANS, CONF, OUT = sys.argv[1:5]
HERE = os.path.dirname(os.path.abspath(__file__))
FONT = os.path.join(HERE, "..", "assets", "fonts", "Montserrat-VariableFont_wght.ttf")
C = {"y": 0.73, "size": 70, "max_words": 4, "max_chars": 24, "pause": 0.15, "fixes": {},
     "starts": None, "avoid": [], "highlight_numbers": True, "box_opacity": 200}
C.update(json.load(open(CONF)) if os.path.exists(CONF) else {})
W, H = 1080, 1920
YELLOW = (255, 216, 77)

words = json.load(open(TRANS))["words"]
DUR = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", VIDEO],
                           capture_output=True, text=True).stdout)

def merge_number_fragments(ws):
    """Whisper splits '6-0' into '6' + '-0.' and '38.5' into '38' + '.5.'. Glue them back into one word."""
    out = []
    for w in ws:
        if out and re.match(r"^[-.]\d", w["text"]) and re.search(r"\d$", out[-1]["text"]):
            out[-1] = {"text": out[-1]["text"] + w["text"], "start": out[-1]["start"], "end": w["end"]}
        else:
            out.append(dict(w))
    return out

def apply_fixes(ws):
    """Word-level replacements, e.g. {"strength schedule": "strength of schedule", "500": ".500"}.
    Matches whole words (trailing punctuation kept); new words share the old words' time span."""
    for k, v in C["fixes"].items():
        kt, vt = k.split(), v.split()
        i = 0
        while i + len(kt) <= len(ws):
            seg = ws[i:i + len(kt)]
            core = [re.sub(r"[.,!?]+$", "", w["text"]) for w in seg]
            if core == kt:
                tail = re.search(r"[.,!?]*$", seg[-1]["text"]).group(0)
                t0, t1 = seg[0]["start"], seg[-1]["end"]; step = (t1 - t0) / len(vt)
                new = [{"text": t + (tail if j == len(vt) - 1 else ""), "start": t0 + j * step,
                        "end": t0 + (j + 1) * step} for j, t in enumerate(vt)]
                ws[i:i + len(kt)] = new; i += len(vt)
            else:
                i += 1
    return ws

words = apply_fixes(merge_number_fragments(words))

def auto_starts():
    """Split at punctuation and pauses into phrases, then cut long phrases into even pieces."""
    phrases, cur = [], [0]
    for i in range(1, len(words)):
        prev = words[i - 1]
        if prev["text"][-1:] in ".?!," or words[i]["start"] - prev["end"] > C["pause"]:
            phrases.append(cur); cur = [i]
        else:
            cur.append(i)
    phrases.append(cur)
    starts = []
    for ph in phrases:
        n = len(ph); k = -(-n // C["max_words"])
        while True:
            size = -(-n // k); pieces = [ph[j:j + size] for j in range(0, n, size)]
            if all(len(" ".join(words[x]["text"] for x in p)) <= C["max_chars"] for p in pieces) or k >= n: break
            k += 1
        starts += [p[0] for p in pieces]
    return starts

def text_of(a, b):
    return " ".join(w["text"] for w in words[a:b])

starts = C["starts"] or auto_starts()
chunks = []
for k, a in enumerate(starts):
    b = starts[k + 1] if k + 1 < len(starts) else len(words)
    t0 = words[a]["start"]; t1 = words[b]["start"] if b < len(words) else DUR
    chunks.append((text_of(a, b), t0, t1))

def y_for(t0, t1):
    for r in C["avoid"]:
        if t0 < r["to"] and t1 > r["from"]: return r["y"]
    return C["y"]

def font():
    f = ImageFont.truetype(FONT, C["size"])
    try: f.set_variation_by_axes([800])
    except Exception: pass
    return f

tmp = os.path.join(os.path.dirname(os.path.abspath(OUT)), ".caps"); os.makedirs(tmp, exist_ok=True)
paths = []
for i, (text, t0, t1) in enumerate(chunks):
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(img); f = font()
    toks = text.split(" "); sp = d.textlength(" ", font=f)
    ws = [d.textlength(t, font=f) for t in toks]; tw = sum(ws) + sp * (len(toks) - 1)
    if tw > W - 80: print(f"WARNING chunk {i} too wide ({tw:.0f}px): '{text}' - lower max_chars or size")
    asc, desc = f.getmetrics(); th = asc + desc
    x = (W - tw) / 2; y = y_for(t0, t1) * H - th / 2
    d.rounded_rectangle([x - 26, y - 14, x + tw + 26, y + th + 14], radius=18, fill=(0, 0, 0, C["box_opacity"]))
    for t, w in zip(toks, ws):
        col = YELLOW if (C["highlight_numbers"] and re.search(r"\d", t)) else (255, 255, 255)
        d.text((x, y), t, font=f, fill=col); x += w + sp
    p = os.path.join(tmp, f"c{i:03d}.png"); img.save(p); paths.append(p)
    print(f"{t0:6.2f}-{t1:6.2f}  y={y_for(t0, t1):.2f}  {text}")

cmd = ["ffmpeg", "-v", "error", "-y", "-i", VIDEO]
for p in paths: cmd += ["-loop", "1", "-t", f"{DUR}", "-i", p]
chain, last = "[0:v]scale=1080:1920,setsar=1,format=yuv420p[v0]", "v0"
for i, (_, a, b) in enumerate(chunks, start=1):
    chain += f";[{last}][{i}:v]overlay=0:0:enable='between(t,{a:.3f},{b - 0.001:.3f})'[v{i}]"; last = f"v{i}"
cmd += ["-filter_complex", chain, "-map", f"[{last}]", "-map", "0:a:0?", "-t", f"{DUR}",
        "-c:v", "libx264", "-crf", "18", "-preset", "medium", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", OUT]
subprocess.run(cmd, check=True); print("done ->", OUT)
