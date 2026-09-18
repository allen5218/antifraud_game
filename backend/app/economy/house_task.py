"""首次購屋查證任務、家園裝飾與車輛資產事件（T4 / AC6, AC7, AC8）。

- 首次購屋必須先完成 2-3 個有意義查證動作的交易任務。
- 可疑交易被識破後算通過任務，可改走官方交易渠道完成購屋，不額外扣除購屋款。
- 後端伺服器權威驗證，不可被前端 flag 繞過。
- 已有房產玩家不需重做。
"""

from __future__ import annotations

from typing import Any

from sqlmodel import Session, col, select

from app.models import (
    User,
    UserHouseTask,
    UserProperty,
)

DECOR_CATALOG: list[dict[str, Any]] = [
    {
        "id": "cozy_rug",
        "name": "防詐溫馨地毯",
        "cost": 500,
        "description": "柔軟舒適的手工編織地毯，象徵踏實穩健的資產積累。",
        "icon": "🧶",
    },
    {
        "id": "security_cam",
        "name": "智能門禁監控",
        "cost": 1000,
        "description": "即時雲端警報與雙向語音，隨時把關家庭門禁安全。",
        "icon": "📹",
    },
    {
        "id": "panoramic_window",
        "name": "景觀落地全景窗",
        "cost": 2000,
        "description": "採光通透明亮的景觀落地窗，展望豐收富足的未來生活。",
        "icon": "🪟",
    },
]

TASK_STEPS: dict[str, dict[str, dict[str, str]]] = {
    "suspicious": {
        "step_title": {
            "name": "查對地政機關建物謄本",
            "description": "透過內政部地政資訊網線上調閱建物謄本，核對產權歸屬。",
            "evidence": "謄本顯示所有權人為陳林女士，且查無任何授權該名自稱代理人之合法公證委任書。",
        },
        "step_escrow": {
            "name": "堅持要求銀行履約保證專戶",
            "description": "要求買賣價金匯入指定建經公司信託專戶，拒絕私下匯款。",
            "evidence": "對方強烈抗拒履約保證，藉口手續繁瑣且需負擔額外信託費，堅持匯入其私人戶頭。",
        },
        "step_inspection": {
            "name": "要求現場看房與核驗仲介執照",
            "description": "約定現況點交看屋，並請營業員出示經紀人證照。",
            "evidence": "對方以鑰匙不在或臨時出差為由一再推拖，反向催促先轉一成保留金否則轉賣他人。",
        },
    },
    "legit": {
        "step_title": {
            "name": "核對地政建物謄本與身分證明",
            "description": "比對建物標示部與所有權人身分資料，確認無查封或二胎借貸爭議。",
            "evidence": "地政系統紀錄完整，房屋產權單一清晰，現況與謄本記載完全一致。",
        },
        "step_escrow": {
            "name": "確認銀行履約保證專戶受款戶名",
            "description": "向承辦銀行確認履約保證信託專戶帳號真實性。",
            "evidence": "銀行專員確認受款帳戶為合法建經公司不動產價金信託專戶，資金受第三方保障。",
        },
        "step_inspection": {
            "name": "現場查對屋況現況說明書",
            "description": "現場逐項檢視水電、瓦斯、鋼筋外露與滲漏水保固條款。",
            "evidence": "仲介人員親自陪同看屋，逐項簽署現況說明書並附提供漏水保固承諾。",
        },
    },
}


def get_or_create_house_task(
    session: Session, user_id: Any, tier_id: int = 1
) -> UserHouseTask:
    task = session.exec(
        select(UserHouseTask).where(
            UserHouseTask.user_id == user_id,
            UserHouseTask.tier_id == tier_id,
        )
    ).first()
    if not task:
        task = UserHouseTask(
            user_id=user_id,
            tier_id=tier_id,
            variant="suspicious",
            completed_steps=[],
            is_passed=False,
        )
        session.add(task)
        session.commit()
        session.refresh(task)
    return task


def user_owns_any_property(session: Session, user_id: Any) -> bool:
    """檢查玩家是否已持有任何房產（舊玩家不需重做任務）。"""
    stmt = select(UserProperty).where(
        col(UserProperty.user_id) == user_id,
        col(UserProperty.sold_at).is_(None),
    )
    return len(list(session.exec(stmt).all())) > 0


def is_eligible_to_buy_house(session: Session, user: User) -> bool:
    """判斷玩家是否有資格購屋（舊有房主免試，新玩家需通過查證任務）。"""
    if user.first_home_task_completed or user_owns_any_property(session, user.id):
        return True
    task = session.exec(
        select(UserHouseTask).where(
            col(UserHouseTask.user_id) == user.id,
            col(UserHouseTask.is_passed).is_(True),
        )
    ).first()
    return task is not None


HOUSE_TASK_SCENARIO = (
    "你在售屋平台上相中一間條件優渥的溫馨套房，開價明顯低於市場行情。"
    "自稱受屋主全權委託的代理人要求你先匯款付定，否則將轉讓給其他買家。"
    "在正式簽約前，請依序執行產權、金流與屋況現場查證，防範假房東與二房東捲款詐騙。"
)

HOME_EVENT_INFO = {
    "event_id": "home_repair_check",
    "title": "裝修追加工程款與修繕查證",
    "scenario": "剛入住新家，自稱社區合作的裝修工班主動敲門，稱檢測到全棟外牆滲水，需立即支付 8,000 元材料定金安排施工，否則損害自負。",
    "verification_step": "前往社區管委會與管理中心查證有無該項公共工程招標與配合廠商公告。",
    "evidence": "管理中心公告表示目前並未委託任何外部工班逐戶收費，此為常見假冒工程詐騙，管委會已報警備案。",
}

VEHICLE_EVENT_INFO = {
    "event_id": "vehicle_lien_check",
    "title": "中古車定金與監理產權查證",
    "scenario": "你在二手車網上看中一台自售中古代步車，賣家聲稱出國急售，要求先匯 5,000 元保留看車順位。",
    "verification_step": "利用公路總局監理服務網查詢車籍異常、里程紀錄與有無動產擔保設定。",
    "evidence": "監理系統顯示該車牌目前處於動產抵押扣押狀態，且賣家出示之行照已被監理所通報註銷。",
}
