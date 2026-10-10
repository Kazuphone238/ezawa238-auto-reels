"""Publish one approved queue item; persist claims before any publication."""
import base64
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time
from zoneinfo import ZoneInfo
from check_instagram_connection import check, CheckError
from prepare_instagram_reel import api

STATE = 'posting/state.json'
REPO = 'Kazuphone238/ezawa238-auto-reels'

def gh(arguments):
    p = subprocess.run(['gh','api',*arguments],capture_output=True,text=True)
    if p.returncode:
        raise CheckError('投稿記録を保存できませんでした。重複防止のため停止します。')
    return json.loads(p.stdout) if p.stdout.strip() else {}

def read_state():
    r=gh([f'repos/{REPO}/contents/{STATE}'])
    return json.loads(base64.b64decode(r['content'])),r['sha']

def save_state(state,sha):
    payload={'message':'Record daily Instagram publication state',
             'content':base64.b64encode((json.dumps(state,ensure_ascii=False,indent=2)+'\n').encode()).decode(),
             'sha':sha,'branch':'main'}
    p=Path('posting-state-request.json');p.write_text(json.dumps(payload))
    r=gh(['--method','PUT',f'repos/{REPO}/contents/{STATE}','--input',str(p)])
    return r['content']['sha']

def main():
    env=os.environ
    check(env)
    if env.get('GITHUB_EVENT_NAME')!='schedule':
        print('Instagram接続確認成功。公開は実行していません。')
        return
    now=datetime.now(ZoneInfo('Asia/Tokyo'))
    if (now.hour,now.minute)<(17,30):
        raise CheckError('日本時間17:30より前のため投稿しません。')
    state,sha=read_state()
    today=now.date().isoformat()
    if state.get('last_post_date')==today:
        print('本日の動画は投稿済みです。');return
    queue=json.loads(Path('posting/queue.json').read_text())
    records=state.setdefault('items',{})
    unresolved=[r for r in records.values() if r.get('status')!='published']
    if unresolved:
        raise CheckError('以前の投稿結果が未確定です。重複防止のため確認が必要です。')
    item=next((i for i in queue if i['id'] not in records),None)
    if item is None:
        print('未投稿の承認済み動画がないため、本日の投稿を見送ります。');return
    path=Path(item['path'])
    if hashlib.sha256(path.read_bytes()).hexdigest()!=item['sha256']:
        raise CheckError('承認済み動画の内容が変わったため停止しました。')
    # Claim is durable before creating or publishing a container. Never auto-retry an unknown POST.
    record={'status':'claimed','date':today}
    records[item['id']]=record
    sha=save_state(state,sha)
    url=f'https://raw.githubusercontent.com/{REPO}/{env["GITHUB_SHA"]}/{item["path"]}'
    created=api(env,env['IG_USER_ID'].strip()+'/media',
                {'media_type':'REELS','video_url':url,'caption':item['caption'],'share_to_feed':'true'})
    cid=created.get('id')
    if not isinstance(cid,str) or not cid.isdigit():raise CheckError('動画準備IDを確認できませんでした。')
    record.update(status='processing',container_id=cid)
    sha=save_state(state,sha)
    for _ in range(60):
        status=api(env,cid+'?fields=status_code').get('status_code')
        if status=='FINISHED':break
        if status!='IN_PROGRESS':raise CheckError('Instagramの動画処理が完了しませんでした。')
        time.sleep(5)
    else:raise CheckError('Instagramの動画処理が時間内に完了しませんでした。')
    record['status']='publishing';sha=save_state(state,sha)
    result=api(env,env['IG_USER_ID'].strip()+'/media_publish',{'creation_id':cid})
    mid=result.get('id')
    if not isinstance(mid,str) or not mid.isdigit():raise CheckError('公開結果を確定できませんでした。自動再送はしません。')
    record.update(status='published',media_id=mid)
    state['last_post_date']=today
    save_state(state,sha)
    print('Instagram投稿成功: @ezawa238 / '+item['id'])

if __name__=='__main__':
    try:main()
    except CheckError as e:print(str(e));raise SystemExit(1)
    except Exception:print('投稿を確認できませんでした。重複防止のため停止しました。');raise SystemExit(1)
