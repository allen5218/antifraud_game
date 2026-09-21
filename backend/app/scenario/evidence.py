"""情境探索查證工具與固定客觀事實庫（T2 / AC2, AC3）。

提供獨立且客觀的查證事實：
- 查看自己的紀錄（訂單、網銀、通聯）
- 主管機關與公開登記名冊（商工、證期局、地政、醫事）
- 獨立官方客服與 165 反詐諮詢管道
"""

from __future__ import annotations

from typing import Any

from app.schemas import ScenarioEvidenceItem, ScenarioToolItem

AVAILABLE_TOOLS: list[ScenarioToolItem] = [
    ScenarioToolItem(
        tool_id="check_personal_records",
        name="查看個人內部紀錄",
        description="登入自己掌握之官方 App、網銀帳戶或對話通聯紀錄，查對原始事實。",
    ),
    ScenarioToolItem(
        tool_id="check_official_registry",
        name="查詢獨立主管機關名冊",
        description="透過金管會、數位部、地政網或衛福部等法定公開系統查核登記資質。",
    ),
    ScenarioToolItem(
        tool_id="check_independent_service",
        name="獨立客服與 165 專線求證",
        description="自行手動撥打金融卡背面客服或 165 防詐專線，不使用對方提供的聯絡電話。",
    ),
]

