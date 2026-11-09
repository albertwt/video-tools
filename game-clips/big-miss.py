#!/usr/bin/env python3
"""Big-miss reel: punch-in, captions, slow-mo replay with freeze, CTA. ffmpeg + PIL only."""
import subprocess, os
from PIL import Image, ImageDraw, ImageFont, ImageFilter

SRC = "/root/.claude/uploads/cd106a21-0c49-573d-9b40-d6e22f38828b/1974fdc4-big_miss_oop-1.mov"
FONT = os.path.expanduser("~/.claude/skills/famous-reel-editor/assets/fonts/Montserrat-VariableFont_wght.ttf")
MUSIC = os.path.expanduser("~/.claude/skills/famous-reel-editor/assets/bg-music.m4a")
D = "/home/user/reels/big-miss"
CAP = f"{D}/edit/caps"; os.makedirs(CAP, exist_ok=True); os.makedirs(f"{D}/renders", exist_ok=True)
W, H, FPS = 1080, 1920, 30
RED, ACC = (255, 90, 90), (47, 224, 129)

# crops in source pixels (2160x3840): wide punch-in keeps hoop + players, replay zooms on shooter + rim
WIDE = "crop=1620:2880:120:270"
TIGHT = "crop=1224:2176:180:780"

def font(size):
    f = ImageFont.truetype(FONT, size)
    try: f.set_variation_by_axes([900])
    except Exception: pass
    return f

def caption(name, lines, y=300, size=96, color=(255, 255, 255), tag=None):
    """lines: list of str. Renders a black rounded box with white UPPERCASE text."""
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(img); f = font(size)
    cy = y
    for ln in lines:
        ln = ln.upper(); bx = d.textbbox((0, 0), ln, font=f); tw, th = bx[2] - bx[0], bx[3] - bx[1]
        pad = 26; x = (W - tw) // 2
        d.rounded_rectangle([x - pad, cy - pad, x + tw + pad, cy + th + pad], radius=22, fill=(0, 0, 0, 215))
        d.text((x - bx[0], cy - bx[1]), ln, font=f, fill=color)
        cy += th + pad * 2 + 14
    if tag:
        tf = font(44); bx = d.textbbox((0, 0), tag, font=tf)
        d.rounded_rectangle([40, 90, 40 + bx[2] + 40, 90 + bx[3] + 30], radius=14, fill=RED + (255,))
        d.text((60 - bx[0], 105 - bx[1]), tag, font=tf, fill=(255, 255, 255))
    p = f"{CAP}/{name}.png"; img.save(p); return p

def run(cmd):
    print(" ".join(cmd[:6]), "..."); subprocess.run(cmd, check=True)

# ---- captions (times are relative to each segment's own start) ----
A_caps = [  # segment A: source 0.5-6.9, real speed (6.4s)
    (caption("a1", ["1-on-1", "in transition"], size=110), 0.0, 3.8),
    (caption("a2", ["so I pull up"], size=110), 3.8, 5.8),
    (caption("a3", ["brick."], size=150, color=RED), 5.8, 6.4),
]
REPLAY_TAG = "REPLAY"
B_caps = [  # segment B: source 3.9-6.3 at 0.5x (4.8s) + 0.9s freeze on the miss
    (caption("b1", ["should've", "attacked"], size=110, tag=REPLAY_TAG), 0.0, 2.4),
    (caption("b2", ["make the defense", "react"], size=84, tag=REPLAY_TAG), 2.4, 4.8),
    (caption("b3", ["not this."], size=140, color=RED, tag=REPLAY_TAG), 4.8, 5.7),
]
C_caps = [  # segment C: source 6.9-8.05 real speed (1.15s) + 1.9s freeze
    (caption("c1", ["comment your", "worst shot", "selection"], size=96), 0.0, 3.05),
]

def segment(out, vf_core, caps, dur, extra_in=None):
    """Render one silent segment with caption overlays."""
    inputs = ["-i", SRC] if extra_in is None else extra_in
    cmd = ["ffmpeg", "-v", "error", "-y"] + inputs
    for p, _, _ in caps: cmd += ["-loop", "1", "-t", str(dur), "-i", p]
    chain = f"[0:v]{vf_core},fps={FPS},scale={W}:{H}:flags=lanczos,setsar=1,format=yuv420p[v0]"
    last = "v0"
    for i, (_, a, b) in enumerate(caps, start=1):
        chain += f";[{last}][{i}:v]overlay=0:0:enable='between(t,{a},{b - 0.001})'[v{i}]"; last = f"v{i}"
    cmd += ["-filter_complex", chain, "-map", f"[{last}]", "-t", str(dur), "-an",
            "-c:v", "libx264", "-crf", "18", "-preset", "medium", "-pix_fmt", "yuv420p", out]
    run(cmd)

# A: real speed, wide punch-in
segment(f"{D}/edit/A.mp4", f"trim=0.5:6.9,setpts=PTS-STARTPTS,{WIDE}", A_caps, 6.4)
# B: slow-mo replay (0.5x) tight on shooter, then freeze on the miss for 0.9s
segment(f"{D}/edit/B.mp4",
        f"trim=3.9:6.3,setpts=2*(PTS-STARTPTS),{TIGHT},tpad=stop_mode=clone:stop_duration=0.9",
        B_caps, 5.7)
# C: reaction, wide, then freeze for the CTA
segment(f"{D}/edit/C.mp4",
        f"trim=6.9:8.05,setpts=PTS-STARTPTS,{WIDE},tpad=stop_mode=clone:stop_duration=1.9",
        C_caps, 3.05)

# ---- audio: original gym sound under A and C, silence under the replay, music bed throughout ----
TOTAL = 6.4 + 5.7 + 3.05
afc = (
    "[0:a]atrim=0.5:6.9,asetpts=PTS-STARTPTS,aresample=48000[aA];"
    "anullsrc=r=48000:cl=stereo,atrim=0:5.7[aB];"
    "[0:a]atrim=6.9:8.05,asetpts=PTS-STARTPTS,aresample=48000,apad=pad_dur=1.9[aC];"
    "[aA][aB][aC]concat=n=3:v=0:a=1,aformat=channel_layouts=stereo,volume=1.0[orig];"
    f"[1:a]atrim=0:{TOTAL},asetpts=PTS-STARTPTS,aresample=48000,aformat=channel_layouts=stereo,"
    f"volume=0.35,afade=t=out:st={TOTAL - 1.2}:d=1.2[mus];"
    "[orig][mus]amix=inputs=2:normalize=0:duration=first,alimiter=limit=0.891:level=false[aout]"
)
run(["ffmpeg", "-v", "error", "-y", "-i", SRC, "-i", MUSIC, "-filter_complex", afc,
     "-map", "[aout]", "-t", str(TOTAL), "-c:a", "aac", "-b:a", "192k", f"{D}/edit/audio.m4a"])

# ---- join video (concat filter, sample-accurate) + mux audio ----
run(["ffmpeg", "-v", "error", "-y", "-i", f"{D}/edit/A.mp4", "-i", f"{D}/edit/B.mp4", "-i", f"{D}/edit/C.mp4",
     "-i", f"{D}/edit/audio.m4a",
     "-filter_complex", "[0:v][1:v][2:v]concat=n=3:v=1:a=0[v]",
     "-map", "[v]", "-map", "3:a", "-c:v", "libx264", "-crf", "18", "-preset", "medium",
     "-pix_fmt", "yuv420p", "-c:a", "copy", "-shortest", "-movflags", "+faststart",
     f"{D}/renders/big-miss-FINAL.mp4"])
print("done")
