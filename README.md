# 市川教習所（Ichikawa Kyoshujo）「空」通知ボット（Playwright + Signal）

このプロジェクトは、市川教習所の予約ページを自動で巡回し、ラベルが **「空」** になっている枠（空き）を検出します。
空きが見つかった場合（かつ `ignored_dates` に含まれていない場合）、通知を送り、さらに勝利音を鳴らします。

> 通知は `send_notification()`（`notification.py`）で行われます。あなたの構成では **Signalグループへ投稿**する実装になっています。

---

## 機能

| 機能 | 説明 |
|---|---|
| 自動ログイン | Playwrightで iframe 内のフォームにユーザー名・パスワードを入力し、認証ボタンを押下 |
| 空き枠スキャン | `div.blocks` を読み取り、`badge == "空"` のブロックを探します |
| 除外リスト | 検出した日付が `ignored_dates` に含まれていればスキップ |
| 通知 | 新規に見つけた「空」日付に対して `send_notification(date)` を呼び出します |
| サウンド | 検出時に `victory_sound()` を鳴らします |
| 週移動 | スキャンのサイクルごとに「次/前の週」を切り替えます |

---

## スクリプトがやっていること（概要）

1. Playwrightで Chromium を起動
2. `start_url` にアクセス
3. `#scroll iframe` 内のログインフォームを待機
4. iframe内で以下を入力
   - `#txtKyoushuuseiNO`（ユーザー名）
   - `#txtPassword`（パスワード）
5. `#btnAuthentication` をクリックしてログイン
6. iframe内で `#btnMenu_Kyoushuuyoyaku` をクリックしてメニューを開く
7. ループ処理で繰り返しチェック
   - `div.blocks` から各ブロックの
     - `date`（`span.lbl`）
     - `badge`（`span.badge`）
     を抽出
   - `badge == "空"` かつ `date not in ignored_dates` の場合
     - `send_notification(date)`
     - `victory_sound()`
   - ページ更新/待機の後、週を移動する `click_week(...)` を実行

---

## .env で環境変数を読み込む

このプロジェクトでは **`.env` ファイルを使って環境変数を読み込み**ます。
`python-dotenv` の `load_dotenv()` により、`.env` 内の値が `os.environ` に入ります。

### `.env` 例

```env
START_URL=&quot;https://ichikyo.obic7.obicnet.ne.jp/xyz&quot;
IGNORED_DATES=&quot;2026/06/28 (日),2026/06/29 (月),2026/06/30 (火),2026/07/01 (水),2026/07/02 (木),2026/07/03 (金),2026/07/04 (土),2026/07/05 (日)&quot;
USERNAME=&quot;123456&quot;
PASSWORD=&quot;1234&quot;
SIGNAL_GROUP_ID=&quot;xyz&quot;
SIGNAL_USER_PHONE_NUMBER=&quot;+180456789&quot;
```

## 実行方法（uv）

main.py を以下のコマンドで実行します。

```bash
uv run main.py
```

main.py の概要（抜粋）
. load_dotenv() で .env を読み込み
. START_URL, USERNAME, PASSWORD, IGNORED_DATES を os.getenv() から取得
. run_check(start_url, username, password, ignored_dates) を呼び出します

## セットアップ

### 必要パッケージのインストール（例）

```bash
pip install playwright bs4 python-dotenv
```

### Playwright のブラウザをセットアップ

```bash
playwright install
```

### 注意点 / トラブルシューティング

iframe前提：ログインやメニュー操作は #scroll iframe 内にあります。セレクタ
#txtKyoushuuseiNO、#txtPassword、#btnAuthentication、#btnMenu_Kyoushuuyoyaku
がサイト変更で変わった場合、更新が必要です。
動的描画：div.blocks の読み取りが不安定な場合は、待機（wait）やリロードのタイミングを調整します。
除外リストの一致条件：ignored_dates はサイトが返す span.lbl の文字列と 完全一致で比較されます（item.get("date") not in ignored_dates）。