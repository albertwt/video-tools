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

## Setup
`setup.sh` installs `faster-whisper` and pre-downloads the model. The cloud environment runs it
at the start of each session. On a restricted network, Hugging Face hosts must be allowed
(see the skill's SKILL.md).
