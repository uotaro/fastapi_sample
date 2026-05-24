# FastAPI サンプル

当サンプルは、logrotate 機能ありの前提です。  
DB は sqLite 使用。

## 参考URL
- 公式日本語ドキュメント: [https://fastapi.tiangolo.com/ja/](https://fastapi.tiangolo.com/ja/)

## 初回設定
### 1. 必要モジュールをインストール
以下を pip install インストールします。

| モジュール  | 説明                       |
|------------|----------------------------|
| fastapi    | FastAPIサーバー構築のため   | 
| sqlalchemy | DB 操作のため              |
| dotenv     | .env から環境変数読取のため |

### 1. ログローテートのパス変更
ログローテート設定ファイル `/logrotate/logrotate.conf` のパスを修正してください。

### 2. 環境変数を設定

`.env` ファイルを編集してポート番号などを設定します。

```bash
# --- FastAPI ポート番号 ------------------------------------------------------
FASTAPI_SERVER_PORT=51485

# --- sqLite -----------------------------------------------------------------
SQLITE_DB_PATH=./data.db

# --- ログ設定 ----------------------------------------------------------------
LOG_LEVEL=info
LOG_FILENAME=fastapi_server.log
# ↓ 10MB
LOG_MAX_BYTES=10485760
LOG_BACKUP_COUNT=10
```


## サーバーの起動・停止

```bash
# サーバー起動（仮想環境への自動移行あり）
bash run_fastapi_server.sh start

# サーバー停止
bash run_fastapi_server.sh stop

# 稼働状況確認
bash run_fastapi_server.sh status

# リアルタイムログ表示（Ctrl+C で終了）
bash run_fastapi_server.sh log
```

---

## フォルダ構成
各ディレクトリには下記ファイル以外に `__init__.py` を配置する。  


```
プロジェクトルート/
├── app/
│   │
│   ├── main.py                     # FastAPI アプリエントリーポイント
│   ├── config.py                   # 設定管理（.env 読み込み）
│   │
│   ├── routers/                    # ルーティング定義
│   │   ├── health.py               # GET /health, GET /info
│   │   └── search.py               # POST /search/paper/*
│   │
│   ├── db/                         # DB設定に関する処理を記述したファイルを配置
│   │   └── session.py              # DBセッションの生成と管理
│   │
│   ├── models/                     # データベースのテーブル定義
│   │   ├── emp.py                  # 社員テーブル（カラム(すべてTEXT型): emp_id, emp_name, mail, did, birth_date, start_date, end_date）
│   │   └── dept.py                 # 所属部署テーブル（カラム(すべてTEXT型): dept_id, dept_name）
│   │
│   ├── schemas/                    # データのスキーマ定義を行うファイルを配置
│   │   ├── base.py                 # 共通スキーマ（HitItem, SearchResponse）
│   │   ├── entry.py                # 登録リクエストスキーマ
│   │   └── search.py               # 検索リクエストスキーマ
│   │
│   ├── services/                   # アプリロジックを配置
│   │   ├── entry/
│   │   │   └── emp.py              # 社員情報登録
│   │   └── search/
│   │       └── emp.py              # 社員情報検索
│   │
│   └── utils/
│       ├── logger.py               # ログ設定
│       └── common_utils.py         # 共通ユーティリティ
│
├── tests/                          # テスト用ファイルを配置
│   ├── conftest.py
│   ├── ・・・略・・・
│   └── test_etest_searchntry.py
│
├── logrotate/ 
│   └── logrotate.conf              # ログローテート設定ファイル
│
├── logs/                           # ログ出力先
├── .env                            # 環境変数設定
└── run_fastapi_server.sh           # 起動/停止スクリプト
```

---

## API エンドポイント一覧

| メソッド | パス              | 説明                                 |
|---------|-------------------|-------------------------------------|
|   GET   | `/health`         | ヘルスチェック（DB接続 / モデル状態）  |
|   GET   | `/info`           | サーバー情報                         |
|   GET   | `/`               | Hello, World                        |
|   GET   | `/docs`           | Swagger UI（API ドキュメント）       |
|   POST  | `/entry/init`     | DB初期化（テーブル作成＋初期データ登録 |
|   POST  | `/entry/emp`      | 指定社員番号の社員データ登録          |
|   POST  | `/search/emp`     | 指定社員番号の社員データ取得          |
|   POST  | `/search/emplist` | 指定部署の社員情報リスト取得          |

Swagger UI は起動後に `http://<サーバーIP>:<ポート番号>/docs` でアクセスできます。

---

## DB のテーブル構成
当サンプルでは、下記テーブルを作成して使用するサンプルです。

### emp テーブル

| カラム名      | 型   |                    |
|--------------|------|--------------------|
| emp_id       | TEXT |  社員番号, 主キー   |
| emp_name     | TEXT |  社員名            |
| emp_kana     | TEXT |  社員かな名         |
| mail         | TEXT |  メールアドレス     |
| did          | TEXT |  所属部署コード     |
| birth_date   | TEXT |  生年月日           |
| start_date   | TEXT |  入社日             |
| end_date     | TEXT |  退社日             |

| emp_id | emp_name   |    emp_kana       |   mail                     |   did     |  birth_date   |  start_date  | end_date |
|--------|------------|-------------------|----------------------------|-----------|---------------|--------------|----------|
|  E001  | 近藤勇     |  こんどういさむ     |   ikondo@example.com       |   D001    |  1990-01-01   |  2020-04-01  |          |
|  E002  | 土方歳三   |  ひじかたとしぞう   |   thijikata@example.com    |   D002    |  1992-05-15   |  2021-03-01  |          |
|  E003  | 井上源三郎 |  いのうえげんざろう  |   ginoue@example.com      |   D003    |  1988-12-10   |  2019-07-01  |          |
|  E004  | 藤堂平助   |  とうどうへいすけ   |   htoudo@example.com       |   D004    |  1995-08-20   |  2022-01-01  |          |
|  E005  | 前田慶次   |  まえだけいじ       |   maeda@example.com        |   D003    |  1988-12-10   |  2019-07-01  |          |
|  E006  | 澤村遥     |  さわむらはるか     |   sawamura@example.com     |   D004    |  2001-11-25   |  2026-10-01  |          |
|  E007  | 山南敬助   |  やみなみけいすけ   |   kyamanami@example.com    |   D004    |  1990-03-15   |  2021-09-01  |          |
|  E008  | 永倉新八   |  ながくらしんぱち   |   snagakura@example.com    |   D004    |  1991-09-12   |  2020-06-01  |          |
 
### dept テーブル

| カラム名      | 型   |                      |
|--------------|------|----------------------|
| dept_id      | TEXT | 所属部署コード。主キー |
| dept_name    | TEXT | 部署名                |

| dept_id | dept_name |
|---------|-----------|
|  D001   |  総務部    |
|  D002   |  人事部    |
|  D003   |  営業部    |
|  D004   |  技術部    |
 


# テスト実行方法
プロジェトルートで下記コマンドを実行してください。

```
# 全テスト実行
.venv_wsl/bin/pytest test/

# 詳細表示（どのテストが Pass/Fail か一覧表示）
.venv_wsl/bin/pytest test/ -v

# ----- ファイルを絞って実行 -----
# ファイル単位
.venv_wsl/bin/pytest test/test_health.py -v
.venv_wsl/bin/pytest test/test_search.py -v

# テスト名をキーワードで絞る（-k オプション）
.venv_wsl/bin/pytest test/ -k "search_emp" -v

# ----- よく使うオプション -----
# 最初の失敗で止める（-x）
.venv_wsl/bin/pytest test/ -x

# 失敗したテストだけ再実行
.venv_wsl/bin/pytest test/ --lf

# print() や logger の出力を表示（-s）
.venv_wsl/bin/pytest test/ -v -s
```
