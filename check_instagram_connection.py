"""Read-only Instagram connection check. Never creates or publishes media."""
import json
import os
import re
import sys
import urllib.error
import urllib.request


class CheckError(Exception):
    pass


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def check(env, open_request=None, publishing_limit=False):
    names = ("IG_ACCESS_TOKEN", "IG_USER_ID", "IG_API_VERSION", "IG_LOGIN_METHOD")
    missing = [name for name in names if not env.get(name, "").strip()]
    if missing:
        raise CheckError("未設定: " + ", ".join(missing))
    user_id = env["IG_USER_ID"].strip()
    version = env["IG_API_VERSION"].strip()
    method = env["IG_LOGIN_METHOD"].strip()
    if not re.fullmatch(r"[0-9]+", user_id):
        raise CheckError("IG_USER_IDにはユーザーネームではなく数字のInstagramアカウントIDを設定してください。")
    if not re.fullmatch(r"v[0-9]+\.0", version):
        raise CheckError("IG_API_VERSIONにはMetaの設定画面で確認したバージョンをvXX.0形式で設定してください。")
    hosts = {"instagram": "graph.instagram.com", "facebook": "graph.facebook.com"}
    if method not in hosts:
        raise CheckError("IG_LOGIN_METHODはinstagramまたはfacebookにしてください。")
    endpoint = "/content_publishing_limit?fields=quota_usage" if publishing_limit else "?fields=id,username"
    request = urllib.request.Request(
        f"https://{hosts[method]}/{version}/{user_id}{endpoint}",
        headers={"Authorization": "Bearer " + env["IG_ACCESS_TOKEN"].strip()},
        method="GET",
    )
    if open_request is None:
        open_request = urllib.request.build_opener(NoRedirect()).open
    try:
        with open_request(request, timeout=30) as response:
            payload = json.load(response)
    except urllib.error.HTTPError as error:
        # Only the numeric code is reported; error text may contain sensitive values.
        try:
            code = json.loads(error.read()).get("error", {}).get("code")
        except (ValueError, AttributeError):
            code = None
        if code == 190:
            detail = "トークンの期限・有効性・ログイン方式を確認してください。"
        elif code in (10, 200):
            detail = "権限・アプリの利用者設定・対象アカウントを確認してください。"
        else:
            detail = "ID・ログイン方式・APIバージョン・権限を確認してください。"
        numeric_code = code if isinstance(code, int) else "不明"
        raise CheckError(f"Meta APIエラー: HTTP {error.code}, code {numeric_code}。{detail}") from None
    except (urllib.error.URLError, TimeoutError, OSError):
        raise CheckError("Meta APIへの通信に失敗しました。接続を確認して再実行してください。") from None
    except ValueError:
        raise CheckError("Meta APIから正常なJSON応答を取得できませんでした。") from None
    if not isinstance(payload, dict):
        raise CheckError("Meta APIの応答形式を確認できませんでした。")
    if publishing_limit:
        data = payload.get("data")
        if not isinstance(data, list) or not data or not isinstance(data[0], dict):
            raise CheckError("投稿枠の応答形式を確認できませんでした。")
        usage = data[0].get("quota_usage")
        if type(usage) is not int or usage < 0:
            raise CheckError("投稿枠の利用数を確認できませんでした。")
        return usage
    expected = env.get("IG_EXPECTED_USERNAME", "ezawa238").strip().lstrip("@").lower()
    username = payload.get("username")
    if not expected or not isinstance(username, str) or username.lower() != expected:
        raise CheckError("接続先が想定ユーザーネームと一致しません。IDとトークンを確認してください。")
    return expected


def main():
    try:
        username = check(os.environ)
        print(f"接続確認成功: @{username}")
        usage = check(os.environ, publishing_limit=True)
    except CheckError as error:
        print(str(error))
        return 1
    except Exception:
        # Never emit a traceback containing request details.
        print("診断処理で予期しないエラーが発生しました。設定と実装を確認してください。")
        return 1
    print(f"投稿枠の読み取り成功: 利用数 {usage}")
    print("確認範囲: 対象アカウント情報と投稿枠の読み取り。動画投稿・定期投稿は未確認です。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
