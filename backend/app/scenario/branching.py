"""人脈、處置記憶與五類狀態分支（C4 / A5）。

維護與管理每位聯絡人的好感牽絆記憶：
- trust: 0 ~ 100 (預設 50)
- reliability: 0 ~ 100 (預設 50)
- event_flags:
  * "respects_privacy" (尊重隱私)
  * "evidence_grounded" (依據充分)
  * "rash_accusation" (曾草率指責)
  * "kept_promise" (完成承諾)

五類狀態分支條件（遊戲中皆具備真實可達之分支）：
1. cash (金錢): 現金水準影響對話建議與替代處置
2. network (人脈/關係): trust 與 reliability 影響聯絡人配合度與開放深入話題
3. handling (處置記憶): 過往 flags 影響聯絡人對待查證建議的態度
4. property/vehicle (住宅/車輛): 擁有車房產觸發特定物業諮詢與載運取證
5. xp/item (經驗/物品): 擁有特定工具/信物解鎖特殊查證工具或即時破冰

數值僅在結案或明確處置行動時有界調整，嚴禁每句文字刷好感。
"""

from __future__ import annotations

from typing import Any


FLAG_RESPECTS_PRIVACY = "respects_privacy"
FLAG_EVIDENCE_GROUNDED = "evidence_grounded"
FLAG_RASH_ACCUSATION = "rash_accusation"
FLAG_KEPT_PROMISE = "kept_promise"

VALID_FLAGS = {
    FLAG_RESPECTS_PRIVACY,
    FLAG_EVIDENCE_GROUNDED,
    FLAG_RASH_ACCUSATION,
    FLAG_KEPT_PROMISE,
}


def clamp_metric(val: int) -> int:
    return max(0, min(100, val))


def update_contact_relation(
    current_trust: int,
    current_reliability: int,
    existing_flags: list[str],
    outcome: str,
    has_evidence: bool,
    action: str,
) -> tuple[int, int, list[str]]:
    """確定性更新聯絡人之信任、可靠度與事件標籤。"""
    trust = current_trust
    reliability = current_reliability
    flags = list(existing_flags)

    if outcome == "win_report":
        # 成功揭發詐騙
        if has_evidence:
            trust = clamp_metric(trust + 15)
            reliability = clamp_metric(reliability + 10)
            if FLAG_EVIDENCE_GROUNDED not in flags:
                flags.append(FLAG_EVIDENCE_GROUNDED)
            if FLAG_RASH_ACCUSATION in flags:
                flags.remove(FLAG_RASH_ACCUSATION)
        else:
            # 盲猜揭發
            trust = clamp_metric(trust + 5)
            reliability = clamp_metric(reliability - 5)
            if FLAG_RASH_ACCUSATION not in flags:
                flags.append(FLAG_RASH_ACCUSATION)

    elif outcome == "win_trust":
        # 正當案件確認合作
        trust = clamp_metric(trust + 15)
        reliability = clamp_metric(reliability + 15)
        if has_evidence and FLAG_EVIDENCE_GROUNDED not in flags:
            flags.append(FLAG_EVIDENCE_GROUNDED)

    elif outcome == "lose_misreport":
        # 誤指控正當對象
        trust = clamp_metric(trust - 25)
        reliability = clamp_metric(reliability - 20)
        if FLAG_RASH_ACCUSATION not in flags:
            flags.append(FLAG_RASH_ACCUSATION)

    elif outcome == "lose_scammed":
        # 輕信受害
        trust = clamp_metric(trust - 10)
        reliability = clamp_metric(reliability - 25)

    elif outcome == "safe_exit":
        # 穩健暫停查證
        trust = clamp_metric(trust + 8)
        reliability = clamp_metric(reliability + 12)
        if FLAG_KEPT_PROMISE not in flags:
            flags.append(FLAG_KEPT_PROMISE)
        if FLAG_RESPECTS_PRIVACY not in flags:
            flags.append(FLAG_RESPECTS_PRIVACY)

    return trust, reliability, flags


