import unittest
from daily_instagram import validate_content
from check_instagram_connection import CheckError

class CustomVideoTests(unittest.TestCase):
    def item(self):
        return dict(visual_template='approved_dj_yokai', visual_verified=True,
                    sha256='reviewed-video', caption='DJ party',
                    custom_approval=dict(sha256='reviewed-video', reason='User requested this finished DJ video', no_bpm_text_verified=True))

    def test_explicit_custom_video(self):
        validate_content(self.item())

    def test_wrong_video_or_unreviewed_exception_is_rejected(self):
        for change in [dict(sha256='different'), dict(visual_verified=False), dict(custom_approval={}), dict(caption='128 BPM'), dict(visual_template='raw_upload')]:
            with self.subTest(change=change), self.assertRaises(CheckError):
                validate_content(dict(self.item(), **change))

    def test_retired_duet_is_rejected(self):
        with self.assertRaises(CheckError):
            validate_content(dict(self.item(), visual_template='approved_duet'))