# 依 (fraud_type, persona_role, tool_id) 映射客觀事實
FACTS_MAP: dict[tuple[str, str, str], dict[str, str]] = {
    # ── 假網路拍賣 (fake-sale) ──
    ("fake-sale", "scam", "check_personal_records"): {
        "title": "拍賣賣家後台訂單檢查",
        "content": "登入拍賣平台賣家後台：訂單清單並無該筆商品之交易成功紀錄，後台系統亦無任何款項被凍結或需簽署協定之警示通知。",
    },
    ("fake-sale", "scam", "check_official_registry"): {
        "title": "買家傳送之客服網址查驗",
        "content": "透過 TWNIC 域名查詢系統檢視買家傳來之連結：該網址為境外個人於三日前註冊之釣魚仿冒網頁，非拍賣平台官方伺服器。",
    },
    ("fake-sale", "scam", "check_independent_service"): {
        "title": "平台官方客服與 165 諮詢",
        "content": "向官方客服求證：客服說明平台絕無『未簽署協定需加 LINE 認證』之規定，所有款項異動均由站內官方通知，此為假買家假客服詐騙。",
    },
    ("fake-sale", "legit", "check_personal_records"): {
        "title": "拍賣賣家後台訂單檢查",
        "content": "登入拍賣平台後台：確認買家已透過平台官方付款機制結帳，系統顯示『已付款待出貨』，價金由平台第三方履約專戶保管中。",
    },
    ("fake-sale", "legit", "check_official_registry"): {
        "title": "買家帳號信用與身分認證",
        "content": "檢視買家平台檔案：帳號已通過雙重手機與實名驗證，註冊時間超過三年，擁有數十筆五星正面交易評價。",
    },
    ("fake-sale", "legit", "check_independent_service"): {
        "title": "平台官方客服諮詢",
        "content": "平台站內系統說明：只要維持在官方物流與金流系統內寄送交割，交易全程享有平台買賣雙方保障機制。",
    },
    # ── 解除分期付款（ATM） (atm) ──
    ("atm", "scam", "check_personal_records"): {
        "title": "購物網站會員與付款明細",
        "content": "自行開啟購物網站官方 App 查看歷史訂單：該筆商品已於上週完成配送並以信用卡一次付清，帳戶設定中並無任何分期扣款方案。",
    },
    ("atm", "scam", "check_official_registry"): {
        "title": "來電號碼與電信特碼查核",
        "content": "檢視手機來電紀錄：號碼開頭帶有『+886』境外轉接字樣。警政署公告提醒：政府機關與合規業者絕不會以『+886』開頭號碼主動聯繫。",
    },
    ("atm", "scam", "check_independent_service"): {
        "title": "重撥卡背客服與 165 專線",
        "content": "依提款卡背面電話重撥銀行：行員確認帳戶一切正常，嚴正提醒 ATM 只有提款與轉出功能，絕無任何解除分期設定之操作模式。",
    },
    ("atm", "legit", "check_personal_records"): {
        "title": "信用卡即時消費紀錄對帳",
        "content": "開啟網路銀行 App 查閱未出帳明細：確實存在一筆爭議扣款授權紀錄，金額與來電專員所提及者相符。",
    },
    ("atm", "legit", "check_official_registry"): {
        "title": "銀行官方聯絡管道比對",
        "content": "比對通話號碼與銀行官網公開客服專線：兩者號碼完全一致，通話中專員主動提示可隨時掛斷並重撥確認身分。",
    },
    ("atm", "legit", "check_independent_service"): {
        "title": "銀行臨櫃或官方重撥確認",
        "content": "親自撥打信用卡背面客服專線：系統確認有此爭議款項調查通報，專員寄出書面爭議款切結書，未要求任何機台操作。",
    },
    # ── 假投資詐欺 (investment) ──
    ("investment", "scam", "check_personal_records"): {
        "title": "通訊群組與出金要求紀錄",
        "content": "查閱群組對話與轉帳紀錄：所謂『出金審核』已連續兩次要求額外繳納保證金，且受款帳戶均為不同的個人人頭戶頭。",
    },
    ("investment", "scam", "check_official_registry"): {
        "title": "金管會證券期貨局名冊查詢",
        "content": "至金管會證期局『合法投資顧問業者名冊』系統查詢：查無該老師或所謂『海外機構』之特許登記執照與核准營業字號。",
    },
    ("investment", "scam", "check_independent_service"): {
        "title": "165 反詐騙專線通報資料庫",
        "content": "致電 165 專線諮詢：專員表示本週已接獲多起該投資 App 之受害通報，該平台以虛擬帳面獲利誘使投資人不斷匯款補繳稅費後拒絕出金。",
    },
    ("investment", "legit", "check_personal_records"): {
        "title": "銀行同名交割帳戶扣款紀錄",
        "content": "登入個人銀行帳戶確認：每月定期定額資金均自個人名下薪轉戶自動扣繳，無任何私人或不明第三方帳號經手。",
    },
    ("investment", "legit", "check_official_registry"): {
        "title": "金融監督管理委員會登記查驗",
        "content": "於主管機關網站核對：該銀行理財專員證照齊全，所推薦之基金具有金管會核准銷售字號，公開說明書依法主動揭露各項市場風險。",
    },
    ("investment", "legit", "check_independent_service"): {
        "title": "銀行總行客服與分行確認",
        "content": "撥打銀行總行官方專線：客服確認該商品為總行合規架上產品，專員全程在分行營業場所服務，無違規私下代操情事。",
    },
    # ── 一般購物詐欺 (shopping) ──
    ("shopping", "scam", "check_personal_records"): {
        "title": "通聯紀錄與要求脫離平台",
        "content": "檢視買賣對話歷史：賣家以『節省手續費、當日快速出貨』為藉口，強烈要求脫離具備保障的拍賣平台改用 LINE 私下匯款。",
    },
    ("shopping", "scam", "check_official_registry"): {
        "title": "賣場公司商工登記與統一編號",
        "content": "查詢經濟部商業司商工登記公示資料：該一頁式購物網站未標註任何營業人名稱、統編或實體地址，查無任何合法登記資料。",
    },
    ("shopping", "scam", "check_independent_service"): {
        "title": "消基會與 165 高風險賣場通報",
        "content": "向 165 反詐資料庫查詢：該賣家個人帳號與提供之匯款帳號已有其他買家通報『付款後賣家封鎖失聯』之警示通報。",
    },
    ("shopping", "legit", "check_personal_records"): {
        "title": "官方平台訂單編號與發票紀錄",
        "content": "檢視商城官方購物明細：系統開立財政部電子發票，載明完整營業人統編與訂單編號，物流配送碼可即時追蹤貨態。",
    },
    ("shopping", "legit", "check_official_registry"): {
        "title": "經濟部商業司商工登記核驗",
        "content": "商工登記資料庫核對：電商業者依法登記在案，資本額與營業項目齊全，官網公開載明消保法七日猶豫期與退換貨地址。",
    },
    ("shopping", "legit", "check_independent_service"): {
        "title": "品牌官方授權專線確認",
        "content": "向原廠授權客服求證：原廠確認該商城為其官方認證之線上授權經銷通路，售出商品享有原廠正品保固。",
    },
    # ── 假愛情交友 (romance) ──
    ("romance", "scam", "check_personal_records"): {
        "title": "交往互動與通聯視訊紀錄",
        "content": "檢視雙方通聯紀錄：交往三個月期間，每逢提議面對面見面或即時視訊，對方均以訊號受阻、基地管制或涉密為由迴避，從未露面。",
    },
    ("romance", "scam", "check_official_registry"): {
        "title": "海關稅費繳納法令規章查核",
        "content": "查詢財政部關務署官方作業手冊：所有進口包裹之關稅與規費一律由海關掣發正式稅單由納稅義務人繳入國庫，絕無要求匯入個人帳號之規定。",
    },
    ("romance", "scam", "check_independent_service"): {
        "title": "外交部領務局與 165 專線求證",
        "content": "致電 165 諮詢：專員指出『外籍軍醫／工程師寄送貴重行李卡在海關需墊稅』為跨國交友詐騙的高頻手法，對方出示之證件照片多為盜圖變造。",
    },
    ("romance", "legit", "check_personal_records"): {
        "title": "日常生活互動與共同社交圈",
        "content": "檢視日常交往紀錄：雙方經常於公開場合見面用餐，互動自然透明，彼此均認識對方的同事或朋友，無任何金錢借貸或投資邀約。",
    },
    ("romance", "legit", "check_official_registry"): {
        "title": "專門職業及技術人員執業登記",
        "content": "至衛福部醫事查詢系統核驗：確認對方確實登記於本市醫療機構服務，執業科別與工作地點與其陳述完全吻合。",
    },
    ("romance", "legit", "check_independent_service"): {
        "title": "共同熟人與社交圈交叉確認",
        "content": "向當初介紹認識之大學同學求證：同學確認對方為真實認識多年的正當朋友，作風穩健誠懇，背景單純。",
    },
}


