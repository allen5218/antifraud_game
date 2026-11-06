"""檢測整合測試；素材與人格在測試內提供，不呼叫真實 AI。"""

import csv
import io
import json
import uuid
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import text
from sqlmodel import delete, select

from app.core.cases import (
    get_case,
    list_published_for_quiz,
    list_published_verification_questions,
    pick_case,
)
from app.core.config import settings
from app.models import (
    Cohort,
    ExamAttempt,
    ExamBadge,
    PracticeAnswer,
    ScenarioSession,
    SwipeCard,
    User,
)

API = settings.API_V1_STR


@pytest.fixture(autouse=True)
def exam_material(db, monkeypatch, tmp_path):
    for ft in ("investment", "shopping", "fake-sale", "romance", "atm"):
        for scam in (True, False):
            for _n in range(3):
                db.add(
                    SwipeCard(
                        pool="exam",
                        fraud_type=ft,
                        is_scam=scam,
                        scenario="測試專用訊息。",
                        source_label="訊息通知",
                    )
                )
        for pool, pairs in (
            ("exam_message", 8),
            ("exam_scenario", 2),
            ("exam_tactics", 2),
        ):
            for n in range(pairs):
                scam_id = db.execute(
                    text(
                        "INSERT INTO game_cases (case_key,fraud_type,is_scam,title,narrative,red_flags,provenance,status,pool) VALUES (:key,:ft,true,'聯絡人的訊息','請先看這份說明。',CAST(:flags AS jsonb),'測試素材','published',:pool) RETURNING id"
                    ),
                    {
                        "key": f"pytest-exam-{ft}-{pool}-{n}-scam",
                        "ft": ft,
                        "pool": pool,
                        "flags": json.dumps(
                            [
                                {"tag": "greed", "text": "承諾收益"},
                                {"tag": "authority", "text": "自稱專員"},
                            ]
                        ),
                    },
                ).scalar_one()
                if pool != "exam_tactics":
                    db.execute(
                        text(
                            "INSERT INTO game_cases (case_key,fraud_type,is_scam,title,narrative,red_flags,provenance,status,pool,mirror_of) VALUES (:key,:ft,false,'聯絡人的訊息','請先看這份說明。','[]','測試素材','published',:pool,:mirror)"
                        ),
                        {
                            "key": f"pytest-exam-{ft}-{pool}-{n}-legit",
                            "ft": ft,
                            "pool": pool,
                            "mirror": scam_id,
                        },
                    )
    db.commit()
    for ft in ("investment", "shopping", "fake-sale", "romance", "atm"):
        root = tmp_path / f"fraud-{ft}"
        (root / "personas").mkdir(parents=True)
        (root / "SKILL.md").write_text("檢測用領域知識", encoding="utf-8")
        for role in ("scammer", "legit", "exam-scammer", "exam-legit"):
            (root / "personas" / f"{role}.soul.md").write_text(
                "---\nname: 測試人物\nteaser: 你好，請先看說明。\nprimary_tactics: []\n---\n檢測人格",
                encoding="utf-8",
            )
    monkeypatch.setattr("app.scenario.agent.SKILLS_DIR", str(tmp_path))
    yield
    db.rollback()
    db.execute(delete(ExamBadge))
    db.execute(delete(ScenarioSession).where(ScenarioSession.pool == "exam"))
    db.execute(delete(ExamAttempt))
    db.execute(delete(SwipeCard).where(SwipeCard.pool == "exam"))
    db.execute(text("DELETE FROM game_cases WHERE case_key LIKE 'pytest-exam-%'"))
    db.commit()


def req(client, h, method, path, body=None):
    return getattr(client, method)(
        f"{API}{path}", headers=h, **({"json": body} if body is not None else {})
    )


def start(client, h, mode="specialized"):
    r = req(
        client,
        h,
        "post",
        "/exam/start",
        {
            "mode": mode,
            **({"fraud_type": "investment"} if mode == "specialized" else {}),
        },
    )
    assert r.status_code == 200, r.text
    return r.json()


def attempt(db, state):
    db.expire_all()
    row = db.get(ExamAttempt, uuid.UUID(state["id"]))
    assert row
    return row