def evaluate_state_branches(
    cash: int,
    trust: int,
    reliability: int,
    flags: list[str],
    has_property: bool,
    has_vehicle: bool,
    owned_item_ids: list[str],
    story_id: str,
) -> dict[str, bool]:
    """評估玩家 5 類狀態在該事件中的分支可達性。"""
    active_branches = {}

    # 1. cash 分支
    active_branches["branch_high_cash"] = cash >= 5000
    active_branches["branch_low_cash_alternative"] = cash < 2000

    # 2. network 分支
    active_branches["branch_high_trust"] = trust >= 60
    active_branches["branch_cautious_partner"] = reliability >= 60

    # 3. handling 分支
    active_branches["branch_evidence_grounded"] = FLAG_EVIDENCE_GROUNDED in flags
    active_branches["branch_needs_redemption"] = FLAG_RASH_ACCUSATION in flags
    active_branches["branch_respects_privacy"] = FLAG_RESPECTS_PRIVACY in flags

    # 4. property / vehicle 分支
    active_branches["branch_property_owner"] = has_property
    active_branches["branch_vehicle_support"] = has_vehicle

    # 5. xp / item 分支
    active_branches["branch_has_second_phone"] = "second_phone" in owned_item_ids
    active_branches["branch_has_document_scanner"] = "document_scanner" in owned_item_ids
    active_branches["branch_has_polaroid"] = "secondhand_polaroid" in owned_item_ids
    active_branches["branch_has_pet_supplies"] = "pet_supplies" in owned_item_ids
    active_branches["branch_has_doll"] = "collectible_doll" in owned_item_ids
    active_branches["branch_has_plaque"] = "commemorative_plaque" in owned_item_ids

    return active_branches


BRANCH_ACTION_DESCRIPTIONS: dict[str, str] = {
    "branch_high_cash": "【資金優勢】可動用充足預算聘請第三方公證或履約保證",
    "branch_low_cash_alternative": "【預算受限】向對方主張免預付款或採小額分期測試",
    "branch_high_trust": "【高度信任】請求聯絡人提供完整對話紀錄與未公開原始通聯",
    "branch_cautious_partner": "【謹慎夥伴】要求與聯絡人共同列席向主管機關或對方對質",
    "branch_evidence_grounded": "【嚴謹記錄】引用過去已建立之官方查驗紀錄進行交叉比對",
    "branch_needs_redemption": "【修復關係】為先前的草率判斷致歉並以更高標準查驗",
    "branch_respects_privacy": "【尊重界線】在不侵犯個資前提下進行外圍公開資料核查",
    "branch_property_owner": "【不動產背景】調閱名下物業登記規約以比對大樓管理與地址真偽",
    "branch_vehicle_support": "【機動支援】駕車前往接洽方登記實體地址進行現勘確認",
    "branch_has_second_phone": "【隔離測試】使用備用手機在安全沙箱環境比對不明連結",
    "branch_has_document_scanner": "【文件比對】使用文件掃描器進行合約防偽浮水印與印鑑核對",
    "branch_has_polaroid": "【實體存證】使用拍立得拍攝現場合約與實體物件存證",
    "branch_has_pet_supplies": "【生活印證】出示同款寵物晶片登記與用品證明以核實背景",
    "branch_has_doll": "【工藝核實】比對限量手作玩偶之防偽刺繡與授權編號",
    "branch_has_plaque": "【社群信譽】出示社區感謝獎牌以建立良性對等對話",
}


from app.schemas import ScenarioBranchAction


# 每個行動只在有作者內容支撐的故事出現。資產與道具改變處理方法，
# 不會跨故事產生「一定未授權／一定是假文件」之類的結論。
ACTION_STORIES: dict[str, set[str]] = {
    "cash_escrow_consultation": {"art_auction_consignment", "influencer_mcn_contract"},
    "cash_low_budget_alternative": {"art_auction_consignment", "influencer_mcn_contract"},
    "network_deep_chat_inquiry": set(),  # 空集合代表所有故事皆可使用的關係行動
    "network_cautious_neutral_channel": set(),
    "handling_grounded_evidence_review": set(),
    "handling_remedy_rashness": set(),
    "property_building_rules_check": {"vacant_house_group", "subsidized_social_housing", "fire_safety_inspection"},
    "vehicle_on_site_inspection": {"industry_summit_exhibition"},
    "xp_expert_analysis": set(),
    "use_item_second_phone": {"art_auction_consignment", "vacant_house_group", "fire_safety_inspection"},
    "use_item_document_scanner": {"living_farewell", "cosplay_custom_import", "influencer_mcn_contract"},
    "use_item_secondhand_polaroid": {"lookalike_doll"},
    "use_item_pet_supplies": {"scheduled_goodnight", "co_parenting_cat"},
    "use_item_collectible_doll": {"lookalike_doll"},
    "use_item_dashcam": {"industry_summit_exhibition"},
}

