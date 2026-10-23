"""試測問卷：誰能填、何時能填、只能交一次、計時，以及匯出與發錢條件。"""

import csv
import io
import uuid
from collections.abc import Generator
from datetime import timedelta
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, delete

from app.core.config import settings
from app.models import (
    Cohort,
    ExamAttempt,
    PretestAttempt,
    TrialSurvey,
    User,
    get_datetime_utc,
)
from app.trial.survey import ATTENTION_ID, QUESTIONS

BASE = settings.API_V1_STR


@pytest.fixture
def cohort(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> Generator[dict, None, None]:
    response = client.post(
        f"{BASE}/admin/cohorts",
        json={"name": "問卷梯次"},
        headers=superuser_token_headers,
    )
    assert response.status_code == 200, response.text
    data = response.json()
    yield data
    db.execute(delete(User).where(User.cohort_id == uuid.UUID(data["id"])))
    db.execute(delete(Cohort).where(Cohort.id == uuid.UUID(data["id"])))
    db.commit()


def redeem(client: TestClient, token: str) -> tuple[dict[str, str], uuid.UUID]:
    response = client.post(f"{BASE}/invite/{token}/redeem")
    assert response.status_code == 200, response.text
    headers = {"Authorization": f"Bearer {response.json()['access_token']}"}
    me = client.get(f"{BASE}/users/me", headers=headers).json()
    return headers, uuid.UUID(me["id"])


def answers(attention: int = 4) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for q in QUESTIONS:
        if q.kind == "consent":
            result[q.id] = True
        elif q.kind == "single":
            result[q.id] = q.options[0]
        elif q.kind == "multi":
            result[q.id] = [q.options[0]]
        elif q.kind == "scale":
            result[q.id] = 4
    result[ATTENTION_ID] = attention
    return result


def add_exam(db: Session, user_id: uuid.UUID, seconds: float, **kw: Any) -> None:
    start = get_datetime_utc() - timedelta(hours=2)
    values: dict[str, Any] = {
        "mode": "specialized",
        "fraud_type": "romance",
        "status": "completed",
        "expires_at": start + timedelta(hours=1),
        "created_at": start,
        "completed_at": start + timedelta(seconds=seconds),
        "total_score": 80,
        **kw,
    }
    db.add(ExamAttempt(user_id=user_id, **values))
    db.commit()


def summary(client: TestClient, headers: dict[str, str]) -> dict[str, Any]:
    response = client.get(f"{BASE}/home/summary", headers=headers)
    assert response.status_code == 200, response.text
    return response.json()  # type: ignore[no-any-return]


def test_only_trial_accounts(
    client: TestClient, normal_user_token_headers: dict[str, str]
) -> None:
    for method, path in [
        ("get", "/trial/survey"),
        ("post", "/trial/survey/start"),
        ("post", "/trial/survey"),
    ]:
        kwargs = {"json": {"answers": {}}} if method == "post" else {}
        response = getattr(client, method)(
            f"{BASE}{path}", headers=normal_user_token_headers, **kwargs
        )
        assert response.status_code == 400
        assert response.json()["detail"]["code"] == "trial_only"
    home = summary(client, normal_user_token_headers)
    assert home["survey_pending"] is False and home["survey_ready"] is False


def test_survey_needs_a_finished_exam_then_submits_once(
    client: TestClient, cohort: dict, db: Session
) -> None:
    headers, user_id = redeem(client, cohort["token"])
    data = client.get(f"{BASE}/trial/survey", headers=headers).json()
    assert [q["id"] for q in data["questions"]] == [q.id for q in QUESTIONS]
    assert data["questions"][0]["kind"] == "consent"
    assert (data["started"], data["submitted"], data["exam_done"]) == (
        False,
        False,
        False,
    )
    home = summary(client, headers)
    assert home["survey_pending"] is True and home["survey_ready"] is False

    # 檢測還沒交卷（放棄的不算）就不能開始
    add_exam(db, user_id, 600, status="abandoned")
    response = client.post(f"{BASE}/trial/survey/start", headers=headers)
    assert response.json()["detail"]["code"] == "exam_required"
    response = client.post(
        f"{BASE}/trial/survey", headers=headers, json={"answers": answers()}
    )
    assert response.json()["detail"]["code"] == "survey_not_started"

    add_exam(db, user_id, 600)
    assert summary(client, headers)["survey_ready"] is True
    response = client.post(f"{BASE}/trial/survey/start", headers=headers)
    assert response.status_code == 200, response.text
    assert response.json()["started"] is True
    # 計時從第一次開始算，重開問卷頁不會重新計時
    survey = db.get(TrialSurvey, user_id)
    assert survey is not None
    survey.started_at = get_datetime_utc() - timedelta(seconds=90)
    db.add(survey)
    db.commit()
    client.post(f"{BASE}/trial/survey/start", headers=headers)

    bad = answers()
    bad["satisfied"] = 9
    response = client.post(
        f"{BASE}/trial/survey", headers=headers, json={"answers": bad}
    )
    assert response.status_code == 400
    assert response.json()["detail"]["code"] == "survey_invalid"
    assert response.json()["detail"]["question_id"] == "satisfied"

    response = client.post(
        f"{BASE}/trial/survey", headers=headers, json={"answers": answers(attention=2)}
    )
    assert response.status_code == 200, response.text
    assert response.json()["submitted"] is True
    # 回應不透露注意力題的結果
    assert set(response.json()) == {"questions", "started", "submitted", "exam_done"}
    db.expire_all()
    survey = db.get(TrialSurvey, user_id)
    assert survey is not None and survey.submitted_at is not None
    assert survey.attention_ok is False
    assert survey.duration_seconds is not None and 89 <= survey.duration_seconds < 120

    response = client.post(
        f"{BASE}/trial/survey", headers=headers, json={"answers": answers()}
    )
    assert response.json()["detail"]["code"] == "survey_submitted"
    home = summary(client, headers)
    assert home["survey_pending"] is False and home["survey_ready"] is False


def read_csv(
    client: TestClient, cohort: dict, headers: dict[str, str], name: str
) -> list[dict[str, str]]:
    response = client.get(
        f"{BASE}/admin/cohorts/{cohort['id']}/{name}", headers=headers
    )
    assert response.status_code == 200, response.text
    assert response.content.startswith(b"\xef\xbb\xbf")
    return list(csv.DictReader(io.StringIO(response.content.decode("utf-8-sig"))))


def submit(
    client: TestClient,
    db: Session,
    headers: dict[str, str],
    user_id: uuid.UUID,
    seconds: float,
    payload: dict[str, Any],
) -> None:
    assert client.post(f"{BASE}/trial/survey/start", headers=headers).status_code == 200
    survey = db.get(TrialSurvey, user_id)
    assert survey is not None
    survey.started_at = get_datetime_utc() - timedelta(seconds=seconds)
    db.add(survey)
    db.commit()
    response = client.post(
        f"{BASE}/trial/survey", headers=headers, json={"answers": payload}
    )
    assert response.status_code == 200, response.text


def test_export_payout_rules_and_survey_csv(
    client: TestClient,
    cohort: dict,
    db: Session,
    superuser_token_headers: dict[str, str],
) -> None:
    good_headers, good = redeem(client, cohort["token"])
    rushed_headers, rushed = redeem(client, cohort["token"])
    _, idle = redeem(client, cohort["token"])
    start = get_datetime_utc() - timedelta(days=1)
    # 第一次前測才算：good 第一次 75 秒、重做 5 秒；rushed 第一次 20 秒
    for user_id, seconds, offset in [(good, 75.4, 0), (good, 5, 1), (rushed, 20, 0)]:
        db.add(
            PretestAttempt(
                user_id=user_id,
                weakest_type="atm",
                duration_seconds=seconds,
                created_at=start + timedelta(hours=offset),
            )
        )
    db.commit()
    # good 有一次考太快、一次考夠久：看最長的那次
    add_exam(db, good, 100)
    add_exam(db, good, 400)
    add_exam(db, rushed, 120)
    submit(client, db, good_headers, good, 200, answers())
    rushed_answers = answers(attention=1)
    rushed_answers["favorite"] = "其他"
    rushed_answers["favorite_other"] = "=HYPERLINK()"
    submit(client, db, rushed_headers, rushed, 30, rushed_answers)

    rows = {
        row["user_id"]: row
        for row in read_csv(client, cohort, superuser_token_headers, "export.csv")
    }
    row = rows[str(good)]
    assert row["pretest_seconds"] == "75"
    assert row["exam_seconds"] == "400"
    assert row["survey_done"] == "true" and row["survey_attention_ok"] == "true"
    assert 199 <= int(row["survey_seconds"]) <= 230
    assert row["payout_eligible"] == "true" and row["payout_reasons"] == ""

    row = rows[str(rushed)]
    assert row["payout_eligible"] == "false"
    assert row["payout_reasons"] == "前測太快；檢測太快；問卷注意力題答錯；問卷太快"

    row = rows[str(idle)]
    assert row["payout_eligible"] == "false"
    assert row["payout_reasons"] == "前測沒做；檢測沒有交卷；問卷沒填"
    assert row["survey_done"] == "false" and row["survey_seconds"] == ""

    # 管理頁的進度和成員 CSV 是同一套判定
    response = client.get(
        f"{BASE}/admin/cohorts/{cohort['id']}/progress",
        headers=superuser_token_headers,
    )
    assert response.status_code == 200, response.text
    progress = response.json()
    assert (
        progress["member_count"],
        progress["pretest_done"],
        progress["exam_completed"],
        progress["survey_done"],
        progress["payout_eligible"],
    ) == (3, 2, 2, 2, 1)
    by_code = {m["participant_code"]: m for m in progress["members"]}
    for user_id, row in rows.items():
        code = db.get(User, uuid.UUID(user_id)).participant_code  # type: ignore[union-attr]
        member = by_code[code]
        assert str(member["payout_eligible"]).lower() == row["payout_eligible"]
        assert "；".join(member["payout_reasons"]) == row["payout_reasons"]
    good_code = db.get(User, good).participant_code  # type: ignore[union-attr]
    assert by_code[good_code]["pretest_seconds"] == 75
    assert by_code[good_code]["exam_seconds"] == 400
    assert by_code[good_code]["survey_attention_ok"] is True
    lists = client.get(f"{BASE}/admin/cohorts", headers=superuser_token_headers)
    listed = next(c for c in lists.json() if c["id"] == cohort["id"])
    assert listed["member_count"] == 3

    survey_rows = read_csv(client, cohort, superuser_token_headers, "survey.csv")
    assert len(survey_rows) == 2
    by_code = {r["participant_code"]: r for r in survey_rows}
    fields = list(survey_rows[0])
    assert fields[:4] == [
        "participant_code",
        "submitted_at",
        "survey_seconds",
        "survey_attention_ok",
    ]
    assert "favorite_other" in fields and ATTENTION_ID in fields
    codes = {
        u.id: u.participant_code
        for u in (db.get(User, good), db.get(User, rushed))
        if u
    }
    rushed_row = by_code[str(codes[rushed])]
    assert rushed_row["survey_attention_ok"] == "false"
    assert rushed_row["favorite"] == "其他"
    # 使用者寫的字開頭是公式符號要中和
    assert rushed_row["favorite_other"] == "'=HYPERLINK()"
    good_row = by_code[str(codes[good])]
    assert good_row["consent"] == "true"
    assert good_row["satisfied"] == "4"
    assert good_row["improve"] == ""