def submit(client, h, db, state, stage, wrong=False):
    answers = []
    for item in attempt(db, state).items[stage]:
        if stage == "pretest":
            answers.append(
                {"question_id": item["id"], "selected_option": item["correct_option"]}
            )
        elif stage == "swipe":
            answers.append(
                {"card_id": item["id"], "guess_is_scam": item["is_scam"] != wrong}
            )
        elif item["kind"] == "tactics":
            answers.append(
                {
                    "item_id": item["item_id"],
                    "tags": [] if wrong else item["correct_tags"],
                }
            )
        else:
            answers.append(
                {"item_id": item["item_id"], "guess_is_scam": item["is_scam"] != wrong}
            )
    r = req(client, h, "post", f"/exam/{state['id']}/{stage}", {"answers": answers})
    assert r.status_code == 200, r.text
    return r.json(), answers


def finish(client, h, db, state, wrong=False):
    if state["stage"] == "pretest":
        state, _ = submit(client, h, db, state, "pretest")
    state, _ = submit(client, h, db, state, "swipe", wrong)
    state, _ = submit(client, h, db, state, "message", wrong)
    for _ in range(1 if state["mode"] == "comprehensive" else 2):
        r = req(client, h, "post", f"/exam/{state['id']}/scenario/start")
        assert r.status_code == 200, r.text
        sc = db.get(ScenarioSession, uuid.UUID(r.json()["scenario"]["session_id"]))
        action = "report" if (sc.persona_role == "scam") != wrong else "comply"
        r = req(
            client,
            h,
            "post",
            f"/exam/{state['id']}/scenario/judge",
            {"action": action, "session_id": str(sc.id)},
        )
        assert r.status_code == 200, r.text
        state = r.json()
    return state


@pytest.mark.parametrize("mode", ["comprehensive", "specialized"])
def test_cohort_exam_csv_full_workflow(client, superuser_token_headers, db, mode):
    admin = superuser_token_headers
    response = req(client, admin, "post", "/admin/cohorts", {"name": "檢測匯出試測"})
    assert response.status_code == 200
    cohort = response.json()
    token = client.post(f"{API}/invite/{cohort['token']}/redeem").json()["access_token"]
    h = {"Authorization": f"Bearer {token}"}
    me = req(client, h, "get", "/users/me").json()
    try:
        # 測試素材的代號也要像正式種子一樣可供分析者辨識。
        for card in db.exec(select(SwipeCard).where(SwipeCard.pool == "exam")).all():
            card.seed_key = f"exam-swipe-{card.id.hex}"
            db.add(card)
        db.commit()
        state = finish(client, h, db, start(client, h, mode))
        row = attempt(db, state)
        result = state["result"]
        response = req(client, admin, "get", f"/admin/cohorts/{cohort['id']}/exam.csv")
        assert response.status_code == 200, response.text
        rows = list(csv.DictReader(io.StringIO(response.content.decode("utf-8-sig"))))
        assert len(rows) == sum(len(items) for items in row.items.values())
        assert len(rows) == (30 if mode == "comprehensive" else 17)
        assert {item["correct"] for item in rows} == {"true"}
        assert {item["mode"] for item in rows} == {mode}
        assert {item["fraud_type"] for item in rows} == {row.fraud_type}
        assert {item["attempt_id"] for item in rows} == {state["id"]}
        assert {item["total_score"] for item in rows} == {str(result["total_score"])}
        assert {item["passed"] for item in rows} == {"true"}
        assert rows[0]["started_at"] == row.created_at.isoformat()
        assert rows[0]["completed_at"] == row.completed_at.isoformat()
        assert (
            float(rows[0]["duration_seconds"])
            == (row.completed_at - row.created_at).total_seconds()
        )
        for item in rows:
            assert item["participant_code"] == me["participant_code"]
            if item["stage"] == "pretest":
                assert item["item_key"] in {q["id"] for q in row.items["pretest"]}
                assert item["is_scam"] == ""
            elif item["stage"] == "swipe":
                assert item["item_key"].startswith("exam-swipe-")
            else:
                assert item["item_key"].startswith("pytest-exam-")
        response = req(
            client, admin, "get", f"/admin/cohorts/{cohort['id']}/export.csv"
        )
        summary = list(
            csv.DictReader(io.StringIO(response.content.decode("utf-8-sig")))
        )
        assert len(summary) == 1
        assert summary[0]["exam_attempt_count"] == summary[0]["exam_pass_count"] == "1"
        assert summary[0]["badges"] == result["badges"][0]["name"]
    finally:
        db.rollback()
        db.execute(delete(User).where(User.cohort_id == uuid.UUID(cohort["id"])))
        db.execute(delete(Cohort).where(Cohort.id == uuid.UUID(cohort["id"])))
        db.commit()


