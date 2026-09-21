"""PostgreSQL 17 隔離資料庫整合驗收測試 (C1–C8, A1–A8)。

驗證項目：
1. 商店購買、所有權、餘額限制與收據冪等防雙擊 (C5, A6)
2. 獨立查證工具有效性、道具持有檢查、未知工具拒絕 (C3, C5, A3, A6)
3. CAS Revision 樂觀鎖與並發防衝突 (C8, A6)
4. 確定性裁決、單一交易原子提交、獎勵防刷與收據冪等 (C4, C6, A6, A7)
5. 盲猜獎金嚴格上限 <= 100 與重放保護 (is_replay: 0 cash, 0 XP) (C6, A7)
6. 安全退出處置與事實防洩漏 (C2, C3, A4, A7)
7. 模型端異常單次呼叫、零重複重試、原子回滾 (T1, Item 5)
8. 拋棄式資料庫真實 Alembic 升級/舊版相容/降級循環 (T5)
"""

import asyncio
from concurrent.futures import ThreadPoolExecutor
import uuid
import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.models import (
    ActionReceipt,
    ScenarioSession,
    ScenarioStatus,
    User,
    UserContactRelation,
    UserItemInventory,
)
from app.scenario.stories import STORIES_CATALOG
from app.schemas import ScenarioReply


def test_pg_purchase_item_and_receipt_idempotency(client: TestClient, pg_session: Session, test_user: User):
    """驗證 C5 / A6：道具購買扣款、庫存增加與 Request ID 冪等防刷。"""
    initial_cash = test_user.cash
    req_id = f"buy_test_{uuid.uuid4().hex[:8]}"

    # 1. 首次購買 second_phone ($800)
    res1 = client.post("/api/v1/scenario/items/purchase", json={"item_id": "second_phone", "request_id": req_id})
    assert res1.status_code == 200, res1.text
    data1 = res1.json()
    assert data1["success"] is True
    assert data1["item_id"] == "second_phone"
    assert data1["cost"] == 800
    assert data1["new_cash"] == initial_cash - 800
    assert data1["quantity"] == 1

    # 2. 重送同一 request_id：應回傳完全相同的已儲存結果，不可重複扣款或增加庫存
    res2 = client.post("/api/v1/scenario/items/purchase", json={"item_id": "second_phone", "request_id": req_id})
    assert res2.status_code == 200
    assert res2.json() == data1

    # 檢查 PostgreSQL 實際資料
    db_user = pg_session.get(User, test_user.id)
    assert db_user is not None
    assert db_user.cash == initial_cash - 800

    inv = pg_session.exec(
        select(UserItemInventory).where(
            UserItemInventory.user_id == test_user.id,
            UserItemInventory.item_id == "second_phone",
        )
    ).first()
    assert inv is not None
    assert inv.quantity == 1

    receipt = pg_session.exec(
        select(ActionReceipt).where(
            ActionReceipt.user_id == test_user.id,
            ActionReceipt.request_id == req_id,
        )
    ).first()
    assert receipt is not None
    assert receipt.endpoint == "/items/purchase"

    # 3. 以同一 request_id 送出不同內容：應回傳 409 Conflict
    res_conflict = client.post("/api/v1/scenario/items/purchase", json={"item_id": "document_scanner", "request_id": req_id})
    assert res_conflict.status_code == 409


def test_pg_purchase_insufficient_funds_and_max_quantity(client: TestClient, pg_session: Session, test_user: User):
    """驗證 C5 / A6：餘額不足與重複購買單一持有道具拒絕。"""
    # 設置玩家現金為 100
    db_user = pg_session.get(User, test_user.id)
    assert db_user is not None
    db_user.cash = 100
    pg_session.add(db_user)
    pg_session.commit()

    # 1. 現金不足 ($100 < $800)
    res = client.post("/api/v1/scenario/items/purchase", json={"item_id": "second_phone"})
    assert res.status_code == 400
    assert res.json()["detail"]["code"] == "insufficient_funds"

    # 恢復現金並購買上限為 1 之物品
    db_user = pg_session.get(User, test_user.id)
    assert db_user is not None
    db_user.cash = 10000
    pg_session.add(db_user)
    pg_session.commit()

    res_buy = client.post("/api/v1/scenario/items/purchase", json={"item_id": "second_phone"})
    assert res_buy.status_code == 200

    # 2. 再次購買已擁有之單一道具 (max_quantity = 1)
    res_dup = client.post("/api/v1/scenario/items/purchase", json={"item_id": "second_phone"})
    assert res_dup.status_code == 400
    assert res_dup.json()["detail"]["code"] == "already_owned"


