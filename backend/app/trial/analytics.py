"""管理頁的試測數據與問卷分析。只讀、只統計，判定沿用成員 CSV 的那一套。

輸入是成員 CSV 的列（`admin_cohorts.build_export_rows`），再補查綜合檢測前測關的分類型答對數。
前測和之後作答的比較（成效）在 `app/trial/effect.py`；問卷的前後對照是信心題。
"""

import statistics
import uuid
from collections.abc import Sequence
from typing import Any

from sqlmodel import Session, SQLModel, col, select

from app.exam.export import item_answer
from app.models import ExamAttempt, TrialSurvey
from app.trial.effect import EffectAnalytics, effect_analytics, load_effect_input
from app.trial.payout import EXAM_MIN_SECONDS
from app.trial.survey import (
    ATTENTION_ID,
    OTHER,
    QUESTIONS,
    TAM_CONSTRUCTS,
    Question,
)
from app.trial.survey import (
    MIN_SECONDS as SURVEY_MIN_SECONDS,
)

CsvRow = dict[str, str | int]
FRAUD_TYPE_ORDER = ("investment", "fake-sale", "shopping", "romance", "atm")


class FunnelStep(SQLModel):
    key: str
    label: str
    count: int


class TypeAccuracy(SQLModel):
    """第一次考完的綜合檢測，前測關這一類的答對率與題數。"""

    fraud_type: str
    accuracy: float | None
    n: int


class HistogramBin(SQLModel):
    label: str
    count: int
    # 落在發錢門檻以下（太快）的區間
    below: bool = False


class ScoreStats(SQLModel):
    n: int
    passed: int
    mean: float | None
    bins: list[HistogramBin]


class TimingStats(SQLModel):
    key: str
    label: str
    threshold_seconds: int
    n: int
    below: int
    median_seconds: float | None
    bins: list[HistogramBin]


class LikertItem(SQLModel):
    id: str
    section: str
    question: str
    labels: list[str]
    counts: list[int]
    n: int
    mean: float | None


class ChoiceCount(SQLModel):
    label: str
    count: int


class ChoiceItem(SQLModel):
    id: str
    question: str
    multi: bool
    n: int
    options: list[ChoiceCount]


class TextAnswer(SQLModel):
    participant_code: str
    text: str


class TextItem(SQLModel):
    id: str
    question: str
    answers: list[TextAnswer]


class ConfidenceShift(SQLModel):
    n: int
    before_mean: float | None
    after_mean: float | None
    diff_mean: float | None
    improved: int
    same: int
    worse: int


class TamConstruct(SQLModel):
    """科技接受模式一個構面：每人有答的題目取平均，再算全部人的平均。"""

    key: str
    label: str
    items: list[str]
    mean: float | None
    n: int
    # 構面題目全部答過的人數，與這些人算出的 Cronbach's α（變異為 0 或少於 2 人時是 null）
    complete: int
    alpha: float | None


class SurveyAnalytics(SQLModel):
    """交了問卷的人全部算進來（注意力題答錯、作答太快也算）；注意力題本身不列。"""

    responses: int
    tam: list[TamConstruct]
    likert: list[LikertItem]
    confidence: ConfidenceShift
    choices: list[ChoiceItem]
    texts: list[TextItem]


class TrialAnalytics(SQLModel):
    member_count: int
    funnel: list[FunnelStep]
    type_accuracy: list[TypeAccuracy]
    scores: ScoreStats
    timings: list[TimingStats]
    survey: SurveyAnalytics
    effect: EffectAnalytics


def _mean(values: Sequence[float]) -> float | None:
    return round(statistics.fmean(values), 2) if values else None


def _number(value: str | int) -> int | None:
    return None if value == "" else int(value)


def funnel(rows: list[CsvRow], payout: bool = True) -> list[FunnelStep]:
    steps = [
        FunnelStep(key="joined", label="加入", count=len(rows)),
        FunnelStep(
            key="exam",
            label="檢測交卷",
            count=sum(r["exam_completed"] == "true" for r in rows),
        ),
        FunnelStep(
            key="survey",
            label="交問卷",
            count=sum(r["survey_done"] == "true" for r in rows),
        ),
        FunnelStep(
            key="payout",
            label="可以領錢",
            count=sum(r["payout_eligible"] == "true" for r in rows),
        ),
    ]
    return steps if payout else [s for s in steps if s.key != "payout"]


