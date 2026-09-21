"""天梯主線旅程狀態解析（Brief 10 / 10b）。

純狀態解析函式，無 DB 副作用。
根據玩家 completed_chapters、UserChapterProgress、active/paused session 與故事紀錄，
解析出五階天梯之公開狀態、遮罩資訊與唯一的下一步推薦（next_step）。
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.economy.chapters import LADDER_RUNGS, get_unlocked_contact_ids
from app.models import ScenarioSession, ScenarioStatus, UserChapterProgress
from app.scenario.stories import CONTACTS, pick_story_for_contact
from app.schemas import (
    JourneyChapterPublic,
    JourneyNextStepPublic,
    JourneyResponse,
    JourneyStepPublic,
)

if TYPE_CHECKING:
    pass


def resolve_journey_state(
    completed_chapters: int,
    progress_by_chapter: dict[int, UserChapterProgress | None],
    active_or_paused_session: ScenarioSession | None,
    user_completed_story_ids: set[str],
) -> JourneyResponse:
    """純狀態解析函式：決定天梯進度與唯一 next_step。

    優先順序：
    1. 任一 owned active/paused session：回到原 session（即使是歷史高階人物）
    2. 當前階 quiz_completed == false：先看一眼 -> /quick/quiz
    3. 當前階 scenario_completed == false：接下委託 -> 符合當前階之可達故事
    4. 剛升階：顯示新人物解鎖與開場
    5. 五階完成：來一件新的生活事件（不顯示不存在的第六階）
    """
    safe_completed = min(5, max(0, completed_chapters))
    unlocked_contact_ids = get_unlocked_contact_ids(safe_completed)
    current_rung_id = min(5, safe_completed + 1)
    is_all_completed = safe_completed >= 5

    # 1. 建立五階天梯資訊（含遮罩與防洩漏）
    all_chapters: list[JourneyChapterPublic] = []
    for r in LADDER_RUNGS:
        prog = progress_by_chapter.get(r.rung_id)
        quiz_done = prog.quiz_completed if prog else False
        scenario_done = prog.scenario_completed if prog else False

        is_rung_completed = r.rung_id <= safe_completed
        is_rung_current = (r.rung_id == current_rung_id) and not is_all_completed
        is_rung_locked = r.rung_id > (safe_completed + 1)

        # 聯絡人資訊遮罩（防洩漏）
        contact_info = CONTACTS.get(r.contact_id)
        if is_all_completed or r.rung_id <= safe_completed + 1:
            # 已完成或當前階或五階全通：顯示正常公開資訊
            c_id = r.contact_id
            c_name = contact_info.name if contact_info else r.contact_id
            c_avatar = contact_info.avatar if contact_info else "👤"
            c_persona = contact_info.persona_desc if contact_info else ""
        elif r.rung_id == safe_completed + 2:
            # 下一個即將解鎖的階級：遮罩，顯示下一階預告或剪影，不洩漏故事
            c_id = None
            c_name = f"下一階解鎖：{contact_info.name}" if contact_info else "新聯絡人"
            c_avatar = "🔒"
            c_persona = "完成當前階級後解鎖此人物故事線"
        else:
            # 距離超過一階的高階：完全剪影
            c_id = None
            c_name = "神秘聯絡人"
            c_avatar = "🔒"
            c_persona = "天梯更高階解鎖"

        # 節點狀態（先看一眼／接下委託）
        if is_rung_completed:
            steps = [
                JourneyStepPublic(id="quiz", label="先看一眼", status="completed"),
                JourneyStepPublic(id="scenario", label="接下委託", status="completed"),
            ]
        elif is_rung_current:
            quiz_status = "completed" if quiz_done else "current"
            if scenario_done:
                scenario_status = "completed"
            elif quiz_done:
                scenario_status = "current"
            else:
                scenario_status = "upcoming"
            steps = [
                JourneyStepPublic(id="quiz", label="先看一眼", status=quiz_status),
                JourneyStepPublic(id="scenario", label="接下委託", status=scenario_status),
            ]
        else:
            steps = [
                JourneyStepPublic(id="quiz", label="先看一眼", status="upcoming"),
                JourneyStepPublic(id="scenario", label="接下委託", status="upcoming"),
            ]

        # 標題與簡介防洩漏：未解鎖的高階只顯示主題，不洩漏細節
        if is_rung_locked and r.rung_id > safe_completed + 1:
            desc = "通關前置階級以解鎖本階內容。"
        else:
            desc = r.description

        all_chapters.append(
            JourneyChapterPublic(
                id=r.rung_id,
                title=r.chapter_title,
                rung_title=r.rung_title,
                description=desc,
                completed=is_rung_completed,
                is_current=is_rung_current,
                is_locked=is_rung_locked,
                contact_id=c_id,
                contact_name=c_name,
                contact_avatar=c_avatar,
                contact_persona=c_persona,
                steps=steps,
            )
        )

    # 2. 當前主要階級（若全通則為第 5 階）
    current_chapter_public = (
        all_chapters[-1] if is_all_completed else all_chapters[current_rung_id - 1]
    )

    # 3. 推薦優先順序判定（Next Step）
    # 優先級 1：任一 owned active/paused session
    if active_or_paused_session is not None:
        s = active_or_paused_session
        s_title = None
        if s.story_snapshot and "title" in s.story_snapshot:
            s_title = s.story_snapshot["title"]

        if s_title:
            title = f"回去處理：{s.display_name}的「{s_title}」"
        else:
            title = f"回去看看{s.display_name}怎麼了"

        if s.status == ScenarioStatus.PAUSED:
            reason = "這件事先暫停了，先把相關通聯與資料確認清楚。"
        else:
            reason = f"{s.display_name}還在等待你的回覆。"

        next_step = JourneyNextStepPublic(
            kind="resume_scenario",
            title=title,
            reason=reason,
            href=f"/scenarios/{s.id}",
            contact_id=s.contact_id,
            story_id=s.story_id,
            scenario_id=str(s.id),
        )
    elif is_all_completed:
        # 優先級 5：五階全數完成
        next_step = JourneyNextStepPublic(
            kind="all_completed",
            title="來一件新的生活事件",
            reason="你已完成五階天梯考驗，隨時可以前往收件匣挑戰其他生活委託。",
            href="/scenarios",
        )
    else:
        current_prog = progress_by_chapter.get(current_rung_id)
        q_done = current_prog.quiz_completed if current_prog else False
        s_done = current_prog.scenario_completed if current_prog else False
        current_rung = LADDER_RUNGS[current_rung_id - 1]
        current_contact = CONTACTS.get(current_rung.contact_id)
        contact_name = current_contact.name if current_contact else "聯絡人"

        if not q_done:
            # 優先級 2：當前階 quiz_completed == false
            next_step = JourneyNextStepPublic(
                kind="quiz",
                title=f"先看一眼：{current_rung.chapter_title}",
                reason=f"在幫{contact_name}處理事情前，先看幾則相關案例掌握判讀重點。",
                href="/quick/quiz",
                estimated_time="約 2 分鐘",
                contact_id=current_rung.contact_id,
            )
        elif not s_done:
            # 優先級 3：當前階 scenario_completed == false
            story = pick_story_for_contact(
                current_rung.contact_id, user_completed_story_ids
            )
            if story:
                next_step = JourneyNextStepPublic(
                    kind="start_scenario",
                    title=f"接下委託：{story.title}",
                    reason=f"{contact_name}有件事想請教你。",
                    href=f"/scenarios?contact_id={current_rung.contact_id}",
                    contact_id=current_rung.contact_id,
                    story_id=story.story_id,
                )
            else:
                next_step = JourneyNextStepPublic(
                    kind="start_scenario",
                    title=f"幫{contact_name}處理事件",
                    reason=f"前往收件匣看看{contact_name}的最新動態。",
                    href="/scenarios",
                    contact_id=current_rung.contact_id,
                )
        else:
            # 優先級 4：剛升階（當前階兩步皆剛完成，晉級到下一階）
            next_rung_id = current_rung_id + 1
            if next_rung_id <= len(LADDER_RUNGS):
                next_rung = LADDER_RUNGS[next_rung_id - 1]
                next_c = CONTACTS.get(next_rung.contact_id)
                next_name = next_c.name if next_c else "新聯絡人"
                next_step = JourneyNextStepPublic(
                    kind="chapter_cleared",
                    title=f"解鎖新聯絡人：{next_name}",
                    reason=f"你已完成第 {current_rung_id} 階！即將開啟第 {next_rung_id} 階「{next_rung.chapter_title}」。",
                    href="/quick/quiz",
                    contact_id=next_rung.contact_id,
                )
            else:
                next_step = JourneyNextStepPublic(
                    kind="all_completed",
                    title="來一件新的生活事件",
                    reason="五階天梯考驗已全數通過！",
                    href="/scenarios",
                )

    return JourneyResponse(
        chapter=current_chapter_public,
        next_step=next_step,
        all_chapters=all_chapters,
        completed_chapters=safe_completed,
        unlocked_contact_ids=unlocked_contact_ids,
    )