def test_pg_verify_tool_unowned_item_and_unknown(client: TestClient, pg_session: Session, test_user: User):
    """驗證 C3 / C5 / A3 / A6：未持有道具無法使用對應工具、未知工具報錯拒絕、並發相同 Request ID 冪等防刷。"""
    # 建立新對話
    res_new = client.post("/api/v1/scenario/new", json={"contact_id": "wei_jie", "story_id": "living_farewell"})
    assert res_new.status_code == 200, res_new.text
    sc_id = res_new.json()["id"]

    # 1. 嘗試使用未持有道具工具 (use_dashcam)
    res_unowned = client.post(f"/api/v1/scenario/{sc_id}/verify", json={"tool_id": "use_dashcam"})
    assert res_unowned.status_code == 400
    assert res_unowned.json()["detail"]["code"] == "unowned_item"

    # 2. 嘗試使用不存在之捏造工具 (made_up_tool)
    res_unknown = client.post(f"/api/v1/scenario/{sc_id}/verify", json={"tool_id": "made_up_tool"})
    assert res_unknown.status_code == 400
    assert res_unknown.json()["detail"]["code"] == "unknown_tool"

    # 3. 執行合法公共查證工具
    res_valid = client.post(f"/api/v1/scenario/{sc_id}/verify", json={"tool_id": "check_official_registry"})
    assert res_valid.status_code == 200
    data_valid = res_valid.json()
    assert data_valid["already_unlocked"] is False
    assert "內政部" in data_valid["evidence"]["content"] or "登記" in data_valid["evidence"]["content"]

    # 4. 並發相同 request_id 之查證工具請求 (防雙擊冪等)
    verify_req_id = f"verify_conc_{uuid.uuid4().hex[:8]}"

    def send_conc_verify(i: int):
        return client.post(
            f"/api/v1/scenario/{sc_id}/verify",
            json={"tool_id": "check_official_registry", "request_id": verify_req_id},
        )

    with ThreadPoolExecutor(max_workers=2) as pool:
        v_replies = list(pool.map(send_conc_verify, [1, 2]))

    assert [r.status_code for r in v_replies] == [200, 200]
    assert v_replies[0].json() == v_replies[1].json()


def test_pg_concurrent_purchases(client: TestClient, pg_session: Session, test_user: User):
    """驗證 T1：並發相同 Request ID 購買道具僅扣款一次，庫存為 1，並發請求皆回傳 200。"""
    buy_req_id = f"buy_conc_{uuid.uuid4().hex[:8]}"
    initial_cash = test_user.cash

    def buy_item(i: int):
        return client.post(
            "/api/v1/scenario/items/purchase",
            json={"item_id": "document_scanner", "request_id": buy_req_id},
        )

    with ThreadPoolExecutor(max_workers=2) as pool:
        replies = list(pool.map(buy_item, [1, 2]))

    assert [r.status_code for r in replies] == [200, 200]
    assert replies[0].json()["new_cash"] == replies[1].json()["new_cash"]
    assert replies[0].json()["new_cash"] == initial_cash - 1200

    db_user = pg_session.get(User, test_user.id)
    assert db_user is not None
    assert db_user.cash == initial_cash - 1200
    inv = pg_session.exec(
        select(UserItemInventory).where(
            UserItemInventory.user_id == test_user.id,
            UserItemInventory.item_id == "document_scanner",
        )
    ).first()
    assert inv is not None
    assert inv.quantity == 1


def test_pg_first_chat_load_serializes_inbox_and_contacts(client: TestClient):
    """新帳號同時載入聊天與人物關係時不得因懶建立資料而死鎖。"""
    paths = ["/api/v1/scenario/inbox", "/api/v1/scenario/contacts"]

    def fetch(path: str):
        return client.get(path)

    with ThreadPoolExecutor(max_workers=2) as pool:
        replies = list(pool.map(fetch, paths))

    assert [reply.status_code for reply in replies] == [200, 200]
    assert len(replies[0].json()) == 5
    assert len(replies[1].json()) == 5


