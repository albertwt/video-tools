#!/usr/bin/env python3
"""Kon Knueppel reel, draft 1: punch-in on the court, 4 timed captions, original arena audio."""
import subprocess, os
from PIL import Image, ImageDraw, ImageFont

SRC = "/root/.claude/uploads/cd106a21-0c49-573d-9b40-d6e22f38828b/d85c05bc-IMG_5826.MOV"
FONT = os.path.expanduser("~/.claude/skills/famous-reel-editor/assets/fonts/Montserrat-VariableFont_wght.ttf")
EMOJI = "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf"
D = "/home/user/reels/kon"
CAP = f"{D}/edit/caps"; os.makedirs(CAP, exist_ok=True); os.makedirs(f"{D}/renders", exist_ok=True)
W, H, FPS = 1080, 1920, 30
DUR = 9.88
# source decodes as 1080x1920 (rotation applied). 1.4x punch-in: hoop at top, free-throw line + players in the middle
CROP = "crop=864:1536:40:300"

CAPS = [  # (text, start, end); "\n" = hand-set line break
    ("went to see\nkon knueppel", 0.0, 2.5),
    ("he got injured\n6 min in \U0001F62D", 2.5, 5.0),
    ("caught his only\npoints of the szn \U0001F480", 5.0, 8.5),
    ("get well soon \U0001F64F", 8.5, DUR),
]

def font(size):
    f = ImageFont.truetype(FONT, size)
    try: f.set_variation_by_axes([800])
    except Exception: pass
    return f

def wrap(d, text, f, maxw):
    lines, cur = [], ""
    for w in text.split():
        t = (cur + " " + w).strip()
        if d.textlength(t, font=f) <= maxw: cur = t
        else: lines.append(cur); cur = w
    lines.append(cur); return lines

def caption(i, text, y=250, size=76):  # y=250: below TikTok's top tabs, above the hoop, far from the bottom UI
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(img); f = font(size)
    emoji = None
    if text and ord(text[-1]) > 0x1F000:  # trailing emoji -> render in color after the last line
        ch = text[-1]; text = text[:-1].strip()
        e = ImageFont.truetype(EMOJI, 109)  # Noto Color Emoji only renders at 109px
        em = Image.new("RGBA", (136, 128), (0, 0, 0, 0))
        ImageDraw.Draw(em).text((0, 0), ch, font=e, embedded_color=True)
        emoji = em.resize((int(136 * size / 100), int(128 * size / 100)), Image.LANCZOS)
    lines = text.split("\n")
    cy = y
    for li, ln in enumerate(lines):
        bx = d.textbbox((0, 0), ln, font=f); tw, th = bx[2] - bx[0], bx[3] - bx[1]
        extra = emoji.width + 16 if (emoji and li == len(lines) - 1) else 0
        pad = 22; x = (W - tw - extra) // 2
        d.rounded_rectangle([x - pad, cy - pad, x + tw + extra + pad, cy + th + pad], radius=20, fill=(0, 0, 0, 205))
        d.text((x - bx[0], cy - bx[1]), ln, font=f, fill=(255, 255, 255))
        if extra:
            img.alpha_composite(emoji, (x + tw + 16, cy + th // 2 - emoji.height // 2))
        cy += th + pad * 2 + 12
    p = f"{CAP}/c{i}.png"; img.save(p); return p

paths = [caption(i, t) for i, (t, _, _) in enumerate(CAPS)]
cmd = ["ffmpeg", "-v", "error", "-y", "-i", SRC]
for p in paths: cmd += ["-loop", "1", "-t", str(DUR), "-i", p]
chain = f"[0:v]{CROP},fps={FPS},scale={W}:{H}:flags=lanczos,setsar=1,format=yuv420p[v0]"
last = "v0"
for i, (_, a, b) in enumerate(CAPS, start=1):
    chain += f";[{last}][{i}:v]overlay=0:0:enable='between(t,{a},{b - 0.001})'[v{i}]"; last = f"v{i}"
chain += f";[0:a:0]aresample=48000,afade=t=out:st={DUR - 0.6}:d=0.6[a]"
cmd += ["-filter_complex", chain, "-map", f"[{last}]", "-map", "[a]", "-t", str(DUR),
        "-c:v", "libx264", "-crf", "18", "-preset", "medium", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", f"{D}/renders/kon-FINAL.mp4"]
subprocess.run(cmd, check=True); print("done")
