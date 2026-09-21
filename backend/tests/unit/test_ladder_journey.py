"""測試天梯主線、聯絡人解鎖與狀態驅動之旅程推薦（Brief 10 / 10b）。"""

from __future__ import annotations

import uuid
from typing import Any
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException

from app.api.routes import economy as economy_routes
from app.api.routes import scenario as scenario_routes
from app.economy.chapters import (
    LADDER_ORDER,
    get_unlocked_contact_ids,
    is_contact_unlocked,
    record_ladder_scenario_progress,
    record_quiz_progress,
    record_scenario_progress,
)
from app.economy.journey import resolve_journey_state
from app.models import ScenarioSession, ScenarioStatus, User, UserChapterProgress
from app.schemas import ScenarioNewRequest


class FakeSession:
    """輕量記憶體 Session 供免 DB 單元測試使用。"""

    def __init__(self) -> None:
        self.data: list[Any] = []

    def add(self, obj: Any) -> None:
        if obj not in self.data:
            self.data.append(obj)

    def flush(self) -> None:
        pass

    def exec(self, query: Any) -> FakeResult:
        target_ch = None
        try:
            for cl in getattr(query, "_where_criteria", []):
                for child in getattr(cl, "clauses", [cl]):
                    if getattr(child, "left", None) is not None and getattr(child.left, "key", None) == "chapter_id":
                        target_ch = getattr(child.right, "value", None)
        except Exception:
            pass

        progs = [x for x in self.data if isinstance(x, UserChapterProgress)]
        if target_ch is not None:
            progs = [p for p in progs if p.chapter_id == target_ch]
        return FakeResult(progs)


class FakeResult:

    def __init__(self, items: list[Any]) -> None:
        self.items = items

    def first(self) -> Any | None:
        return self.items[0] if self.items else None

    def all(self) -> list[Any]:
        return list(self.items)


def test_ladder_unlocks_by_completed_chapters() -> None:
    """驗證完成 0..5 章時的解鎖聯絡人集合。"""
    # 0 章：僅起始人物房東阿姨
    assert get_unlocked_contact_ids(0) == ["landlady"]
    assert is_contact_unlocked("landlady", 0) is True
    assert is_contact_unlocked("li_li", 0) is False
    assert is_contact_unlocked("a_can", 0) is False
    assert is_contact_unlocked("hao_ge", 0) is False
    assert is_contact_unlocked("wei_jie", 0) is False

    # 1 章：解鎖梨梨
    assert get_unlocked_contact_ids(1) == ["landlady", "li_li"]
    assert is_contact_unlocked("li_li", 1) is True
    assert is_contact_unlocked("a_can", 1) is False

    # 2 章：解鎖阿燦
    assert get_unlocked_contact_ids(2) == ["landlady", "li_li", "a_can"]
    assert is_contact_unlocked("a_can", 2) is True
    assert is_contact_unlocked("hao_ge", 2) is False

    # 3 章：解鎖豪哥
    assert get_unlocked_contact_ids(3) == ["landlady", "li_li", "a_can", "hao_ge"]
    assert is_contact_unlocked("hao_ge", 3) is True
    assert is_contact_unlocked("wei_jie", 3) is False

    # 4 章：五人全數解鎖
    assert get_unlocked_contact_ids(4) == LADDER_ORDER
    assert is_contact_unlocked("wei_jie", 4) is True

    # 5 章以上：保持五人全解鎖
    assert get_unlocked_contact_ids(5) == LADDER_ORDER
    assert get_unlocked_contact_ids(6) == LADDER_ORDER


def test_ladder_scenario_progression_contact_matching() -> None:
    """驗證以 contact_id 進行天梯 scenario 進度判定。"""
    session = FakeSession()
    u = User(
        id=uuid.uuid4(),
        email="ladder@test.com",
        hashed_password="h",
        completed_chapters=0,
    )

    # 1. 第 1 階當前人物為 landlady；若完成其他人物（如歷史殘留 wei_jie），不推進第 1 階
    advanced = record_ladder_scenario_progress(
        session, u, contact_id="wei_jie", has_evidence=True
    )
    assert advanced is False
    assert u.completed_chapters == 0

    # 2. 無查證證據時，即使人物相符也不完成
    advanced = record_ladder_scenario_progress(
        session, u, contact_id="landlady", has_evidence=False
    )
    assert advanced is False
    assert u.completed_chapters == 0

    # 3. 符合當前階人物且有充分證據 -> 標記 scenario_completed
    advanced = record_ladder_scenario_progress(
        session, u, contact_id="landlady", has_evidence=True
    )
    assert advanced is False  # 因 quiz 尚未完成，未晉級
    assert u.completed_chapters == 0

    # 4. 補上 quiz -> 雙條件滿足，自動晉級至第 1 章
    advanced = record_quiz_progress(session, u)
    assert advanced is True
    assert u.completed_chapters == 1

    # 5. 第 2 階人物為 li_li；完成 li_li 且有證據，若先做完 quiz
    advanced = record_quiz_progress(session, u)
    assert advanced is False
    advanced = record_ladder_scenario_progress(
        session, u, contact_id="li_li", has_evidence=True
    )
    assert advanced is True
    assert u.completed_chapters == 2