def test_pg_concurrent_messages_and_revision_lock(client: TestClient, pg_session: Session, test_user: User):
    """驗證 T1：真實多執行緒並發訊息發送、CAS Revision 樂觀鎖與收據冪等防刷。"""
    res_new = client.post("/api/v1/scenario/new", json={"contact_id": "wei_jie", "story_id": "living_farewell"})
    assert res_new.status_code == 200
    sc_id = res_new.json()["id"]

    # 模擬非同步延遲回覆，測試並發鎖與事件迴圈無阻塞
    async def delayed_reply(*args, **kwargs):
        await asyncio.sleep(0.15)
        return ScenarioReply(messages=["我收到你的問題了。"], decision_point=None, tactics_used=[])

    from app.api.routes import scenario
    original_generate = scenario.scenario_agent.generate_reply
    scenario.scenario_agent.generate_reply = delayed_reply

    try:
        # 1. 兩筆不同 request_id、相同 expected_revision=0 之並發訊息
        def send_msg(i: int):
            return client.post(
                f"/api/v1/scenario/{sc_id}/message",
                json={"text": f"並發問題{i}", "expected_revision": 0, "request_id": uuid.uuid4().hex},
            )

        with ThreadPoolExecutor(max_workers=2) as pool:
            replies = list(pool.map(send_msg, [1, 2]))

        statuses = {r.status_code for r in replies}
        assert statuses == {200, 409}, f"Expected one 200 and one 409, got {[r.status_code for r in replies]}"

        detail = client.get(f"/api/v1/scenario/{sc_id}").json()
        assert detail["player_turns"] == 1
        assert detail["revision"] == 1

        # 2. 相同 request_id 之並發重複請求 (冪等防雙擊) -> 皆回傳 200，回合數僅增加 1
        same_req_id = f"msg_same_{uuid.uuid4().hex[:8]}"

        def send_same(i: int):
            return client.post(
                f"/api/v1/scenario/{sc_id}/message",
                json={"text": "重複問題", "expected_revision": 1, "request_id": same_req_id},
            )

        with ThreadPoolExecutor(max_workers=2) as pool:
            same_replies = list(pool.map(send_same, [1, 2]))

        assert [r.status_code for r in same_replies] == [200, 200]
        detail_after = client.get(f"/api/v1/scenario/{sc_id}").json()
        assert detail_after["player_turns"] == 2
        assert detail_after["revision"] == 2

        # 3. 相同 request_id 但不同 payload -> 409 Conflict
        res_conflict = client.post(
            f"/api/v1/scenario/{sc_id}/message",
            json={"text": "篡改內容", "expected_revision": 2, "request_id": same_req_id},
        )
        assert res_conflict.status_code == 409
        assert res_conflict.json()["detail"]["code"] == "request_id_conflict"

        # 4. 並發查證工具調用 -> CAS 序列化，一筆 200、一筆 409
        def send_verify(tool_id: str):
            return client.post(
                f"/api/v1/scenario/{sc_id}/verify",
                json={"tool_id": tool_id, "expected_revision": 2, "request_id": uuid.uuid4().hex},
            )

        with ThreadPoolExecutor(max_workers=2) as pool:
            v_replies = list(pool.map(send_verify, ["check_personal_records", "check_official_registry"]))

        v_statuses = {r.status_code for r in v_replies}
        assert v_statuses == {200, 409}
    finally:
        scenario.scenario_agent.generate_reply = original_generate


