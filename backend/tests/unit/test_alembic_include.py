"""alembic autogenerate 白名單:只納管 SQLModel metadata 的表,管線表絕不觸碰。"""
from app.alembic.env_filters import include_object


class _FakeTable:
    def __init__(self, name: str) -> None:
        self.name = name


def test_pipeline_tables_excluded_when_reflected():
    for name in ["documents", "game_cases", "document_chunks", "staging_documents",
                 "fraud_categories", "document_categories", "category_evidence"]:
        assert include_object(_FakeTable(name), name, "table", reflected=True, compare_to=None) is False


def test_game_tables_included():
    for name in ["user", "scenario_session", "swipe_card", "property_tier"]:
        assert include_object(_FakeTable(name), name, "table", reflected=True, compare_to=None) is True


def test_non_table_objects_pass_through():
    assert include_object(object(), "whatever_idx", "index", reflected=True, compare_to=None) is True
