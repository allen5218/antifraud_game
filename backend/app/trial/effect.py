"""試測的成效分析：前測和之後的作答比一比。只讀、只統計，不呼叫 AI。

`load_effect_input` 把資料庫讀成純資料，其餘都是純函式（單元測試不用資料庫）。
答對率一律用百分比（0–100，小數一位）。

- 檢測：第一次考完的綜合檢測，前測關挑出的最弱一類，對照後三關（同一類）。
- 考兩次以上：第一次和最近一次正常交卷的綜合檢測。
- 入門前測到檢測前測關：兩者同題庫、同抽法，可以直接配對。
- 日常練習：起點（入門前測，沒有就用檢測前測關）之後的滑卡、訊息判讀、情境對抗。
"""

import statistics
import uuid
from collections import defaultdict
from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field
from datetime import datetime

from sqlmodel import Session, SQLModel, col, select

from app.core.weakness import WEAKNESS_LABELS
from app.daily.dates import TAIPEI
from app.exam.export import item_answer
from app.exam.scoring import round_score
from app.models import ExamAttempt, PracticeAnswer, PretestAttempt, PretestResult

FRAUD_TYPE_ORDER = ("investment", "fake-sale", "shopping", "romance", "atm")
LATER_STAGES = (("swipe", "滑卡"), ("message", "訊息判讀"), ("scenario", "情境對抗"))
PRACTICE_MODES = (("swipe", "滑卡"), ("quiz", "訊息判讀"), ("scenario", "情境對抗"))
CURVE_STEP = 10
CURVE_LAST = 51  # 第 51 題以後併成一段
MODE_MIN_ANSWERS = 4


# ---------- 輸入（純資料） ----------


@dataclass
class ExamRecord:
    user_id: uuid.UUID
    created_at: datetime
    completed_at: datetime | None
    status: str
    counted: bool
    mode: str
    passed: bool
    score: int
    weakest: str | None
    pretest: list[tuple[str, bool]]
    later: dict[str, list[bool]] = field(default_factory=dict)

    @property
    def done_at(self) -> datetime:
        return self.completed_at or self.created_at


@dataclass
class EntryPretest:
    user_id: uuid.UUID
    at: datetime
    answers: list[tuple[str, bool]]


@dataclass
class Answer:
    user_id: uuid.UUID
    mode: str
    fraud_type: str
    correct: bool
    missed_tags: list[str]
    at: datetime


@dataclass
class EffectInput:
    exams: list[ExamRecord]
    entries: list[EntryPretest]
    answers: list[Answer]


# ---------- 輸出 ----------


class PairedChange(SQLModel):
    n: int
    before_mean: float | None
    after_mean: float | None
    diff_mean: float | None
    improved: int
    same: int
    worse: int


class StageAccuracy(SQLModel):
    key: str
    label: str
    accuracy: float | None
    people: int
    items: int


class TypePair(SQLModel):
    fraud_type: str
    before: float | None
    after: float | None
    people: int


class CurvePoint(SQLModel):
    label: str
    accuracy: float | None
    missed_rate: float | None
    people: int
    items: int


class TagShift(SQLModel):
    tag: str
    label: str
    first_half: int
    second_half: int


class ModeHalves(SQLModel):
    mode: str
    label: str
    change: PairedChange


class ExamStageEffect(SQLModel):
    stages: list[StageAccuracy]
    change: PairedChange


class RepeatEffect(SQLModel):
    people: int
    pretest: PairedChange
    score: PairedChange
    failed_first: int
    retook: int
    retake_passed: int


class EntryEffect(SQLModel):
    total: PairedChange
    by_type: list[TypePair]
    practiced_between: int


class PracticeEffect(SQLModel):
    baseline_people: int
    by_type: list[TypePair]
    curve: list[CurvePoint]
    tags: list[TagShift]
    modes: list[ModeHalves]


class PracticeVolume(SQLModel):
    exam_people: int
    practiced_people: int
    median_answers: float | None
    median_days: float | None
    scenario_rounds: int


class EffectAnalytics(SQLModel):
    exam: ExamStageEffect
    repeat: RepeatEffect
    entry: EntryEffect
    practice: PracticeEffect
    volume: PracticeVolume


# ---------- 小工具 ----------


def _mean(values: Sequence[float]) -> float | None:
    return round(statistics.fmean(values), 1) if values else None


def _rate(marks: Iterable[bool]) -> float | None:
    marks = list(marks)
    return round(100 * sum(marks) / len(marks), 1) if marks else None


