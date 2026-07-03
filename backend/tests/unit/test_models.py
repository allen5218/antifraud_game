import uuid

from app.models import (
    FraudType,
    MascotItem,
    PretestQuestion,
    PretestResult,
    UserMascotItem,
    UserScore,
)


def test_fraud_type_enum():
    assert FraudType.INVESTMENT == "investment"
    assert FraudType.SHOPPING == "shopping"
    assert FraudType.FAKE_SALE == "fake-sale"
    assert FraudType.ROMANCE == "romance"
    assert FraudType.ATM == "atm"


def test_pretest_question_creation():
    q = PretestQuestion(
        fraud_type=FraudType.INVESTMENT,
        question_text="這是一個測試題目",
        options=[
            {"key": "A", "text": "選項 A", "is_correct": True},
            {"key": "B", "text": "選項 B", "is_correct": False},
        ],
        explanation="解說",
        difficulty=1,
    )
    assert q.fraud_type == "investment"
    assert len(q.options) == 2


def test_pretest_result_creation():
    r = PretestResult(
        user_id=uuid.uuid4(),
        fraud_type=FraudType.SHOPPING,
        question_id=uuid.uuid4(),
        selected_option="A",
        is_correct=True,
    )
    assert r.is_correct is True
    assert r.fraud_type == "shopping"


def test_user_score_defaults():
    score = UserScore(
        user_id=uuid.uuid4(),
    )
    assert score.total_score == 0
    assert score.games_played == 0


def test_mascot_item_creation():
    item = MascotItem(
        name="紳士帽",
        category="hat",
        cost=100,
        image_url="/images/hat.png",
    )
    assert item.name == "紳士帽"
    assert item.cost == 100


def test_user_mascot_item_creation():
    umi = UserMascotItem(
        user_id=uuid.uuid4(),
        item_id=uuid.uuid4(),
    )
    assert umi.is_equipped is False
