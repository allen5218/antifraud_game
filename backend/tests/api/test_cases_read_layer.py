from sqlmodel import Session

from app.core.cases import GameCaseRow, get_case, list_published, pick_case


def test_list_published_returns_rows(db: Session) -> None:
    rows = list_published(db, limit=5)
    assert 1 <= len(rows) <= 5
    assert all(isinstance(r, GameCaseRow) for r in rows)
    assert all(r.narrative and r.provenance for r in rows)


def test_list_published_filters_fraud_type(db: Session) -> None:
    rows = list_published(db, fraud_type="investment", limit=10)
    assert rows and all(r.fraud_type == "investment" for r in rows)


def test_pick_case_matches_stance(db: Session) -> None:
    case = pick_case(db, fraud_type="romance", is_scam=True)
    assert case is not None and case.is_scam is True and case.fraud_type == "romance"


def test_get_case_roundtrip_and_missing(db: Session) -> None:
    some = list_published(db, limit=1)[0]
    fetched = get_case(db, some.id)
    assert fetched is not None and fetched.id == some.id
    assert get_case(db, 999999999) is None
