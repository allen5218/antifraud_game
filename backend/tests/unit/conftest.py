"""純 Python 單元測試——不需要資料庫連線"""

import pytest


@pytest.fixture(scope="session", autouse=True)
def db():  # type: ignore
    """覆寫上層 conftest 的 db fixture，避免連接 PostgreSQL"""
    yield None
