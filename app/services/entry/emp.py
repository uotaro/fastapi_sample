"""
/app/services/entry/emp.py
===================================
社員情報登録サービス
"""
from sqlalchemy import inspect

from app.db.session import engine, SessionLocal, Base
from app.models.dept import Dept
from app.models.emp import Emp
from app.utils.logger import get_logger

logger = get_logger(__name__)

# ORM インスタンスをモジュールレベルで持つと、一度 commit した後は
# SQLAlchemy が「変更なし」と判断して INSERT を発行しなくなるため、
# データ定義は辞書リストで保持し、呼び出し時に毎回新しいインスタンスを生成する。
_INITIAL_DEPT_DATA = [
    {"dept_id": "D001", "dept_name": "総務部"},
    {"dept_id": "D002", "dept_name": "人事部"},
    {"dept_id": "D003", "dept_name": "営業部"},
    {"dept_id": "D004", "dept_name": "技術部"},
]

_INITIAL_EMP_DATA = [
    {"emp_id": "E001", "emp_name": "近藤勇",   "emp_kana": "こんどういさむ",     "mail": "ikondo@example.com",    "did": "D001", "birth_date": "1990-01-01", "start_date": "2020-04-01", "end_date": ""},
    {"emp_id": "E002", "emp_name": "土方歳三", "emp_kana": "ひじかたとしぞう",   "mail": "thijikata@example.com", "did": "D002", "birth_date": "1992-05-15", "start_date": "2021-03-01", "end_date": ""},
    {"emp_id": "E003", "emp_name": "井上源三郎","emp_kana": "いのうえげんざろう", "mail": "ginoue@example.com",    "did": "D003", "birth_date": "1988-12-10", "start_date": "2019-07-01", "end_date": ""},
    {"emp_id": "E004", "emp_name": "藤堂平助", "emp_kana": "とうどうへいすけ",   "mail": "htoudo@example.com",    "did": "D004", "birth_date": "1995-08-20", "start_date": "2022-01-01", "end_date": ""},
    {"emp_id": "E005", "emp_name": "前田慶次", "emp_kana": "まえだけいじ",       "mail": "maeda@example.com",     "did": "D003", "birth_date": "1988-12-10", "start_date": "2019-07-01", "end_date": ""},
    {"emp_id": "E006", "emp_name": "澤村遥",   "emp_kana": "さわむらはるか",     "mail": "sawamura@example.com",  "did": "D004", "birth_date": "2001-11-25", "start_date": "2026-10-01", "end_date": ""},
    {"emp_id": "E007", "emp_name": "山南敬助", "emp_kana": "やみなみけいすけ",   "mail": "kyamanami@example.com", "did": "D004", "birth_date": "1990-03-15", "start_date": "2021-09-01", "end_date": ""},
    {"emp_id": "E008", "emp_name": "永倉新八", "emp_kana": "ながくらしんぱち",   "mail": "snagakura@example.com", "did": "D004", "birth_date": "1991-09-12", "start_date": "2020-06-01", "end_date": ""},
]

def _init_dept() -> None:
    """
    部署テーブルの初期化。
    テーブルが存在しない場合のみ作成して初期データを登録する。
    """
    try:
        # 部署テーブルが存在しない場合は作成する
        if not inspect(engine).has_table("dept"):
            Base.metadata.create_all(engine, tables=[Dept.__table__])
            # 初期データ登録（毎回新しいインスタンスを生成）
            with SessionLocal() as session:
                session.add_all([Dept(**d) for d in _INITIAL_DEPT_DATA])
                session.commit()
            logger.info("部署テーブルを作成し初期データを登録しました")
    except Exception as e:
        logger.error(f"部署情報テーブル初期化エラー: {e}")
        raise ValueError(f"部署情報テーブル初期化に失敗しました。{e}")

def _init_emp() -> None:
    """
    社員テーブルの初期化。
    テーブルが存在しない場合のみ作成して初期データを登録する。
    """
    try:
        # 社員テーブルが存在しない場合は作成する
        if not inspect(engine).has_table("emp"):
            Base.metadata.create_all(engine, tables=[Emp.__table__])
            # 初期データ登録（毎回新しいインスタンスを生成）
            with SessionLocal() as session:
                session.add_all([Emp(**e) for e in _INITIAL_EMP_DATA])
                session.commit()
            logger.info("社員テーブルを作成し初期データを登録しました")
    except Exception as e:
        logger.error(f"社員情報テーブル初期化エラー: {e}")
        raise ValueError(f"社員情報テーブル初期化に失敗しました。{e}")
        
def init_db() -> str:
    """
    dept・emp テーブルを初期データで作成する。
    テーブルがすでに存在する場合は何もしない。

    Returns:
        処理結果のメッセージ
    """
    dept_created = not inspect(engine).has_table("dept")
    emp_created  = not inspect(engine).has_table("emp")

    _init_dept()
    _init_emp()

    if dept_created and emp_created:
        return "dept・emp テーブルを初期データで作成しました。"
    elif dept_created:
        return "dept テーブルを初期データで作成しました。emp テーブルはすでに存在します。"
    elif emp_created:
        return "emp テーブルを初期データで作成しました。dept テーブルはすでに存在します。"
    else:
        return "dept・emp テーブルはすでに存在します。何もしませんでした。"


def entry_emp(emp_data: dict) -> bool:
    """
    社員情報登録処理。
    - 登録前に部署テーブルの初期化を行う
    - 社員テーブルが存在しない場合は作成する
    - 社員データを登録する

    Args:
        emp_data: EmpEntryRequest.model_dump() の結果
    Returns:
        True: 登録成功
    """
    try:
        # 登録前に部署テーブルの初期化を行う
        _init_dept()
        # 社員テーブルが存在しない場合は作成する
        _init_emp()
        # 社員データを登録する      
        emp = Emp(
            emp_id=emp_data["emp_id"],
            emp_name=emp_data["emp_name"],
            emp_kana=emp_data["emp_kana"],
            mail=emp_data["mail"],
            did=emp_data["did"],
            birth_date=emp_data["birth_date"],
            start_date=emp_data["start_date"],
            end_date=emp_data["end_date"],
        )
        with SessionLocal() as session:
            session.add(emp)
            session.commit()
        logger.info(f"社員登録完了: {emp_data['emp_id']}")
        return True

    except Exception as e:
        logger.error(f"社員情報登録エラー: {e}")
        raise