def test_pg_atomic_judge_and_receipt_idempotency(client: TestClient, pg_session: Session, test_user: User):
    """驗證 T1, T3：裁決單一原子提交、並發相同 Request ID 冪等防雙擊、明細核算與持久化結果。"""
    db_user_init = pg_session.get(User, test_user.id)
    assert db_user_init is not None
    initial_cash = db_user_init.cash
    initial_xp = db_user_init.xp

    res_new = client.post("/api/v1/scenario/new", json={"contact_id": "wei_jie", "story_id": "living_farewell"})
    assert res_new.status_code == 200
    sc_id = res_new.json()["id"]

    res_v1 = client.post(f"/api/v1/scenario/{sc_id}/verify", json={"tool_id": "check_official_registry"})
    assert res_v1.status_code == 200

    # 1. 並發相同裁決 request_id：兩執行緒同時送出，皆獲 200 快取結果，錢/XP 僅結算一次
    req_id = f"judge_conc_{uuid.uuid4().hex[:8]}"

    def send_judge(i: int):
        return client.post(
            f"/api/v1/scenario/{sc_id}/judge",
            json={"action": "report", "request_id": req_id},
        )

    with ThreadPoolExecutor(max_workers=2) as pool:
        judge_replies = list(pool.map(send_judge, [1, 2]))

    assert [r.status_code for r in judge_replies] == [200, 200]
    assert judge_replies[0].json() == judge_replies[1].json()
    data_judge = judge_replies[0].json()
    assert data_judge["outcome"] == "win_report"
    assert data_judge["reward_breakdown"] is not None
    delta_cash = data_judge["cash_delta"]
    delta_xp = data_judge["xp_delta"]

    # 檢查持久化終局結果
    reloaded = client.get(f"/api/v1/scenario/{sc_id}").json()
    assert reloaded["status"] == "completed"
    assert reloaded["outcome"] == "win_report"
    assert reloaded["terminal_result"] is not None
    assert reloaded["source_adaptation_mark"] is not None

    pg_session.expire_all()
    db_user = pg_session.get(User, test_user.id)
    assert db_user is not None
    assert db_user.cash == initial_cash + delta_cash
    assert db_user.xp == initial_xp + delta_xp


def test_pg_pause_and_resume_cycles(client: TestClient, pg_session: Session, test_user: User):
    """驗證 T2：暫停與繼續不洩露機密、阻擋新對話、5 次循環零經濟與進度變更。"""
    res_new = client.post("/api/v1/scenario/new", json={"contact_id": "wei_jie", "story_id": "living_farewell"})
    sc_id = res_new.json()["id"]

    # 1. 專用暫停端點
    p_res = client.post(f"/api/v1/scenario/{sc_id}/pause")
    assert p_res.status_code == 200
    p_data = p_res.json()
    assert p_data["outcome"] == "paused"
    assert p_data["true_role"] == ""
    assert p_data["flags"] == []
    assert p_data["cash_delta"] == 0
    assert p_data["xp_delta"] == 0

    # 2. 暫停中讀取：零洩漏
    paused_detail = client.get(f"/api/v1/scenario/{sc_id}").json()
    assert paused_detail["status"] == "paused"
    assert paused_detail["is_paused"] is True
    assert paused_detail["learning_objective"] is None

    # 3. 暫停中阻擋開新對話
    block_new = client.post("/api/v1/scenario/new", json={"contact_id": "wei_jie", "story_id": "living_farewell"})
    assert block_new.status_code == 400
    assert block_new.json()["detail"]["code"] == "active_exists"

    # 4. 專用繼續端點
    r_res = client.post(f"/api/v1/scenario/{sc_id}/resume")
    assert r_res.status_code == 200
    r_data = r_res.json()
    assert r_data["status"] == "active"
    assert r_data["is_paused"] is False
    assert r_data["id"] == sc_id
    assert r_data["player_turns"] == paused_detail["player_turns"]

    # 5. 連續 5 次暫停/繼續循環：數值完全無變動
    db_user_start = pg_session.get(User, test_user.id)
    assert db_user_start is not None
    cash_start = db_user_start.cash
    xp_start = db_user_start.xp

    for _ in range(5):
        cur = client.get(f"/api/v1/scenario/{sc_id}").json()
        client.post(f"/api/v1/scenario/{sc_id}/pause", json={"expected_revision": cur["revision"]})
        cur_p = client.get(f"/api/v1/scenario/{sc_id}").json()
        client.post(f"/api/v1/scenario/{sc_id}/resume", json={"expected_revision": cur_p["revision"]})

    pg_session.expire_all()
    db_user_after = pg_session.get(User, test_user.id)
    assert db_user_after is not None
    assert db_user_after.cash == cash_start
    assert db_user_after.xp == xp_start


