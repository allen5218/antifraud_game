"""檢測題數、配分、期限與補考條件的唯一設定。"""

from dataclasses import dataclass

EXAM_DURATION_SECONDS = 3600
EXAM_DAILY_LIMIT = 3
EXAM_PASS_SCORE = 70
EXAM_RETAKE_WAIT_HOURS = 0
BADGE_RETEST_DAYS = 90
RETAKE_SWIPE = 6
RETAKE_QUIZ = 5
RETAKE_SCENARIO = 1
RETAKE_RECENT = 10
RETAKE_CORRECT = 7
PRETEST_PER_SIDE = 2


@dataclass(frozen=True)
class ExamConfig:
    swipe_per_side: int
    message_per_side: int
    scenario_count: int
    max_turns: int
    pretest_points: float
    swipe_points: float
    verdict_points: float
    tactics_points: float
    scenario_points: float
    cash: int
    xp: int


MODES = {
    "comprehensive": ExamConfig(2, 2, 1, 5, 1.5, 5, 7.5, 5, 15, 5000, 300),
    "specialized": ExamConfig(3, 4, 2, 8, 0, 4, 6, 8, 10, 3000, 150),
}