def paired(pairs: Sequence[tuple[float, float]]) -> PairedChange:
    diffs = [after - before for before, after in pairs]
    return PairedChange(
        n=len(pairs),
        before_mean=_mean([b for b, _ in pairs]),
        after_mean=_mean([a for _, a in pairs]),
        diff_mean=_mean(diffs),
        improved=sum(d > 0 for d in diffs),
        same=sum(d == 0 for d in diffs),
        worse=sum(d < 0 for d in diffs),
    )


def _by_type(answers: Iterable[tuple[str, bool]]) -> dict[str, list[bool]]:
    cells: dict[str, list[bool]] = defaultdict(list)
    for fraud_type, correct in answers:
        cells[fraud_type].append(correct)
    return cells


def _type_pairs(
    pairs: Sequence[tuple[dict[str, list[bool]], dict[str, list[bool]]]],
) -> list[TypePair]:
    """每類把所有人的題目合起來算答對率；只算兩邊都有這一類的人。"""
    rows = []
    for fraud_type in FRAUD_TYPE_ORDER:
        before: list[bool] = []
        after: list[bool] = []
        people = 0
        for b, a in pairs:
            if b.get(fraud_type) and a.get(fraud_type):
                people += 1
                before += b[fraud_type]
                after += a[fraud_type]
        rows.append(
            TypePair(
                fraud_type=fraud_type,
                before=_rate(before),
                after=_rate(after),
                people=people,
            )
        )
    return rows


def first_exams(exams: Sequence[ExamRecord]) -> dict[uuid.UUID, ExamRecord]:
    """每人第一次考完（作廢與進行中不算）的綜合檢測；第一次是專項的人不列。"""
    firsts: dict[uuid.UUID, ExamRecord] = {}
    seen: set[uuid.UUID] = set()
    for record in sorted(exams, key=lambda e: e.created_at):
        if record.user_id in seen or not record.counted or record.status == "active":
            continue
        seen.add(record.user_id)
        if record.mode == "comprehensive":
            firsts[record.user_id] = record
    return firsts


# ---------- 各段計算 ----------


def exam_stage_effect(firsts: dict[uuid.UUID, ExamRecord]) -> ExamStageEffect:
    weakest: list[bool] = []
    weakest_people = 0
    stage_marks: dict[str, list[bool]] = defaultdict(list)
    stage_people: dict[str, int] = defaultdict(int)
    pairs: list[tuple[float, float]] = []
    for record in firsts.values():
        mine = [ok for t, ok in record.pretest if t == record.weakest]
        later = [ok for key, _ in LATER_STAGES for ok in record.later.get(key, [])]
        for key, _ in LATER_STAGES:
            if record.later.get(key):
                stage_marks[key] += record.later[key]
                stage_people[key] += 1
        if mine:
            weakest += mine
            weakest_people += 1
        before, after = _rate(mine), _rate(later)
        if before is not None and after is not None:
            pairs.append((before, after))
    stages = [
        StageAccuracy(
            key="pretest_weakest",
            label="前測關（最弱一類）",
            accuracy=_rate(weakest),
            people=weakest_people,
            items=len(weakest),
        )
    ] + [
        StageAccuracy(
            key=key,
            label=label,
            accuracy=_rate(stage_marks[key]),
            people=stage_people[key],
            items=len(stage_marks[key]),
        )
        for key, label in LATER_STAGES
    ]
    return ExamStageEffect(stages=stages, change=paired(pairs))


def repeat_effect(exams: Sequence[ExamRecord]) -> RepeatEffect:
    done: dict[uuid.UUID, list[ExamRecord]] = defaultdict(list)
    for record in sorted(exams, key=lambda e: e.created_at):
        if record.mode == "comprehensive" and record.counted:
            if record.status == "completed":
                done[record.user_id].append(record)
    pretest_pairs: list[tuple[float, float]] = []
    score_pairs: list[tuple[float, float]] = []
    failed_first = retook = retake_passed = 0
    for records in done.values():
        first, last = records[0], records[-1]
        if len(records) >= 2:
            pretest_pairs.append(
                (sum(ok for _, ok in first.pretest), sum(ok for _, ok in last.pretest))
            )
            score_pairs.append((first.score, last.score))
        if not first.passed:
            failed_first += 1
            if len(records) >= 2:
                retook += 1
                retake_passed += any(r.passed for r in records[1:])
    return RepeatEffect(
        people=len(score_pairs),
        pretest=paired(pretest_pairs),
        score=paired(score_pairs),
        failed_first=failed_first,
        retook=retook,
        retake_passed=retake_passed,
    )


