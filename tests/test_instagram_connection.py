import io
import json
import unittest
from urllib.error import HTTPError
from check_instagram_connection import check, CheckError

class ConnectionTests(unittest.TestCase):
    def setUp(self):
        self.env = dict(IG_ACCESS_TOKEN="test-secret", IG_USER_ID="1234",
                        IG_API_VERSION="v26.0", IG_LOGIN_METHOD="instagram")

    def test_missing_settings_never_calls_api(self):
        with self.assertRaisesRegex(CheckError, "IG_ACCESS_TOKEN"):
            check({}, lambda *a, **k: self.fail("API must not be called"))

    def test_correct_account_and_read_only_request(self):
        for method, host in (("instagram", "graph.instagram.com"), ("facebook", "graph.facebook.com")):
            self.env["IG_LOGIN_METHOD"] = method
            def fake(request, timeout):
                self.assertEqual(request.get_method(), "GET")
                self.assertEqual(request.full_url, f"https://{host}/v26.0/1234?fields=id,username")
                self.assertNotIn("test-secret", request.full_url)
                self.assertEqual(request.get_header("Authorization"), "Bearer test-secret")
                return io.StringIO(json.dumps({"id": "1234", "username": "ezawa238"}))
            self.assertEqual(check(self.env, fake), "ezawa238")

    def test_wrong_account_fails(self):
        with self.assertRaisesRegex(CheckError, "一致しません"):
            check(self.env, lambda *a, **k: io.StringIO('{"username":"another_account"}'))

    def test_publishing_limit_uses_get_and_never_exposes_token_in_url(self):
        def fake(request, timeout):
            self.assertEqual(request.get_method(), "GET")
            self.assertEqual(request.full_url, "https://graph.instagram.com/v26.0/1234/content_publishing_limit?fields=quota_usage")
            self.assertNotIn("test-secret", request.full_url)
            return io.StringIO('{"data":[{"quota_usage":0}]}')
        self.assertEqual(check(self.env, fake, publishing_limit=True), 0)

    def test_publishing_limit_rejects_malformed_response(self):
        for payload in ({"data": []}, {"data": [{}]}, {"data": [{"quota_usage": True}]},
                        {"data": [{"quota_usage": -1}]}):
            with self.assertRaises(CheckError):
                check(self.env, lambda *a, **k: io.StringIO(json.dumps(payload)), publishing_limit=True)

    def test_publishing_permission_error_is_sanitized(self):
        def fake(*args, **kwargs):
            raise HTTPError("https://example.invalid", 403, "test-secret", {}, io.BytesIO(
                b'{"error":{"code":10,"message":"test-secret"}}'))
        with self.assertRaises(CheckError) as result:
            check(self.env, fake, publishing_limit=True)
        self.assertIn("code 10", str(result.exception))
        self.assertNotIn("test-secret", str(result.exception))

    def test_http_error_never_exposes_token_or_response_message(self):
        def fake(*args, **kwargs):
            raise HTTPError("https://example.invalid", 400, "test-secret", {}, io.BytesIO(
                b'{"error":{"code":190,"message":"test-secret"}}'))
        with self.assertRaises(CheckError) as result:
            check(self.env, fake)
        self.assertIn("190", str(result.exception))
        self.assertNotIn("test-secret", str(result.exception))

    def test_invalid_config_never_calls_api(self):
        for field, value in (("IG_USER_ID", "../me"), ("IG_API_VERSION", "latest"),
                             ("IG_LOGIN_METHOD", "other")):
            env = dict(self.env, **{field: value})
            with self.assertRaises(CheckError):
                check(env, lambda *a, **k: self.fail("API must not be called"))

if __name__ == "__main__":
    unittest.main()