# 道具擴充查證工具定義（對應 6 件具備實際調查/支線觸發功能之道具，R3 / R4）
ITEM_TOOLS: dict[str, ScenarioToolItem] = {
    "second_phone": ScenarioToolItem(
        tool_id="use_second_phone",
        name="使用第二支手機撥號查證",
        description="透過獨立線路直接外撥官方公開登記號碼核實，避免對方轉駁線路。",
    ),
    "document_scanner": ScenarioToolItem(
        tool_id="use_document_scanner",
        name="使用文件掃描器光學比對",
        description="高精細光學掃描合約與公文紙本，留存數位影像以供對比條款與字樣特徵。",
    ),
    "secondhand_polaroid": ScenarioToolItem(
        tool_id="use_secondhand_polaroid",
        name="使用二手拍立得現場取證",
        description="現場即時顯影拍攝作品微距細節，留存具備時間標記之實體相片存證。",
    ),
    "pet_supplies": ScenarioToolItem(
        tool_id="use_pet_supplies",
        name="出示高級寵物用品",
        description="為共養街貓提供用品並參與現場照護，建立鄰里信任並核實共照實況。",
    ),
    "collectible_doll": ScenarioToolItem(
        tool_id="use_collectible_doll",
        name="出示限定收藏玩偶",
        description="出示同好手作玩偶交流並建立共鳴，降低防禦心態獲取詳細創作脈絡。",
    ),
    "dashcam": ScenarioToolItem(
        tool_id="use_dashcam",
        name="調閱行車紀錄器影音",
        description="調閱車輛出勤與現場會勘動線影音，留存交通與會勘佐證紀錄。",
    ),
}