def _practice(answers: Sequence[Answer]) -> dict[uuid.UUID, list[Answer]]:
    modes = {mode for mode, _ in PRACTICE_MODES}
    mine: dict[uuid.UUID, list[Answer]] = defaultdict(list)
    for item in sorted(answers, key=lambda a: a.at):
        if item.mode in modes:
            mine[item.user_id].append(item)
    return mine


def entry_effect(
    entries: Sequence[EntryPretest],
    firsts: dict[uuid.UUID, ExamRecord],
    practice: dict[uuid.UUID, list[Answer]],
) -> EntryEffect:
    totals: list[tuple[float, float]] = []
    types: list[tuple[dict[str, list[bool]], dict[str, list[bool]]]] = []
    practiced = 0
    for entry in entries:
        record = firsts.get(entry.user_id)
        if record is None or record.created_at <= entry.at:
            continue
        before = _rate(ok for _, ok in entry.answers)
        after = _rate(ok for _, ok in record.pretest)
        if before is None or after is None:
            continue
        totals.append((before, after))
        types.append((_by_type(entry.answers), _by_type(record.pretest)))
        practiced += any(
            entry.at < a.at < record.created_at for a in practice.get(entry.user_id, [])
        )
    return EntryEffect(
        total=paired(totals), by_type=_type_pairs(types), practiced_between=practiced
    )


def _curve_label(index: int) -> str:
    if index >= CURVE_LAST - 1:
        return f"{CURVE_LAST} 以後"
    start = index // CURVE_STEP * CURVE_STEP + 1
    return f"{start}–{start + CURVE_STEP - 1}"


def practice_effect(
    baselines: dict[uuid.UUID, tuple[datetime, list[tuple[str, bool]]]],
    practice: dict[uuid.UUID, list[Answer]],
) -> PracticeEffect:
    types: list[tuple[dict[str, list[bool]], dict[str, list[bool]]]] = []
    buckets: dict[str, list[Answer]] = {}
    bucket_people: dict[str, set[uuid.UUID]] = defaultdict(set)
    tags_first: dict[str, int] = defaultdict(int)
    tags_second: dict[str, int] = defaultdict(int)
    modes: dict[str, list[tuple[float, float]]] = defaultdict(list)
    for user_id, (start, base) in baselines.items():
        after = [a for a in practice.get(user_id, []) if a.at > start]
        if not after:
            continue
        types.append(
            (_by_type(base), _by_type((a.fraud_type, a.correct) for a in after))
        )
        for index, item in enumerate(after):
            label = _curve_label(index)
            buckets.setdefault(label, []).append(item)
            bucket_people[label].add(user_id)
        half = len(after) // 2
        for item in after[:half]:
            for tag in item.missed_tags:
                tags_first[tag] += 1
        for item in after[half:]:
            for tag in item.missed_tags:
                tags_second[tag] += 1
        for mode, _ in PRACTICE_MODES:
            mine = [a.correct for a in after if a.mode == mode]
            if len(mine) >= MODE_MIN_ANSWERS:
                cut = len(mine) // 2
                before, later = _rate(mine[:cut]), _rate(mine[cut:])
                if before is not None and later is not None:
                    modes[mode].append((before, later))
    curve = [
        CurvePoint(
            label=label,
            accuracy=_rate(a.correct for a in items),
            missed_rate=_rate(bool(a.missed_tags) for a in items),
            people=len(bucket_people[label]),
            items=len(items),
        )
        for label, items in buckets.items()
    ]
    return PracticeEffect(
        baseline_people=len(baselines),
        by_type=_type_pairs(types),
        curve=curve,
        tags=[
            TagShift(
                tag=tag,
                label=label,
                first_half=tags_first[tag],
                second_half=tags_second[tag],
            )
            for tag, label in WEAKNESS_LABELS.items()
        ],
        modes=[
            ModeHalves(mode=mode, label=label, change=paired(modes[mode]))
            for mode, label in PRACTICE_MODES
        ],
    )


