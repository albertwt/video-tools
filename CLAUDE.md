# video-tools: how to handle a new request

Read the README below first: its **Lessons learned** apply to every video.

## What the user will say, and what to do
| They say | Do |
|---|---|
| "caption this" + a clip | Use the `talking-head-captions` skill. |
| "new video, use the <X> brief as a template, here's my brief" | Read `briefs/<X>.md` for its structure and its "How it actually went" notes, then follow the user's brief. Before editing, push back on gaps: voiceover too short for the target length, missing footage for a beat, a DON'T the recording breaks. |
| "new video" with no brief | Ask for one, pointing to `briefs/_TEMPLATE.md`. Don't guess the concept. |
| a game clip, no voiceover | Start from the closest script in `game-clips/`. |

## Getting files in
- **Attached in chat:** use them directly.
- **Google Drive link:** the Drive connector can't pull big videos (60 MB failed). Ask the user to set the file
  to "Anyone with the link", then download it with
  `curl -L "https://drive.usercontent.google.com/download?id=<FILE_ID>&confirm=t" -o <name>`.
- Put inputs in the scratchpad, one new folder per video, not in the repo.

## Delivering
- Sessions are temporary. Send every finished render to the user with SendUserFile; don't leave it only on disk.
- Never commit videos or audio to this repo.
- After a video that worked, offer to save its brief to `briefs/` with a "How it actually went" section,
  and add new lessons to the README.

@README.md