def test_practice_reads_exclude_exam(client, normal_user_token_headers, db):
    assert all(c.pool == "practice" for c in list_published_for_quiz(db))
    assert pick_case(db, fraud_type="investment", is_scam=True).pool == "practice"
    for q in list_published_verification_questions(db, limit=100):
        assert get_case(db, q.case_id).pool == "practice"
    r = req(client, normal_user_token_headers, "get", "/quick/swipe/deck")
    assert r.status_code == 200
    for card in r.json()["cards"]:
        assert db.get(SwipeCard, uuid.UUID(card["id"])).pool == "practice"


@pytest.mark.parametrize("mode", ["comprehensive", "specialized"])
def test_full_exam_and_first_badge_only(client, normal_user_token_headers, db, mode):
    h = normal_user_token_headers
    initial = start(client, h, mode)
    assert "is_scam" not in json.dumps(initial) and "correct_option" not in json.dumps(
        initial
    )
    for path in (
        "/quick/swipe/deck",
        "/quick/quiz/deck",
        "/pretest/questions",
        "/daily/today",
    ):
        r = req(client, h, "get", path)
        assert r.status_code == 400 and r.json()["detail"]["code"] == "exam_in_progress"
    assert req(client, h, "get", "/exam/active").json() == initial
    state = finish(client, h, db, initial)
    result = state["result"]
    assert result["total_score"] == 100 and result["passed"]
    assert result["weakness_score"] == (70 if mode == "comprehensive" else 100)
    assert result["reward"] == (
        {"cash": 5000, "xp": 300}
        if mode == "comprehensive"
        else {"cash": 3000, "xp": 150}
    )
    assert not any(
        key in json.dumps(state)
        for key in (
            "stage_scores",
            "true_role",
            "persona_role",
            "correct_tags",
            "is_scam",
        )
    )
    assert db.exec(select(PracticeAnswer)).all() == []
    again = finish(client, h, db, start(client, h, mode))
    assert again["result"]["reward"] == {"cash": 0, "xp": 0}
    assert len(req(client, h, "get", "/badges").json()) == 1
    badge = result["badges"][0]
    public = req(
        client, h, "patch", f"/badges/{badge['id']}", {"is_public": True}
    ).json()
    r = client.get(f"{API}/badges/public/{public['public_slug']}")
    assert r.status_code == 200
    assert (
        "score" not in r.text
        and "tested_type" not in r.text
        and "fraud_type" not in r.text
    )
    req(client, h, "patch", f"/badges/{badge['id']}", {"is_public": False})
    assert client.get(f"{API}/badges/public/{public['public_slug']}").status_code == 404


def test_stage_validation_retry_and_owner(
    client, normal_user_token_headers, superuser_token_headers, db
):
    h = normal_user_token_headers
    state = start(client, h)
    aid = state["id"]
    assert (
        req(client, superuser_token_headers, "get", f"/exam/{aid}").status_code == 404
    )
    assert (
        req(client, h, "post", f"/exam/{aid}/message", {"answers": []}).status_code
        == 400
    )
    assert (
        req(client, h, "post", f"/exam/{aid}/swipe", {"answers": []}).status_code == 400
    )
    state, answers = submit(client, h, db, state, "swipe")
    retry = req(client, h, "post", f"/exam/{aid}/swipe", {"answers": answers})
    assert retry.status_code == 200 and retry.json() == state
    answers[0]["guess_is_scam"] = not answers[0]["guess_is_scam"]
    assert (
        req(client, h, "post", f"/exam/{aid}/swipe", {"answers": answers}).status_code
        == 400
    )


def test_expiry_retake_focus_and_new_start_clears_gate(
    client, normal_user_token_headers, db
):
    h = normal_user_token_headers
    state = start(client, h)
    row = attempt(db, state)
    row.expires_at = datetime.now(timezone.utc) - timedelta(seconds=1)
    db.add(row)
    db.commit()
    assert req(client, h, "get", "/exam/active").json() is None
    status = req(client, h, "get", "/exam/status").json()
    assert status["block_reason"] == "retake_gate" and status["daily_used"] == 1
    profile = req(client, h, "get", "/practice/profile").json()
    assert (
        profile["focus_type"] == "investment"
        and profile["weights"]["investment"] == 0.5
    )
    assert profile["retake"]["gate"]["met"] is False
    assert "完成後就能再檢測" in profile["note"]
    row = attempt(db, state)
    for mode, n in (("swipe", 6), ("quiz", 5), ("scenario", 1)):
        for _ in range(n):
            db.add(
                PracticeAnswer(
                    user_id=row.user_id,
                    mode=mode,
                    fraud_type="investment",
                    correct=True,
                )
            )
    db.commit()
    assert req(client, h, "get", "/exam/status").json()["gate"]["met"]
    # 練滿之後、還沒重考前，練習重點卡要說可以再檢測，不能還叫人先練
    assert "可以再檢測" in req(client, h, "get", "/practice/profile").json()["note"]
    start(client, h)
    assert req(client, h, "get", "/practice/profile").json()["retake"] is None


