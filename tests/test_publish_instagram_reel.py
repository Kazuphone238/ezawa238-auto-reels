import io
import json
import unittest
from urllib.error import HTTPError
from publish_instagram_reel import publish, CheckError, CAPTION, REPO

class PublishingTests(unittest.TestCase):
    def setUp(self):
        self.env = dict(IG_ACCESS_TOKEN="private-token", IG_USER_ID="123",
                        IG_API_VERSION="v24.0", IG_LOGIN_METHOD="instagram",
                        CONFIRM_PUBLISH="true")
        self.prepared = dict(username="ezawa238", container_id="456", source_run_id="37993973700",
                             caption=CAPTION, published=False, status="FINISHED",
                             video_url=f"https://github.com/{REPO}/releases/download/reel-preview-37993973700/ezawa238_reel.mp4")
        self.requests = []
    def fake(self, responses):
        def opener(req, timeout):
            self.requests.append(req)
            self.assertNotIn("private-token", req.full_url)
            reply = responses.pop(0)
            if isinstance(reply, Exception):
                raise reply
            return io.StringIO(json.dumps(reply))
        return opener
    def test_approval_required_before_any_api_call(self):
        self.env["CONFIRM_PUBLISH"] = "false"
        with self.assertRaises(CheckError):
            publish(self.env, self.prepared, lambda *a, **k: self.fail("No request allowed"))
    def test_tampered_preparation_rejected(self):
        for key, value in (("username","other"),("caption","changed"),("container_id","../me"),
                           ("video_url","https://other.invalid/video.mp4"),("published",True)):
            with self.assertRaises(CheckError):
                publish(self.env, dict(self.prepared, **{key:value}), lambda *a, **k: self.fail("No request allowed"))
    def test_ready_video_publishes_exactly_once(self):
        result = publish(self.env, self.prepared, self.fake([{"username":"ezawa238"},
                         {"status_code":"FINISHED"},{"id":"789"}]))
        self.assertEqual(result["media_id"], "789")
        self.assertEqual(sum(r.get_method()=="POST" for r in self.requests), 1)
        self.assertEqual(self.requests[-1].data, b"creation_id=456")
    def test_already_published_does_not_post_again(self):
        result = publish(self.env, self.prepared, self.fake([{"username":"ezawa238"},{"status_code":"PUBLISHED"}]))
        self.assertTrue(result["already_published"])
        self.assertFalse(any(r.get_method()=="POST" for r in self.requests))
    def test_expired_container_does_not_post(self):
        with self.assertRaises(CheckError):
            publish(self.env, self.prepared, self.fake([{"username":"ezawa238"},{"status_code":"EXPIRED"}]))
        self.assertFalse(any(r.get_method()=="POST" for r in self.requests))
    def test_timeout_after_publication_is_not_retried(self):
        error = HTTPError("https://example.invalid",500,"private-token",{},io.BytesIO(b'{}'))
        result = publish(self.env,self.prepared,self.fake([{"username":"ezawa238"},
                         {"status_code":"FINISHED"},error,{"status_code":"PUBLISHED"}]))
        self.assertTrue(result["published"])
        self.assertEqual(sum(r.get_method()=="POST" for r in self.requests), 1)
    def test_unknown_post_result_is_not_retried_or_logged_unsafely(self):
        error = HTTPError("https://example.invalid",500,"private-token",{},io.BytesIO(b'{}'))
        with self.assertRaises(CheckError) as result:
            publish(self.env,self.prepared,self.fake([{"username":"ezawa238"},
                    {"status_code":"FINISHED"},error,{"status_code":"FINISHED"}]))
        self.assertNotIn("private-token",str(result.exception))
        self.assertEqual(sum(r.get_method()=="POST" for r in self.requests), 1)

if __name__ == "__main__":
    unittest.main()
