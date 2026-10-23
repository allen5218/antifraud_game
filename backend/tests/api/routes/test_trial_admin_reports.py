"""管理頁的個人詳情與數據分析：和成員 CSV 同一套判定，問卷可只看合格的。"""

import uuid
from datetime import timedelta
from typing import Any

from fastapi.testclient import TestClient
from sqlmodel import Session

from app.core.config import settings
from app.models import (
    ExamAttempt,
    PracticeAnswer,
    ScenarioSession,
    User,
    get_datetime_utc,
)
from tests.api.routes.test_trial_survey import (  # noqa: F401
    add_exam,
    answers,
    cohort,
    redeem,
    submit,
)

BASE = settings.API_V1_STR


def do_pretest(
    client: TestClient, headers: dict[str, str], elapsed_ms: int
) -> dict[str, Any]:
    questions = client.get(f"{BASE}/pretest/questions", headers=headers).json()[
        "questions"
    ]
    response = client.post(
        f"{BASE}/pretest/submit",
        headers=headers,
        json={
            "answers": [
                {"question_id": q["id"], "selected_option": q["options"][0]["key"]}
                for q in questions
            ],
            "elapsed_ms": elapsed_ms,
        },
    )
    assert response.status_code == 200, response.text
    return response.json()  # type: ignore[no-any-return]


def add_comprehensive_exam(
    db: Session, user_id: uuid.UUID, correct_by_type: dict[str, int]
) -> None:
    """綜合檢測：前測關每類 4 題，前 `correct` 題答對。"""
    items: list[dict[str, Any]] = []
    picked: dict[str, str] = {}
    for fraud_type, correct in correct_by_type.items():
        for i in range(4):
            item_id = str(uuid.uuid4())
            items.append(
                {"id": item_id, "correct_option": "A", "fraud_type": fraud_type}
            )
            picked[item_id] = "A" if i < correct else "B"
    start = get_datetime_utc() - timedelta(hours=1)
    db.add(
        ExamAttempt(
            user_id=user_id,
            mode="comprehensive",
            fraud_type="romance",
            status="completed",
            created_at=start,
            completed_at=start + timedelta(minutes=10),
            expires_at=start + timedelta(hours=1),
            total_score=72.4,
            passed=True,
            items={"pretest": items},
            answers={"pretest": picked},
            pretest_by_type=correct_by_type,
        )
    )
    db.commit()


def test_member_detail(
    client: TestClient,
    cohort: dict,  # noqa: F811
    db: Session,
    superuser_token_headers: dict[str, str],
) -> None:
    headers, user_id = redeem(client, cohort["token"])
    result = do_pretest(client, headers, 95_000)
    add_exam(db, user_id, 400)
    db.add(
        PracticeAnswer(user_id=user_id, mode="swipe", fraud_type="atm", correct=True)
    )
    db.add(
        PracticeAnswer(user_id=user_id, mode="swipe", fraud_type="atm", correct=False)
    )
    # 收件匣自動開的對話（只有對方的開場）不算聊過
    for history in (
        [{"role": "npc", "content": "你好"}],
        [{"role": "npc", "content": "你好"}, {"role": "player", "content": "嗨"}],
    ):
        db.add(
            ScenarioSession(
                user_id=user_id,
                fraud_type="atm",
                persona_role="scam",
                display_name="客服",
                avatar="atm-1",
                conversation_history=history,
                stake_loss=0,
                reward_win=0,
                reward_legit=0,
                penalty_misreport=0,
            )
        )
    db.commit()
    payload = answers()
    payload["favorite"] = "其他"
    payload["favorite_other"] = "排行榜"
    submit(client, db, headers, user_id, 120, payload)

    url = f"{BASE}/admin/cohorts/{cohort['id']}/members/{user_id}"
    response = client.get(url, headers=superuser_token_headers)
    assert response.status_code == 200, response.text
    detail = response.json()
    code = db.get(User, user_id).participant_code  # type: ignore[union-attr]
    assert detail["participant_code"] == code
    (pretest,) = detail["pretests"]
    assert pretest["seconds"] == 95
    assert pretest["total"] == 20 == len(pretest["items"])
    assert pretest["correct"] == sum(
        r["correct"] for r in result["results_by_type"].values()
    )
    assert all(
        item["is_correct"] == (item["selected"] == item["correct_option"])
        for item in pretest["items"]
    )
    (exam,) = detail["exams"]
    assert exam["seconds"] == 400 and exam["score"] == 80
    practice = {p["mode"]: p for p in detail["practice"]}
    assert practice["swipe"] == {"mode": "swipe", "total": 2, "correct": 1}
    assert practice["quiz"]["total"] == 0
    assert detail["scenario_sessions"] == 1
    survey = detail["survey"]
    assert survey["attention_ok"] is True
    shown = {a["question"]: a["answer"] for a in survey["answers"]}
    assert shown["最喜歡的功能"] == "其他：排行榜"
    assert shown["整體來說，我對這個遊戲感到滿意"] == "4 同意"
    assert detail["last_active_at"] is not None

    # 別的梯次的編號、不存在的帳號都查不到
    other = client.get(
        f"{BASE}/admin/cohorts/{uuid.uuid4()}/members/{user_id}",
        headers=superuser_token_headers,
    )
    assert other.status_code == 404
    # 玩家自己不能看
    assert client.get(url, headers=headers).status_code == 400


