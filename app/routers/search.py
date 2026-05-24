"""
routers/search.py
==================
検索 API エンドポイントのルーターモジュール。

エンドポイント:
  POST /search/emp      - 社員番号で社員データ1件取得
  POST /search/emplist  - 部署コード or 部署名で社員リスト取得

将来的に /search/manual/ や /search/faxback/ を追加する場合は、
このファイルに新しいルーターグループを追加してください。
"""

import traceback
from fastapi import APIRouter, HTTPException, status

from app.schemas.base import SearchResponse
from app.schemas.search import EmpSearchRequest, EmplistSearchRequest
from app.services.search.emp import search_emp_by_emp_id, search_emplist_by_d
from app.utils.logger import get_logger

router = APIRouter(prefix="/search", tags=["Search"])
logger = get_logger(__name__)

#-----------------------------------------------------------------------
@router.post(
    "/emp",
    response_model=SearchResponse,
    summary="社員情報検索",
    description=(
        "社員番号から社員データ検索を実行します。\n\n"
        "- `emp_id` で指定した社員データを返します。"
    ),
)
async def search_emp(req: EmpSearchRequest) -> SearchResponse:
    """
    社員データ検索

    Args:
        req: 検索リクエスト（emp_id: 社員番号）

    Returns:
        SearchResponse: 検索結果
    """
    try:
        return search_emp_by_emp_id(req.emp_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"社員情報検索エラー: {e}")
        logger.debug(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="社員情報の検索中にエラーが発生しました。",
        )


#-----------------------------------------------------------------------
@router.post(
    "/emplist",
    response_model=SearchResponse,
    summary="社員リスト検索",
    description=(
        "指定された部署に所属する社員データリストを検索します。\n\n"
        "- `did` または `dname` で指定した部署の社員データリストを返します。"
    ),
)
async def search_emplist(req: EmplistSearchRequest) -> SearchResponse:
    """
    指定された部署に所属する社員データリストを検索

    Args:
        req: 検索リクエスト（did: 部署コード、dname: 部署名）

    Returns:
        SearchResponse: 検索結果
    """
    try:
        return search_emplist_by_d(req.did, req.dname)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"社員リスト検索エラー: {e}")
        logger.debug(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="社員リストの検索中にエラーが発生しました。",
        )
