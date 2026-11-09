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
They have hard-coded paths and times from those clips. Once there are 2-3 more, turn the pattern
into a `game-clip-editor` skill.

## Setup
`setup.sh` installs `faster-whisper` and pre-downloads the model. The cloud environment runs it
at the start of each session. On a restricted network, Hugging Face hosts must be allowed
(see the skill's SKILL.md).
