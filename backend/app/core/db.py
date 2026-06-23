from sqlmodel import Session, create_engine, select

from app import crud
from app.core.config import settings
from app.game.seed import seed_mascot_items, seed_pretest_questions
from app.models import PropertyTier, SwipeCard, User, UserCreate

engine = create_engine(str(settings.SQLALCHEMY_DATABASE_URI))

PROPERTY_TIERS_SEED = [
    (1, "雅房", "tier-1", 1000, 5, 1),
    (2, "套房", "tier-2", 5000, 35, 1),
    (3, "兩房公寓", "tier-3", 25000, 250, 2),
    (4, "三房公寓", "tier-4", 100000, 1200, 3),
    (5, "別墅", "tier-5", 300000, 4200, 5),
    (6, "豪宅", "tier-6", 1000000, 15000, 10),
]


def seed_property_tiers(session: Session) -> None:
    for id_, name, svg, price, income, unlock in PROPERTY_TIERS_SEED:
        if session.get(PropertyTier, id_):
            continue
        session.add(
            PropertyTier(
                id=id_,
                name=name,
                svg_key=svg,
                price=price,
                daily_income=income,
                unlock_level=unlock,
            )
        )
    session.commit()


# make sure all SQLModel models are imported (app.models) before initializing DB
# otherwise, SQLModel might fail to initialize relationships properly
# for more details: https://github.com/fastapi/full-stack-fastapi-template/issues/28