def test_exam_scenario_failure_voids_and_training_never_reveals(
    client, normal_user_token_headers, db, monkeypatch
):
    h = normal_user_token_headers
    state = start(client, h)
    state, _ = submit(client, h, db, state, "swipe")
    state, _ = submit(client, h, db, state, "message")
    r = req(client, h, "post", f"/exam/{state['id']}/scenario/start")
    sid = r.json()["scenario"]["session_id"]
    assert (
        req(client, h, "post", f"/scenario/{sid}/judge", {"action": "report"}).json()[
            "detail"
        ]["code"]
        == "exam_session"
    )
    r = req(client, h, "get", "/scenario/inbox")
    assert r.status_code == 400 and r.json()["detail"]["code"] == "exam_in_progress"

    async def fail(*_args, **_kwargs):
        raise RuntimeError("模型失敗")

    monkeypatch.setattr("app.scenario.agent.generate_reply", fail)
    assert (
        req(client, h, "post", f"/scenario/{sid}/message", {"text": "你好"}).status_code
        == 502
    )
    db.expire_all()
    sc = db.get(ScenarioSession, uuid.UUID(sid))
    assert sc.player_turns == 0 and len(sc.conversation_history) == 1
    row = attempt(db, state)
    assert row.ai_error_at
    row.expires_at = datetime.now(timezone.utc) - timedelta(seconds=1)
    db.add(row)
    db.commit()
    state = req(client, h, "get", f"/exam/{state['id']}").json()
    assert state["status"] == "voided" and state["result"] is None
    status = req(client, h, "get", "/exam/status").json()
    assert status["daily_used"] == 0 and status["can_start"]
    # 檢測結束後收件匣恢復，但檢測用的對話不會混進練習收件匣
    assert all(i["id"] != sid for i in req(client, h, "get", "/scenario/inbox").json())


def test_judge_retry_cannot_answer_next_session(client, normal_user_token_headers, db):
    h = normal_user_token_headers
    state = start(client, h)
    state, _ = submit(client, h, db, state, "swipe")
    state, _ = submit(client, h, db, state, "message")
    state = req(client, h, "post", f"/exam/{state['id']}/scenario/start").json()
    sid = state["scenario"]["session_id"]
    sc = db.get(ScenarioSession, uuid.UUID(sid))
    action = "report" if sc.persona_role == "scam" else "comply"
    body = {"action": action, "session_id": sid}
    assert (
        req(client, h, "post", f"/exam/{state['id']}/scenario/judge", body).status_code
        == 200
    )
    state = req(client, h, "post", f"/exam/{state['id']}/scenario/start").json()
    retry = req(client, h, "post", f"/exam/{state['id']}/scenario/judge", body)
    assert retry.status_code == 200
    assert retry.json()["stage"] == "scenario"
    assert retry.json()["scenario"]["session_id"] == state["scenario"]["session_id"]


def test_daily_limit_mixed_modes_and_taipei_boundary(
    client, normal_user_token_headers, db, monkeypatch
):
    from datetime import date

    from app.exam.service import daily_used

    h = normal_user_token_headers
    states = [
        finish(client, h, db, start(client, h, mode))
        for mode in ("specialized", "comprehensive", "specialized")
    ]
    r = req(
        client,
        h,
        "post",
        "/exam/start",
        {"mode": "specialized", "fraud_type": "investment"},
    )
    assert r.status_code == 400 and r.json()["detail"] == {
        "code": "exam_daily_limit",
        "limit": 3,
    }
    rows = [attempt(db, s) for s in states]
    uid = rows[0].user_id
    for row, dt in zip(
        rows,
        [
            datetime(2026, 10, 8, 15, 59, tzinfo=timezone.utc),
            datetime(2026, 10, 8, 16, 0, tzinfo=timezone.utc),
            datetime(2026, 10, 9, 16, 0, tzinfo=timezone.utc),
        ],
        strict=True,
    ):
        row.created_at = dt
        db.add(row)
    db.commit()
    monkeypatch.setattr("app.exam.service.taipei_today", lambda: date(2026, 10, 9))
    assert daily_used(db, uid) == 1


