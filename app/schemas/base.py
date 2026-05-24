"""
app/schemas/base.py
===============
複数のエンドポイントで共通して使うスキーマ（データ型定義）をまとめたモジュール。

Pydantic の BaseModel を使うことで、下記が行われる。
    - リクエスト/レスポンスのバリデーション（型チェック）
    - OpenAPI（Swagger UI）への自動ドキュメント生成

ここでは、検索 API 共通のレスポンススキーマを定義する
"""
from pydantic import BaseModel, Field
from typing import Literal, Optional

# =============================================================================
# 検索結果の 1 件分を表すスキーマ
# =============================================================================
class HitItem(BaseModel):
    """
    検索結果の 1 件分を表す共通スキーマ。
    全文検索・ハイブリッド検索・ColPali 検索で共通して使用する。
    """
    emp_id: str = Field(..., description="社員番号")
    name: str = Field(..., description="名前")
    kana: str = Field(..., description="名前ｶﾅ")
    mail: str = Field(..., description="メールアドレス")
    did: str = Field(..., description="部署ｺｰﾄﾞ")
    dname: str = Field(..., description="部署名")

# =============================================================================
# 検索 API 共通レスポンス
# =============================================================================
class SearchResponse(BaseModel):
    """
    検索 API 共通レスポンス。
    """
    total: int = Field(..., description="検索ヒット件数")
    hits: list[HitItem] = Field(default_factory=list, description="検索結果リスト")
    elapsed: float = Field(..., description="検索処理時間（ミリ秒）")

# =============================================================================
# 登録 API 共通レスポンス
# =============================================================================
class EntryResponse(BaseModel):
    """
    登録 API 共通レスポンス。
    """
    success: bool = Field(..., description="登録成功フラグ")
    message: Optional[str] = Field(default=None, description="エラーメッセージ（失敗時のみ）")
