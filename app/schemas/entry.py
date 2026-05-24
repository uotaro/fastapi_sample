"""
app/schemas/search.py
=================
検索 API のリクエスト/レスポンス スキーマ定義モジュール。
"""

from pydantic import BaseModel, Field, model_validator
from typing import Literal, Optional

# =============================================================================
# 社員データ登録 API 共通リクエストボディ
# =============================================================================
class EmpEntryRequest(BaseModel):
    """
    POST /entry/emp のリクエストボディ。
    """
    emp_id: str = Field(..., min_length=1, description="社員番号")
    emp_name: str = Field(..., min_length=1, description="社員名")
    emp_kana: str = Field(..., min_length=1, description="社員かな名")
    mail: str = Field(..., min_length=1, description="メールアドレス")
    did: str = Field(..., description="所属部署コード")
    birth_date: str = Field(..., description="生年月日")
    start_date: str = Field(..., description="入社日")
    end_date: str = Field(..., description="退社日")  # 退社日がない場合は空文字列を指定