ACTION_TOOL_IDS = {
    "use_item_second_phone": "use_second_phone",
    "use_item_document_scanner": "use_document_scanner",
    "use_item_secondhand_polaroid": "use_secondhand_polaroid",
    "use_item_pet_supplies": "use_pet_supplies",
    "use_item_collectible_doll": "use_collectible_doll",
    "use_item_dashcam": "use_dashcam",
}


def get_scenario_branch_actions(
    cash: int,
    trust: int,
    reliability: int,
    flags: list[str],
    has_property: bool,
    has_vehicle: bool,
    user_xp: int,
    owned_item_ids: list[str],
    story_id: str = "",
    completed_action_ids: list[str] | None = None,
) -> list[ScenarioBranchAction]:
    """產出 5 類狀態之型別化分支行動，每項包含可用性與具體原因（C4 / G2）。"""
    actions: list[ScenarioBranchAction] = []

    # 1. cash (金錢) - 充裕諮詢 vs 低預算替代方案對
    cash_high_avail = cash >= 5000
    actions.append(
        ScenarioBranchAction(
            action_id="cash_escrow_consultation",
            category="cash",
            label="聘請第三方公證諮詢",
            description="動用充裕資金委託專業公證人對交易條款出具法律審核意見（需花費現金 500 元）。",
            available=cash_high_avail,
            unavailable_reason=None if cash_high_avail else f"手頭現金需達 5,000 元以上（目前 ${cash:,} 元）。",
        )
    )

    cash_low_avail = cash < 2000
    actions.append(
        ScenarioBranchAction(
            action_id="cash_low_budget_alternative",
            category="cash",
            label="主張零預付與小額驗證",
            description="手頭預算吃緊，向對方明確主張絕不預付大額款項，改採零預付或小額逐次驗收。",
            available=cash_low_avail,
            unavailable_reason=None if cash_low_avail else f"手頭現金充足（${cash:,} 元），不適用低預算防禦主張。",
        )
    )

    # 2. network (人脈/關係) - 高度信任深度對話 vs 謹慎中立管道對
    net_high_avail = trust >= 60 or reliability >= 60
    actions.append(
        ScenarioBranchAction(
            action_id="network_deep_chat_inquiry",
            category="network",
            label="索取完整通聯與轉帳截圖",
            description="基於雙方深厚信任，請聯絡人提供對方原始對話群組通聯與收款帳號截圖進行溯源。",
            available=net_high_avail,
            unavailable_reason=None if net_high_avail else f"與聯絡人的信任或可靠度需達 60 以上（目前信任 {trust}、可靠 {reliability}）。",
        )
    )

    net_low_avail = trust < 50 or reliability < 50
    actions.append(
        ScenarioBranchAction(
            action_id="network_cautious_neutral_channel",
            category="network",
            label="建議尋求第三方公信管道",
            description="雙方關係尚在建立中，建議透過消保官、主管機關等公信中立管道查對事實，避免彼此猜忌。",
            available=net_low_avail,
            unavailable_reason=None if net_low_avail else f"雙方已有良好信任基礎（信任 {trust}、可靠 {reliability}），可直接深入對話。",
        )
    )

    # 3. handling (處置記憶) - 嚴格求證覆核 vs 草率指責修復對
    handling_ev_avail = FLAG_EVIDENCE_GROUNDED in flags
    actions.append(
        ScenarioBranchAction(
            action_id="handling_grounded_evidence_review",
            category="handling",
            label="援引過往查驗記錄交叉核對",
            description="依據過往事件建立之謹慎求證習慣（evidence_grounded），要求對方出示具公信力之存證與公文案號。",
            available=handling_ev_avail,
            unavailable_reason=None if handling_ev_avail else "尚未建立嚴謹查證（evidence_grounded）處置記憶。",
        )
    )

    handling_rash_avail = FLAG_RASH_ACCUSATION in flags
    actions.append(
        ScenarioBranchAction(
            action_id="handling_remedy_rashness",
            category="handling",
            label="真誠致歉並耐心梳理疑點",
            description="為過往的草率判斷（rash_accusation）向對方致意，平復情緒並建立良性客觀對話氛圍。",
            available=handling_rash_avail,
            unavailable_reason=None if handling_rash_avail else "過往紀錄良好，無草率指責紀錄（rash_accusation）需修復。",
        )
    )

    # 4. property / vehicle (住宅 / 車輛)
    prop_avail = has_property
    actions.append(
        ScenarioBranchAction(
            action_id="property_building_rules_check",
            category="property_vehicle",
            label="調閱名下物業規約比對",
            description="調閱名下已登記不動產之大樓管理規約與區分所有權人會議紀錄，比對對方催款或租約通知合法性。",
            available=prop_avail,
            unavailable_reason=None if prop_avail else "名下尚未購置登記任何不動產（需解鎖 UserProperty）。",
        )
    )

    veh_avail = has_vehicle
    actions.append(
        ScenarioBranchAction(
            action_id="vehicle_on_site_inspection",
            category="property_vehicle",
            label="駕車前往登記地址實地現勘",
            description="親自駕駛自用載具前往對方宣稱之實體公司營業所或現場，實地勘驗營業現況。",
            available=veh_avail,
            unavailable_reason=None if veh_avail else "名下尚未登記自用載具（需擁有 UserVehicle）。",
        )
    )

    # 5. xp / item (經驗 / 6種購買道具之可觀察效應)
    xp_avail = user_xp >= 100
    actions.append(
        ScenarioBranchAction(
            action_id="xp_expert_analysis",
            category="xp_item",
            label="資深防詐專家經驗拆解",
            description="運用豐富的防詐調查實戰經驗（XP ≥ 100），快速拆解對方的心理話術陷阱與合約漏洞。",
            available=xp_avail,
            unavailable_reason=None if xp_avail else f"玩家防詐經驗需達 100 XP 以上（目前 {user_xp} XP）。",
        )
    )

    # 道具 1: 第二支手機 (second_phone)
    p1_avail = "second_phone" in owned_item_ids
    actions.append(
        ScenarioBranchAction(
            action_id="use_item_second_phone",
            category="xp_item",
            label="使用第二支手機外線撥打",
            description="用另一支手機自行查找公開聯絡方式並撥號，避免沿用對方提供的號碼；裝置本身不會證明對方真偽。",
            available=p1_avail,
            unavailable_reason=None if p1_avail else "道具欄未持有「第二支手機」。",
        )
    )

    # 道具 2: 文件掃描器 (document_scanner)
    p2_avail = "document_scanner" in owned_item_ids
    actions.append(
        ScenarioBranchAction(
            action_id="use_item_document_scanner",
            category="xp_item",
            label="使用文件掃描器存查比對",
            description="把紙本文件清楚數位化，整理發文人、日期、金額與條款差異；掃描結果不能自行證明真偽。",
            available=p2_avail,
            unavailable_reason=None if p2_avail else "道具欄未持有「文件掃描器」。",
        )
    )

    # 道具 3: 二手拍立得 (secondhand_polaroid)
    p3_avail = "secondhand_polaroid" in owned_item_ids
    actions.append(
        ScenarioBranchAction(
            action_id="use_item_secondhand_polaroid",
            category="xp_item",
            label="使用拍立得現場存證",
            description="拍下現場物件與陳列狀態，保留自己的觀察紀錄，之後仍需向原作者或獨立來源求證。",
            available=p3_avail,
            unavailable_reason=None if p3_avail else "道具欄未持有「二手拍立得」。",
        )
    )

    # 道具 4: 高級寵物用品組 (pet_supplies)
    p4_avail = "pet_supplies" in owned_item_ids
    actions.append(
        ScenarioBranchAction(
            action_id="use_item_pet_supplies",
            category="xp_item",
            label="出示寵物用品深化鄰里牽絆",
            description="提供共照所需用品並留下交接與使用紀錄，完成一次具體照護服務。",
            available=p4_avail,
            unavailable_reason=None if p4_avail else "道具欄未持有「高級寵物用品組」。",
        )
    )

    # 道具 5: 限定收藏玩偶 (collectible_doll)
    p5_avail = "collectible_doll" in owned_item_ids
    actions.append(
        ScenarioBranchAction(
            action_id="use_item_collectible_doll",
            category="xp_item",
            label="出示限定玩偶引起圈內共鳴",
            description="用自己的收藏品比較製作細節與來源說明，列出可再向原作者查證的差異。",
            available=p5_avail,
            unavailable_reason=None if p5_avail else "道具欄未持有「限定收藏玩偶」。",
        )
    )

    # 道具 6: 雙鏡頭行車紀錄器 (dashcam)
    p6_avail = "dashcam" in owned_item_ids
    actions.append(
        ScenarioBranchAction(
            action_id="use_item_dashcam",
            category="xp_item",
            label="調閱行車紀錄器影音存證",
            description="在已安排實際載運時保存行程與交接時間線；影像只證明行程，不證明合作方可信。",
            available=p6_avail,
            unavailable_reason=None if p6_avail else "道具欄未持有「雙鏡頭行車紀錄器」。",
        )
    )

    completed = set(completed_action_ids or [])
    scoped: list[ScenarioBranchAction] = []
    for action in actions:
        allowed_stories = ACTION_STORIES.get(action.action_id)
        if allowed_stories is None or (allowed_stories and story_id not in allowed_stories):
            continue
        if action.action_id in completed:
            action.available = False
            action.completed = True
            action.unavailable_reason = "本事件已完成這項行動，結果已保存在對話紀錄。"
        scoped.append(action)
    return scoped


