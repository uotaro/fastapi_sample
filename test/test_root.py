"""
test/test_root.py
=================
ルートエンドポイント（GET /）のテスト
"""


def test_root_returns_hello(client):
    """GET / が 200 を返し、JSON に "message" キーが含まれることを確認する。"""
    res = client.get("/")
    assert res.status_code == 200
    body = res.json()
    assert "message" in body