def practice_volume(
    firsts: dict[uuid.UUID, ExamRecord], practice: dict[uuid.UUID, list[Answer]]
) -> PracticeVolume:
    counts: list[int] = []
    days: list[int] = []
    scenario = 0
    for user_id, record in firsts.items():
        after = [a for a in practice.get(user_id, []) if a.at > record.done_at]
        if not after:
            continue
        counts.append(len(after))
        days.append(len({a.at.astimezone(TAIPEI).date() for a in after}))
        scenario += sum(a.mode == "scenario" for a in after)
    return PracticeVolume(
        exam_people=len(firsts),
        practiced_people=len(counts),
        median_answers=statistics.median(counts) if counts else None,
        median_days=statistics.median(days) if days else None,
        scenario_rounds=scenario,
    )


def effect_analytics(data: EffectInput) -> EffectAnalytics:
    firsts = first_exams(data.exams)
    practice = _practice(data.answers)
    # 起點：有入門前測用第一次入門前測，沒有就用第一次考完的綜合檢測前測關
    baselines: dict[uuid.UUID, tuple[datetime, list[tuple[str, bool]]]] = {
        user_id: (record.done_at, record.pretest) for user_id, record in firsts.items()
    }
    for entry in data.entries:
        baselines[entry.user_id] = (entry.at, entry.answers)
    return EffectAnalytics(
        exam=exam_stage_effect(firsts),
        repeat=repeat_effect(data.exams),
        entry=entry_effect(data.entries, firsts, practice),
        practice=practice_effect(baselines, practice),
        volume=practice_volume(firsts, practice),
    )


# ---------- 讀資料庫 ----------


def _exam_record(attempt: ExamAttempt) -> ExamRecord:
    def marks(stage: str) -> list[tuple[str, str]]:
        answers = attempt.answers.get(stage, {})
        return [
            (str(item.get("fraud_type", "")), item_answer(stage, i, item, answers)[1])
            for i, item in enumerate(attempt.items.get(stage, []))
        ]

    return ExamRecord(
        user_id=attempt.user_id,
        created_at=attempt.created_at,
        completed_at=attempt.completed_at,
        status=attempt.status,
        counted=attempt.counted,
        mode=attempt.mode,
        passed=attempt.passed,
        score=round_score(attempt.total_score),
        weakest=attempt.fraud_type,
        # 前測關沒作答的算錯（和現有五類答對率一致）；後三關只算有作答的
        pretest=[(t, mark == "true") for t, mark in marks("pretest")],
        later={
            stage: [mark == "true" for _, mark in marks(stage) if mark]
            for stage, _ in LATER_STAGES
        },
    )


def load_effect_input(session: Session, user_ids: list[uuid.UUID]) -> EffectInput:
    if not user_ids:
        return EffectInput([], [], [])
    exams = [
        _exam_record(attempt)
        for attempt in session.exec(
            select(ExamAttempt)
            .where(col(ExamAttempt.user_id).in_(user_ids))
            .order_by(col(ExamAttempt.created_at), col(ExamAttempt.id))
        ).all()
    ]
    # 第一次入門前測：第一筆 attempt 之前（含）的逐題結果（同成員 CSV 的切法）
    firsts: dict[uuid.UUID, datetime] = {}
    for attempt in session.exec(
        select(PretestAttempt)
        .where(col(PretestAttempt.user_id).in_(user_ids))
        .order_by(col(PretestAttempt.created_at), col(PretestAttempt.id))
    ).all():
        if attempt.created_at is not None and attempt.user_id not in firsts:
            firsts[attempt.user_id] = attempt.created_at
    entry_answers: dict[uuid.UUID, list[tuple[str, bool]]] = defaultdict(list)
    for result in session.exec(
        select(PretestResult).where(col(PretestResult.user_id).in_(list(firsts)))
    ).all():
        first = firsts[result.user_id]
        if result.created_at is not None and result.created_at <= first:
            entry_answers[result.user_id].append((result.fraud_type, result.is_correct))
    entries = [
        EntryPretest(user_id, firsts[user_id], answers)
        for user_id, answers in entry_answers.items()
    ]
    answers = [
        Answer(
            user_id=row.user_id,
            mode=row.mode,
            fraud_type=row.fraud_type,
            correct=row.correct,
            missed_tags=list(row.missed_tags),
            at=row.created_at,
        )
        for row in session.exec(
            select(PracticeAnswer).where(
                col(PracticeAnswer.user_id).in_(user_ids),
                col(PracticeAnswer.mode).in_([m for m, _ in PRACTICE_MODES]),
            )
        ).all()
        if row.created_at is not None
    ]
    return EffectInput(exams, entries, answers)