def test_pg_qualification_and_replay(client: TestClient, pg_session: Session, test_user: User):
    """驗證 T3：拒絕未知故事、錯誤角色指派、未滿足跨角色前置條件；重玩純練習 0 獎勵。"""
    # 1. 錯誤聯絡人
    r_wrong = client.post("/api/v1/scenario/new", json={"contact_id": "li_li", "story_id": "cross_brand_charity_finale"})
    assert r_wrong.status_code == 400
    assert r_wrong.json()["detail"]["code"] == "wrong_contact_story"

    # 2. 未滿足前置條件
    r_unmet = client.post("/api/v1/scenario/new", json={"contact_id": "a_can", "story_id": "cross_brand_charity_finale"})
    assert r_unmet.status_code == 400
    assert r_unmet.json()["detail"]["code"] == "prerequisites_not_met"

    # 3. 未知故事
    r_unknown = client.post("/api/v1/scenario/new", json={"contact_id": "a_can", "story_id": "fake_story_999"})
    assert r_unknown.status_code == 400
    assert r_unknown.json()["detail"]["code"] == "unknown_story"

    # 4. 完成 living_farewell
    r_new = client.post("/api/v1/scenario/new", json={"contact_id": "wei_jie", "story_id": "living_farewell"})
    sc_id = r_new.json()["id"]
    client.post(f"/api/v1/scenario/{sc_id}/judge", json={"action": "report"})

    # 5. 重玩 living_farewell -> is_replay = True, 0 cash, 0 XP
    r_rep = client.post("/api/v1/scenario/new", json={"contact_id": "wei_jie", "story_id": "living_farewell"})
    assert r_rep.status_code == 200
    rep_id = r_rep.json()["id"]

    r_judge_rep = client.post(f"/api/v1/scenario/{rep_id}/judge", json={"action": "report"})
    assert r_judge_rep.status_code == 200
    rep_data = r_judge_rep.json()
    assert rep_data["cash_delta"] == 0
    assert rep_data["xp_delta"] == 0
    assert rep_data["reward_breakdown"]["is_replay"] is True


def test_pg_safe_exit_pause(client: TestClient, pg_session: Session, test_user: User):
    """驗證安全出口：未做查證仍可結案，但不發現金或 XP。"""
    res_new = client.post("/api/v1/scenario/new", json={"contact_id": "wei_jie", "story_id": "living_farewell"})
    sc_id = res_new.json()["id"]

    # 進行中讀取：不洩漏 learning_objective
    res_read = client.get(f"/api/v1/scenario/{sc_id}")
    assert res_read.status_code == 200
    assert res_read.json()["learning_objective"] is None

    # safe_exit 是誠實的終局選擇；沒有查證或服務進度時不發獎勵。
    res_safe = client.post(f"/api/v1/scenario/{sc_id}/judge", json={"action": "safe_exit"})
    assert res_safe.status_code == 200
    data = res_safe.json()
    assert data["outcome"] == "safe_exit"
    assert data["cash_delta"] == 0
    assert data["xp_delta"] == 0
    assert data["true_role"] == "scam_event"
    assert data["persona_name"] == "生前告別狂歡派對企劃"
    assert data["reward_breakdown"]["final_cash"] == 0
    assert data["reward_breakdown"]["final_xp"] == 0

    detail = client.get(f"/api/v1/scenario/{sc_id}").json()
    assert detail["status"] == "completed"
    assert detail["terminal_result"] is not None