def test_no_bootstrap_during_exam_and_missing_persona_fails_closed(
    client, normal_user_token_headers, db, monkeypatch, tmp_path
):
    h = normal_user_token_headers
    state = start(client, h)
    uid = attempt(db, state).user_id
    db.execute(
        delete(ScenarioSession).where(
            ScenarioSession.user_id == uid, ScenarioSession.pool == "practice"
        )
    )
    db.commit()
    r = req(client, h, "get", "/scenario/inbox")
    assert r.status_code == 400 and r.json()["detail"]["code"] == "exam_in_progress"
    assert not db.exec(
        select(ScenarioSession).where(
            ScenarioSession.user_id == uid, ScenarioSession.pool == "practice"
        )
    ).all()
    r = req(client, h, "post", "/scenario/new", {"fraud_type": "investment"})
    assert r.status_code == 400 and r.json()["detail"]["code"] == "exam_in_progress"
    req(client, h, "post", f"/exam/{state['id']}/abandon")
    # 使用另一帳號避開放棄後的補考門檻，缺人格不能留下 active attempt。
    from app.exam.service import start_exam
    from app.models import User
    from app.schemas import ExamStartRequest

    user = User(email=f"{uuid.uuid4()}@example.com", hashed_password="unused")
    db.add(user)
    db.commit()
    db.refresh(user)
    monkeypatch.setattr("app.scenario.agent.SKILLS_DIR", str(tmp_path / "missing"))
    from fastapi import HTTPException

    with pytest.raises(HTTPException) as exc:
        start_exam(
            db, user.id, ExamStartRequest(mode="specialized", fraud_type="investment")
        )
    assert exc.value.status_code == 503
    db.rollback()
    assert (
        db.exec(select(ExamAttempt).where(ExamAttempt.user_id == user.id)).all() == []
    )


def test_locked_snapshots_and_wrong_result(client, normal_user_token_headers, db):
    h = normal_user_token_headers
    state = start(client, h)
    for item in attempt(db, state).items["swipe"]:
        card = db.get(SwipeCard, uuid.UUID(item["id"]))
        card.is_scam = not card.is_scam
        db.add(card)
    db.commit()
    state = finish(client, h, db, state, wrong=True)
    assert state["result"]["total_score"] == 0
    assert not state["result"]["passed"]
    assert set(state["result"]["missed_tactics"]) == {"用好處引誘你", "冒充官方或專家"}
    assert state["result"]["reward"] == {"cash": 0, "xp": 0}


def test_ai_recovery_turn_limit_and_expired_partial_score(
    client, normal_user_token_headers, db, monkeypatch
):
    from app.schemas import ScenarioReply

    h = normal_user_token_headers
    state = start(client, h)
    state, _ = submit(client, h, db, state, "swipe")
    state, _ = submit(client, h, db, state, "message")
    state = req(client, h, "post", f"/exam/{state['id']}/scenario/start").json()
    sid = state["scenario"]["session_id"]

    async def fail(*_args, **_kwargs):
        raise RuntimeError("模型失敗")

    monkeypatch.setattr("app.scenario.agent.generate_reply", fail)
    assert (
        req(client, h, "post", f"/scenario/{sid}/message", {"text": "你好"}).status_code
        == 502
    )

    async def reply(_sc, _player_text, case=None):
        assert case.pool == "exam_scenario"
        return ScenarioReply(messages=["你好。"], tactics_used=["greed"])

    monkeypatch.setattr("app.scenario.agent.generate_reply", reply)
    for n in range(8):
        r = req(client, h, "post", f"/scenario/{sid}/message", {"text": "請說明"})
        assert r.status_code == 200 and r.json()["turns_left"] == 7 - n
    assert (
        req(client, h, "post", f"/scenario/{sid}/message", {"text": "請說明"}).json()[
            "detail"
        ]["code"]
        == "turn_limit_reached"
    )
    row = attempt(db, state)
    row.expires_at = datetime.now(timezone.utc) - timedelta(seconds=1)
    db.add(row)
    db.commit()
    state = req(client, h, "get", f"/exam/{state['id']}").json()
    assert state["status"] == "expired" and state["result"]["total_score"] == 80
    assert state["result"]["passed"]
    detail = req(client, h, "get", f"/scenario/{sid}").json()
    assert detail["outcome"] is None and "tactics_used" not in json.dumps(detail)


