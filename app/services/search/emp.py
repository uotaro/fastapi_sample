"""
app/services/search/emp.py
===================================
社員情報検索サービス

【このファイルの役割】
  ルーター (routers/search.py) から呼び出され、
  SQLite DB に対して検索クエリを実行して結果を返す。

【DB テーブル構成】
  emp  テーブル: emp_id, emp_name, emp_kana, mail, did, birth_date, start_date, end_date
  dept テーブル: dept_id, dept_name

  emp.did = dept.dept_id で LEFT JOIN することで部署名を取得できる。
"""

import time
from typing import Optional
from sqlalchemy import select, inspect

from app.db.session import SessionLocal, engine
from app.models.dept import Dept
from app.models.emp import Emp
from app.schemas.base import HitItem, SearchResponse
from app.utils.common_utils import elapsed_ms
from app.utils.logger import get_logger

logger = get_logger(__name__)


def _require_emp_table() -> None:
    """emp テーブルが存在することを確認する。
    存在しない場合は例外を投げる。"""
    if not inspect(engine).has_table("emp"):
        raise ValueError("emp テーブルがありません。まず /entry/init で初期化してください。")


# =============================================================================
# 社員番号で1件検索
# =============================================================================
def search_emp_by_emp_id(emp_id: str) -> SearchResponse:
    """
    社員番号 (emp_id) で社員データを1件検索する。

    【処理の流れ】
      1. emp テーブルを社員番号で絞り込む
      2. dept テーブルと LEFT JOIN して部署名も同時に取得する
         ※ LEFT JOIN なので dept に一致する部署がなくても emp は返る
      3. 結果を HitItem のリストに変換して SearchResponse で返す

    Args:
        emp_id: 検索する社員番号

    Returns:
        SearchResponse: ヒット件数・結果リスト・処理時間（ms）
    """
    # emp テーブルの存在を確認する。なければ例外を投げる。
    _require_emp_table()
    t0 = time.time()
    try:
        # ---------------------------------------------------------------
        # SQLAlchemy ORM でクエリを組み立てる
        # 生 SQL に換算すると下記と同等:
        #   SELECT emp.*, dept.dept_name
        #   FROM emp
        #   LEFT JOIN dept ON emp.did = dept.dept_id
        #   WHERE emp.emp_id = :emp_id
        # ---------------------------------------------------------------
        stmt = (
            select(Emp, Dept.dept_name)
            .outerjoin(Dept, Emp.did == Dept.dept_id)
            .where(Emp.emp_id == emp_id)
        )

        with SessionLocal() as s:
            rows = s.execute(stmt).all()
        # rows は [(Emp オブジェクト, dept_name文字列), ...] のリスト

        # ---------------------------------------------------------------
        # クエリ結果を HitItem のリストに変換する
        # ---------------------------------------------------------------
        hits = [
            HitItem(
                emp_id=emp.emp_id,
                name=emp.emp_name,
                kana=emp.emp_kana,
                mail=emp.mail,
                did=emp.did,
                dname=dept_name or "",   # LEFT JOIN なので dept が NULL の場合がある
            )
            for emp, dept_name in rows
        ]

        elapsed = elapsed_ms(t0)
        logger.info("社員番号検索 完了: %d 件ヒット. %.1f ms", len(hits), elapsed)
        return SearchResponse(total=len(hits), hits=hits, elapsed=elapsed)

    except Exception as e:
        logger.error("search_emp_by_emp_id ERROR: %s", e)
        raise


# =============================================================================
# 部署コード or 部署名で社員リストを検索
# =============================================================================
def search_emplist_by_d(did: Optional[str], dname: Optional[str]) -> SearchResponse:
    """
    部署コード (did) または部署名 (dname) で社員リストを検索する。
    did と dname どちらか片方は必ず指定されている前提（スキーマ側でバリデーション済み）。

    【絞り込み優先順位】
      did が指定されていれば部署コードで絞り込む。
      did が空 / None の場合は部署名 (dname) で絞り込む。

    Args:
        did  : 所属部署コード（例: "D001"）。None または空文字の場合は dname を使う
        dname: 部署名（例: "総務部"）。did が指定されている場合は無視される

    Returns:
        SearchResponse: ヒット件数・結果リスト・処理時間（ms）
    """
    # emp テーブルの存在を確認する。なければ例外を投げる。
    _require_emp_table()
    t0 = time.time()
    try:
        # ---------------------------------------------------------------
        # まず JOIN の土台となるクエリを作る（WHERE は後で追加）
        # 生 SQL に換算すると下記と同等:
        #   SELECT emp.*, dept.dept_name
        #   FROM emp
        #   LEFT JOIN dept ON emp.did = dept.dept_id
        # ---------------------------------------------------------------
        stmt = (
            select(Emp, Dept.dept_name)
            .outerjoin(Dept, Emp.did == Dept.dept_id)
        )

        # ---------------------------------------------------------------
        # WHERE 句を動的に追加する
        #   did が指定されていれば: WHERE emp.did = :did
        #   なければ             : WHERE dept.dept_name = :dname
        # ---------------------------------------------------------------
        if did and did.strip():
            stmt = stmt.where(Emp.did == did.strip())
        else:
            stmt = stmt.where(Dept.dept_name == dname)

        with SessionLocal() as s:
            rows = s.execute(stmt).all()

        # ---------------------------------------------------------------
        # クエリ結果を HitItem のリストに変換する
        # ---------------------------------------------------------------
        hits = [
            HitItem(
                emp_id=emp.emp_id,
                name=emp.emp_name,
                kana=emp.emp_kana,
                mail=emp.mail,
                did=emp.did,
                dname=dept_name or "",
            )
            for emp, dept_name in rows
        ]

        elapsed = elapsed_ms(t0)
        logger.info("部署別社員リスト検索 完了: %d 件ヒット. %.1f ms", len(hits), elapsed)
        return SearchResponse(total=len(hits), hits=hits, elapsed=elapsed)

    except Exception as e:
        logger.error("search_emplist_by_d ERROR: %s", e)
        raise
