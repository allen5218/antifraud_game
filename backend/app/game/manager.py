from app.models import GameSession

# ── 常數 ─────────────────────────────────────────────────────

SCORE_BY_DIFFICULTY = {1: 10, 2: 20, 3: 30}

LEVEL_THRESHOLDS = [
    (2000, 5),
    (1000, 4),
    (500, 3),
    (200, 2),
    (0, 1),
]

BASE_STEPS = 10
MIN_STEPS = 8
MAX_STEPS = 15

MASCOT_TRIGGER_INTERVAL = 5
STREAK_BONUS = 15
STREAK_LENGTH = 3

MASCOT_MESSAGES = [
    "太棒了！你已經連續答對 5 題了！🎉",
    "你真厲害！繼續保持！💪",
    "反詐騙達人就是你！🌟",
    "好棒！吉祥物為你感到驕傲！🥳",
]


class GameSessionManager:
    """純邏輯遊戲狀態管理器——不涉及 DB 操作"""

    def calculate_score(self, is_correct: bool, difficulty: int) -> int:
        if not is_correct:
            return 0
        return SCORE_BY_DIFFICULTY.get(difficulty, 10)

    def adjust_max_steps(self, session: GameSession) -> int:
        """根據表現動態調整題數上限"""
        max_steps = session.max_steps

        # 每答錯 2 題 → +1 題（只加新增的部分）
        expected_wrong_bonus = session.total_wrong // 2
        already_applied = max(0, max_steps - BASE_STEPS)
        new_wrong_bonus = expected_wrong_bonus - already_applied
        if new_wrong_bonus > 0:
            max_steps += new_wrong_bonus

        # 連續答對 3 題 → -1 題
        consecutive_correct = self._count_recent_consecutive_correct(session)
        if consecutive_correct >= STREAK_LENGTH:
            max_steps -= 1

        return max(MIN_STEPS, min(MAX_STEPS, max_steps))

    def check_mascot_trigger(self, session: GameSession) -> bool:
        return (
            session.total_correct > 0
            and session.total_correct % MASCOT_TRIGGER_INTERVAL == 0
        )

    def check_game_over(self, session: GameSession) -> bool:
        return session.current_step >= session.max_steps

    def calculate_grade(self, correct_rate: float) -> str:
        if correct_rate >= 0.9:
            return "S"
        elif correct_rate >= 0.7:
            return "A"
        elif correct_rate >= 0.5:
            return "B"
        else:
            return "C"

    def calculate_streak_bonus(self, session: GameSession) -> int:
        """最近 3 次作答都正確則給予連續獎勵"""
        answers = [
            entry
            for entry in session.conversation_history
            if entry.get("role") == "answer"
        ]
        if len(answers) < STREAK_LENGTH:
            return 0
        last_three = answers[-STREAK_LENGTH:]
        if all(a.get("is_correct") for a in last_three):
            return STREAK_BONUS
        return 0

    def get_level(self, total_score: int) -> int:
        for threshold, level in LEVEL_THRESHOLDS:
            if total_score >= threshold:
                return level
        return 1

    def get_mascot_message(self, total_correct: int) -> str:
        idx = (total_correct // MASCOT_TRIGGER_INTERVAL - 1) % len(MASCOT_MESSAGES)
        return MASCOT_MESSAGES[idx]

    def _count_recent_consecutive_correct(self, session: GameSession) -> int:
        """從最近的作答往回數連續正確次數"""
        answers = [
            entry
            for entry in session.conversation_history
            if entry.get("role") == "answer"
        ]
        count = 0
        for a in reversed(answers):
            if a.get("is_correct"):
                count += 1
            else:
                break
        return count
