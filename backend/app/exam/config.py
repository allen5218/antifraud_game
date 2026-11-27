"""檢測題數、配分、期限與補考條件的唯一設定。

檢測有版本（`ExamAttempt.version`）：舊卷照當時的關卡與配分算分，新開考一律用
`EXAM_VERSION`。改關卡或配分要開新版本，不要改舊版本的數字，否則已經考完的卷
重算會變分數，試測分析也會把兩種卷混在一起。
"""

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

# 計分的部位；`stage_scores` 的鍵
PARTS = ("pretest", "swipe", "card", "verdict", "tactics", "scenario")


@dataclass(frozen=True)
class ExamConfig:
    # 關卡順序（不含結束的 done）
    stages: tuple[str, ...]
    # 前測每類每邊（詐騙／正常）幾題；專項沒有前測
    pretest_per_side: int
    swipe_per_side: int
    # 卡片題張數：同一類的檢測專用卡，每句原料最多一張
    card_count: int
    message_per_side: int
    scenario_count: int
    max_turns: int
    pretest_points: float
    swipe_points: float
    card_points: float
    verdict_points: float
    tactics_points: float
    scenario_points: float
    cash: int
    xp: int

    @property
    def pretest_count(self) -> int:
        return self.pretest_per_side * 2 * 5

    @property
    def total_points(self) -> float:
        return (
            self.pretest_count * self.pretest_points
            + self.swipe_per_side * 2 * self.swipe_points
            + self.card_count * self.card_points
            + self.message_per_side * 2 * self.verdict_points
            + self.tactics_points
            + self.scenario_count * self.scenario_points
        )


VERSIONS: dict[int, dict[str, ExamConfig]] = {
    # 2026-10 上線的第一版：前測 20 題、滑卡與訊息判讀比較多
    1: {
        "comprehensive": ExamConfig(
            stages=("pretest", "swipe", "message", "scenario"),
            pretest_per_side=2,
            swipe_per_side=2,
            card_count=0,
            message_per_side=2,
            scenario_count=1,
            max_turns=5,
            pretest_points=1.5,
            swipe_points=5,
            card_points=0,
            verdict_points=7.5,
            tactics_points=5,
            scenario_points=15,
            cash=5000,
            xp=300,
        ),
        "specialized": ExamConfig(
            stages=("swipe", "message", "scenario"),
            pretest_per_side=0,
            swipe_per_side=3,
            card_count=0,
            message_per_side=4,
            scenario_count=2,
            max_turns=8,
            pretest_points=0,
            swipe_points=4,
            card_points=0,
            verdict_points=6,
            tactics_points=8,
            scenario_points=10,
            cash=3000,
            xp=150,
        ),
    },
    # 2026-11 改版：原本的題型砍半，中間加一關日常卡片的題型；情境關不變
    2: {
        "comprehensive": ExamConfig(
            stages=("pretest", "swipe", "cards", "message", "scenario"),
            pretest_per_side=1,
            swipe_per_side=1,
            card_count=5,
            message_per_side=1,
            scenario_count=1,
            max_turns=5,
            pretest_points=2,
            swipe_points=5,
            card_points=6,
            verdict_points=10,
            tactics_points=5,
            scenario_points=15,
            cash=5000,
            xp=300,
        ),
        "specialized": ExamConfig(
            stages=("swipe", "cards", "message", "scenario"),
            pretest_per_side=0,
            swipe_per_side=1,
            card_count=5,
            message_per_side=2,
            scenario_count=2,
            max_turns=8,
            pretest_points=0,
            swipe_points=5,
            card_points=7,
            verdict_points=7.5,
            tactics_points=5,
            scenario_points=10,
            cash=3000,
            xp=150,
        ),
    },
}
EXAM_VERSION = 2
# 所有版本出現過的關卡，依作答順序（新版插進來的關卡放在它實際的位置）
ALL_STAGES = ("pretest", "swipe", "cards", "message", "scenario")


def exam_config(version: int, mode: str) -> ExamConfig:
    return VERSIONS[version][mode]
