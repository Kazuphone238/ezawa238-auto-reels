import unittest
from track_bpm import validate_bpm
from check_instagram_connection import CheckError

class BpmTests(unittest.TestCase):
    def item(self):
        return dict(bpm=140, bpm_verified=True, bpm_evidence='Measured audio; verified beat grid', bpm_overlay_verified=True, sha256='new-video', bpm_video_sha256='new-video', caption='STONE GROOVE / 140 BPM')
    def test_verified(self):
        validate_bpm(self.item())
    def test_stale_caption_or_video_and_unverified_are_rejected(self):
        for change in [dict(caption='STONE GROOVE / 128 BPM'), dict(bpm_video_sha256='old-video'), dict(bpm_verified=False), dict(bpm_overlay_verified=False), dict(bpm_evidence=''), dict(bpm=float('nan')), dict(bpm=True)]:
            with self.subTest(change=change), self.assertRaises(CheckError):
                validate_bpm(dict(self.item(), **change))
