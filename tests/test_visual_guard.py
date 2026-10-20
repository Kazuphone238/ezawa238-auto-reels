import unittest
from unittest.mock import patch
from datetime import datetime
import daily_instagram as d

class Clock:
    @staticmethod
    def now(tz):
        return datetime.fromisoformat('2026-10-20T22:00:00+09:00')

class VisualGuardTests(unittest.TestCase):
    def test_unverified_upload_never_reaches_instagram_or_claims_state(self):
        with patch.dict(d.os.environ,{'GITHUB_EVENT_NAME':'schedule'},clear=True),patch.object(d,'datetime',Clock),patch.object(d,'check'),patch.object(d,'read_state',return_value=({'items':{}},'sha')),patch.object(d.Path,'read_text',return_value='[{"id":"raw-song"}]'),patch.object(d,'api') as api,patch.object(d,'save_state') as save:
            with self.assertRaises(d.CheckError):
                d.main()
            api.assert_not_called()
            save.assert_not_called()