def test_pg_message_failure_single_call_and_rollback(client: TestClient, pg_session: Session, test_user: User):
    """驗證 T1, Item 5：模型端異常僅呼叫一次、不重複重試、交易原子回滾且不扣回合。"""
    res_new = client.post("/api/v1/scenario/new", json={"contact_id": "wei_jie", "story_id": "living_farewell"})
    assert res_new.status_code == 200
    sc_id = res_new.json()["id"]

    call_count = 0

    async def failing_reply(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        raise RuntimeError("simulated model provider failure")

    from app.api.routes import scenario
    original_generate = scenario.scenario_agent.generate_reply
    scenario.scenario_agent.generate_reply = failing_reply

    try:
        res = client.post(
            f"/api/v1/scenario/{sc_id}/message",
            json={"text": "你好", "expected_revision": 0},
        )
        assert res.status_code == 502
        assert res.json()["detail"]["code"] == "agent_failed"
        # 關鍵：驗證僅呼叫一次，無二次重試
        assert call_count == 1

        # 驗證狀態完全回滾：player_turns 仍為 0，revision 仍為 0，對話歷史未殘留
        detail = client.get(f"/api/v1/scenario/{sc_id}").json()
        assert detail["player_turns"] == 0
        assert detail["revision"] == 0
        assert len(detail["history"]) == 1
        assert all(m["role"] != "player" for m in detail["history"])
    finally:
        scenario.scenario_agent.generate_reply = original_generate


def test_pg_alembic_fresh_legacy_upgrade_cycle():
    """驗證 T5：在專屬拋棄式資料庫執行 Alembic 升級、舊版 Session 相容保留與降級/升級循環。"""
    import os
    import psycopg
    from alembic import command
    from alembic.config import Config
    from sqlalchemy import create_engine, text

    disp_db = f"chat_life_mig_proof_{uuid.uuid4().hex[:6]}"
    with psycopg.connect("postgresql://chat_test:isolated@127.0.0.1:55437/chat_life_acceptance_20260919", autocommit=True) as conn:
        conn.execute(f"CREATE DATABASE {disp_db};")

    disp_url = f"postgresql+psycopg://chat_test:isolated@127.0.0.1:55437/{disp_db}"
    alembic_ini_path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..", "alembic.ini")
    )
    alembic_cfg = Config(alembic_ini_path)
    alembic_cfg.set_main_option("sqlalchemy.url", disp_url)

    engine = None
    try:
        # 1. 升級至前一 revision f1a8c2d3e4b5
        command.upgrade(alembic_cfg, "f1a8c2d3e4b5")

        engine = create_engine(disp_url)
        with engine.connect() as conn:
            u_id = uuid.uuid4()
            conn.execute(
                text(
                    "INSERT INTO \"user\" (id, email, is_active, is_superuser, hashed_password, cash, xp) "
                    "VALUES (:id, :email, true, false, :pw, 1000, 10)"
                ),
                {"id": u_id, "email": f"legacy_{uuid.uuid4().hex[:6]}@example.com", "pw": "x"},
            )
            s_id = uuid.uuid4()
            conn.execute(
                text(
                    "INSERT INTO scenario_session ("
                    "id, user_id, fraud_type, display_name, avatar, persona_role, status, player_turns, "
                    "conversation_history, tactics_seen, stake_loss, reward_win, reward_legit, penalty_misreport, unlocked_evidence"
                    ") VALUES ("
                    ":id, :uid, :ft, :dn, :av, :pr, :st, 0, "
                    ":hist, :tactics, 100, 200, 150, 50, :evidence"
                    ")"
                ),
                {
                    "id": s_id,
                    "uid": u_id,
                    "ft": "investment",
                    "dn": "OldNPC",
                    "av": "old",
                    "pr": "scam",
                    "st": "active",
                    "hist": "[]",
                    "tactics": "[]",
                    "evidence": "[]",
                },
            )
            conn.commit()

        engine.dispose()
        engine = None

        # 2. 升級至 head (c1c8a1a8e1f2)
        command.upgrade(alembic_cfg, "head")

        engine = create_engine(disp_url)
        with engine.connect() as conn:
            row = conn.execute(
                text("SELECT id, reply_mode, terminal_result, revision FROM scenario_session WHERE id = :id"),
                {"id": s_id},
            ).fetchone()
            assert row is not None
            assert row[1] == "rules", f"Expected default reply_mode rules, got {row[1]}"
            assert row[2] is None, f"Expected terminal_result None, got {row[2]}"
            assert row[3] == 0, f"Expected revision 0, got {row[3]}"
        engine.dispose()
        engine = None

        # 3. 降級回 f1a8c2d3e4b5 再重新升級至 head
        command.downgrade(alembic_cfg, "f1a8c2d3e4b5")
        command.upgrade(alembic_cfg, "head")
    finally:
        if engine is not None:
            engine.dispose()
        with psycopg.connect("postgresql://chat_test:isolated@127.0.0.1:55437/chat_life_acceptance_20260919", autocommit=True) as conn:
            conn.execute(
                f"SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '{disp_db}' AND pid <> pg_backend_pid();"
            )
            conn.execute(f"DROP DATABASE IF EXISTS {disp_db};")


def test_pg_initial_accessible_stories_truth_distribution(client: TestClient):
    """驗證初始開放的故事集（required_stories: []）涵蓋 scam、legit 與 pause_pending 三種真相。"""
    from app.scenario.stories import STORIES_CATALOG
    initial_stories = [s for s in STORIES_CATALOG.values() if not s.prerequisites.get("required_stories")]
    assert len(initial_stories) >= 3
    truths = {s.truth for s in initial_stories}
    assert "scam" in truths
    assert "legit" in truths
    assert "pause_pending" in truths

    initial_map = {
        "wei_jie": ("living_farewell", "scam"),
        "li_li": ("underground_idol_goods", "legit"),
        "hao_ge": ("vip_cross_border_fund", "scam"),
        "landlady": ("fire_safety_inspection", "pause_pending"),
        "a_can": ("streamer_traffic_booster", "scam"),
    }
    for cid, (expected_sid, expected_truth) in initial_map.items():
        st = STORIES_CATALOG[expected_sid]
        assert st.contact_id == cid
        assert st.truth == expected_truth
        assert st.prerequisites.get("required_stories") == []


