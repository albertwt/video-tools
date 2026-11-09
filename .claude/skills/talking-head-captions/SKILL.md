---
name: talking-head-captions
description: Burn word-timed phrase captions into a vertical (9:16) talking-head video for TikTok / IG Reels, using free local Whisper. Places captions in a band that avoids the speaker's face, on-screen overlays (screenshots, odds strips, hook text) and the TikTok/IG UI, moving them while an overlay is up. Use when someone says "caption this video", "add captions/subtitles", "auto captions", or "caption it like the Grizzlies one". Not for footage with no speech (game clips, b-roll) and not for full edits with cuts or animated graphics.
argument-hint: [path to the video]
---

# Talking-head captions

Input: one vertical video of someone talking, usually already edited in a phone app (hook text, screenshots).
Output: the same video with bold 2-4 word captions timed to the speech, placed so nothing important is covered.

Scripts (in `scripts/`, run with `python3`):
- `transcribe.py <video> <out.json> [--model large-v3]`: local Whisper, word timestamps
- `inspect.py sheet <video> <out.jpg> [times]`: frames with a 10% height grid
- `inspect.py window <video> x y w h [--bright 200|--dark 40]`: when an overlay is on screen
- `caption.py <video> <transcript.json> <config.json> <out.mp4>`: render (config keys documented at the top of the file)

## Setup (once per machine or cloud session)
- Needs `ffmpeg`, Python 3.10+, `pillow`, `numpy`, `faster-whisper`. Check first and **ask before installing**: `python3 -m pip install faster-whisper`.
- The first transcription downloads the Whisper model (~1.5 GB for `large-v3`; `medium`/`small` are smaller and fine for clear mic audio).
- **Cloud sessions with limited network:** the model comes from Hugging Face. Allowed hosts needed: `huggingface.co`, `us.aws.cdn.hf.co`, `cdn-lfs.hf.co`, `cdn-lfs-us-1.hf.co`, `cdn-lfs.huggingface.co`, `cas-bridge.xethub.hf.co`, `cas-server.xethub.hf.co`. `transcribe.py` sets `HF_HUB_DISABLE_XET=1` to use the plain CDN. A blocked host shows up as `connect_rejected` / `403` from the proxy, not as a Whisper error.

## Workflow
1. **Probe:** `ffprobe` for size, duration and rotation. Expect 1080x1920. If there is no speech, stop and say this skill doesn't fit.
2. **Look before placing anything:** `inspect.py sheet` at ~1s steps, then READ the image. Note as height fractions: the face, every overlay (and roughly when it appears), the hook text.
3. **Time each overlay** that could collide with captions: `inspect.py window` on a small region inside it (white cards: `--bright 200`, dark cards: `--dark 40`). It prints exact on/off times.
4. **Transcribe:** `transcribe.py`. Show the user the transcript and ask about misheard words BEFORE rendering. Split scores and decimals ("6 -0", "38 .5") are re-joined automatically. Put the rest in `fixes` as whole words: a dropped dot ("500" → ".500") or a dropped small word ("strength schedule" → "strength of schedule", which the user confirmed). Captions should match what was said; only fix mishearings, don't clean up the user's speech.
5. **Pick the caption band:** the region that stays clear of the face, every overlay and the platform UI for the most time. Default `y≈0.73` (over the chest). For each overlay that crosses that band, add an `avoid` entry that moves captions just past it for its time window (e.g. odds strip at 0.67-0.74 → captions at `0.78` while it's up).
6. **Write `config.json` and render** with `caption.py`. Fix any `WARNING ... too wide` (lower `max_chars` or `size`).
7. **Verify on frames** (`inspect.py sheet` on the output, including one frame inside every `avoid` window): nothing covers the face, an overlay's text, or the hook; captions are inside the safe zones below; the first and last words are captioned. Fix and re-render before showing.
8. **Deliver:** send the file, list the text fixes you made, and flag anything you're unsure of (a word Whisper may have misheard, a hook in the bottom UI zone).

## Safe zones (approximate; they vary by phone and app version)
| Zone (fraction of height) | What's there | Rule |
|---|---|---|
| 0.00-0.10 | TikTok Following/For You tabs | no captions or hook |
| 0.78-1.00 | username, description, sound bar | no captions; warn if the user's hook sits here |
| right ~12%, 0.45-0.78 | like/comment/share buttons | keep captions centered, never right-aligned |
Tell the user to confirm in the platform's upload preview.

## Style (the user's preference)
- Bold white Montserrat (weight 800) on a dark rounded box (opacity ~200/255), centered, one line, 2-4 words.
- Numbers in yellow (#FFD84D) so the stats stand out.
- Captions are back to back: each stays up until the next phrase starts. New chunk on a pause > 0.15s or the end of a sentence.
- Keep the original audio; no music or sound effects unless asked.

## Lessons from past videos
- **Hook text belongs high up** (~0.30, above the head), not at the bottom where TikTok's description covers it. On screen for 2.5-3 seconds; under ~2 seconds people can't read it. Suggest the change; the user makes it in their app.
- **Sequence:** if the user is changing their own edit (hook, timing), they export that FIRST, then caption. Burned-in captions don't survive re-editing.
- **Re-exports:** `transcribe.py` stores an `audio_md5` and skips work when the audio is identical. Still re-run `inspect.py window` for overlays, since visuals may have moved.
- **Don't cover data:** the first render put a caption over the bottom row of an odds strip. Always sample a frame inside each overlay window.
- **Phrase splitting:** auto chunks split at punctuation and pauses first, then cut long phrases into even pieces. Splitting purely on word count gave orphans like "pretty / fair.". Set `starts` by hand only if a break still reads badly.
- **Whisper on a phone mic is reliable** for this kind of content. `large-v3` got 78/78 words with only formatting fixes needed.

## Worked example (the Grizzlies video)
```json
{
  "y": 0.729, "size": 70,
  "fixes": {"strength schedule": "strength of schedule", "500": ".500"},
  "avoid": [{"from": 8.83, "to": 11.53, "y": 0.779}]
}
```
The odds strip covered y 0.67-0.74 from 8.83s to 11.53s (found with `inspect.py window <video> 160 1300 760 60 --bright 200`). The hook was moved to y≈0.30 by the user.
