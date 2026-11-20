# video-tools
creating social media content captions via claude 

Claude will pick this repo and load the skill in here each time I need "talking-head-captions"

## Skills (load automatically when a Claude Code session starts with this repo)
- `.claude/skills/talking-head-captions/`: word-timed captions for vertical talking-head videos with
  free local Whisper. Avoids the face, on-screen overlays and the TikTok/IG UI.
  Say: "caption this video" and attach the clip.

## Game clips (reference scripts, not a skill yet)
`game-clips/` holds the ffmpeg + Python scripts behind two finished reels:
- `big-miss.py`: punch-in, captions, half-speed replay with a freeze on the miss, comment CTA
- `kon-knueppel.py`: crowd clip, punch-in, timed captions with color emoji, arena audio only

Run: `python3 game-clips/<script>.py <clip.mov> <output-folder>`. The output folder needs `edit/` inside it;
the video lands in `<output-folder>/renders/`. They use the font in the caption skill, so nothing else is needed.
`big-miss.py` adds music only if `MUSIC=/path/to/licensed-track.m4a` is set.
Crop boxes, cut times and caption lines are still hard-coded for those two clips.

**Next:** once there are 2-3 more game clips, turn this pattern into `.claude/skills/game-clip-editor/`
in this repo. Inputs per clip: the video + what happens and roughly when + the caption lines (or the story,
and Claude drafts them). No voiceover needed.

## Briefs
`briefs/` holds video briefs that worked, to copy for the next video. Start with
`briefs/ball-comparison-rock-vs-evo.md`: files, concept, format, a beat table (visual + voiceover),
edit rules and a DON'T list.

## Lessons learned (read before editing a new video)
**Footage**
- Front-camera clips are **mirrored**. Flip them (`hflip`) and check that brand text on the ball/shirt reads
  correctly. Upside-down text is not mirroring; mirroring applies to the whole clip at once.
- A **3:4 photo in a 9:16 frame** crops anything wide (two balls side by side). Show the photo full-width with a
  blurred, darkened copy filling above and below, so push-ins keep both subjects in frame.
- Phone clips are often 4K / 60fps HEVC: plenty of room to punch in 1.2-1.4x on the action.

**Voiceover-driven edits**
- Transcribe the voiceover first; its word timings decide every cut.
- Long pauses: cut each to ~0.2s (keep ~0.5s before the payoff line). 42s became 26s with every word kept.
- **Removing a phrase can blur the join** ("price suggests it is" was heard as "such as it is"). Leave a short
  breath at the cut and re-check that spot with Whisper before rendering.
- Slow a close-up slightly (0.8x on 60fps footage looks smooth) rather than repeating footage to fill a line.

**Captions and text**
- Captions go where nothing important is: check frames for every shot, not just one. When the subject moves
  into the caption band (ball lifted toward the lens), move captions for that time window (`avoid` in config).
- TikTok covers roughly the top 10% (tabs) and bottom 22% (username, description). Hook text goes high
  (~0.15-0.30 of the height), on screen for 2.5-3s.
- Keep a CTA on one line (`keep_together`); overlong captions shrink to fit.

**Content**
- Check numbers and prices before they go on screen; a wrong stat takes over the comments.
- Honest > hype: no fake reactions, no effects that undercut what you're saying.

## Setup
`setup.sh` installs `faster-whisper` and pre-downloads the model. The cloud environment runs it
at the start of each session. On a restricted network, Hugging Face hosts must be allowed
(see the skill's SKILL.md).