def test_analytics(
    client: TestClient,
    cohort: dict,  # noqa: F811
    db: Session,
    superuser_token_headers: dict[str, str],
) -> None:
    good_headers, good = redeem(client, cohort["token"])
    rushed_headers, rushed = redeem(client, cohort["token"])
    redeem(client, cohort["token"])
    good_pretest = do_pretest(client, good_headers, 90_000)
    do_pretest(client, rushed_headers, 20_000)
    add_comprehensive_exam(
        db,
        good,
        {"investment": 4, "fake-sale": 4, "shopping": 3, "romance": 4, "atm": 4},
    )
    add_exam(db, rushed, 100, total_score=40)
    good_answers = answers()
    good_answers["confidence_before"] = 2
    good_answers["confidence_after"] = 5
    good_answers["improve"] = "字可以大一點"
    submit(client, db, good_headers, good, 200, good_answers)
    submit(client, db, rushed_headers, rushed, 30, answers(attention=1))

    url = f"{BASE}/admin/cohorts/analytics"
    response = client.get(
        url, params={"cohort_id": cohort["id"]}, headers=superuser_token_headers
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["member_count"] == 3
    assert [s["count"] for s in data["funnel"]] == [3, 2, 2, 2, 1]

    paired = data["paired_pretest"]
    before = sum(r["correct"] for r in good_pretest["results_by_type"].values())
    assert paired["n"] == 1 and paired["total"] == 20
    assert paired["pairs"] == [{"before": before, "after": 19}]
    assert paired["diff_mean"] == 19 - before

    shopping = next(t for t in data["type_accuracy"] if t["fraud_type"] == "shopping")
    assert shopping["after"] == 0.75 and shopping["after_n"] == 4
    assert shopping["before_n"] == 8  # 兩個人各 4 題

    scores = data["scores"]
    assert scores["n"] == 2 and scores["passed"] == 1
    assert sum(b["count"] for b in scores["bins"]) == 2
    timings = {t["key"]: t for t in data["timings"]}
    assert timings["pretest"]["n"] == 2 and timings["pretest"]["below"] == 1
    assert timings["exam"]["below"] == 1  # rushed 100 秒
    assert timings["survey"]["below"] == 1

    survey = data["survey"]
    assert survey["responses"] == survey["included"] == 2
    assert survey["attention_failed"] == 1 and survey["too_fast"] == 1
    assert all(item["id"] != "attention" for item in survey["likert"])
    satisfied = next(i for i in survey["likert"] if i["id"] == "satisfied")
    assert satisfied["counts"] == [0, 0, 0, 2, 0] and satisfied["mean"] == 4
    assert survey["confidence"]["n"] == 2
    improve = next(t for t in survey["texts"] if t["id"] == "improve")
    assert [a["text"] for a in improve["answers"]] == ["字可以大一點"]

    # 只看合格問卷：注意力錯又太快的那份不算
    valid = client.get(
        url,
        params={"cohort_id": cohort["id"], "valid_only": True},
        headers=superuser_token_headers,
    ).json()["survey"]
    assert valid["responses"] == 2 and valid["included"] == 1
    assert valid["confidence"]["diff_mean"] == 3

    # 不給 cohort_id 是全部梯次合計
    everything = client.get(url, headers=superuser_token_headers)
    assert everything.status_code == 200
    assert everything.json()["member_count"] >= 3