def execute_scenario_branch_action(
    action_id: str,
    cash: int,
    trust: int,
    reliability: int,
    flags: list[str],
    has_property: bool,
    has_vehicle: bool,
    user_xp: int,
    owned_item_ids: list[str],
    story_snapshot: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """執行具體型別化分支行動，回傳狀態變更與結果文字（C4 / G2）。"""
    actions = get_scenario_branch_actions(
        cash=cash,
        trust=trust,
        reliability=reliability,
        flags=flags,
        has_property=has_property,
        has_vehicle=has_vehicle,
        user_xp=user_xp,
        owned_item_ids=owned_item_ids,
        story_id=(story_snapshot or {}).get("story_id", ""),
    )
    act_map = {a.action_id: a for a in actions}
    if action_id not in act_map:
        raise ValueError(f"Unknown action_id: {action_id}")

    target = act_map[action_id]
    if not target.available:
        raise ValueError(target.unavailable_reason or "條件不符無法執行此行動")

    cash_cost = 0
    trust_delta = 0
    rel_delta = 0
    remove_flag: str | None = None
    add_flag: str | None = None
    unlocked_ev_id: str | None = None
    disclosed_facts: list[str] = []
    result_text = ""

    if action_id == "cash_escrow_consultation":
        cash_cost = 500
        rel_delta = 5
        trust_delta = 5
        result_text = "【第三方公證諮詢】律師公證人審閱該接洽條款後出具意見：建議嚴格落實履約專戶保管，未經主管機關核准之境外私人收款均不得逕行撥付。"
        disclosed_facts = ["已取得第三方公證審查意見書，確認款項必須專款專用"]

    elif action_id == "cash_low_budget_alternative":
        trust_delta = 5
        result_text = "【預算受限防禦】你向對方明確主張手頭預算吃緊，堅持不預付大額款項，改採零預付與小額逐次驗收。對方見你態度謹慎，收斂了原本咄咄逼人的催促話術。"
        disclosed_facts = ["已建立零預付防禦立場，化解對方急性催款話術"]

    elif action_id == "network_deep_chat_inquiry":
        trust_delta = 5
        result_text = "【完整通聯整理】聯絡人把接洽方的原始通話紀錄與帳號資訊交給你，雙方逐一對齊對方實際說過的話與留下的資料。"
        disclosed_facts = ["取得對方原始對話群組通聯與收款帳號截圖"]

    elif action_id == "network_cautious_neutral_channel":
        trust_delta = 8
        rel_delta = 5
        result_text = "【尋求中立管道】你建議暫緩私下爭論，共同委請消保專線與公信主管機關調閱客觀登記。聯絡人感受到你的真誠與理性，放下戒心。"
        disclosed_facts = ["達成共識透過公信中立管道查證"]

    elif action_id == "handling_grounded_evidence_review":
        rel_delta = 5
        result_text = "【嚴謹記錄覆核】你依照過往建立的查證程序，把對方提供的文件、案號與仍缺少的欄位逐項列出，留下可供後續比對的紀錄。"
        disclosed_facts = ["依過往查驗標準整理出已提供與尚缺少的資料欄位"]

    elif action_id == "handling_remedy_rashness":
        remove_flag = FLAG_RASH_ACCUSATION
        add_flag = FLAG_KEPT_PROMISE
        trust_delta = 15
        rel_delta = 10
        result_text = "【真誠溝通修復】你主動為先前的急躁判斷向對方致歉，重新以冷靜、客觀的態度梳理案情。雙方冰釋前嫌，重建良性合作關係。"
        disclosed_facts = ["真誠致歉並消除誤會，修復人脈牽絆"]

    elif action_id == "property_building_rules_check":
        rel_delta = 5
        result_text = "【物業經驗比對】你拿出自己保存的管理規約與會議紀錄格式，逐欄比對這次通知的發文人、決議日期、收款名義與聯絡窗口；這些欄位仍需向本案管理單位獨立確認。"
        disclosed_facts = ["整理出管理通知應逐項核對的發文、決議、收款與聯絡欄位"]

    elif action_id == "vehicle_on_site_inspection":
        rel_delta = 5
        result_text = "【載運與交接規劃】你安排以自用車載運參展樣品，先和主辦方確認卸貨時段、交接人與收件紀錄，避免樣品在未留存交接資料前離手。"
        disclosed_facts = ["確認樣品載運的卸貨時段、交接人與收件紀錄"]

    elif action_id == "xp_expert_analysis":
        rel_delta = 5
        result_text = "【經驗整理】你把目前已出現的身分、款項、文件與期限分開列出，標記尚未由獨立來源確認的欄位，方便下一步逐項求證。"
        disclosed_facts = ["完成身分、款項、文件與期限的待查核清單"]

    elif action_id in ACTION_TOOL_IDS:
        tool_id = ACTION_TOOL_IDS[action_id]
        tool_data = (story_snapshot or {}).get("tool_results", {}).get(tool_id)
        if tool_data:
            unlocked_ev_id = tool_id
            result_text = tool_data.get(
                "content", "完成本事件的輔助紀錄。"
            ).removeprefix("【遊戲模擬查證】")
            disclosed_facts = [tool_data.get("title", "完成本事件的輔助紀錄")]
        elif action_id == "use_item_pet_supplies":
            trust_delta = 5
            result_text = "【照護支援】你提供本次共照需要的用品，並把交接數量與使用方式寫進照護紀錄；這是服務進度，不是交易真假的證據。"
            disclosed_facts = ["完成一次有紀錄的照護用品交接"]
        elif action_id == "use_item_collectible_doll":
            result_text = "【實物比較】你用自己的收藏品比對縫線、標籤與來源說明，記下可再向原作者求證的差異；外觀比較本身不能證明真偽。"
            disclosed_facts = ["記錄收藏品可向原作者求證的製作差異"]
        elif action_id == "use_item_dashcam":
            result_text = "【交接時序】行車記錄器保留了前往展場與樣品交接的時間線，能補充行程紀錄，但不能單獨證明合作方身分。"
            disclosed_facts = ["保存樣品載運與交接的時間線"]
        else:
            result_text = "【輔助紀錄】道具已協助整理本案資訊；仍需使用本事件列出的獨立來源查證。"
            disclosed_facts = ["完成一項輔助紀錄"]

    return {
        "action_id": action_id,
        "label": target.label,
        "result_text": result_text,
        "cash_cost": cash_cost,
        "unlocked_evidence_id": unlocked_ev_id,
        "disclosed_facts": disclosed_facts,
        "trust_delta": trust_delta,
        "reliability_delta": rel_delta,
        "remove_flag": remove_flag,
        "add_flag": add_flag,
    }


def get_available_branch_actions(active_branches: dict[str, bool]) -> list[str]:
    """根據啟動的分支條件，產出具體可用的分支行動提示文字（相容舊介面）。"""
    return [
        BRANCH_ACTION_DESCRIPTIONS[key]
        for key, is_active in active_branches.items()
        if is_active and key in BRANCH_ACTION_DESCRIPTIONS
    ]


def generate_prior_callback_text(
    completed_story_ids: list[str],
    contact_name: str,
    trust: int,
    flags: list[str],
    last_outcome: str | None = None,
    prev_snapshot: dict[str, Any] | None = None,
    prev_terminal: dict[str, Any] | None = None,
) -> str:
    """後續 episode 引用已完成之前次結果，維持連續性（C4, R3, G1）。

    規則：
    1. 基於前次已完成 session 之儲存快照（title、truth、frozen amount、outcome）。
    2. 絕不捏造平行劇本或假真相（如將合法案件說成詐騙，或將詐騙說成合法顧問）。
    3. 絕不發明虛假損失金額（如未涉及款項或未損失時，絕不宣稱損失幾萬塊）。
    4. 若目錄定義在之後發生變更，一律以快照當時凍結之 title 與事實為準。
    5. 前次為盲猜（無客觀證據）時，絕不可宣稱「我們查核清楚」，改以中立/幸好停止配合說明。
    """
    if not completed_story_ids:
        return ""

    last_id = completed_story_ids[-1]
    title = None
    truth = None

    if prev_snapshot:
        title = prev_snapshot.get("title")
        truth = prev_snapshot.get("truth")

    if not title:
        from app.scenario.stories import STORIES_CATALOG

        story = STORIES_CATALOG.get(last_id)
        if story:
            title = story.title
            truth = story.truth
        else:
            title = "前次事件"

    title_display = f"「{title}」"

    has_evidence = True
    if prev_terminal is not None:
        ev_count = prev_terminal.get("unlocked_evidence_count", 0)
        has_evidence = ev_count > 0 or bool(
            prev_terminal.get("reward_breakdown", {}).get("has_evidence", True)
        )
    elif prev_snapshot is not None and "has_evidence" in prev_snapshot:
        has_evidence = bool(prev_snapshot["has_evidence"])

    # 1. 成功識破並舉報詐騙 (win_report)
    if last_outcome == "win_report":
        if has_evidence:
            return f"{contact_name}：『上次關於{title_display}，多虧有你提醒把關，我們及時調閱客觀證據查實並停止配合，沒有貿然交付款項。這次又有一件事想找你商量…』"
        else:
            return f"{contact_name}：『上次關於{title_display}，雖然我們當時手邊未掌握完整客觀證據，但幸好及時停止配合，才沒有蒙受損失。這次又有一件事想找你商量…』"

    # 2. 成功核實並推進正當合作 (win_trust)
    if last_outcome == "win_trust":
        if has_evidence:
            return f"{contact_name}：『上次關於{title_display}，我們依合規程序查核清楚後順利完成，真的很謝謝你的幫忙！今天又有新事情想請教你…』"
        else:
            return f"{contact_name}：『上次關於{title_display}，雖然當時我們沒有調閱到完整資料，但事後證明流程確實是正規合法的。真的很謝謝你！今天又有新事情想請教你…』"

    # 3. 謹慎暫緩或安全退出 (safe_exit, paused)
    if last_outcome in ("safe_exit", "paused"):
        return f"{contact_name}：『上次關於{title_display}，我們決定先踩煞車保留查證，這種謹慎的態度真的很重要。這次又有新狀況，你幫我看看好嗎？』"

    # 4. 倉促輕信或未經核實即配合 (lose_scammed)
    if last_outcome == "lose_scammed":
        if truth == "scam":
            return f"{contact_name}：『上次關於{title_display}，我們在查證不齊全的情況下輕信了對方，後來證明確實有問題…這次我們一定要先查核清楚再行動。』"
        else:
            return f"{contact_name}：『上次關於{title_display}，我們處置得太倉促了…這次我們一定要更謹慎地核對各項資訊。』"

    # 5. 草率誤判正當對象 (lose_misreport)
    if last_outcome == "lose_misreport":
        if truth == "legit":
            return f"{contact_name}：『上次關於{title_display}，我們在未充分查證前草率質疑了對方，事後釐清程序其實都是正規的…這次我們務必先依據客觀證據來評估。』"
        else:
            return f"{contact_name}：『上次關於{title_display}，我們在未看清完整資料前下了定論…這次我們先把各方紀錄看齊全。』"

    # 預設中立語句
    return f"{contact_name}：『上次關於{title_display}有你幫忙分析真的很可靠，這次又有一件需要你審核的事情…』"
