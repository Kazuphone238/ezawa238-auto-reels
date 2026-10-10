from datetime import datetime as RealClock
import sys
import unittest
from unittest.mock import patch
sys.path.insert(0,'..')
import daily_instagram as d

class Clock:
    @staticmethod
    def now(tz):return RealClock.fromisoformat('2026-10-11T18:00:00+09:00')

class DailyTests(unittest.TestCase):
    def run_case(self,state,queue='[]'):
        with patch.dict(d.os.environ,{'GITHUB_EVENT_NAME':'schedule'},clear=True),patch.object(d,'datetime',Clock),patch.object(d,'check'),patch.object(d,'read_state',return_value=(state,'sha')),patch.object(d.Path,'read_text',return_value=queue),patch.object(d,'api') as a:
            d.main();a.assert_not_called()
    def test_already_posted(self):self.run_case({'last_post_date':'2026-10-11'})
    def test_empty_queue(self):self.run_case({'items':{}})
    def test_published_item_not_repeated(self):self.run_case({'items':{'x':{'status':'published'}}},'[{"id":"x"}]')
    def test_uncertain_post_stops(self):
        with self.assertRaises(d.CheckError):self.run_case({'items':{'x':{'status':'publishing'}}})
    def test_push_checks_connection_only(self):
        with patch.dict(d.os.environ,{'GITHUB_EVENT_NAME':'push'},clear=True),patch.object(d,'check') as c,patch.object(d,'api') as a:
            d.main();c.assert_called_once();a.assert_not_called()
