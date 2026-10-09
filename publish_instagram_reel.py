"""Publish one reviewed, prepared Reel only after explicit workflow approval."""
import json
import os
from pathlib import Path
import re
import sys
from check_instagram_connection import check, CheckError
from prepare_instagram_reel import api, CAPTION, REPO

def publish(env, prepared, opener=None):
    if env.get("CONFIRM_PUBLISH") != "true":
        raise CheckError("公開の確認が選択されていません。公開は実行しません。")
    if not isinstance(prepared, dict):
        raise CheckError("準備結果の形式を確認できませんでした。")
    source = prepared.get("source_run_id")
    cid = prepared.get("container_id")
    if (not isinstance(source, str) or not re.fullmatch(r"[0-9]+", source)
            or not isinstance(cid, str) or not re.fullmatch(r"[0-9]+", cid)
            or prepared.get("username") != "ezawa238"
            or prepared.get("caption") != CAPTION
            or prepared.get("status") != "FINISHED"
            or prepared.get("published") is not False
            or prepared.get("video_url") != f"https://github.com/{REPO}/releases/download/reel-preview-{source}/ezawa238_reel.mp4"):
        raise CheckError("動画・投稿文・接続先が確認済みの準備結果と一致しません。")
    check(env, opener)
    status = api(env, cid + "?fields=status_code", opener=opener).get("status_code")
    if status == "PUBLISHED":
        return {"published": True, "already_published": True, "media_id": None,
                "container_id": cid, "source_run_id": source}
    if status != "FINISHED":
        raise CheckError("動画が公開可能な状態ではありません。期限切れの場合はアップロードテストからやり直してください。")
    try:
        result = api(env, env["IG_USER_ID"].strip() + "/media_publish",
                     {"creation_id": cid}, opener)
    except CheckError:
        # A timeout may happen after publication. Do not issue a second POST.
        try:
            latest = api(env, cid + "?fields=status_code", opener=opener).get("status_code")
        except CheckError:
            latest = None
        if latest == "PUBLISHED":
            return {"published": True, "already_published": False, "media_id": None,
                    "container_id": cid, "source_run_id": source}
        raise CheckError("公開要求の結果を確定できませんでした。重複を防ぐため自動再送していません。Instagramのプロフィールを確認してください。") from None
    media_id = result.get("id")
    if not isinstance(media_id, str) or not re.fullmatch(r"[0-9]+", media_id):
        raise CheckError("公開応答を確定できませんでした。重複を防ぐため自動再送していません。プロフィールを確認してください。")
    return {"published": True, "already_published": False, "media_id": media_id,
            "container_id": cid, "source_run_id": source}

def main():
    try:
        prepared = json.loads(Path("prepared/prepared.json").read_text(encoding="utf-8"))
        result = publish(os.environ, prepared)
        out = Path("publish-result")
        out.mkdir(exist_ok=True)
        (out / "published.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        summary = ("Instagram公開確認: @ezawa238\n"
                   + ("この動画は公開済みです。追加投稿は実行していません。\n" if result["already_published"]
                      else "確認した動画を公開しました。\n"))
        if result["media_id"]:
            summary += f"投稿ID: {result['media_id']}\n"
        summary += "プロフィール: https://www.instagram.com/ezawa238/\n"
        print(summary)
        if os.environ.get("GITHUB_STEP_SUMMARY"):
            with open(os.environ["GITHUB_STEP_SUMMARY"], "a", encoding="utf-8") as handle:
                handle.write(summary)
        return 0
    except CheckError as error:
        print(str(error))
    except Exception:
        print("公開処理の結果を確認できませんでした。自動再送せず、プロフィールで確認してください。")
    return 1

if __name__ == "__main__":
    sys.exit(main())
