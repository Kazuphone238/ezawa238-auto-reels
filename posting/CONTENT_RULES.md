# EZAWA238 Instagram content rules

All uploaded songs are audio sources only. Use the approved two-statue dance video for both Reels and Stories unless the user explicitly requests another visual.

Before adding an item to queue.json: combine the supplied audio with the approved_duet video; verify the full output decodes; inspect beginning, middle and end; confirm the supplied audio is present; record sha256, source_library_file_id, visual_template: approved_duet and visual_verified: true. Do not queue a raw song upload as the final visual.

The publisher rejects new queue items lacking the visual verification fields. A conversation acknowledgement does not register a queue item: registration is complete only when media and queue.json exist on main and have been read back. Existing published records must never be removed to resend a video. Upload ingestion and queue replenishment still require an execution step; they are not automatically triggered by a chat attachment.

## Per-track BPM (required from 2026-10-22)

The approved template contains a burned-in `STONE GROOVE / 128 BPM` line. Replacing audio or changing a caption does NOT update that line. For each new song, measure the actual supplied audio, check beats across multiple sections, resolve half/double-tempo ambiguity, and record the method/result in `bpm_evidence`. Never infer BPM from a generation prompt or copy the preceding song's value. If unresolved, do not mark it verified.

After combining the song with the approved two-statue template, run `python track_bpm.py INPUT.mp4 OUTPUT.mp4 --bpm VERIFIED_VALUE --evidence 'measurement and beat-check details'`. This replaces the old title line with an opaque title strip, preserves audio without re-encoding, and keeps frame timing. Inspect beginning/middle/end and confirm audio, BPM display and full decode before registering the output. Copy the generated metadata into the queue item, set `bpm_overlay_verified: true` only after visual review, and use the new output path/hash. Preserve all existing visual verification fields. The caption must contain the same BPM.

The publisher requires `bpm`, `bpm_verified`, `bpm_evidence`, `bpm_overlay_verified`, and `bpm_video_sha256` matching the final `sha256` before claiming a new item. Reels and Stories share this verified final video. Already-published items are historical and must not be requeued. No BPM is automatically assumed correct by this renderer.