def test_abandon_forces_failure_even_above_seventy(
    client, normal_user_token_headers, db
):
    h = normal_user_token_headers
    state = start(client, h)
    state, _ = submit(client, h, db, state, "swipe")
    state, _ = submit(client, h, db, state, "message")
    result = req(client, h, "post", f"/exam/{state['id']}/abandon").json()
    assert result["status"] == "abandoned" and result["result"]["total_score"] == 80
    assert result["result"]["passed"] is False and result["result"]["badges"] == []


def test_concurrent_start_only_creates_one_attempt(
    client, normal_user_token_headers, db
):
    from concurrent.futures import ThreadPoolExecutor

    h = normal_user_token_headers
    with ThreadPoolExecutor(max_workers=2) as executor:
        responses = list(
            executor.map(
                lambda _: req(
                    client,
                    h,
                    "post",
                    "/exam/start",
                    {"mode": "specialized", "fraud_type": "investment"},
                ),
                range(2),
            )
        )
    assert sorted(r.status_code for r in responses) == [200, 400]
    assert (
        next(r for r in responses if r.status_code == 400).json()["detail"]["code"]
        == "exam_in_progress"
    )
    assert (
        len(db.exec(select(ExamAttempt).where(ExamAttempt.status == "active")).all())
        == 1
    )


def test_retake_focus_keeps_half_with_skewed_old_profile(
    client, normal_user_token_headers, db
):
    from app.models import PracticeProfile

    h = normal_user_token_headers
    state = finish(client, h, db, start(client, h), wrong=True)
    uid = attempt(db, state).user_id
    db.add(
        PracticeProfile(
            user_id=uid,
            focus_type="shopping",
            weights={
                "investment": 0.08,
                "shopping": 0.5,
                "fake-sale": 0.14,
                "romance": 0.14,
                "atm": 0.14,
            },
            source="rule",
        )
    )
    db.commit()
    profile = req(client, h, "get", "/practice/profile").json()
    assert profile["focus_type"] == "investment"
    assert profile["weights"]["investment"] == 0.5
    assert min(profile["weights"].values()) >= 0.08


def test_concurrent_final_judgment_rewards_once(client, normal_user_token_headers, db):
    from concurrent.futures import ThreadPoolExecutor

    from app.models import User

    h = normal_user_token_headers
    state = start(client, h)
    state, _ = submit(client, h, db, state, "swipe")
    state, _ = submit(client, h, db, state, "message")
    for n in range(2):
        state = req(client, h, "post", f"/exam/{state['id']}/scenario/start").json()
        sid = state["scenario"]["session_id"]
        sc = db.get(ScenarioSession, uuid.UUID(sid))
        action = "report" if sc.persona_role == "scam" else "comply"
        if n == 0:
            req(
                client,
                h,
                "post",
                f"/exam/{state['id']}/scenario/judge",
                {"action": action, "session_id": sid},
            )
    uid = attempt(db, state).user_id
    user = db.get(User, uid)
    db.refresh(user)
    cash, xp = user.cash, user.xp
    with ThreadPoolExecutor(max_workers=2) as executor:
        responses = list(
            executor.map(
                lambda _: req(
                    client,
                    h,
                    "post",
                    f"/exam/{state['id']}/scenario/judge",
                    {"action": action, "session_id": sid},
                ),
                range(2),
            )
        )
    assert all(r.status_code == 200 for r in responses)
    assert responses[0].json() == responses[1].json()
    db.refresh(user)
    assert (user.cash - cash, user.xp - xp) == (3000, 150)
    assert len(db.exec(select(ExamBadge).where(ExamBadge.user_id == uid)).all()) == 1


def test_training_pretest_cannot_probe_exam_answers(
    client, normal_user_token_headers, db
):
    from app.models import PretestAttempt, PretestResult

    h = normal_user_token_headers
    state = start(client, h, "comprehensive")
    row = attempt(db, state)
    # 五類各交一題，舊端點的每類 correct 就是逐題答案探針。
    chosen = {item["fraud_type"]: item for item in row.items["pretest"]}
    body = {
        "answers": [
            {"question_id": item["id"], "selected_option": item["correct_option"]}
            for item in chosen.values()
        ]
    }
    before = [
        len(db.exec(select(model).where(model.user_id == row.user_id)).all())
        for model in (PretestAttempt, PretestResult, PracticeAnswer)
    ]
    r = req(client, h, "post", "/pretest/submit", body)
    assert r.status_code == 400 and r.json()["detail"]["code"] == "exam_in_progress"
    db.expire_all()
    assert before == [
        len(db.exec(select(model).where(model.user_id == row.user_id)).all())
        for model in (PretestAttempt, PretestResult, PracticeAnswer)
    ]