# ── 滑卡種子資料（格式：scenario, source_label, is_scam, fraud_type, weakness_tags, explanation, difficulty）
SWIPE_CARDS_SEED = [
    # ── 投資詐欺（6 張：4 詐騙 + 2 合法）──
    (
        "老師說這檔三天漲 30%，名額剩 3 個！先轉一筆資金到合作券商鎖額度，賺了隨時出金。",
        "投資群組 飆股VIP·林老師",
        True,
        "investment",
        ["authority", "greed", "time_pressure"],
        "保證高報酬、催促匯款到『合作券商』是典型投資詐騙；正規投資不會保證獲利或催你限時匯款。",
        1,
    ),
    (
        "群組裡每天都有人曬獲利截圖，大家都賺翻了！分析師說加入 VIP 就能跟單，月穩定 20%，我同事已經賺 50 萬了！",
        "LINE 群組·財富自由交流",
        True,
        "investment",
        ["social_proof", "greed", "trust_building"],
        "曬單截圖可輕易偽造，暗樁假扮群友製造賺錢假象；『月穩定 20%』不符合任何合規金融商品。",
        2,
    ),
    (
        "這是馬斯克親自推薦的 AI 投資平台，新聞報導過，先小額試試，出金給你看再決定要不要加大。",
        "廣告訊息·AI財富平台",
        True,
        "investment",
        ["authority", "trust_building", "greed"],
        "冒用名人代言 + 先讓小額出金建立信任，是引導大額投資後無法提領的詐騙標準手法。",
        2,
    ),
    (
        "限時 48 小時！金管會核准的海外 ETF，保本保息、年化 15%，超過限額就關閉申購，現在轉帳就能鎖定。",
        "電子郵件·國際資產管理",
        True,
        "investment",
        ["authority", "time_pressure", "greed"],
        "金管會核准的商品不會主動要求你『限時轉帳鎖額度』；保本保息承諾本身即違反金融法規。",
        1,
    ),
    (
        "您好，這是 XX 銀行理財專員，您預約的諮詢。這檔債券基金近 5 年約 4%，但有本金波動風險，您可帶 DM 回家考慮。",
        "XX 銀行·王專員",
        False,
        "investment",
        [],
        "主動揭露風險與費用、不催促、不要求私人轉帳——合規金融商品的正常銷售。",
        1,
    ),
    (
        "您好，我是富邦投信客服，請問您在官網申購的台灣 50 ETF 定期定額設定有問題需要確認，請登入官網帳號查詢，我不會向您索取密碼。",
        "富邦投信·客服中心",
        False,
        "investment",
        [],
        "引導走官方管道、明確聲明不索取密碼——正規金融機構的標準服務行為。",
        2,
    ),
    # ── 假愛情交友詐騙（5 張：3 詐騙 + 2 合法）──
    (
        "親愛的，我在杜拜工程出了點狀況，海關卡住一批設備，能先幫我墊 8 萬手續費嗎？回國一定還你。",
        "交友軟體·Michael",
        True,
        "romance",
        ["trust_building", "time_pressure"],
        "從不視訊、編造海外急難要錢，是假愛情交友詐騙的核心套路。",
        2,
    ),
    (
        "寶貝，我發現一個加密貨幣套利機會，我們一起投資，你先入金 10 萬，我這邊也會匹配，等解鎖期一過就能提領雙倍。",
        "交友軟體·外資分析師 David",
        True,
        "romance",
        ["trust_building", "greed", "authority"],
        "感情建立後帶入假投資（殺豬盤），先養感情、後導入假平台是此類詐騙的典型二階段手法。",
        3,
    ),
    (
        "我是聯合國維和部隊醫官，護照在辦，視訊設備壞了，但我媽媽緊急住院需要手術費，你是我唯一能求助的人。",
        "Facebook·Dr. James",
        True,
        "romance",
        ["authority", "trust_building", "time_pressure"],
        "虛構高社會地位身分 + 無法視訊藉口 + 緊急醫療費，是海外軍官/醫官詐騙的標準劇本。",
        2,
    ),
    (
        "哈囉！我看到你的照片覺得你很有趣，可以加個 LINE 嗎？如果方便的話，下週想約你喝咖啡，我住台北信義區。",
        "交友 App·小涵",
        False,
        "romance",
        [],
        "願意留在平台內聯絡、主動提議見面且地點具體——是真誠交友的正常行為，無索錢或拒絕視訊的紅旗。",
        1,
    ),
    (
        "我覺得我們聊得很開心，可以視訊嗎？我想讓你看看我的臉，也想多了解你一點。",
        "交友 App·Alan",
        False,
        "romance",
        [],
        "主動要求視訊是真誠交友的重要特徵；詐騙者通常以各種理由迴避視訊。",
        1,
    ),
    # ── 解除分期 ATM 詐騙（5 張：3 詐騙 + 2 合法）──
    (
        "您好，我是 momo 購物客服，您 6/20 的訂單被誤設成分期付款，請現在到 ATM 操作解除，別掛電話我線上帶您。",
        "momo 客服·陳小姐",
        True,
        "atm",
        ["authority", "time_pressure", "trust_building"],
        "真客服不會請你到 ATM『解除設定』（那是把錢轉出去）、不會要 OTP、不會不讓你掛電話。",
        2,
    ),
    (
        "您的帳戶被偵測到異常使用，需立即到 ATM 將存款轉至『安全帳戶』保護資金，今天下班前不處理帳戶將被凍結。",
        "電話·XX 銀行風控中心",
        True,
        "atm",
        ["authority", "time_pressure"],
        "銀行絕對不會要求你把錢轉到「安全帳戶」；凍結帳戶的威脅是製造恐慌讓你不假思索匯款。",
        1,
    ),
    (
        "配合警察局洗錢清查行動，您的帳戶涉及可疑，需在 ATM 操作配合辦案，全程保持通話不要告知家人。",
        "電話·警察局刑事組",
        True,
        "atm",
        ["authority", "time_pressure", "trust_building"],
        "公務員辦案不會用電話指示操作 ATM，要求不告知家人是孤立受害者的手段，此為政府機關假冒詐騙。",
        1,
    ),
    (
        "您的訂單已出貨，如需查詢請至 App『我的訂單』，有問題可於站內客服留言，我們不會請您操作 ATM 或提供卡號。",
        "電商·官方通知",
        False,
        "atm",
        [],
        "正常出貨通知，引導走官方 App、明確聲明不會要 ATM/卡號——非詐騙。",
        1,
    ),
    (
        "提醒您：台新銀行不會主動來電要求您操作 ATM 或轉帳，如接獲此類電話請立即掛斷並撥打 165 反詐騙專線。",
        "台新銀行·官方簡訊",
        False,
        "atm",
        [],
        "正規銀行主動發送防詐提醒、提供官方查詢管道——是銀行保護客戶的正常行為，非詐騙。",
        1,
    ),
    # ── 購物詐欺（4 張：3 詐騙 + 1 合法）──
    (
        "這件全新只賣市價三折，我私下出清，加我 LINE 直接匯款，不用走平台手續費比較快。",
        "社團賣家·小美",
        True,
        "shopping",
        ["greed", "trust_building"],
        "低於市價過多 + 要求離開平台私下匯款 = 收錢不出貨的高風險；走平台金流才有保障。",
        1,
    ),
    (
        "全新 iPhone 只要 8,000，急售！可貨到付款，幫你寄黑貓，先付 500 訂金確保你優先，其他人也在問。",
        "蝦皮私訊·賣家",
        True,
        "shopping",
        ["greed", "time_pressure", "trust_building"],
        "聲稱貨到付款但要求先付訂金相互矛盾；價格遠低市價 + 限時催付是購物詐騙的經典組合。",
        2,
    ),
    (
        "我是代購達人，幫你從日本帶 Switch 遊戲，先匯代購款 4,500 給我，我明天出發前確認名單，超過就排下次。",
        "Instagram·日本代購·莉莉",
        True,
        "shopping",
        ["greed", "time_pressure", "social_proof"],
        "代購先收款後消失是常見手法；無平台保障的個人匯款無法追回，代購應走有擔保的交易平台。",
        2,
    ),
    (
        "您好！感謝購買，商品已從倉庫出貨，預計 2-3 個工作天到貨，追蹤連結在蝦皮訂單頁，有問題請站內訊息我。",
        "蝦皮賣家·正品3C",
        False,
        "shopping",
        [],
        "透過平台站內系統通知、提供官方追蹤連結、引導站內溝通——正規賣家的標準出貨流程。",
        1,
    ),
    # ── 假網路拍賣（4 張：3 詐騙 + 1 合法）──
    (
        "您在本拍賣得標！請先支付『解鎖保證金』才能出貨，30 分鐘內未付款將取消資格並列入黑名單。",
        "拍賣平台客服·小陳",
        True,
        "fake-sale",
        ["time_pressure", "greed"],
        "真平台不會要『解鎖保證金』、不會用限時威脅，假得標通知誘導先付款是假拍賣詐騙。",
        2,
    ),
    (
        "您好，我是蝦皮官方客服，偵測到您帳戶異常，需要加我 LINE：shopee_service2024 處理，請勿在 App 操作以免影響調查。",
        "蝦皮站內訊息·蝦皮客服",
        True,
        "fake-sale",
        ["authority", "trust_building", "time_pressure"],
        "真蝦皮客服只在官方 App 內聯絡，要求加 LINE 是仿冒客服；帳號格式也與官方不符。",
        2,
    ),
    (
        "恭喜您的商品已售出！買家已付款，但您需先點擊以下連結確認賣家身分，收款才會入帳。",
        "Yahoo 拍賣·系統通知",
        True,
        "fake-sale",
        ["authority", "greed", "trust_building"],
        "正規平台不會要求賣家『點連結確認身分才能收款』；此為假買家誘導賣家點釣魚連結或先退款的詐騙。",
        3,
    ),
    (
        "提醒您：本平台客服只透過站內訊息聯繫，不會請您加 LINE 或外部帳號，也不會要求先付解鎖費，請小心詐騙。",
        "拍賣平台·官方提醒",
        False,
        "fake-sale",
        [],
        "主動防詐提醒、堅持站內交易——正規平台的正常行為，非詐騙。",
        1,
    ),
]


