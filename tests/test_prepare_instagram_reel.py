import io
import json
import unittest
from urllib.error import HTTPError
from prepare_instagram_reel import prepare, CheckError

class UploadTests(unittest.TestCase):
    def setUp(self):
        self.env = dict(IG_ACCESS_TOKEN="private-token", IG_USER_ID="123",
                        IG_API_VERSION="v24.0", IG_LOGIN_METHOD="instagram",
                        SOURCE_RUN_ID="37993973700")
        self.requests = []
    def fake(self, replies):
        def open_request(req, timeout):
            self.requests.append(req)
            self.assertNotIn("private-token", req.full_url)
            self.assertNotIn("/media_publish", req.full_url)
            self.assertEqual(req.get_header("Authorization"), "Bearer private-token")
            return io.StringIO(json.dumps(replies.pop(0)))
        return open_request
    def test_ready_container_never_publishes(self):
        result = prepare(self.env, self.fake([{"username":"ezawa238"},{"id":"456"},
                         {"status_code":"IN_PROGRESS"},{"status_code":"FINISHED"}]),
                         sleep=lambda _: None)
        self.assertFalse(result["published"])
        self.assertEqual(result["container_id"], "456")
        self.assertEqual([r.get_method() for r in self.requests], ["GET","POST","GET","GET"])
        body = self.requests[1].data.decode()
        self.assertIn("media_type=REELS", body)
        self.assertIn("reel-preview-37993973700", body)
    def test_invalid_source_never_calls_api(self):
        self.env["SOURCE_RUN_ID"] = "../bad"
        with self.assertRaises(CheckError):
            prepare(self.env, lambda *a, **k: self.fail("No API call allowed"))
    def test_wrong_account_never_creates_container(self):
        with self.assertRaises(CheckError):
            prepare(self.env, self.fake([{"username":"other"}]))
        self.assertEqual(len(self.requests), 1)
    def test_failed_processing_stops(self):
        for status in ("ERROR","EXPIRED","PUBLISHED","unknown",None):
            self.requests = []
            with self.assertRaises(CheckError):
                prepare(self.env, self.fake([{"username":"ezawa238"},{"id":"456"},
                                             {"status_code":status}]))
            self.assertEqual(len(self.requests), 3)
    def test_processing_timeout_does_not_repeat_container_creation(self):
        with self.assertRaises(CheckError):
            prepare(self.env, self.fake([{"username":"ezawa238"},{"id":"456"},
                                        {"status_code":"IN_PROGRESS"}]), attempts=1)
        self.assertEqual(sum(r.get_method()=="POST" for r in self.requests), 1)
    def test_http_error_does_not_expose_token(self):
        def failure(req, timeout):
            if req.get_method() == "GET":
                return io.StringIO('{"username":"ezawa238"}')
            raise HTTPError(req.full_url,400,"private-token",{},io.BytesIO(
                b'{"error":{"code":10,"message":"private-token"}}'))
        with self.assertRaises(CheckError) as error:
            prepare(self.env, failure)
        self.assertNotIn("private-token", str(error.exception))
        self.assertIn("code 10", str(error.exception))

if __name__ == "__main__":
    unittest.main()
