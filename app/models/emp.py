# 社員テーブル定義
# テーブル名: emp
# カラム:
#  - emp_id: str, 社員番号, 主キー
#  - emp_name: str, 社員名
#  - emp_kana: str, 社員かな名
#  - mail: str, メールアドレス
#  - did: str, 所属部署コード
#  - birth_date: str, 生年月日
#  - start_date: str, 入社日
#  - end_date: str, 退社日

from sqlalchemy import Column, Text
from app.db.session import Base

class Emp(Base):
    __tablename__ = "emp"
    emp_id     = Column(Text, primary_key=True)
    emp_name   = Column(Text, nullable=False)
    emp_kana   = Column(Text, nullable=False)
    mail       = Column(Text, nullable=False)
    did        = Column(Text, nullable=False)
    birth_date = Column(Text, nullable=False)
    start_date = Column(Text, nullable=False)
    end_date   = Column(Text, nullable=True)