def test_legacy_scenario_progression_fallback() -> None:
    """舊版無 story_id 之情境繼續走 skill_type / fraud_type 邏輯。"""
    session = FakeSession()
    u = User(
        id=uuid.uuid4(),
        email="legacy@test.com",
        hashed_password="h",
        completed_chapters=0,
    )
    # 第 1 章 skill_type 為 fake-sale
    advanced = record_scenario_progress(
        session, u, fraud_type="fake-sale", has_evidence=True
    )
    assert advanced is False  # 還缺 quiz
    record_quiz_progress(session, u)
    assert u.completed_chapters == 1


def test_journey_seven_states() -> None:
    """測試七種關鍵狀態之解析結果：

    1. 新玩家 (completed_chapters=0, 無進度)
    2. quiz-only
    3. scenario-only
    4. active session
    5. paused session
    6. chapter complete (剛升階)
    7. all complete (五階全通)
    """
    user_id = uuid.uuid4()

    # 1. 新玩家：第 1 階，推薦「先看一眼」短判讀
    res_new = resolve_journey_state(
        completed_chapters=0,
        progress_by_chapter={},
        active_or_paused_session=None,
        user_completed_story_ids=set(),
    )
    assert res_new.completed_chapters == 0
    assert res_new.chapter.id == 1
    assert res_new.chapter.contact_name == "房東阿姨"
    assert res_new.next_step.kind == "quiz"
    assert res_new.next_step.href == "/quick/quiz"
    assert "先看一眼" in res_new.next_step.title
    assert res_new.chapter.steps[0].status == "current"
    assert res_new.chapter.steps[1].status == "upcoming"

    # 2. quiz-only：已完成短判讀，推薦當前階人物委託
    prog_q_only = UserChapterProgress(
        user_id=user_id,
        chapter_id=1,
        quiz_completed=True,
        scenario_completed=False,
    )
    res_q_only = resolve_journey_state(
        completed_chapters=0,
        progress_by_chapter={1: prog_q_only},
        active_or_paused_session=None,
        user_completed_story_ids=set(),
    )
    assert res_q_only.next_step.kind == "start_scenario"
    assert res_q_only.next_step.contact_id == "landlady"
    assert res_q_only.next_step.story_id == "fire_safety_inspection"
    assert "接下委託" in res_q_only.next_step.title
    assert res_q_only.chapter.steps[0].status == "completed"
    assert res_q_only.chapter.steps[1].status == "current"

    # 3. scenario-only：已完成情境查證，推薦短判讀
    prog_s_only = UserChapterProgress(
        user_id=user_id,
        chapter_id=1,
        quiz_completed=False,
        scenario_completed=True,
    )
    res_s_only = resolve_journey_state(
        completed_chapters=0,
        progress_by_chapter={1: prog_s_only},
        active_or_paused_session=None,
        user_completed_story_ids=set(),
    )
    assert res_s_only.next_step.kind == "quiz"
    assert res_s_only.next_step.href == "/quick/quiz"

    # 4. active session：優先回到進行中對話
    active_sess_id = uuid.uuid4()
    active_sc = ScenarioSession(
        id=active_sess_id,
        user_id=user_id,
        fraud_type="investment",
        persona_role="scam",
        display_name="薇姐",
        avatar="WEI",
        contact_id="wei_jie",
        story_id="living_farewell",
        story_snapshot={"title": "生前告別狂歡派對企劃"},
        status=ScenarioStatus.ACTIVE,
        stake_loss=1000,
        reward_win=1000,
        reward_legit=500,
        penalty_misreport=200,
    )
    res_active = resolve_journey_state(
        completed_chapters=0,
        progress_by_chapter={},
        active_or_paused_session=active_sc,
        user_completed_story_ids=set(),
    )
    assert res_active.next_step.kind == "resume_scenario"
    assert res_active.next_step.href == f"/scenarios/{active_sess_id}"
    assert "薇姐" in res_active.next_step.title
    assert "等" in res_active.next_step.reason

    # 5. paused session：優先回到暫停中對話
    paused_sess_id = uuid.uuid4()
    paused_sc = ScenarioSession(
        id=paused_sess_id,
        user_id=user_id,
        fraud_type="atm",
        persona_role="legit",
        display_name="房東阿姨",
        avatar="LAND",
        contact_id="landlady",
        story_id="fire_safety_inspection",
        story_snapshot={"title": "消防設備複查通知"},
        status=ScenarioStatus.PAUSED,
        stake_loss=1000,
        reward_win=1000,
        reward_legit=500,
        penalty_misreport=200,
    )
    res_paused = resolve_journey_state(
        completed_chapters=0,
        progress_by_chapter={},
        active_or_paused_session=paused_sc,
        user_completed_story_ids=set(),
    )
    assert res_paused.next_step.kind == "resume_scenario"
    assert res_paused.next_step.href == f"/scenarios/{paused_sess_id}"
    assert "暫停" in res_paused.next_step.reason

    # 6. chapter complete (兩步皆完成，即將晉級)
    prog_both = UserChapterProgress(
        user_id=user_id,
        chapter_id=1,
        quiz_completed=True,
        scenario_completed=True,
        is_completed=True,
    )
    res_chapter_cleared = resolve_journey_state(
        completed_chapters=0,
        progress_by_chapter={1: prog_both},
        active_or_paused_session=None,
        user_completed_story_ids=set(),
    )
    assert res_chapter_cleared.next_step.kind == "chapter_cleared"
    assert "梨梨" in res_chapter_cleared.next_step.title

    # 7. all complete (五階全通)
    res_all_done = resolve_journey_state(
        completed_chapters=5,
        progress_by_chapter={},
        active_or_paused_session=None,
        user_completed_story_ids=set(),
    )
    assert res_all_done.completed_chapters == 5
    assert res_all_done.next_step.kind == "all_completed"
    assert res_all_done.next_step.title == "來一件新的生活事件"
    assert res_all_done.next_step.href == "/scenarios"
    # 確保天梯只有 5 階，不出現第 6 階
    assert len(res_all_done.all_chapters) == 5
    assert all(c.completed for c in res_all_done.all_chapters)


