# Instagram接続確認

現在の動画生成は成功しています。次に、Meta APIで対象アカウントを読み取れるかを確認します。
この診断はGETリクエストだけを使用します。投稿やメディア作成は行いません。
成功しても投稿権限、トークン自動更新、動画アップロード、定期投稿の成功を意味しません。

## 設定
GitHubの Settings → Secrets and variables → Actions → New repository secret に設定します。
- IG_ACCESS_TOKEN: 対象アカウントのアクセストークン
- IG_USER_ID: 数字のInstagramアカウントID（FacebookページIDやユーザーネームではありません）

秘密値をチャット・コード・スクリーンショットに載せないでください。
既存Secretsが別名の場合は、ワークフローの参照名を合わせます。

Actions → EZAWA238 Instagram Connection Check → Run workflow で、
Metaアプリの設定に合うログイン方式とAPIバージョンを入力します。
バージョンは推測せず、Meta画面の値を使用します。
- instagram: Instagram Login、graph.instagram.com
- facebook: Facebook Login、graph.facebook.com

接続診断ファイルをmainへ追加・更新した時も診断が実行されます。
この自動診断にはSettings → Secrets and variables → Actions → Variablesで
IG_LOGIN_METHODとIG_API_VERSIONを設定します。同名のSecretsも使用できます。
設定が不足している場合は、不足した名前を表示して停止します。
手動実行では画面で入力した値が優先されます。

## 結果
- 未設定: 表示された設定名を補います。
- code 190: トークンの有効性・期限とログイン方式を確認します。
- code 10 / 200: 権限とアプリ利用者設定を確認します。
- 接続先不一致: @ezawa238を指すIDとトークンに直します。
- 接続確認成功: 次は投稿権限確認と、動画転送方式の選定・テストを進めます。

## 次の実装
接続と投稿権限を確認後、動画アップロード、処理状況の確認、公開、重複防止を実装します。
定期実行はテスト投稿が成功した後に設定します。
現在のgenerate.ymlにはscheduleとInstagramへの投稿処理はありません。

## 参照
- https://developers.facebook.com/docs/instagram-platform/
- https://www.postman.com/meta/instagram/documentation/6yqw8pt/instagram-api

## オフライン確認
python3 -m unittest discover -s tests -p 'test_instagram_connection.py' -v
