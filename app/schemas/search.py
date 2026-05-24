"""
app/schemas/search.py
=================
検索 API のリクエスト/レスポンス スキーマ定義モジュール。
"""

from pydantic import BaseModel, Field, model_validator
from typing import Literal, Optional

# =============================================================================
# 社員番号検索 API 共通リクエストボディ
# =============================================================================
class EmpSearchRequest(BaseModel):
    """
    POST /search/***/fulltext のリクエストボディ。
    BM25 全文検索用。
    """
    emp_id: str = Field(..., min_length=1, description="社員番号")


# =============================================================================
# 社員リスト検索 API 共通リクエストボディ
# =============================================================================
class EmplistSearchRequest(BaseModel):
    """
    POST /search/emp/hybrid のリクエストボディ。
    """
    did: Optional[str] = Field(default=None, description="所属ｺｰﾄﾞ")
    dname: Optional[str] = Field(default=None, description="所属部署名")

    @model_validator(mode="after")
    def check_query_or_image(self) -> "EmplistSearchRequest":
        """
        did と query_idnamemage_b64 の少なくとも一方が指定されているかをチェックします。
        """
        if not self.did and not self.dname:
            raise ValueError(
                "所属ｺｰﾄﾞ または 所属部署名 のどちらか一方を指定してください"
            )
        return self
