# EZAWA238
承認済みの「鳥居の背景・全編2体並び」ダンス映像に、毎回新しいオリジナル曲を合わせます。

## 公開動画
[完成動画を見る](assets/approved_duet.mp4)
[完成動画をダウンロード](https://github.com/Kazuphone238/ezawa238-auto-reels/raw/refs/heads/main/assets/approved_duet.mp4)
[プログラム一式をダウンロード](https://github.com/Kazuphone238/ezawa238-auto-reels/archive/refs/heads/main.zip)

## 新曲を作る
1. GitHubのActionsで「EZAWA238 Generate Reel」を開く。
2. 「Run workflow」でmainを実行する。
3. 完了後、実行ページの「ezawa238-reel」をダウンロードする。

各実行で128 BPM・15秒のインスト曲を生成します。メロディー、キー、コード進行、ベースパターンなどが変化します。動画ストリームは再エンコードせずコピーするため、承認済みの動き・背景・人物は変わりません。新しい振付を生成する機能ではありません。
GitHub Actionsの成果物ダウンロードにはGitHubへのログインが必要です。上の固定完成動画とプログラム一式は公開リポジトリから誰でもダウンロードできます。成果物の保存期間は3日です。

## ローカル実行
Python 3、NumPy、FFmpegを用意して `python3 generate_reel.py` を実行します。
同じ曲を再現する場合は `python3 generate_reel.py --seed 238`。
出力は `output/ezawa238_reel.mp4`、`output/music.wav`、`output/music_info.json`。

有料の画像・動画・音楽APIは使用しません。音楽はプログラムによる合成で、歌声は含みません。
生成は手動実行と関連ファイルのmain更新で開始します。定期実行は設定していません。Instagram投稿は既存の別ワークフローで、この生成処理から投稿しません。
