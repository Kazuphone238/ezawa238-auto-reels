# EZAWA238 Instagram content rules

All uploaded songs are audio sources only. Use the approved two-statue dance video for both Reels and Stories unless the user explicitly requests another visual.

Before adding an item to queue.json: combine the supplied audio with the approved_duet video; verify the full output decodes; inspect beginning, middle and end; confirm the supplied audio is present; record sha256, source_library_file_id, visual_template: approved_duet and visual_verified: true. Do not queue a raw song upload as the final visual.

The publisher rejects new queue items lacking the visual verification fields. A conversation acknowledgement does not register a queue item: registration is complete only when media and queue.json exist on main and have been read back. Existing published records must never be removed to resend a video. Upload ingestion and queue replenishment still require an execution step; they are not automatically triggered by a chat attachment.