def test_expiry_relock_rechecks_new_active(
    client, normal_user_token_headers, db, monkeypatch
):
    from fastapi import HTTPException
    from sqlmodel import Session

    from app.exam import lifecycle
    from app.exam.service import start_exam
    from app.schemas import ExamStartRequest

    state = finish(
        client, normal_user_token_headers, db, start(client, normal_user_token_headers)
    )
    uid = attempt(db, state).user_id
    expired = start(client, normal_user_token_headers)
    row = attempt(db, expired)
    # 已作答的 80 分到期仍通過，因此不會有補考門檻干擾新開考。
    submit(client, normal_user_token_headers, db, expired, "swipe")
    stage = req(
        client, normal_user_token_headers, "get", f"/exam/{expired['id']}"
    ).json()
    submit(client, normal_user_token_headers, db, stage, "message")
    row = attempt(db, expired)
    row.expires_at = datetime.now(timezone.utc) - timedelta(seconds=1)
    db.add(row)
    db.commit()
    original = lifecycle.lock_exam_user
    calls = 0

    def interleaved_lock(session, user_id):
        nonlocal calls
        if session is db:
            calls += 1
            if calls == 2:
                # 模擬已排隊的開考在到期 commit 與重新取鎖之間先完成。
                with Session(db.bind) as other:
                    start_exam(
                        other,
                        uid,
                        ExamStartRequest(mode="specialized", fraud_type="investment"),
                    )
        original(session, user_id)

    monkeypatch.setattr(lifecycle, "lock_exam_user", interleaved_lock)
    with pytest.raises(HTTPException) as exc:
        lifecycle.require_no_active_exam(db, uid)
    assert exc.value.detail == {"code": "exam_in_progress"}
    db.rollback()


def test_daily_challenge_commit_cannot_release_training_guard(
    client, normal_user_token_headers, db, monkeypatch
):
    from sqlmodel import Session

    from app.api.routes import daily
    from app.daily.dates import taipei_today
    from app.exam.service import start_exam
    from app.models import DailyChallenge, QuizSession, User
    from app.schemas import ExamStartRequest

    h = normal_user_token_headers
    uid = uuid.UUID(req(client, h, "get", "/users/me").json()["id"])
    user = db.get(User, uid)
    user.xp = 1000
    db.add(user)
    db.execute(
        delete(QuizSession).where(
            QuizSession.user_id == uid, QuizSession.daily_date == taipei_today()
        )
    )
    db.execute(delete(DailyChallenge).where(DailyChallenge.day == taipei_today()))
    db.commit()
    original = daily.get_or_create_challenge

    def interleaved_challenge(session, day):
        challenge = original(session, day)
        assert challenge is not None
        with Session(db.bind) as other:
            start_exam(
                other,
                uid,
                ExamStartRequest(mode="specialized", fraud_type="investment"),
            )
        return challenge

    monkeypatch.setattr(daily, "get_or_create_challenge", interleaved_challenge)
    r = req(client, h, "get", "/daily/today")
    assert r.status_code == 400 and r.json()["detail"]["code"] == "exam_in_progress"
    assert (
        db.exec(
            select(QuizSession).where(
                QuizSession.user_id == uid, QuizSession.daily_date == taipei_today()
            )
        ).all()
        == []
    )


def test_voided_retake_does_not_revive_previous_gate(
    client, normal_user_token_headers, db, monkeypatch
):
    h = normal_user_token_headers
    state = finish(client, h, db, start(client, h), wrong=True)
    uid = attempt(db, state).user_id
    for mode, n in (("swipe", 6), ("quiz", 5), ("scenario", 1)):
        for _ in range(n):
            db.add(
                PracticeAnswer(
                    user_id=uid, mode=mode, fraud_type="investment", correct=True
                )
            )
    db.commit()
    state = start(client, h)
    state, _ = submit(client, h, db, state, "swipe")
    state, _ = submit(client, h, db, state, "message")
    state = req(client, h, "post", f"/exam/{state['id']}/scenario/start").json()

    async def fail(*_args, **_kwargs):
        raise RuntimeError("模型失敗")

    monkeypatch.setattr("app.scenario.agent.generate_reply", fail)
    assert (
        req(
            client,
            h,
            "post",
            f"/scenario/{state['scenario']['session_id']}/message",
            {"text": "你好"},
        ).status_code
        == 502
    )
    row = attempt(db, state)
    row.expires_at = datetime.now(timezone.utc) - timedelta(seconds=1)
    db.add(row)
    db.commit()
    assert req(client, h, "get", f"/exam/{state['id']}").json()["status"] == "voided"
    status = req(client, h, "get", "/exam/status").json()
    assert status["can_start"] and status["gate"] is None and status["daily_used"] == 1
    assert req(client, h, "get", "/practice/profile").json()["retake"] is None


