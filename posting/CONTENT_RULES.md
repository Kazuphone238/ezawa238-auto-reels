# EZAWA238 Instagram content rules

## Current visual template — effective October 23, 2026

The user explicitly replaced the old two-statue video for ALL future posts.
Use `assets/approved_dj_yokai.mp4`, identified by `posting/visual_template.json`,
as the visual for both Reels and Stories. This is the approved 15-second
DJ/yokai animation with rotation, zoom and frame-outs. Newly supplied files
are audio sources unless the user expressly requests a visual change.
Never select the retired two-statue video for a new post. Preserve historical
published videos and state records; do not republish or delete them.

## Prepare and register each song

Combine the supplied music with the approved DJ visual; preserve the user's
chosen audio segment. Verify full decoding, duration, audio presence, and
beginning/middle/end images. Set `visual_template: approved_dj_yokai`,
`visual_verified: true`, the template SHA-256, final SHA-256 and source IDs.
Bind `custom_approval.sha256` to that exact final artifact and record the
user's visual selection in `custom_approval.reason`.

The DJ visual has no burned-in BPM label. Never copy 128 BPM or claim an
unverified tempo. Record unresolved BPM honestly and leave BPM out of the
video and caption. `custom_approval.no_bpm_text_verified: true` requires
visual review and a caption without BPM. Do not use the old STONE GROOVE
overlay renderer, which was calibrated for the retired statue template.

A chat acknowledgement is not a booking. Registration is complete only when
the final media and queue entry exist on main and have been read back.
The existing daily Reel job is scheduled at 17:30 Asia/Tokyo; Story follows
the successful Reel. GitHub Actions start times can be delayed.
Do not change successful or uncertain publication records to force a retry.

## October 23 queued deliverable

`dj-yokai-20261023`: the approved 15-second DJ animation with the first
15 seconds of 1000000325.mp4 and a short ending fade. Intended for the
October 23 Reel and Story. Remote registration remains pending until the
media upload and commit have succeeded.
