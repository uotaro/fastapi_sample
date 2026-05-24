"""
test/test_health.py
===================
ヘルスチェック・サーバー情報エンドポイントのテスト

テスト対象:
  GET /health
  GET /info
"""


# =============================================================================
# GET /health
# =============================================================================

def test_health_status_200(client):
    """GET /health が 200 を返すことを確認する。"""
    res = client.get("/health")
    assert res.status_code == 200


def test_health_response_fields(client):
    """GET /health のレスポンスに必須フィールドが含まれることを確認する。"""
    res = client.get("/health")
    body = res.json()
    assert "status" in body
    assert "db" in body
    assert "llm_model" in body
    assert "version" in body


def test_health_status_value(client):
    """ダミー実装では status が "ok" になることを確認する。"""
    res = client.get("/health")
    body = res.json()
    assert body["status"] == "ok"
    assert body["db"] == "connected"
    assert body["llm_model"] == "loaded"


# =============================================================================
# GET /info
# =============================================================================

def test_info_status_200(client):
    """GET /info が 200 を返すことを確認する。"""
    res = client.get("/info")
    assert res.status_code == 200


def test_info_response_fields(client):
    """GET /info のレスポンスに app・version フィールドが含まれることを確認する。"""
    res = client.get("/info")
    body = res.json()
    assert "app" in body
    assert "version" in body


def test_info_sets_cookie(client):
    """GET /info が TEST_TOKEN クッキーをセットすることを確認する。"""
    res = client.get("/info")
    assert "TEST_TOKEN" in res.cookies