def test_judge_without_session_id_cannot_submit_next_scene(
    client, normal_user_token_headers, db
):
    h = normal_user_token_headers
    state = start(client, h)
    state, _ = submit(client, h, db, state, "swipe")
    state, _ = submit(client, h, db, state, "message")
    state = req(client, h, "post", f"/exam/{state['id']}/scenario/start").json()
    sid = state["scenario"]["session_id"]
    sc = db.get(ScenarioSession, uuid.UUID(sid))
    action = "report" if sc.persona_role == "scam" else "comply"
    assert (
        req(
            client,
            h,
            "post",
            f"/exam/{state['id']}/scenario/judge",
            {"action": action, "session_id": sid},
        ).status_code
        == 200
    )
    req(client, h, "post", f"/exam/{state['id']}/scenario/start")
    r = req(
        client, h, "post", f"/exam/{state['id']}/scenario/judge", {"action": action}
    )
    assert r.status_code == 422
    assert len(attempt(db, state).answers["scenario"]) == 1


def test_inbox_stays_readable_when_exam_starts_during_bootstrap(
    client, normal_user_token_headers, db, monkeypatch
):
    from sqlmodel import Session

    from app.api.routes import scenario
    from app.exam.service import start_exam
    from app.schemas import ExamStartRequest

    h = normal_user_token_headers
    uid = uuid.UUID(req(client, h, "get", "/users/me").json()["id"])
    db.execute(
        delete(ScenarioSession).where(
            ScenarioSession.user_id == uid, ScenarioSession.pool == "practice"
        )
    )
    db.commit()
    original = scenario._create_session

    def interleaved_create(session, user_id, fraud_type):
        sc = original(session, user_id, fraud_type)
        with Session(db.bind) as other:
            start_exam(
                other,
                uid,
                ExamStartRequest(mode="specialized", fraud_type="investment"),
            )
        return sc

    monkeypatch.setattr(scenario, "_create_session", interleaved_create)
    r = req(client, h, "get", "/scenario/inbox")
    assert r.status_code == 200 and len(r.json()) == 1
    assert (
        len(
            db.exec(
                select(ScenarioSession).where(
                    ScenarioSession.user_id == uid, ScenarioSession.pool == "practice"
                )
            ).all()
        )
        == 1
    )


def test_training_opened_before_the_exam_is_paused_until_it_ends(
    client, normal_user_token_headers, monkeypatch
):
    # 檢測中暫停三種訓練：開考前就打開的練習局也不能作答，否則等於考到一半翻書
    h = normal_user_token_headers
    swipe = req(client, h, "get", "/quick/swipe/deck").json()
    quiz = req(client, h, "get", "/quick/quiz/deck").json()
    practice = req(client, h, "get", "/scenario/inbox").json()[0]
    state = start(client, h)

    def blocked(r):
        return r.status_code == 400 and r.json()["detail"]["code"] == "exam_in_progress"

    card = swipe["cards"][0]["id"]
    assert blocked(
        req(
            client,
            h,
            "post",
            "/quick/swipe/answer",
            {"session_id": swipe["session_id"], "card_id": card, "guess_is_scam": True},
        )
    )
    item = quiz["items"][0]["item_id"]
    assert blocked(
        req(
            client,
            h,
            "post",
            "/quick/quiz/answer",
            {"session_id": quiz["session_id"], "item_id": item, "guess_is_scam": True},
        )
    )

    async def never(*_args, **_kwargs):
        raise AssertionError("檢測中不該呼叫練習情境的 AI")

    monkeypatch.setattr("app.scenario.agent.generate_reply", never)
    pid = practice["id"]
    assert blocked(req(client, h, "post", f"/scenario/{pid}/message", {"text": "你好"}))
    assert blocked(
        req(client, h, "post", f"/scenario/{pid}/judge", {"action": "report"})
    )
    assert blocked(req(client, h, "get", "/scenario/inbox"))

    req(client, h, "post", f"/exam/{state['id']}/abandon")
    # 檢測結束後（這裡是放棄進補考期）原本的練習局照常可以作答
    r = req(
        client,
        h,
        "post",
        "/quick/swipe/answer",
        {"session_id": swipe["session_id"], "card_id": card, "guess_is_scam": True},
    )
    assert r.status_code == 200, r.text
