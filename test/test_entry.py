"""
test/test_entry.py
==================
社員データ登録エンドポイントのテスト

テスト対象:
  POST /entry/init  – DB 初期化（テーブル作成＋初期データ登録）
  POST /entry/emp   – 社員データ1件登録
"""

import pytest


# =============================================================================
# POST /entry/init
# =============================================================================

def test_init_creates_tables(client, clean_db):
    """POST /entry/init が 200 を返し success=True になることを確認する。"""
    res = client.post("/entry/init")
    assert res.status_code == 200
    body = res.json()
    assert body["success"] is True


def test_init_idempotent(client, clean_db):
    """POST /entry/init を2回呼んでも 200 が返ることを確認する（冪等性）。"""
    client.post("/entry/init")
    res = client.post("/entry/init")
    assert res.status_code == 200
    body = res.json()
    assert body["success"] is True


# =============================================================================
# POST /entry/emp
# =============================================================================

_NEW_EMP = {
    "emp_id": "E099",
    "emp_name": "テスト太郎",
    "emp_kana": "てすとたろう",
    "mail": "test.taro@example.com",
    "did": "D001",
    "birth_date": "2000-01-01",
    "start_date": "2024-04-01",
    "end_date": "",
}


def test_entry_emp_success(client, clean_db):
    """POST /entry/emp で社員データが正常に登録できることを確認する。"""
    # テーブルが存在しない状態からの登録（サービス内で自動初期化される）
    res = client.post("/entry/emp", json=_NEW_EMP)
    assert res.status_code == 200
    body = res.json()
    assert body["success"] is True


def test_entry_emp_can_search_after_entry(client, clean_db):
    """登録した社員が /search/emp で検索できることを確認する（結合テスト）。"""
    client.post("/entry/emp", json=_NEW_EMP)
    res = client.post("/search/emp", json={"emp_id": _NEW_EMP["emp_id"]})
    assert res.status_code == 200
    body = res.json()
    assert body["total"] == 1
    assert body["hits"][0]["emp_id"] == _NEW_EMP["emp_id"]


@pytest.mark.parametrize("missing_field", ["emp_id", "emp_name", "emp_kana", "mail"])
def test_entry_emp_missing_required_field(client, missing_field):
    """必須フィールドが欠けている場合に 422 が返ることを確認する。"""
    payload = dict(_NEW_EMP)
    del payload[missing_field]
    res = client.post("/entry/emp", json=payload)
    assert res.status_code == 422


def test_entry_emp_empty_emp_id(client):
    """emp_id が空文字の場合に 422 が返ることを確認する（min_length=1 バリデーション）。"""
    payload = dict(_NEW_EMP, emp_id="")
    res = client.post("/entry/emp", json=payload)
    assert res.status_code == 422
