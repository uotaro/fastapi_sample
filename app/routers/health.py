"""
routers/health.py
==================
ヘルスチェック・サーバー情報エンドポイントのルーターモジュール。

エンドポイント:
  GET /health  - Milvus 接続 / モデルロード状態を確認
  GET /info    - サーバー設定情報を返す
"""

from fastapi import APIRouter,  Request, Response, HTTPException, status
from pydantic import BaseModel
import traceback

from app.config import settings
from app.utils.logger import get_logger

router = APIRouter()
logger = get_logger(__name__)

# =============================================================================
# レスポンスモデル
# =============================================================================

class HealthResponse(BaseModel):
    """GET /health のレスポンスモデル"""
    status: str
    db: str
    llm_model: str
    version: str

class InfoResponse(BaseModel):
    """GET /info のレスポンスモデル"""
    app: str
    version: str

# =============================================================================
# エンドポイント定義
# =============================================================================

@router.get(
    "/health",
    response_model=HealthResponse,
    summary="ヘルスチェック",
    description="xxx 接続状態とモデルロード状態を確認します。",
)
async def health_check() -> HealthResponse:
    """
    各コンポーネントの状態を確認して返す。

    Returns:
        HealthResponse:
            - status: 全コンポーネント正常なら "ok"、1 つでも異常なら "degraded"
            - db: "connected" または "disconnected: <エラーメッセージ>"
            - llm_model: "loaded" または "not_loaded"
            - version: アプリバージョン
    """
    try:
        # ダミー情報なので決め打ち
        db_status = "connected"
        model_status = "loaded"

        # 全コンポーネントが正常であれば "ok"、そうでなければ "degraded"
        all_ok = (
            db_status == "connected"
            and model_status == "loaded"
        )
        overall_status = "ok" if all_ok else "degraded"

        logger.info(
            "ヘルスチェック: status=%s, db=%s, llm_model=%s",
            overall_status, db_status, model_status,
        )

        return HealthResponse(
            status=overall_status,
            db=db_status,
            llm_model=model_status,
            version=settings.APP_VERSION,
        )
    except Exception as e:
        logger.error(f"ヘルスチェックエラー: {e}")
        logger.debug(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="ヘルスチェック中にエラーが発生しました。",
        )


#-----------------------------------------------------------------------
@router.get(
    "/info",
    response_model=InfoResponse,
    summary="サーバー情報",
    description="サーバーの設定情報を返します。",
)
async def server_info(request: Request, response: Response) -> InfoResponse:
    """
    サーバーの設定情報を返します。

    Returns:
        InfoResponse: サーバー名・バージョン
    """
    try:
        # クライアントのIPアドレスを取得
        client_ip = request.client.host if request.client else "unknown"

        logger.info(
            "リクエスト元IP: %s | サーバー情報: app=%s, version=%s",
            client_ip, settings.APP_NAME, settings.APP_VERSION,
        )

        # クッキーに TEST_TOKEN="abcde" をセット（おためし）
        response.set_cookie(key="TEST_TOKEN", value="abcde")

        return InfoResponse(
            app=settings.APP_NAME,
            version=settings.APP_VERSION,
        )
    except Exception as e:
        logger.error(f"サーバー設定情報取得エラー: {e}")
        logger.debug(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="サーバー設定情報の取得中にエラーが発生しました。",
        )
