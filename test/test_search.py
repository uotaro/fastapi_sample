"""
test/test_search.py
===================
社員検索エンドポイントのテスト

テスト対象:
  POST /search/emp      – 社員番号で1件検索
  POST /search/emplist  – 部署コード or 部署名でリスト検索
"""

import pytest


# =============================================================================
# 共通フィクスチャ: テスト用初期データを /entry/init で投入する
# =============================================================================

@pytest.fixture(autouse=True)
def init_data(client, clean_db):
    """各テスト前に DB を初期化して初期データを登録する。"""
    client.post("/entry/init")


# =============================================================================
# POST /search/emp  – 社員番号検索
# =============================================================================

def test_search_emp_hit(client):
    """初期データの社員番号で検索してヒットすることを確認する。"""
    res = client.post("/search/emp", json={"emp_id": "E001"})
    assert res.status_code == 200
    body = res.json()
    assert body["total"] == 1
    assert body["hits"][0]["emp_id"] == "E001"
    assert body["hits"][0]["name"] == "近藤勇"


def test_search_emp_returns_dept_name(client):
    """検索結果に部署名（dname）が含まれることを確認する。"""
    res = client.post("/search/emp", json={"emp_id": "E001"})
    body = res.json()
    assert body["hits"][0]["dname"] == "総務部"


def test_search_emp_not_found(client):
    """存在しない社員番号で検索すると total=0 になることを確認する。"""
    res = client.post("/search/emp", json={"emp_id": "Z999"})
    assert res.status_code == 200
    body = res.json()
    assert body["total"] == 0
    assert body["hits"] == []


def test_search_emp_has_elapsed(client):
    """レスポンスに elapsed（処理時間）が含まれることを確認する。"""
    res = client.post("/search/emp", json={"emp_id": "E001"})
    body = res.json()
    assert "elapsed" in body
    assert body["elapsed"] >= 0


def test_search_emp_missing_emp_id(client):
    """emp_id を指定しないと 422 が返ることを確認する。"""
    res = client.post("/search/emp", json={})
    assert res.status_code == 422


def test_search_emp_empty_emp_id(client):
    """emp_id が空文字だと 422 が返ることを確認する（min_length=1 バリデーション）。"""
    res = client.post("/search/emp", json={"emp_id": ""})
    assert res.status_code == 422


# =============================================================================
# POST /search/emplist  – 部署別社員リスト検索
# =============================================================================

def test_search_emplist_by_did(client):
    """部署コード (did) で絞り込んで社員リストが返ることを確認する。"""
    res = client.post("/search/emplist", json={"did": "D004"})
    assert res.status_code == 200
    body = res.json()
    # D004（技術部）には初期データで4名所属している
    assert body["total"] == 4
    for hit in body["hits"]:
        assert hit["did"] == "D004"


def test_search_emplist_by_dname(client):
    """部署名 (dname) で絞り込んで社員リストが返ることを確認する。"""
    res = client.post("/search/emplist", json={"dname": "営業部"})
    assert res.status_code == 200
    body = res.json()
    # D003（営業部）には初期データで2名所属している
    assert body["total"] == 2
    for hit in body["hits"]:
        assert hit["dname"] == "営業部"


def test_search_emplist_did_takes_priority_over_dname(client):
    """did と dname を両方指定した場合、did が優先されることを確認する。"""
    res = client.post("/search/emplist", json={"did": "D001", "dname": "営業部"})
    assert res.status_code == 200
    body = res.json()
    # D001（総務部）の社員だけが返るはず
    assert body["total"] >= 1
    for hit in body["hits"]:
        assert hit["did"] == "D001"


def test_search_emplist_not_found(client):
    """存在しない部署コードで検索すると total=0 になることを確認する。"""
    res = client.post("/search/emplist", json={"did": "D999"})
    assert res.status_code == 200
    body = res.json()
    assert body["total"] == 0


def test_search_emplist_no_params_returns_422(client):
    """did も dname も指定しない場合に 422 が返ることを確認する（スキーマバリデーション）。"""
    res = client.post("/search/emplist", json={})
    assert res.status_code == 422


def test_search_emplist_has_elapsed(client):
    """レスポンスに elapsed（処理時間）が含まれることを確認する。"""
    res = client.post("/search/emplist", json={"did": "D001"})
    body = res.json()
    assert "elapsed" in body
    assert body["elapsed"] >= 0
