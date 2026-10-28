"""班級總覽：全班哪一類最弱、每份作業誰還沒做完；學生詳情與 CSV 也在這裡組。"""

import uuid
from typing import Any

from sqlmodel import Session, col, select

from app.classroom.members import last_active, latest_exam_scores, member_rows
from app.classroom.mine import assignments_for
from app.classroom.progress import AssignmentProgress, assignment_progress
from app.classroom.schemas import (
    AssignmentSummary,
    ClassMemberDetail,
    ClassOverview,
    PendingStudent,
)
from app.core.fraud_types import FRAUD_TYPE_LABELS
from app.exam.export import item_answer
from app.models import ClassAssignment, ClassMember, ExamAttempt
from app.trial.analytics import FRAUD_TYPE_ORDER, TypeAccuracy
from app.trial.detail import (
    exam_details,
    practice_details,
    practice_rows_of,
    pretest_details,
)

KINDS = ("comprehensive", "specialized", "practice", "pretest")
PRACTICE_MODES = (("swipe", "滑卡"), ("quiz", "訊息判讀"), ("scenario", "情境對抗"))
STATUS_LABELS = {
    "todo": "還沒做",
    "done": "完成",
    "late": "遲交",
    "overdue": "過期沒做",
}


class InvalidAssignment(ValueError):
    pass


def clean_params(kind: str, params: dict[str, Any]) -> dict[str, Any]:
    """依種類留下需要的欄位；不合理就丟 InvalidAssignment（路由回 400）。"""
    if kind not in KINDS:
        raise InvalidAssignment(kind)
    fraud_type = params.get("fraud_type") or None
    if fraud_type is not None and fraud_type not in FRAUD_TYPE_LABELS:
        raise InvalidAssignment(fraud_type)
    if kind == "comprehensive":
        return {"require_pass": bool(params.get("require_pass"))}
    if kind == "specialized":
        if fraud_type is None:
            raise InvalidAssignment("fraud_type")
        return {
            "fraud_type": fraud_type,
            "require_pass": bool(params.get("require_pass")),
        }
    if kind == "practice":
        counts: dict[str, Any] = {}
        for mode, _ in PRACTICE_MODES:
            value = params.get(mode) or 0
            if not isinstance(value, int) or value < 0 or value > 500:
                raise InvalidAssignment(mode)
            counts[mode] = value
        if not any(counts.values()):
            raise InvalidAssignment("empty")
        return {**counts, "fraud_type": fraud_type}
    return {}


def auto_title(kind: str, params: dict[str, Any]) -> str:
    if kind == "comprehensive":
        return "綜合檢測（要過關）" if params["require_pass"] else "綜合檢測"
    if kind == "specialized":
        label = f"專項檢測：{FRAUD_TYPE_LABELS[params['fraud_type']]}"
        return f"{label}（要過關）" if params["require_pass"] else label
    if kind == "practice":
        parts = [
            f"{label} {params[mode]}" for mode, label in PRACTICE_MODES if params[mode]
        ]
        prefix = (
            f"練習{FRAUD_TYPE_LABELS[params['fraud_type']]}："
            if params.get("fraud_type")
            else "練習："
        )
        return prefix + "、".join(parts)
    return "入門前測"


def _exam_pretest_marks(exam: ExamAttempt) -> list[tuple[str, bool]]:
    answers = exam.answers.get("pretest", {})
    return [
        (
            str(item.get("fraud_type", "")),
            item_answer("pretest", index, item, answers)[1] == "true",
        )
        for index, item in enumerate(exam.items.get("pretest", []))
    ]


def class_type_accuracy(
    session: Session, user_ids: list[uuid.UUID]
) -> tuple[list[TypeAccuracy], int]:
    """每人取最近一次正常交卷的綜合檢測前測關；沒有就取最近一次入門前測。"""
    marks_by_user: dict[uuid.UUID, list[tuple[str, bool]]] = {}
    if user_ids:
        for exam in session.exec(
            select(ExamAttempt)
            .where(
                col(ExamAttempt.user_id).in_(user_ids),
                ExamAttempt.mode == "comprehensive",
                ExamAttempt.status == "completed",
                col(ExamAttempt.counted).is_(True),
            )
            .order_by(col(ExamAttempt.completed_at).desc())
        ).all():
            if exam.user_id not in marks_by_user:
                marks = _exam_pretest_marks(exam)
                if marks:
                    marks_by_user[exam.user_id] = marks
        for uid in user_ids:
            if uid in marks_by_user:
                continue
            pretests = [p for p in pretest_details(session, uid) if p.items]
            if pretests:
                marks_by_user[uid] = [
                    (i.fraud_type, i.is_correct) for i in pretests[-1].items
                ]
    cells: dict[str, list[int]] = {t: [0, 0] for t in FRAUD_TYPE_ORDER}
    for marks in marks_by_user.values():
        for fraud_type, ok in marks:
            cell = cells.setdefault(fraud_type, [0, 0])
            cell[0] += int(ok)
            cell[1] += 1
    accuracy = [
        TypeAccuracy(
            fraud_type=t,
            accuracy=round(cells[t][0] / cells[t][1], 3) if cells[t][1] else None,
            n=cells[t][1],
        )
        for t in FRAUD_TYPE_ORDER
    ]
    return accuracy, len(marks_by_user)


def weakest_types(accuracy: list[TypeAccuracy]) -> list[str]:
    known = [t for t in accuracy if t.accuracy is not None]
    if not known:
        return []
    lowest = min(t.accuracy for t in known if t.accuracy is not None)
    return [t.fraud_type for t in known if t.accuracy == lowest]