def type_accuracy(session: Session, user_ids: list[uuid.UUID]) -> list[TypeAccuracy]:
    """各類答對率：每人第一次考完的綜合檢測前測關（和 CSV 的 first_exam 同一份）。"""
    cells: dict[str, list[int]] = {t: [0, 0] for t in FRAUD_TYPE_ORDER}
    if user_ids:
        seen: set[uuid.UUID] = set()
        for exam in session.exec(
            select(ExamAttempt)
            .where(
                col(ExamAttempt.user_id).in_(user_ids),
                ExamAttempt.counted == True,  # noqa: E712
                ExamAttempt.status != "active",
            )
            .order_by(col(ExamAttempt.created_at), col(ExamAttempt.id))
        ).all():
            if exam.user_id in seen:
                continue
            seen.add(exam.user_id)
            if exam.mode != "comprehensive":
                continue
            answers = exam.answers.get("pretest", {})
            for index, item in enumerate(exam.items.get("pretest", [])):
                mark = item_answer("pretest", index, item, answers)[1]
                cell = cells.setdefault(str(item.get("fraud_type", "")), [0, 0])
                cell[0] += int(mark == "true")
                cell[1] += 1
    return [
        TypeAccuracy(
            fraud_type=t,
            accuracy=round(cells[t][0] / cells[t][1], 3) if cells[t][1] else None,
            n=cells[t][1],
        )
        for t in FRAUD_TYPE_ORDER
    ]


def score_stats(rows: list[CsvRow]) -> ScoreStats:
    """每人最好的一次正常交卷分數。"""
    scores = [int(r["best_exam_score"]) for r in rows if r["best_exam_score"] != ""]
    bins = [
        HistogramBin(
            label=f"{low}–{low + 9 if low < 90 else 100}",
            count=sum(low <= s <= (low + 9 if low < 90 else 100) for s in scores),
            below=low + 9 < 70,
        )
        for low in range(0, 100, 10)
    ]
    return ScoreStats(
        n=len(scores),
        passed=sum(s >= 70 for s in scores),
        mean=_mean(scores),
        bins=bins,
    )


def histogram(
    values: list[int], edges: Sequence[int], threshold: int, unit: int = 1
) -> list[HistogramBin]:
    """`edges` 是秒數的區間起點；最後一格是「以上」。`unit` 60 時標籤用分鐘。"""
    bins: list[HistogramBin] = []
    for i, low in enumerate(edges):
        high = edges[i + 1] if i + 1 < len(edges) else None
        label = (
            f"{low // unit}–{high // unit}" if high is not None else f"{low // unit}+"
        )
        bins.append(
            HistogramBin(
                label=label,
                count=sum(low <= v and (high is None or v < high) for v in values),
                below=high is not None and high <= threshold,
            )
        )
    return bins


def timing_stats(rows: list[CsvRow]) -> list[TimingStats]:
    specs = (
        (
            "exam",
            "檢測（分鐘）",
            "exam_seconds",
            EXAM_MIN_SECONDS,
            (0, 180, 300, 600, 900, 1800, 3600),
            60,
        ),
        (
            "survey",
            "問卷（秒）",
            "survey_seconds",
            SURVEY_MIN_SECONDS,
            (0, 60, 120, 180, 300, 600),
            1,
        ),
    )
    stats: list[TimingStats] = []
    for key, label, field, threshold, edges, unit in specs:
        values = [v for r in rows if (v := _number(r[field])) is not None]
        stats.append(
            TimingStats(
                key=key,
                label=label,
                threshold_seconds=threshold,
                n=len(values),
                below=sum(v < threshold for v in values),
                median_seconds=statistics.median(values) if values else None,
                bins=histogram(values, edges, threshold, unit),
            )
        )
    return stats


def likert_item(q: Question, answers: list[dict[str, Any]]) -> LikertItem:
    values = [v for a in answers if isinstance(v := a.get(q.id), int)]
    return LikertItem(
        id=q.id,
        section=q.section,
        question=q.text,
        labels=list(q.labels),
        counts=[values.count(point) for point in range(1, len(q.labels) + 1)],
        n=len(values),
        mean=_mean(values),
    )