def test_journey_does_not_leak_locked_stories() -> None:
    """驗證未解鎖階級不洩漏故事標題、真假、固定事實或對白。"""
    res = resolve_journey_state(
        completed_chapters=0,
        progress_by_chapter={},
        active_or_paused_session=None,
        user_completed_story_ids=set(),
    )
    # 第 1 階（當前階）：公開房東阿姨
    assert res.all_chapters[0].contact_id == "landlady"
    assert res.all_chapters[0].contact_name == "房東阿姨"
    assert res.all_chapters[0].is_locked is False

    # 第 2 階（下一階）：遮罩預告，不洩漏具體故事
    assert res.all_chapters[1].contact_id is None
    assert "下一階解鎖" in (res.all_chapters[1].contact_name or "")
    assert res.all_chapters[1].contact_avatar == "🔒"
    assert res.all_chapters[1].is_locked is True

    # 第 3 階（更高階）：神秘聯絡人剪影
    assert res.all_chapters[2].contact_id is None
    assert res.all_chapters[2].contact_name == "神秘聯絡人"
    assert res.all_chapters[2].contact_avatar == "🔒"
    assert res.all_chapters[2].is_locked is True

    # 第 4、5 階：均為剪影
    for higher_rung in res.all_chapters[3:]:
        assert higher_rung.contact_id is None
        assert higher_rung.contact_name == "神秘聯絡人"
        assert higher_rung.is_locked is True


def test_api_contact_locked_enforcement() -> None:
    """驗證玩家無法直接新建未解鎖聯絡人之故事（回傳 contact_locked）。"""
    # 模擬 locked_user completed_chapters = 0
    u = User(
        id=uuid.uuid4(),
        email="test@test.com",
        hashed_password="h",
        completed_chapters=0,
    )

    # 房東阿姨已解鎖
    assert is_contact_unlocked("landlady", u.completed_chapters) is True

    # 薇姐尚未解鎖
    assert is_contact_unlocked("wei_jie", u.completed_chapters) is False


def test_create_scenario_route_blocks_locked_contact(monkeypatch: pytest.MonkeyPatch) -> None:
    """驗證 POST /scenario/new 對未解鎖人物拋出 400 contact_locked。"""
    session = MagicMock()
    user = User(
        id=uuid.uuid4(),
        email="test@test.com",
        hashed_password="h",
        completed_chapters=0,
    )
    monkeypatch.setattr(scenario_routes, "lock_user", lambda _s, u: u)

    with pytest.raises(HTTPException) as exc_info:
        scenario_routes.create_scenario(
            ScenarioNewRequest(contact_id="wei_jie"),
            session=session,
            current_user=user,
        )
    assert exc_info.value.status_code == 400
    assert exc_info.value.detail["code"] == "contact_locked"


def test_get_journey_route_read_only_and_user_isolated() -> None:
    """驗證 GET /economy/journey 無副作用且嚴格隔離使用者 session。"""
    session = MagicMock()
    user = User(
        id=uuid.uuid4(),
        email="owner@test.com",
        hashed_password="h",
        completed_chapters=0,
    )

    def mock_exec(stmt: Any) -> Any:
        mock_res = MagicMock()
        str_stmt = str(stmt)
        if "scenario_session" in str_stmt.lower():
            mock_res.first.return_value = None
        elif "user_chapter_progress" in str_stmt.lower():
            mock_res.all.return_value = []
        elif "user_contact_relation" in str_stmt.lower():
            mock_res.all.return_value = []
        return mock_res

    session.exec = mock_exec

    journey = economy_routes.get_journey(session=session, current_user=user)
    assert session.add.call_count == 0
    assert session.commit.call_count == 0
    assert journey.next_step.kind == "quiz"
    assert journey.next_step.href == "/quick/quiz"