def get_available_tools(
    owned_item_ids: list[str] | None = None,
    story_snapshot: dict | None = None,
) -> list[ScenarioToolItem]:
    """回傳基礎查證工具與玩家道具解鎖之專用工具（過濾適用於本事件者）。"""
    tools = list(AVAILABLE_TOOLS)
    owned_set = set(owned_item_ids or [])
    story_tools = (
        set(story_snapshot.get("tool_results", {}).keys())
        if story_snapshot and "tool_results" in story_snapshot
        else None
    )

    for item_id, tool_item in ITEM_TOOLS.items():
        if item_id in owned_set:
            if story_tools is not None and tool_item.tool_id not in story_tools:
                continue
            if tool_item not in tools:
                tools.append(tool_item)
    return tools


def get_evidence_for_scenario(
    fraud_type: str,
    persona_role: str,
    tool_id: str,
    story_snapshot: dict | None = None,
) -> ScenarioEvidenceItem:
    """依情境狀態確定性產出客觀事實證據（優先自固定事實 snapshot 讀取；拒絕未知工具）。"""
    if story_snapshot and "tool_results" in story_snapshot:
        tool_results = story_snapshot.get("tool_results", {})
        if tool_id not in tool_results:
            raise ValueError(f"Tool '{tool_id}' is not available for this scenario.")
        tool_dict = tool_results[tool_id]
        content = tool_dict.get("content", "").removeprefix("【遊戲模擬查證】")
        return ScenarioEvidenceItem(
            tool_id=tool_id,
            title=tool_dict.get("title", "查證結果"),
            content=content,
        )

    # 舊版 Session 相容兜底
    key = (fraud_type, persona_role, tool_id)
    fact = FACTS_MAP.get(key)
    if not fact:
        raise ValueError(f"Tool '{tool_id}' is unknown or unavailable.")
    content = fact["content"].removeprefix("【遊戲模擬查證】")
    return ScenarioEvidenceItem(
        tool_id=tool_id,
        title=fact["title"],
        content=content,
    )


def get_unlocked_evidence_items(
    fraud_type: str,
    persona_role: str,
    unlocked_tool_ids: list[str],
    story_snapshot: dict | None = None,
) -> list[ScenarioEvidenceItem]:
    res: list[ScenarioEvidenceItem] = []
    for tid in unlocked_tool_ids:
        try:
            res.append(get_evidence_for_scenario(fraud_type, persona_role, tid, story_snapshot))
        except ValueError:
            pass
    return res


def is_sufficient_evidence(
    unlocked_tool_ids: list[str],
    story_id_or_snapshot: str | dict | None = None,
) -> bool:
    """驗證查證是否達到充分標準（C3, R4）。

    原則：
    1. 依必要證據與來源獨立性判斷，不只單純看數量。
    2. 同一轉接鏈或對同一文件的兩次檢驗不算獨立來源（例如 personal_records 與 document_scanner 均為 contract_paper）。
    3. 紀念性/展示性物品無獨立查證來源，不可充當證據。
    4. 至少涵蓋 2 個獨立客觀來源。
    """
    if not unlocked_tool_ids:
        return False

    from app.scenario.stories import STORIES_CATALOG

    tool_results: dict[str, Any] | None = None
    if isinstance(story_id_or_snapshot, dict):
        tool_results = story_id_or_snapshot.get("tool_results")
    elif isinstance(story_id_or_snapshot, str) and story_id_or_snapshot in STORIES_CATALOG:
        tool_results = STORIES_CATALOG[story_id_or_snapshot].tool_results

    if tool_results:
        distinct_sources: set[str] = set()
        for tid in unlocked_tool_ids:
            t_data = tool_results.get(tid)
            if not t_data:
                continue
            # 只有明確標註 is_independent 且具備有效 source_id 的工具才算作獨立來源
            if t_data.get("is_independent") and t_data.get("source_id"):
                distinct_sources.add(t_data["source_id"])
        return len(distinct_sources) >= 2

    # 舊版 Session 相容兜底
    distinct_sources = set()
    for tid in unlocked_tool_ids:
        if tid == "check_personal_records":
            distinct_sources.add("internal_records")
        elif tid == "check_official_registry":
            distinct_sources.add("official_registry")
        elif tid in ("check_independent_service", "use_second_phone"):
            distinct_sources.add("independent_hotline")
        elif tid in ("use_document_scanner", "use_secondhand_polaroid"):
            distinct_sources.add("forensic_record")

    return len(distinct_sources) >= 2