def cronbach_alpha(rows: list[list[int]]) -> float | None:
    """α = k/(k-1) × (1 − 各題變異數總和 / 總分變異數)；用樣本變異數。"""
    if len(rows) < 2 or len(rows[0]) < 2:
        return None
    k = len(rows[0])
    total_var = statistics.variance([sum(r) for r in rows])
    if total_var == 0:
        return None
    item_var = sum(statistics.variance([r[i] for r in rows]) for i in range(k))
    return round(k / (k - 1) * (1 - item_var / total_var), 2)


def tam_constructs(answers: list[dict[str, Any]]) -> list[TamConstruct]:
    rows: list[TamConstruct] = []
    for key, label in TAM_CONSTRUCTS:
        ids = [q.id for q in QUESTIONS if q.construct == key]
        person_means: list[float] = []
        complete: list[list[int]] = []
        for a in answers:
            values = [v for i in ids if isinstance(v := a.get(i), int)]
            if values:
                person_means.append(statistics.fmean(values))
            if len(values) == len(ids):
                complete.append(values)
        rows.append(
            TamConstruct(
                key=key,
                label=label,
                items=[q.text for q in QUESTIONS if q.construct == key],
                mean=_mean(person_means),
                n=len(person_means),
                complete=len(complete),
                alpha=cronbach_alpha(complete),
            )
        )
    return rows


def survey_analytics(surveys: list[tuple[str, TrialSurvey]]) -> SurveyAnalytics:
    """`surveys` 是交過的問卷與受試編號。"""
    answers = [s.answers for _, s in surveys]
    likert = [
        likert_item(q, answers)
        for q in QUESTIONS
        if q.kind == "scale" and q.id != ATTENTION_ID
    ]
    shifts = [
        (a["confidence_before"], a["confidence_after"])
        for a in answers
        if isinstance(a.get("confidence_before"), int)
        and isinstance(a.get("confidence_after"), int)
    ]
    diffs = [after - before for before, after in shifts]
    choices = [
        ChoiceItem(
            id=q.id,
            question=q.text,
            multi=q.kind == "multi",
            n=sum(q.id in a for a in answers),
            options=[
                ChoiceCount(
                    label=option,
                    count=sum(
                        option in v
                        if isinstance(v := a.get(q.id), list)
                        else v == option
                        for a in answers
                    ),
                )
                for option in q.options
            ],
        )
        for q in QUESTIONS
        if q.kind in ("single", "multi")
    ]
    texts = [
        TextItem(
            id=key,
            question=f"{q.text}：{OTHER}" if key.endswith("_other") else q.text,
            answers=[
                TextAnswer(participant_code=code, text=text)
                for code, s in surveys
                if isinstance(text := s.answers.get(key), str) and text
            ],
        )
        for q in QUESTIONS
        for key in (
            (f"{q.id}_other",) if q.other else (q.id,) if q.kind == "text" else ()
        )
    ]
    return SurveyAnalytics(
        responses=len(surveys),
        tam=tam_constructs(answers),
        likert=likert,
        confidence=ConfidenceShift(
            n=len(shifts),
            before_mean=_mean([b for b, _ in shifts]),
            after_mean=_mean([a for _, a in shifts]),
            diff_mean=_mean(diffs),
            improved=sum(d > 0 for d in diffs),
            same=sum(d == 0 for d in diffs),
            worse=sum(d < 0 for d in diffs),
        ),
        choices=choices,
        texts=texts,
    )


def trial_analytics(
    session: Session,
    rows: list[CsvRow],
    surveys: list[tuple[str, TrialSurvey]],
    payout: bool = True,
) -> TrialAnalytics:
    user_ids = [uuid.UUID(str(r["user_id"])) for r in rows]
    return TrialAnalytics(
        member_count=len(rows),
        funnel=funnel(rows, payout),
        type_accuracy=type_accuracy(session, user_ids),
        scores=score_stats(rows),
        timings=timing_stats(rows),
        survey=survey_analytics(surveys),
        effect=effect_analytics(load_effect_input(session, user_ids)),
    )
