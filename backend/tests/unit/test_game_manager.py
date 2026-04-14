import uuid

from app.game.manager import GameSessionManager
from app.models import FraudType, GameSession, GameStatus


def _make_session(**overrides) -> GameSession:
    defaults = {
        "user_id": uuid.uuid4(),
        "fraud_type": FraudType.INVESTMENT,
        "status": GameStatus.IN_PROGRESS,
        "current_step": 0,
        "total_correct": 0,
        "total_wrong": 0,
        "score": 0,
        "max_steps": 10,
        "conversation_history": [],
    }
    defaults.update(overrides)
    return GameSession(**defaults)


mgr = GameSessionManager()


# ── calculate_score ──────────────────────────────────────────


class TestCalculateScore:
    def test_correct_difficulty_1(self):
        assert mgr.calculate_score(is_correct=True, difficulty=1) == 10

    def test_correct_difficulty_2(self):
        assert mgr.calculate_score(is_correct=True, difficulty=2) == 20

    def test_correct_difficulty_3(self):
        assert mgr.calculate_score(is_correct=True, difficulty=3) == 30

    def test_wrong(self):
        assert mgr.calculate_score(is_correct=False, difficulty=3) == 0


# ── adjust_max_steps ─────────────────────────────────────────


class TestAdjustMaxSteps:
    def test_add_step_per_2_wrong(self):
        session = _make_session(total_wrong=2, max_steps=10)
        new_max = mgr.adjust_max_steps(session)
        assert new_max == 11

    def test_reduce_step_per_3_consecutive_correct(self):
        history = [
            {"role": "answer", "is_correct": True},
            {"role": "answer", "is_correct": True},
            {"role": "answer", "is_correct": True},
        ]
        session = _make_session(
            total_correct=3, max_steps=10, conversation_history=history
        )
        new_max = mgr.adjust_max_steps(session)
        assert new_max == 9

    def test_clamp_min_8(self):
        history = [
            {"role": "answer", "is_correct": True},
            {"role": "answer", "is_correct": True},
            {"role": "answer", "is_correct": True},
        ]
        session = _make_session(
            total_correct=3, max_steps=8, conversation_history=history
        )
        new_max = mgr.adjust_max_steps(session)
        assert new_max == 8

    def test_clamp_max_15(self):
        session = _make_session(total_wrong=12, max_steps=15)
        new_max = mgr.adjust_max_steps(session)
        assert new_max == 15

    def test_no_change_baseline(self):
        session = _make_session(total_wrong=1, max_steps=10)
        new_max = mgr.adjust_max_steps(session)
        assert new_max == 10


# ── check_mascot_trigger ─────────────────────────────────────


class TestCheckMascotTrigger:
    def test_trigger_at_5(self):
        session = _make_session(total_correct=5)
        assert mgr.check_mascot_trigger(session) is True

    def test_trigger_at_10(self):
        session = _make_session(total_correct=10)
        assert mgr.check_mascot_trigger(session) is True

    def test_no_trigger_at_0(self):
        session = _make_session(total_correct=0)
        assert mgr.check_mascot_trigger(session) is False

    def test_no_trigger_at_3(self):
        session = _make_session(total_correct=3)
        assert mgr.check_mascot_trigger(session) is False


# ── check_game_over ──────────────────────────────────────────


class TestCheckGameOver:
    def test_game_over_when_step_equals_max(self):
        session = _make_session(current_step=10, max_steps=10)
        assert mgr.check_game_over(session) is True

    def test_game_over_when_step_exceeds_max(self):
        session = _make_session(current_step=11, max_steps=10)
        assert mgr.check_game_over(session) is True

    def test_not_over(self):
        session = _make_session(current_step=5, max_steps=10)
        assert mgr.check_game_over(session) is False


# ── calculate_grade ──────────────────────────────────────────


class TestCalculateGrade:
    def test_grade_s(self):
        assert mgr.calculate_grade(0.95) == "S"
        assert mgr.calculate_grade(0.9) == "S"

    def test_grade_a(self):
        assert mgr.calculate_grade(0.85) == "A"
        assert mgr.calculate_grade(0.7) == "A"

    def test_grade_b(self):
        assert mgr.calculate_grade(0.6) == "B"
        assert mgr.calculate_grade(0.5) == "B"

    def test_grade_c(self):
        assert mgr.calculate_grade(0.4) == "C"
        assert mgr.calculate_grade(0.0) == "C"


# ── calculate_streak_bonus ───────────────────────────────────


class TestCalculateStreakBonus:
    def test_streak_bonus_3_correct(self):
        history = [
            {"role": "answer", "is_correct": True},
            {"role": "answer", "is_correct": True},
            {"role": "answer", "is_correct": True},
        ]
        session = _make_session(conversation_history=history)
        assert mgr.calculate_streak_bonus(session) == 15

    def test_no_streak_bonus_broken(self):
        history = [
            {"role": "answer", "is_correct": True},
            {"role": "answer", "is_correct": False},
            {"role": "answer", "is_correct": True},
        ]
        session = _make_session(conversation_history=history)
        assert mgr.calculate_streak_bonus(session) == 0

    def test_no_streak_bonus_less_than_3(self):
        history = [
            {"role": "answer", "is_correct": True},
            {"role": "answer", "is_correct": True},
        ]
        session = _make_session(conversation_history=history)
        assert mgr.calculate_streak_bonus(session) == 0

    def test_streak_bonus_from_longer_history(self):
        history = [
            {"role": "answer", "is_correct": False},
            {"role": "answer", "is_correct": True},
            {"role": "answer", "is_correct": True},
            {"role": "answer", "is_correct": True},
        ]
        session = _make_session(conversation_history=history)
        assert mgr.calculate_streak_bonus(session) == 15


# ── get_level ────────────────────────────────────────────────


class TestGetLevel:
    def test_level_1(self):
        assert mgr.get_level(0) == 1
        assert mgr.get_level(199) == 1

    def test_level_2(self):
        assert mgr.get_level(200) == 2
        assert mgr.get_level(499) == 2

    def test_level_3(self):
        assert mgr.get_level(500) == 3
        assert mgr.get_level(999) == 3

    def test_level_4(self):
        assert mgr.get_level(1000) == 4
        assert mgr.get_level(1999) == 4

    def test_level_5(self):
        assert mgr.get_level(2000) == 5
        assert mgr.get_level(9999) == 5
