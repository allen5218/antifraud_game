from fastapi.testclient import TestClient
from sqlmodel import Session

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
    assert len(data["questions"]) == 15

    # 驗證每種類型都有 3 題
    type_counts: dict[str, int] = {}
    for q in data["questions"]:
        ft = q["fraud_type"]
        type_counts[ft] = type_counts.get(ft, 0) + 1
    for fraud_type in FraudType:
        assert type_counts.get(fraud_type.value) == 3

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

    # 清理
    from sqlmodel import delete

    from app.models import PretestResult

    db.execute(delete(PretestResult))
    for q in questions:
        db.delete(q)
    db.commit()