def seed_swipe_cards(session: Session) -> None:
    existing = session.exec(select(SwipeCard).limit(1)).first()
    if existing:
        return
    for scenario, source, is_scam, ftype, tags, expl, diff in SWIPE_CARDS_SEED:
        session.add(
            SwipeCard(
                scenario=scenario,
                source_label=source,
                is_scam=is_scam,
                fraud_type=ftype,
                weakness_tags=list(tags),
                explanation=expl,
                difficulty=diff,
            )
        )
    session.commit()


def init_db(session: Session) -> None:
    # Tables should be created with Alembic migrations
    # But if you don't want to use migrations, create
    # the tables un-commenting the next lines
    # from sqlmodel import SQLModel

    # This works because the models are already imported and registered from app.models
    # SQLModel.metadata.create_all(engine)

    user = session.exec(
        select(User).where(User.email == settings.FIRST_SUPERUSER)
    ).first()
    if not user:
        user_in = UserCreate(
            email=settings.FIRST_SUPERUSER,
            password=settings.FIRST_SUPERUSER_PASSWORD,
            is_superuser=True,
        )
        user = crud.create_user(session=session, user_create=user_in)

    seed_pretest_questions(session)
    seed_mascot_items(session)
    seed_property_tiers(session)
    seed_swipe_cards(session)
