from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.api.routes import pretest as pretest_routes
from app.core.config import settings
from app.models import FraudType, PretestQuestion


def _seed_pretest_questions(db: Session) -> list[PretestQuestion]:
    """每種詐騙類型建立 3 題測試題。"""
    questions = []
    for fraud_type in FraudType:
        for i in range(3):
            q = PretestQuestion(
                fraud_type=fraud_type.value,
                question_text=f"{fraud_type.value} 測試題 {i + 1}",
                options=[
                    {"key": "A", "text": "選項 A", "is_correct": i == 0},
                    {"key": "B", "text": "選項 B", "is_correct": i == 1},
                    {"key": "C", "text": "選項 C", "is_correct": i == 2},
                ],
                explanation=f"解說 {i + 1}",
                difficulty=1,
            )
            db.add(q)
            questions.append(q)
    db.commit()
    for q in questions:
        db.refresh(q)
    return questions


def test_get_pretest_questions(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    questions = _seed_pretest_questions(db)
    response = client.get(
        f"{settings.API_V1_STR}/pretest/questions",
        headers=superuser_token_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert "questions" in data
    # 每類抽 QUESTIONS_PER_TYPE 題(種子題庫每類 6 題,加上本測試另外塞的 3 題)
    per_type = pretest_routes.QUESTIONS_PER_TYPE
    assert len(data["questions"]) == per_type * len(FraudType)
    type_counts: dict[str, int] = {}
    for q in data["questions"]:
        ft = q["fraud_type"]
        type_counts[ft] = type_counts.get(ft, 0) + 1
    for fraud_type in FraudType:
        assert type_counts.get(fraud_type.value) == per_type

    # 詐騙與正常情境各半:種子題庫每類都有標記,各抽一半
    by_id = {str(q.id): q for q in db.exec(select(PretestQuestion)).all()}
    for fraud_type in FraudType:
        picked = [
            by_id[q["id"]]
            for q in data["questions"]
            if q["fraud_type"] == fraud_type.value
        ]
        assert sum(q.is_scam is True for q in picked) == per_type // 2
        assert sum(q.is_scam is False for q in picked) == per_type // 2

    # 不能把「是不是詐騙」送到前端
    assert all("is_scam" not in q for q in data["questions"])

    # 驗證不包含 is_correct
    for q in data["questions"]:
        for opt in q["options"]:
            assert "is_correct" not in opt

    # 清理
    for q in questions:
        db.delete(q)
    db.commit()


def test_submit_pretest(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    questions = _seed_pretest_questions(db)

    # 建立答案：每種類型第一題答 A（正確），其餘答 A（只有第一題 A 是正確的）
    answers = []
    for q in questions:
        answers.append({"question_id": str(q.id), "selected_option": "A"})

    response = client.post(
        f"{settings.API_V1_STR}/pretest/submit",
        headers=superuser_token_headers,
        json={"answers": answers},
    )
    assert response.status_code == 200
    data = response.json()

    assert "results_by_type" in data
    assert "weakest_type" in data
    assert data["ready_for_game"] is True

    # 每種類型都應有結果
    for fraud_type in FraudType:
        ft = fraud_type.value
        assert ft in data["results_by_type"]
        assert data["results_by_type"][ft]["total"] == 3
        # 每種類型第一題 A 正確，第二三題 A 錯誤 → 各 1/3
        assert data["results_by_type"][ft]["correct"] == 1

    # 結論要記下來,題組發牌與情境收件匣才讀得到
    from sqlmodel import delete, select

    from app.core.pretest import latest_weakest_type
    from app.models import PretestAttempt, PretestResult, User

    user = db.exec(select(User).where(User.email == settings.FIRST_SUPERUSER)).one()
    db.expire_all()
    assert latest_weakest_type(db, user.id) == data["weakest_type"]

    # 清理。PretestAttempt 不刪的話,後面的發牌測試會被偏重到這一類
    db.execute(delete(PretestAttempt))
    db.execute(delete(PretestResult))
    for q in questions:
        db.delete(q)
    db.commit()


def test_submit_pretest_counts_each_question_once(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    """同一題送很多次只算一次,練習紀錄也只寫一筆。"""
    from sqlmodel import delete

    from app.models import PracticeAnswer, PretestAttempt, PretestResult, User

    questions = _seed_pretest_questions(db)
    answers = [{"question_id": str(q.id), "selected_option": "A"} for q in questions]
    wrong = {"question_id": str(questions[1].id), "selected_option": "A"}
    response = client.post(
        f"{settings.API_V1_STR}/pretest/submit",
        headers=superuser_token_headers,
        json={"answers": answers + [wrong] * 80},
    )
    assert response.status_code == 200
    assert response.json()["results_by_type"][questions[1].fraud_type]["total"] == 3

    user = db.exec(select(User).where(User.email == settings.FIRST_SUPERUSER)).one()
    db.expire_all()
    logged = db.exec(
        select(PracticeAnswer).where(
            PracticeAnswer.user_id == user.id, PracticeAnswer.mode == "pretest"
        )
    ).all()
    assert len(logged) == len(questions)

    db.execute(delete(PretestAttempt))
    db.execute(delete(PretestResult))
    for q in questions:
        db.delete(q)
    db.commit()


def test_submit_pretest_without_valid_answers(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    response = client.post(
        f"{settings.API_V1_STR}/pretest/submit",
        headers=superuser_token_headers,
        json={
            "answers": [
                {
                    "question_id": "00000000-0000-0000-0000-000000000000",
                    "selected_option": "A",
                }
            ]
        },
    )
    assert response.status_code == 400


def test_submit_pretest_needs_every_type(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    """只交一類的話那一類必定最弱,等於讓玩家自己挑練習重點。"""
    questions = _seed_pretest_questions(db)
    one_type = [
        {"question_id": str(q.id), "selected_option": "B"}
        for q in questions
        if q.fraud_type == questions[0].fraud_type
    ]
    response = client.post(
        f"{settings.API_V1_STR}/pretest/submit",
        headers=superuser_token_headers,
        json={"answers": one_type},
    )
    assert response.status_code == 400
    for q in questions:
        db.delete(q)
    db.commit()


def test_submit_pretest_breaks_ties_in_fixed_order(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    """兩類同分最低時照固定順序取,和練習重點的選法一致(不看交卷順序)。"""
    from sqlmodel import delete

    from app.core.fraud_types import FRAUD_TYPES
    from app.models import PretestAttempt, PretestResult

    questions = _seed_pretest_questions(db)
    weak = {"romance", "shopping"}

    def answer(q: PretestQuestion) -> str:
        right = next(o["key"] for o in q.options if o["is_correct"])
        wrong = next(o["key"] for o in q.options if not o["is_correct"])
        return wrong if q.fraud_type in weak else right

    answers = [
        {"question_id": str(q.id), "selected_option": answer(q)}
        for q in reversed(questions)
    ]
    response = client.post(
        f"{settings.API_V1_STR}/pretest/submit",
        headers=superuser_token_headers,
        json={"answers": answers},
    )
    assert response.status_code == 200
    assert response.json()["weakest_type"] == next(
        ft for ft in FRAUD_TYPES if ft in weak
    )
    db.execute(delete(PretestAttempt))
    db.execute(delete(PretestResult))
    for q in questions:
        db.delete(q)
    db.commit()