def class_assignments(
    session: Session, classroom_id: uuid.UUID
) -> list[ClassAssignment]:
    return list(
        session.exec(
            select(ClassAssignment)
            .where(ClassAssignment.classroom_id == classroom_id)
            .order_by(col(ClassAssignment.due_at), col(ClassAssignment.created_at))
        ).all()
    )


def class_members(session: Session, classroom_id: uuid.UUID) -> list[ClassMember]:
    return list(
        session.exec(
            select(ClassMember)
            .where(ClassMember.classroom_id == classroom_id)
            .order_by(
                col(ClassMember.student_number).nulls_last(), col(ClassMember.joined_at)
            )
        ).all()
    )


def pending_student_count(session: Session, classroom_id: uuid.UUID) -> int:
    members = class_members(session, classroom_id)
    ids = [m.user_id for m in members]
    pending: set[uuid.UUID] = set()
    for row in class_assignments(session, classroom_id):
        for uid, progress in assignment_progress(session, row, ids).items():
            if progress.status in ("todo", "overdue"):
                pending.add(uid)
    return len(pending)


def _student(m: ClassMember, p: AssignmentProgress) -> PendingStudent:
    return PendingStudent(
        user_id=m.user_id,
        student_number=m.student_number,
        student_name=m.student_name,
        status=p.status,
        progress_text=p.progress_text,
    )


def class_overview(session: Session, classroom_id: uuid.UUID) -> ClassOverview:
    members = class_members(session, classroom_id)
    ids = [m.user_id for m in members]
    accuracy, used = class_type_accuracy(session, ids)
    summaries: list[AssignmentSummary] = []
    for row in class_assignments(session, classroom_id):
        progress = assignment_progress(session, row, ids)

        summaries.append(
            AssignmentSummary(
                **row.model_dump(),
                done=sum(p.status == "done" for p in progress.values()),
                late=sum(p.status == "late" for p in progress.values()),
                pending=[
                    _student(m, progress[m.user_id])
                    for m in members
                    if progress[m.user_id].status in ("todo", "overdue")
                ],
                late_students=[
                    _student(m, progress[m.user_id])
                    for m in members
                    if progress[m.user_id].status == "late"
                ],
            )
        )
    return ClassOverview(
        member_count=len(members),
        type_accuracy=accuracy,
        accuracy_n=used,
        weakest=weakest_types(accuracy),
        assignments=summaries,
    )


def member_detail(session: Session, member: ClassMember) -> ClassMemberDetail:
    uid = member.user_id
    return ClassMemberDetail(
        user_id=uid,
        student_number=member.student_number,
        student_name=member.student_name,
        joined_at=member.joined_at,
        last_active_at=last_active(session, [uid]).get(uid),
        exams=exam_details(session, uid),
        practice=practice_details(practice_rows_of(session, uid)),
        assignments=assignments_for(session, member.classroom_id, uid),
    )


EXPORT_FIELDS = (
    "student_number",
    "student_name",
    "joined_at",
    "last_active_at",
    "latest_exam_score",
    "latest_exam_pretest_correct",
    "swipe_total",
    "quiz_total",
    "scenario_total",
)


def export_rows(
    session: Session, classroom_id: uuid.UUID
) -> tuple[tuple[str, ...], list[dict[str, str | int]]]:
    """一人一列；每份作業兩欄「<標題>_狀態」「<標題>_完成時間」。"""
    members = class_members(session, classroom_id)
    ids = [m.user_id for m in members]
    rows_public = {r.user_id: r for r in member_rows(session, classroom_id)}
    scores = latest_exam_scores(session, ids)
    latest_pretest: dict[uuid.UUID, int] = {}
    for exam in session.exec(
        select(ExamAttempt)
        .where(
            col(ExamAttempt.user_id).in_(ids),
            ExamAttempt.mode == "comprehensive",
            ExamAttempt.status == "completed",
            col(ExamAttempt.counted).is_(True),
        )
        .order_by(col(ExamAttempt.completed_at).desc())
    ).all():
        if exam.user_id not in latest_pretest:
            latest_pretest[exam.user_id] = sum(
                ok for _, ok in _exam_pretest_marks(exam)
            )
    assignments = class_assignments(session, classroom_id)
    progress = {a.id: assignment_progress(session, a, ids) for a in assignments}
    # 同名作業加上序號，欄位才不會互相覆蓋
    titles: list[str] = []
    for a in assignments:
        title = a.title
        n = 2
        while title in titles:
            title = f"{a.title}（{n}）"
            n += 1
        titles.append(title)
    fields = EXPORT_FIELDS + tuple(
        column for title in titles for column in (f"{title}_狀態", f"{title}_完成時間")
    )
    rows: list[dict[str, str | int]] = []
    for m in members:
        practice = {
            p.mode: p.total
            for p in practice_details(practice_rows_of(session, m.user_id))
        }
        public = rows_public[m.user_id]
        row: dict[str, str | int] = {
            "student_number": m.student_number or "",
            "student_name": m.student_name or "",
            "joined_at": m.joined_at.isoformat(),
            "last_active_at": public.last_active_at.isoformat()
            if public.last_active_at
            else "",
            "latest_exam_score": scores.get(m.user_id, ""),
            "latest_exam_pretest_correct": latest_pretest.get(m.user_id, ""),
            "swipe_total": practice.get("swipe", 0),
            "quiz_total": practice.get("quiz", 0),
            "scenario_total": practice.get("scenario", 0),
        }
        for a, title in zip(assignments, titles, strict=True):
            p = progress[a.id][m.user_id]
            row[f"{title}_狀態"] = STATUS_LABELS[p.status]
            row[f"{title}_完成時間"] = (
                p.completed_at.isoformat() if p.completed_at else ""
            )
        rows.append(row)
    return fields, rows
