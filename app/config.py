"""
config.py
=========
アプリケーション全体の設定を一元管理する。

.env から環境変数を読み込み、定数として提供する。
セキュリティ上隠したい値や起動時に変更したい場合のある値などは .env に定義すること。

使い方:
    from app.config import settings
    print(settings.MILVUS_URI)
"""
from __future__ import annotations

import os
from pathlib import Path
from dotenv import load_dotenv


# =============================================================================
# .env の読み込み
# =============================================================================
# プロジェクトルート（このファイルの1つ上の階層）
_project_root = Path(__file__).resolve().parent.parent

# .env の読み込み（既に設定済みの環境変数は上書きしない）
load_dotenv(_project_root / ".env", override=False)

class _Settings:
    # =============================================================================
    # アプリケーション情報
    # =============================================================================
    APP_NAME: str = "FastAPI Server"
    APP_VERSION: str = "1.0.2"
    PROJECT_ROOT:str = _project_root

    # =============================================================================
    # サーバー設定
    # =============================================================================
    FASTAPI_SERVER_PORT: int=int(os.getenv("FASTAPI_SERVER_PORT", "51485"))

    # =============================================================================
    # Llama.cpp API サーバー設定（実際の値は .env で指定すること）
    #     リリース環境:       http://prod.ipai.isg.sel.co.jp:9525
    #     リリーステスト環境:  http://dev.ipai.isg.sel.co.jp:9520
    # =============================================================================
    LLAMA_API_HOST:str = os.getenv("LLAMA_API_HOST", "http://prod.ipai.isg.sel.co.jp:9525")
    LLAMA_API_MODEL:str = os.getenv("LLAMA_API_MODEL", "Qwen3.5-122B-A10B")
    LLAMA_API_URI: str = f"{LLAMA_API_HOST}/service/{LLAMA_API_MODEL}/v1/chat/completions"
    LLAMA_API_TOKEN: str = os.getenv("LLAMA_API_TOKEN", ".envで指定してね")

    # =============================================================================
    # sqLite
    # =============================================================================
    SQLITE_DB_PATH: str = os.getenv("SQLITE_DB_PATH", "./data.db")

    # =============================================================================
    # ログ設定（実際の値は .env で指定すること）
    # =============================================================================
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "info")
    LOG_DIR: str = os.path.join(_project_root, "logs")
    LOG_FILENAME: str = os.getenv("LOG_FILENAME", "fastapi_server.log")
    LOG_MAX_BYTES: int = int(os.getenv("LOG_MAX_BYTES", 10 * 1024 * 1024))  # デフォルト 10MB
    LOG_BACKUP_COUNT: int = int(os.getenv("LOG_BACKUP_COUNT", 10))          # デフォルト 10 世代

# モジュールロード時に1度だけインスタンスを生成し、使い回す（シングルトン）
settings = _Settings()
