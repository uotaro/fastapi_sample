# 所属部署テーブル定義
# テーブル名: dept
# カラム:
# - dept_id: str, 所属部署コード。主キー
# - dept_name: str, 部署名

from sqlalchemy import Column, Text
from app.db.session import Base

class Dept(Base):
    __tablename__ = "dept"
    dept_id   = Column(Text, primary_key=True)
    dept_name = Column(Text, nullable=False)