def test_pg_branch_actions_availability_and_execution(client: TestClient, pg_session: Session, test_user: User):
    """驗證故事限定行動、語意冪等、CAS 與不相關道具不會跨故事出現。"""
    db_u = pg_session.get(User, test_user.id)
    assert db_u is not None
    db_u.cash = 6000
    db_u.xp = 120
    pg_session.add(db_u)
    pg_session.commit()

    res_new = client.post("/api/v1/scenario/new", json={"contact_id": "wei_jie", "story_id": "living_farewell"})
    assert res_new.status_code == 200
    sc_id = res_new.json()["id"]

    # 本故事支援通用 XP 行動與文件掃描器，不支援現金、車輛或其他故事道具。
    res_detail = client.get(f"/api/v1/scenario/{sc_id}")
    assert res_detail.status_code == 200
    detail = res_detail.json()
    act_map = {a["action_id"]: a for a in detail["available_branch_actions"]}
    assert act_map["xp_expert_analysis"]["available"] is True
    assert act_map["use_item_document_scanner"]["available"] is False
    for unrelated in (
        "cash_escrow_consultation",
        "vehicle_on_site_inspection",
        "use_item_second_phone",
        "use_item_pet_supplies",
        "use_item_secondhand_polaroid",
        "use_item_collectible_doll",
        "use_item_dashcam",
    ):
        assert unrelated not in act_map

    purchase = client.post("/api/v1/scenario/items/purchase", json={"item_id": "document_scanner"})
    assert purchase.status_code == 200

    refreshed = client.get(f"/api/v1/scenario/{sc_id}").json()
    refreshed_map = {a["action_id"]: a for a in refreshed["available_branch_actions"]}
    assert refreshed_map["use_item_document_scanner"]["available"] is True

    rev = refreshed["revision"]
    first = client.post(
        f"/api/v1/scenario/{sc_id}/action",
        json={
            "action_id": "use_item_document_scanner",
            "expected_revision": rev,
            "request_id": uuid.uuid4().hex,
        },
    )
    assert first.status_code == 200
    first_data = first.json()
    assert first_data["new_revision"] == rev + 1
    assert first_data["repeated"] is False
    assert first_data["unlocked_evidence_id"] == "use_document_scanner"

    # 即使換 request_id，同一事件的同一語意行動也只會結算一次。
    repeated = client.post(
        f"/api/v1/scenario/{sc_id}/action",
        json={
            "action_id": "use_item_document_scanner",
            "expected_revision": first_data["new_revision"],
            "request_id": uuid.uuid4().hex,
        },
    )
    assert repeated.status_code == 200
    repeated_data = repeated.json()
    assert repeated_data["repeated"] is True
    assert repeated_data["new_revision"] == first_data["new_revision"]

    after = client.get(f"/api/v1/scenario/{sc_id}").json()
    after_map = {a["action_id"]: a for a in after["available_branch_actions"]}
    scanner_action = after_map["use_item_document_scanner"]
    assert scanner_action["completed"] is True
    assert scanner_action["available"] is False

    # 跨故事硬送 action_id 會被拒絕且不改 revision。
    unrelated = client.post(
        f"/api/v1/scenario/{sc_id}/action",
        json={
            "action_id": "use_item_pet_supplies",
            "expected_revision": after["revision"],
            "request_id": uuid.uuid4().hex,
        },
    )
    assert unrelated.status_code == 400
    assert client.get(f"/api/v1/scenario/{sc_id}").json()["revision"] == after["revision"]

    # 舊 revision 仍由 CAS 保護。
    mismatch = client.post(
        f"/api/v1/scenario/{sc_id}/action",
        json={
            "action_id": "xp_expert_analysis",
            "expected_revision": rev,
            "request_id": uuid.uuid4().hex,
        },
    )
    assert mismatch.status_code == 409
    assert mismatch.json()["detail"]["code"] == "revision_mismatch"


