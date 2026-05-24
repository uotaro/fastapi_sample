"""
test/conftest.py
================
pytest 共通フィクスチャ

テスト用インメモリ SQLite DB を使うため、アプリのモジュールをインポートする前に
SQLITE_DB_PATH 環境変数を上書きし、engine / SessionLocal をテスト用DBへ差し替える。
"""

import os
import pytest
import tempfile

# ── テスト用 DB はテンポラリファイルを使う ──────────────────────────────────
#   インメモリ (:memory:) は同一スレッド・同一接続でないとデータが共有されないため
#   テンポラリファイルを使用する。
_tmp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
_tmp_db.close()
_TEST_DB_PATH = _tmp_db.name

# アプリの設定・エンジンよりも先に環境変数を上書きする（モジュールロード前が必須）
os.environ["SQLITE_DB_PATH"] = _TEST_DB_PATH

# ── アプリのインポートは環境変数セット後に行う ─────────────────────────────
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import app.db.session as db_session
from app.db.session import Base
from app.models import dept, emp  # noqa: F401 – テーブルメタデータを登録する

# テスト用エンジンを再構築してモジュールレベルのオブジェクトを差し替える
_test_engine = create_engine(
    f"sqlite:///{_TEST_DB_PATH}",
    connect_args={"check_same_thread": False},
)
_TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_test_engine)

db_session.engine = _test_engine
db_session.SessionLocal = _TestSessionLocal

# サービス側でも直接インポートしているため、そちらも差し替える
import app.services.entry.emp as entry_emp_svc
import app.services.search.emp as search_emp_svc

entry_emp_svc.engine = _test_engine
entry_emp_svc.SessionLocal = _TestSessionLocal
search_emp_svc.engine = _test_engine
search_emp_svc.SessionLocal = _TestSessionLocal

# ── FastAPI TestClient ────────────────────────────────────────────────────────
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture(scope="session")
def client():
    """セッション全体で共有する TestClient。"""
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="session", autouse=True)
def setup_db():
    """テストセッション開始時にテーブルを作成し、終了時に DB ファイルを削除する。"""
    Base.metadata.create_all(_test_engine)
    yield
    Base.metadata.drop_all(_test_engine)
    _test_engine.dispose()
    try:
        os.unlink(_TEST_DB_PATH)
    except OSError:
        pass


@pytest.fixture()
def clean_db():
    """各テストの前後で emp・dept テーブルをリセットするフィクスチャ。
    テーブルを削除した状態で yield するので、テスト内（または依存フィクスチャ内）で
    /entry/init を呼べばテーブル作成＋初期データ投入まで行われる。
    使いたいテストだけ引数に指定する（autouse ではない）。"""
    Base.metadata.drop_all(_test_engine)
    yield
    Base.metadata.drop_all(_test_engine)
