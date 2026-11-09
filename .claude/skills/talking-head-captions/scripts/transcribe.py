#!/usr/bin/env python3
"""Word-level transcript with local Whisper (faster-whisper). Free, offline after the first model download.

Usage:  python3 transcribe.py <video> <out.json> [--model large-v3|medium|small] [--language en]
Output: {"language": "en", "audio_md5": "...", "words": [{"text","start","end"}, ...]}

Audio is decoded with ffmpeg and passed to Whisper as a numpy array. This sidesteps a PyAV
version mismatch in faster-whisper's own loader ("open() got an unexpected keyword argument
'metadata_errors'"). audio_md5 lets you reuse a transcript when a re-export has identical audio.
"""
import argparse, hashlib, json, os, subprocess, sys

ap = argparse.ArgumentParser()
ap.add_argument("video"); ap.add_argument("out")
ap.add_argument("--model", default="large-v3")
ap.add_argument("--language", default="en")
a = ap.parse_args()

os.environ.setdefault("HF_HUB_DISABLE_XET", "1")  # plain CDN download; fewer hosts to allow on restricted networks
import numpy as np
from faster_whisper import WhisperModel

raw = subprocess.run(["ffmpeg", "-v", "error", "-i", a.video, "-vn", "-ac", "1", "-ar", "16000", "-f", "f32le", "-"],
                     check=True, capture_output=True).stdout
md5 = hashlib.md5(raw).hexdigest()
if os.path.exists(a.out):
    old = json.load(open(a.out))
    if old.get("audio_md5") == md5:
        print(f"cached (identical audio): {a.out}"); sys.exit(0)

model = WhisperModel(a.model, device="cpu", compute_type="int8")
segs, _ = model.transcribe(np.frombuffer(raw, dtype=np.float32), language=a.language, word_timestamps=True)
words = []
for s in segs:
    for w in (s.words or []):
        start, end = round(w.start, 3), round(w.end, 3)
        if end <= start: end = round(start + 0.12, 3)  # repair zero-width words (caption would flash 0 frames)
        words.append({"text": w.word.strip(), "start": start, "end": end})
json.dump({"language": a.language, "audio_md5": md5, "words": words}, open(a.out, "w"), indent=2, ensure_ascii=False)
print(f"{len(words)} words -> {a.out}")
for i, w in enumerate(words): print(i, w["start"], w["end"], w["text"])
