# FastAPI サーバーの起動方法
#    仮想環境に入って uvicorn コマンドで FastAPI アプリケーションを起動。
#    - 0.0.0.0でコンテナ外部からのアクセスを許可
#    - ポート番号は暫定で 51485 とする
#    - --reload オプションでコード変更時に自動的にリロード
#    コマンド:
#        cd (main.py があるディレクトリ＝プロジェクトルートディレクトリ)
#        sing-ai2_202605 bash -c "uvicorn main:app --host 0.0.0.0 --port 51485 --workers 1 --reload"
# 注意事項:
#    - main.py という名前は変えないでください。プロジェクトルート直下の main.py が FastAPI のエントリポイントです。
# 起動確認方法
#    - 事務PCのブラウザで、下記URLにアクセス（gncv2で起動した場合）
#      http://dev.ipai.isg.sel.co.jp:51485/
#      http://dev.ipai.isg.sel.co.jp:51485/docs
# 参考になりそうなサイト:
#    - https://note.com/meru_tech/n/n3b974417e36b

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.config import settings
from app.routers import health, entry, search
from app.utils.logger import get_logger

logger = get_logger(__name__)

# =============================================================================
# lifespan: アプリ起動・終了時の処理
# =============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI の lifespan ハンドラ。
    yield の前が起動時処理、yield の後が終了時処理。

    起動時:
      1. ログシステムの初期化
      2. DBなどへの接続確立（必要があれば・・・）
      3. モデルのロード（必要があれば・・・）


    終了時:
      - DB接続のクローズなど（必要があれば・・・）
    """
    # ---- 起動時処理 ----
    logger.info("=" * 60)
    logger.info("%s v%s 起動中...", settings.APP_NAME, settings.APP_VERSION)
    logger.info("  port: %d", settings.FASTAPI_SERVER_PORT)

    # DBなどへの接続確立（必要があれば・・・）
    logger.info("[1/2] XXX に接続中...")
    try:
        # get_xxx_client()
        logger.info("  → XXX 接続 OK")
    except Exception as e:
        # Milvus 接続に失敗してもサーバーは起動する（ヘルスチェックで "disconnected" になる）
        logger.error("  → XXX 接続失敗（後で再試行してください）: %s", e)

    # モデルのロード（必要があれば・・・）
    logger.info("[2/] モデルをロード中...")
    try:
        # load_model()
        logger.info("  → モデル ロード OK")
    except Exception as e:
        logger.error("  → モデル ロード失敗: %s", e)

    logger.info("=" * 60)
    logger.info("✅ %s 起動完了！", settings.APP_NAME)

    yield  # ここでサーバーが稼働状態になる

    # ---- 終了時処理 ----
    logger.info("%s シャットダウン中...", settings.APP_NAME)
    # DB接続のクローズなど（必要があれば・・・）
    # result = close_xxx_client()
    # logger.info("xxx クライアントクローズ結果: %s", result)
    logger.info("✅ シャットダウン完了")

# =============================================================================
# FastAPIアプリケーションのインスタンスを作成
# =============================================================================

app = FastAPI(
    title="おためしサンプル: " + settings.APP_NAME,
    version=settings.APP_VERSION,
    description=(
        "社員番号データ検索を提供する API サーバーです。\n\n"
        "DB に emp テーブルが存在しない場合は、まず `/entry/init` エンドポイントで初期化してください。\n\n"
        "初期化後は `/search/emp/emp_id/{emp_id}` エンドポイントで社員番号検索ができます。"
    ),
    lifespan=lifespan,
)

# =============================================================================
# CORS ミドルウェア設定
# LAN 内の他マシンからも API にアクセスできるよう全オリジンを許可します。
# セキュリティ要件に応じて allow_origins を特定の IP/ドメインに制限してください。
# =============================================================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # 全オリジンを許可（LAN 内アクセス対応）
    allow_credentials=True,
    allow_methods=["*"],          # GET / POST / PUT / DELETE など全メソッドを許可
    allow_headers=["*"],          # 全ヘッダーを許可
)

# =============================================================================
# ルーターの登録
# =============================================================================
# サーバー情報
app.include_router(health.router)
# 登録エンドポイント（/entry/emp/...）
app.include_router(entry.router)
# 検索エンドポイント（/search/paper/...）
app.include_router(search.router)
# =============================================================================
# ルートエンドポイント
# =============================================================================
# ルートパス("/")に対するGETリクエストのハンドラーを定義
@app.get("/")
def read_root():
    # JSON形式でメッセージを返す
    return {"message": "Hello World!! welcome to FastAPI:)"}