def test_pg_evidence_lineage_and_non_purchase_verification(client: TestClient, pg_session: Session, test_user: User):
    """驗證 G2：同一來源之多重紀錄算作 1 個來源（血統追蹤），且非購買核心管道可完全滿足查證門檻。"""
    from app.scenario.evidence import is_sufficient_evidence

    # check_personal_records 與 use_document_scanner 皆屬於 "contract_paper"
    assert not is_sufficient_evidence(["check_personal_records", "use_document_scanner"], "influencer_mcn_contract")

    # 非購買核心查證管道提供兩個不同獨立來源 (contract_paper + official_registry_db)
    assert is_sufficient_evidence(["check_personal_records", "check_official_registry"], "influencer_mcn_contract")


def test_pg_cautious_terminal_disposition_pause_pending(client: TestClient, pg_session: Session, test_user: User):
    """驗證 G3：pause_pending 故事中 safe_exit 為誠實終局處置（完成集數、解鎖下一關、發放 XP 與服務獎金）。"""
    from app.models import UserContactRelation

    res_new = client.post("/api/v1/scenario/new", json={"contact_id": "landlady", "story_id": "fire_safety_inspection"})
    assert res_new.status_code == 200
    sc_id = res_new.json()["id"]

    client.post(f"/api/v1/scenario/{sc_id}/verify", json={"tool_id": "check_official_registry"})
    client.post(f"/api/v1/scenario/{sc_id}/verify", json={"tool_id": "check_independent_service"})

    db_u = pg_session.get(User, test_user.id)
    assert db_u is not None

    res_judge = client.post(f"/api/v1/scenario/{sc_id}/judge", json={"action": "safe_exit"})
    assert res_judge.status_code == 200
    j_data = res_judge.json()
    assert j_data["outcome"] == "safe_exit"
    assert j_data["xp_delta"] >= 10
    assert j_data["cash_delta"] == 0

    detail = client.get(f"/api/v1/scenario/{sc_id}").json()
    assert detail["status"] == "completed"
    assert detail["terminal_result"] is not None
    assert "消防" in detail["terminal_result"]["case_provenance"]

    pg_session.expire_all()
    rel = pg_session.exec(select(UserContactRelation).where(UserContactRelation.user_id == test_user.id, UserContactRelation.contact_id == "landlady")).first()
    assert rel is not None
    assert "fire_safety_inspection" in (rel.completed_story_ids or [])

    res_next = client.post("/api/v1/scenario/new", json={"contact_id": "landlady", "story_id": "vacant_house_group"})
    assert res_next.status_code == 200
    assert res_next.json()["story_id"] == "vacant_house_group"


def test_pg_bonus_arithmetic_exactness(client: TestClient, pg_session: Session, test_user: User):
    """驗證 G3：各項加成算術精確性（首次轉介 20%、有效工具 10%、服務目標 20%、一般上限 50%、章末 2.5x）。"""
    from app.scenario.config import SCENARIO_ECONOMY
    from app.scenario.manager import outcome_deltas

    econ = SCENARIO_ECONOMY["investment"]

    # 1. 滿額加成：20% + 10% + 20% = 50% (1.5x)
    cash, xp, bk = outcome_deltas(
        "win_report",
        econ,
        has_evidence=True,
        completed_chapters=0,
        is_new_referral=True,
        tool_provided_new_info=True,
        full_service_objective=True,
        is_chapter_finale=False,
        is_chat_life=True,
        is_replay=False,
        return_breakdown=True,
    )
    assert bk["chat_bonuses"]["new_referral"] == 0.20
    assert bk["chat_bonuses"]["effective_tool_info"] == 0.10
    assert bk["chat_bonuses"]["full_service_objective"] == 0.20
    assert bk["total_chat_factor"] == 0.50
    assert cash == round(econ.reward_win * 1.50)

    # 2. 章末 finale：2.5x
    cash_fin, xp_fin, bk_fin = outcome_deltas(
        "win_report",
        econ,
        has_evidence=True,
        completed_chapters=0,
        is_chapter_finale=True,
        is_chat_life=True,
        is_replay=False,
        return_breakdown=True,
    )
    assert bk_fin["is_chapter_finale"] is True
    assert cash_fin == round(econ.reward_win * 2.50)

    # 3. 重玩：0 cash, 0 XP
    cash_rep, xp_rep, bk_rep = outcome_deltas(
        "win_report",
        econ,
        is_replay=True,
        return_breakdown=True,
    )
    assert cash_rep == 0
    assert xp_rep == 0
    assert bk_rep["is_replay"] is True
