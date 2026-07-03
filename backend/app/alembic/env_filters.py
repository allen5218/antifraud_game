"""alembic autogenerate 的物件過濾:遊戲表白名單。

資料管線(data_pipeline skill)在同一個 Supabase 庫用原生 SQL 管理自己的表;
它們不在 SQLModel metadata 裡。若無此過濾,autogenerate 會把反射到的管線表
視為「多餘」而生成 DROP 遷移。
"""
from typing import Any

from sqlmodel import SQLModel

from app import models as _models  # noqa: F401  # 確保所有遊戲表已註冊進 metadata


def include_object(
    obj: Any, name: str, type_: str, reflected: bool, compare_to: Any
) -> bool:
    if type_ == "table":
        return name in SQLModel.metadata.tables
    return True
