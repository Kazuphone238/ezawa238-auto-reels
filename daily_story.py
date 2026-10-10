"""Share today's approved Reel video to Stories once on eligible accounts."""
from datetime import datetime
import json
import os
import time
from zoneinfo import ZoneInfo
from check_instagram_connection import check, CheckError
from prepare_instagram_reel import api
from daily_instagram import read_state, save_state, REPO

def account_type(env):
    check(env)
    return api(env,env['IG_USER_ID'].strip()+'?fields=account_type').get('account_type')

def main():
    env=os.environ
    kind=account_type(env)
    print('ストーリー対応確認: アカウント種別 '+str(kind))
    if kind!='BUSINESS':
        print('ストーリー自動投稿にはビジネスアカウントが必要です。ストーリーは見送り、リール設定は維持します。');return
    if env.get('GITHUB_EVENT_NAME')!='schedule':
        print('ストーリー接続確認のみ。公開は実行していません。');return
    state,sha=read_state()
    today=datetime.now(ZoneInfo('Asia/Tokyo')).date().isoformat()
    eligible=[(key,r) for key,r in state.get('items',{}).items() if r.get('date')==today and r.get('status')=='published']
    if not eligible:
        print('本日投稿したリールがないためストーリーを見送ります。');return
    key,record=eligible[0]
    if record.get('story'):
        if record['story']['status']=='published':print('本日のストーリーは投稿済みです。');return
        raise CheckError('以前のストーリー結果が未確定です。重複防止のため自動再送しません。')
    queue=json.load(open('posting/queue.json'))
    item=next(i for i in queue if i['id']==key)
    story={'status':'claimed'};record['story']=story
    sha=save_state(state,sha)
    url=f'https://raw.githubusercontent.com/{REPO}/{env["GITHUB_SHA"]}/{item["path"]}'
    created=api(env,env['IG_USER_ID'].strip()+'/media',{'media_type':'STORIES','video_url':url})
    cid=created.get('id')
    if not isinstance(cid,str) or not cid.isdigit():raise CheckError('ストーリーの準備IDを確認できませんでした。')
    story.update(status='processing',container_id=cid);sha=save_state(state,sha)
    for _ in range(60):
        status=api(env,cid+'?fields=status_code').get('status_code')
        if status=='FINISHED':break
        if status!='IN_PROGRESS':raise CheckError('ストーリーの処理が完了しませんでした。')
        time.sleep(5)
    else:raise CheckError('ストーリーの動画処理が時間内に完了しませんでした。')
    story['status']='publishing';sha=save_state(state,sha)
    published=api(env,env['IG_USER_ID'].strip()+'/media_publish',{'creation_id':cid})
    mid=published.get('id')
    if not isinstance(mid,str) or not mid.isdigit():raise CheckError('ストーリーの公開結果が未確定です。自動再送しません。')
    story.update(status='published',media_id=mid);save_state(state,sha)
    print('ストーリー投稿成功: @ezawa238 / '+key)

if __name__=='__main__':
    try:main()
    except CheckError as e:print(str(e));raise SystemExit(1)
    except Exception:print('ストーリー投稿を確認できませんでした。自動再送せず停止しました。');raise SystemExit(1)
