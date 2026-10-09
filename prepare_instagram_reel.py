"""Prepare the reviewed Reel on Instagram, without publishing it."""
import json
import os
from pathlib import Path
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from check_instagram_connection import CheckError, NoRedirect, check

CAPTION = "EZAWA238 | Original music\n128 BPM / 15 seconds\n#EZAWA238 #OriginalMusic #EDM #Trance"
REPO = "Kazuphone238/ezawa238-auto-reels"

def api(env, path, data=None, opener=None):
    host = {"instagram": "graph.instagram.com", "facebook": "graph.facebook.com"}[env["IG_LOGIN_METHOD"].strip()]
    body = urllib.parse.urlencode(data).encode() if data is not None else None
    req = urllib.request.Request(
        f"https://{host}/{env['IG_API_VERSION'].strip()}/{path}", data=body,
        headers={"Authorization": "Bearer " + env["IG_ACCESS_TOKEN"].strip()},
        method="POST" if data is not None else "GET")
    if opener is None:
        opener = urllib.request.build_opener(NoRedirect()).open
    try:
        with opener(req, timeout=60) as response:
            payload = json.load(response)
    except urllib.error.HTTPError as error:
        try:
            detail = json.loads(error.read()).get("error", {})
            code, subcode = detail.get("code"), detail.get("error_subcode")
        except (ValueError, AttributeError):
            code, subcode = None, None
        code = code if type(code) is int else "不明"
        subcode = subcode if type(subcode) is int else "不明"
        raise CheckError(f"Instagram準備エラー: HTTP {error.code}, code {code}, subcode {subcode}。投稿権限・動画URL・トークンを確認してください。") from None
    except (urllib.error.URLError, TimeoutError, OSError, ValueError):
        raise CheckError("Instagram準備中の通信または応答に問題がありました。公開は実行していません。") from None
    if not isinstance(payload, dict) or "error" in payload:
        raise CheckError("Instagram準備の応答形式を確認できませんでした。")
    return payload

def prepare(env, opener=None, sleep=time.sleep, attempts=60):
    run_id = env.get("SOURCE_RUN_ID", "").strip()
    if not re.fullmatch(r"[0-9]+", run_id):
        raise CheckError("SOURCE_RUN_IDには確認済み動画生成の実行番号を指定してください。")
    # Account and all API configuration are validated before any write.
    username = check(env, opener)
    video_url = f"https://github.com/{REPO}/releases/download/reel-preview-{run_id}/ezawa238_reel.mp4"
    result = api(env, env["IG_USER_ID"].strip() + "/media",
                 {"media_type": "REELS", "video_url": video_url,
                  "caption": CAPTION, "share_to_feed": "true"}, opener)
    container_id = result.get("id")
    if not isinstance(container_id, str) or not re.fullmatch(r"[0-9]+", container_id):
        raise CheckError("Instagramの準備IDを確認できませんでした。")
    for attempt in range(attempts):
        status = api(env, container_id + "?fields=status_code", opener=opener).get("status_code")
        if status == "FINISHED":
            return {"username": username, "container_id": container_id, "source_run_id": run_id,
                    "video_url": video_url, "caption": CAPTION, "published": False,
                    "status": status}
        if status in ("ERROR", "EXPIRED", "PUBLISHED") or status != "IN_PROGRESS":
            raise CheckError("Instagramの動画処理が正常な準備状態になりませんでした。")
        if attempt + 1 < attempts:
            sleep(5)
    raise CheckError("Instagramの動画処理が確認時間内に完了しませんでした。公開は実行していません。")

def main():
    try:
        result = prepare(os.environ)
        output = Path("upload-result")
        output.mkdir(exist_ok=True)
        (output / "prepared.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        summary = (f"Instagram動画準備成功: @{result['username']}\n"
                   f"動画生成の実行番号: {result['source_run_id']}\n"
                   "動画処理: FINISHED\nInstagram公開: 未実行\n\n"
                   "投稿文案:\n" + CAPTION + "\n")
        (output / "result.txt").write_text(summary, encoding="utf-8")
        print(summary)
        if os.environ.get("GITHUB_STEP_SUMMARY"):
            with open(os.environ["GITHUB_STEP_SUMMARY"], "a", encoding="utf-8") as handle:
                handle.write(summary)
        return 0
    except CheckError as error:
        print(str(error))
    except Exception:
        print("動画準備で予期しないエラーが発生しました。公開は実行していません。")
    return 1

if __name__ == "__main__":
    sys.exit(main())
