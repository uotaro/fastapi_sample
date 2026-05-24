"""
routers/entry.py
==================
社員データ登録 API エンドポイントのルーターモジュール。

エンドポイント:
  POST /entry/emp  - 社員データ登録(社員番号、名前、メールアドレス、所属部署コード、生年月日、入社日、退社日). empテーブルがなければ作成も行う
"""

import time
from fastapi import APIRouter, HTTPException, status
import traceback

from app.config import settings
from app.schemas.base import (
    EntryResponse,
)
from app.schemas.entry import (
    EmpEntryRequest,
)
from app.services.entry.emp import entry_emp, init_db
from app.utils.logger import get_logger 

router = APIRouter(prefix="/entry", tags=["Entry"])
logger = get_logger(__name__)
#-----------------------------------------------------------------------
@router.post(
    "/init",
    response_model=EntryResponse,
    summary="DB初期化（テーブル作成＋初期データ登録）",
    description=(
        "dept・emp テーブルが存在しない場合に作成し、初期データを登録します。\n\n"
        "テーブルがすでに存在する場合は何もしません。"
    ),
)
async def init_db_endpoint() -> EntryResponse:
    try:
        message = init_db()
        logger.info(message)
        return EntryResponse(success=True, message=message)
    except Exception as e:
        logger.error(f"DB初期化エラー: {e}")
        logger.debug(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="DB初期化中にエラーが発生しました。"
        )
#-----------------------------------------------------------------------
@router.post(
    "/emp",
    response_model=EntryResponse,
    summary="社員データ登録",
    description=(
        "社員データを登録します。\n\n"
        "- `emp_id` で指定した社員番号を登録します。\n"
        "- `emp_name` で指定した社員名を登録します。\n"
        "- `emp_kana` で指定した社員かな名を登録します。\n"
        "- `mail` で指定したメールアドレスを登録します。\n"
        "- `did` で指定した所属部署コードを登録します。\n"
        "- `birth_date` で指定した生年月日を登録します。\n"
        "- `start_date` で指定した入社日を登録します。\n"
        "- `end_date` で指定した退社日を登録します。退社日がない場合は空文字列を指定してください。"
    ),
)
async def entry_emp_endpoint(req: EmpEntryRequest) -> EntryResponse:
    """
    社員データ登録エンドポイント

    Args:
        req: 登録リクエスト

    Returns:
        EntryResponse: 登録結果
    """
    try:
        # 登録処理実行
        success = entry_emp(req.model_dump())
        if success:
            return EntryResponse(success=True)
        else:
            return EntryResponse(success=False, message="登録に失敗しました。")
    except Exception as e:
        logger.error(f"社員データ登録エラー: {e}")
        logger.debug(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="社員データの登録中にエラーが発生しました。"
        )

