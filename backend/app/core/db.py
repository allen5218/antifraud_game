from typing import Any

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

# ── 滑卡題庫 ──
# 每類 6 張:詐騙 3 張、正常 3 張。發牌依玩家的練習重點加權抽(routes/quick.py)。
#
# 出題規則(改卡前先讀):
# - 正常的訊息要像**真的日常訊息**(出貨通知、預約提醒、朋友聊天),
#   不能寫成防詐提醒 —— 舊版的正常卡幾乎都是「本平台不會要你加 LINE」,
#   看到「不會要你…」就知道是正常的,等於洩題。
# - 來源標籤只寫管道和名字,不能帶「飆股VIP」這種一看就知道是詐騙的字。
# - 解說用白話,一兩句講清楚。
#
# legacy_text:舊版卡片的原文,用來認出既有資料庫裡的那一列並改寫。
# seed_key 上線後不要改,改了會變成新增一張。


def _card(
    seed_key: str,
    fraud_type: str,
    is_scam: bool,
    source: str,
    scenario: str,
    tags: list[str],
    explanation: str,
    difficulty: int = 1,
    legacy_text: str | None = None,
) -> dict[str, Any]:
    return {
        "seed_key": seed_key,
        "fraud_type": fraud_type,
        "is_scam": is_scam,
        "source_label": source,
        "scenario": scenario,
        "weakness_tags": list(tags),
        "explanation": explanation,
        "difficulty": difficulty,
        "legacy_text": legacy_text,
    }


SWIPE_CARDS_SEED = [
    # ── 投資詐騙 ──
    _card(
        "swipe-inv-01",
        "investment",
        True,
        "LINE 群組·林老師",
        "這檔明天開盤就會漲停，名額只剩 3 個。先把資金轉到我們合作的券商帳戶，我幫你卡位。",
        ["authority", "greed", "time_pressure"],
        "要你把錢轉到「合作券商」、保證會漲，是投資詐騙。正規券商的錢只會進你自己名下的交割帳戶。",
        legacy_text="老師說這檔三天漲 30%，名額剩 3 個！先轉一筆資金到合作券商鎖額度，賺了隨時出金。",
    ),
    _card(
        "swipe-inv-02",
        "investment",
        True,
        "LINE 群組·財富交流",
        "群裡大家每天都在貼獲利截圖，我同事上個月也賺了 50 萬。加入 VIP 就能跟著老師買，每個月穩穩賺 20%。",
        ["social_proof", "greed", "authority"],
        "獲利截圖很容易造假，群組裡說自己賺到錢的人可能都是同一夥的。每個月穩賺 20% 不可能。",
        difficulty=2,
        legacy_text="群組裡每天都有人曬獲利截圖，大家都賺翻了！分析師說加入 VIP 就能跟單，月穩定 20%，我同事已經賺 50 萬了！",
    ),
    _card(
        "swipe-inv-03",
        "investment",
        True,
        "臉書廣告·AI 交易平台",
        "名人推薦的 AI 交易平台，新聞都有報導。先小額試試，讓你先領出來看看，再決定要不要加碼。",
        ["authority", "trust_building", "greed"],
        "冒用名人推薦，先讓你小額出金，等你放大筆錢就領不出來了。",
        difficulty=2,
        legacy_text="這是馬斯克親自推薦的 AI 投資平台，新聞報導過，先小額試試，出金給你看再決定要不要加大。",
    ),
    _card(
        "swipe-inv-04",
        "investment",
        False,
        "XX 銀行·王專員",
        "您好，跟您確認下週二下午兩點預約的理財諮詢，地點在本行信義分行，當天請帶身分證。",
        [],
        "約在銀行分行、確認你自己預約的時間，沒有要你匯款或給密碼，是正常的預約提醒。",
        legacy_text="您好，這是 XX 銀行理財專員，您預約的諮詢。這檔債券基金近 5 年約 4%，但有本金波動風險，您可帶 DM 回家考慮。",
    ),
    _card(
        "swipe-inv-05",
        "investment",
        False,
        "券商 App·通知",
        "您的定期定額已於 9/6 扣款 3,000 元，成交明細請到 App「帳務查詢」查看。",
        [],
        "你自己設定的定期定額扣款通知，請你到 App 裡看明細，沒有要你做其他事。",
        legacy_text="您好，我是富邦投信客服，請問您在官網申購的台灣 50 ETF 定期定額設定有問題需要確認，請登入官網帳號查詢，我不會向您索取密碼。",
    ),
    _card(
        "swipe-inv-06",
        "investment",
        False,
        "同事·阿凱",
        "我都是自己開券商帳戶買 ETF，每個月扣三千。你有興趣的話，可以自己去券商開戶研究看看。",
        [],
        "同事分享自己的做法，錢留在你自己的帳戶，沒有要你把錢交給他。",
    ),
    # ── 假交友 ──
    _card(
        "swipe-rom-01",
        "romance",
        True,
        "交友 App·Michael",
        "親愛的，我在杜拜的工地出了點狀況，海關扣住一批設備，能先幫我墊 8 萬手續費嗎？回國馬上還你。",
        ["trust_building"],
        "沒見過面、人在國外、突然急需一筆錢，是假交友最常見的說法。",
        difficulty=2,
        legacy_text="親愛的，我在杜拜工程出了點狀況，海關卡住一批設備，能先幫我墊 8 萬手續費嗎？回國一定還你。",
    ),
    _card(
        "swipe-rom-02",
        "romance",
        True,
        "交友 App·David",
        "寶貝，我找到一個加密貨幣的套利機會。你先入金 10 萬，我這邊也投一樣多，解鎖後就能領回兩倍。",
        ["trust_building", "greed"],
        "先談感情，再帶你去投資假平台，錢放進去就領不出來。",
        difficulty=3,
        legacy_text="寶貝，我發現一個加密貨幣套利機會，我們一起投資，你先入金 10 萬，我這邊也會匹配，等解鎖期一過就能提領雙倍。",
    ),
    _card(
        "swipe-rom-03",
        "romance",
        True,
        "臉書·James",
        "我是聯合國維和部隊的醫官，視訊鏡頭壞了。我媽媽突然住院要開刀，你是我唯一能求助的人。",
        ["authority", "trust_building", "time_pressure"],
        "自稱軍人或醫官、一直找理由不視訊、家人急病要錢，這幾件事加在一起就是詐騙。",
        difficulty=2,
        legacy_text="我是聯合國維和部隊醫官，護照在辦，視訊設備壞了，但我媽媽緊急住院需要手術費，你是我唯一能求助的人。",
    ),
    _card(
        "swipe-rom-04",
        "romance",
        False,
        "交友 App·小涵",
        "跟你聊天很開心！下週六下午要不要約在信義區的咖啡廳見面？你方便的時間再跟我說。",
        [],
        "約在公開場所見面、讓你決定時間，也沒有提到錢，是正常的交友。",
        legacy_text="哈囉！我看到你的照片覺得你很有趣，可以加個 LINE 嗎？如果方便的話，下週想約你喝咖啡，我住台北信義區。",
    ),
    _card(
        "swipe-rom-05",
        "romance",
        False,
        "交友 App·阿倫",
        "我們聊了好一陣子了，今晚方便視訊嗎？想看看你本人，也讓你看看我。",
        [],
        "主動要求視訊、願意露臉，是正常交友的樣子。詐騙的人通常會一直找理由不視訊。",
        legacy_text="我覺得我們聊得很開心，可以視訊嗎？我想讓你看看我的臉，也想多了解你一點。",
    ),
    _card(
        "swipe-rom-06",
        "romance",
        False,
        "交友 App·小安",
        "上次吃飯是你請客，這次換我！我訂好週五晚上七點的餐廳了，到時候見。",
        [],
        "見過面、輪流請客、主動安排，沒有要你出錢，是正常的交往。",
    ),
    # ── 解除分期 ──
    _card(
        "swipe-atm-01",
        "atm",
        True,
        "電話·購物網客服",
        "您 6 月 20 日的訂單被誤設成分期付款，請您現在到 ATM，我在電話上一步一步帶您取消，先不要掛電話。",
        ["authority", "time_pressure"],
        "ATM 沒有「取消分期」的功能，照做就是把錢轉出去。客服不會要你到 ATM 操作。",
        difficulty=2,
        legacy_text="您好，我是 momo 購物客服，您 6/20 的訂單被誤設成分期付款，請現在到 ATM 操作解除，別掛電話我線上帶您。",
    ),
    _card(
        "swipe-atm-02",
        "atm",
        True,
        "電話·銀行風控中心",
        "您的帳戶偵測到異常，今天下班前要把存款轉到安全帳戶，不然帳戶會被凍結。",
        ["authority", "time_pressure"],
        "沒有「安全帳戶」這種東西，銀行也不會叫你把錢轉走。",
        legacy_text="您的帳戶被偵測到異常使用，需立即到 ATM 將存款轉至『安全帳戶』保護資金，今天下班前不處理帳戶將被凍結。",
    ),
    _card(
        "swipe-atm-03",
        "atm",
        True,
        "電話·刑事警察局",
        "你的帳戶涉及洗錢案，需要配合調查，到 ATM 照我的指示操作。這是偵查不公開，不要告訴家人。",
        ["authority"],
        "警察不會用電話叫你操作 ATM。叫你不要告訴家人，是為了不讓別人攔住你。",
        legacy_text="配合警察局洗錢清查行動，您的帳戶涉及可疑，需在 ATM 操作配合辦案，全程保持通話不要告知家人。",
    ),
    _card(
        "swipe-atm-04",
        "atm",
        False,
        "購物網·訂單通知",
        "您的訂單已出貨，預計 2 天內送達，可到 App「我的訂單」查看物流進度。",
        [],
        "單純的出貨通知，請你到 App 查詢，沒有要你做任何操作。",
        legacy_text="您的訂單已出貨，如需查詢請至 App『我的訂單』，有問題可於站內客服留言，我們不會請您操作 ATM 或提供卡號。",
    ),
    _card(
        "swipe-atm-05",
        "atm",
        False,
        "銀行 App·刷卡通知",
        "您的信用卡於 9/12 20:31 在全聯消費 1,286 元。如非本人消費，請在 App 內申請暫停卡片。",
        [],
        "刷卡通知請你在自己的 App 裡處理，沒有要你回電或到 ATM，是正常通知。",
        legacy_text="提醒您：台新銀行不會主動來電要求您操作 ATM 或轉帳，如接獲此類電話請立即掛斷並撥打 165 反詐騙專線。",
    ),
    _card(
        "swipe-atm-06",
        "atm",
        False,
        "你撥打的卡片背面客服",
        "您好，這裡是信用卡客服。為了確認是您本人，請提供身分證字號後四碼和生日，我再幫您查分期手續費。",
        [],
        "是你自己打官方電話過去，客服核對身分是正常流程。要小心的是對方主動打來要你做事。",
        difficulty=2,
    ),
    # ── 購物詐騙 ──
    _card(
        "swipe-shop-01",
        "shopping",
        True,
        "臉書社團·小美",
        "全新的，只賣市價三折。我私下出清，加我 LINE 直接匯款，不用付平台手續費比較快。",
        ["greed"],
        "價格低得離譜，又要你離開平台私下匯款，錢匯出去很可能就收不到貨。",
        legacy_text="這件全新只賣市價三折，我私下出清，加我 LINE 直接匯款，不用走平台手續費比較快。",
    ),
    _card(
        "swipe-shop-02",
        "shopping",
        True,
        "私訊·賣家",
        "全新 iPhone 只要 8,000！可以貨到付款，不過要先付 500 訂金幫你保留，很多人在問。",
        ["greed", "time_pressure", "social_proof"],
        "說好貨到付款又要先付訂金，前後矛盾。價格太低、又催你付錢，就要小心。",
        difficulty=2,
        legacy_text="全新 iPhone 只要 8,000，急售！可貨到付款，幫你寄黑貓，先付 500 訂金確保你優先，其他人也在問。",
    ),
    _card(
        "swipe-shop-03",
        "shopping",
        True,
        "IG·日本代購莉莉",
        "我明天飛日本，可以幫你帶限量球鞋。先匯全額 4,500 給我，今晚十點截止，名額不多。",
        ["time_pressure", "greed"],
        "個人代購先收全額、又限時截止，錢匯出去沒有任何保障。",
        difficulty=2,
        legacy_text="我是代購達人，幫你從日本帶 Switch 遊戲，先匯代購款 4,500 給我，我明天出發前確認名單，超過就排下次。",
    ),
    _card(
        "swipe-shop-04",
        "shopping",
        False,
        "購物網·賣家",
        "感謝購買！商品已從倉庫出貨，大約 2 到 3 天到貨，物流進度可以在訂單頁查看。",
        [],
        "在平台裡通知出貨、請你到訂單頁查詢，是正常的賣家訊息。",
        legacy_text="您好！感謝購買，商品已從倉庫出貨，預計 2-3 個工作天到貨，追蹤連結在蝦皮訂單頁，有問題請站內訊息我。",
    ),
    _card(
        "swipe-shop-05",
        "shopping",
        False,
        "超商·取貨通知",
        "您的包裹已送達 7-ELEVEN 信義門市，取貨付款 890 元，請於 7 天內取貨。",
        [],
        "單純的到店通知，沒有連結、沒有要你先付錢。取貨時核對金額和自己的訂單一樣就好。",
    ),
    _card(
        "swipe-shop-06",
        "shopping",
        False,
        "網路商店·客服",
        "已收到您的退貨申請，退貨單號 R20231。請把商品寄回網站上的退貨地址，收到後 5 個工作天內退款到您的信用卡。",
        [],
        "你自己申請的退貨，錢退回原本的信用卡，沒有要你給帳號或到 ATM，是正常流程。",
        difficulty=2,
    ),
    # ── 假網拍 ──
    _card(
        "swipe-sale-01",
        "fake-sale",
        True,
        "拍賣網·客服",
        "恭喜得標！請先付「解鎖保證金」才能出貨，30 分鐘內沒付就取消資格。",
        ["time_pressure", "greed", "authority"],
        "拍賣平台不會收「解鎖保證金」。限時要你先付錢，是假的得標通知。",
        difficulty=2,
        legacy_text="您在本拍賣得標！請先支付『解鎖保證金』才能出貨，30 分鐘內未付款將取消資格並列入黑名單。",
    ),
    _card(
        "swipe-sale-02",
        "fake-sale",
        True,
        "蝦皮聊聊·官方客服",
        "系統偵測到您的帳戶異常，請加客服 LINE：shopee_service2024 處理，先不要在 App 裡操作。",
        ["authority"],
        "要你加 LINE、還叫你不要在 App 裡操作，就是假客服。真的客服只會在 App 裡處理。",
        difficulty=2,
        legacy_text="您好，我是蝦皮官方客服，偵測到您帳戶異常，需要加我 LINE：shopee_service2024 處理，請勿在 App 操作以免影響調查。",
    ),
    _card(
        "swipe-sale-03",
        "fake-sale",
        True,
        "二手平台·系統通知",
        "您的商品已售出，買家已付款。請點下方連結完成賣家認證，款項才會撥入帳戶。",
        ["authority", "greed"],
        "正規平台不會要你點連結認證才能收款。這種連結是要騙你的帳號，或讓你先付錢。",
        difficulty=3,
        legacy_text="恭喜您的商品已售出！買家已付款，但您需先點擊以下連結確認賣家身分，收款才會入帳。",
    ),
    _card(
        "swipe-sale-04",
        "fake-sale",
        False,
        "二手平台·買家",
        "請問相機還在嗎？我可以約週末在台北車站面交，當場看過沒問題就付現。",
        [],
        "面交、當場驗貨再付錢，對雙方都有保障，是正常的買家。",
        legacy_text="提醒您：本平台客服只透過站內訊息聯繫，不會請您加 LINE 或外部帳號，也不會要求先付解鎖費，請小心詐騙。",
    ),
    _card(
        "swipe-sale-05",
        "fake-sale",
        False,
        "拍賣網·訂單通知",
        "您已得標「二手單眼相機」，請在 3 天內到 App 訂單頁完成付款，逾期會自動取消。",
        [],
        "在 App 裡通知、請你在訂單頁付款，沒有要你匯到個人帳戶，是正常的得標通知。",
    ),
    _card(
        "swipe-sale-06",
        "fake-sale",
        False,
        "二手平台·賣家",
        "已經幫你寄出了，物流單號 8801234，可以在平台的訂單頁查。收到後記得按完成訂單喔。",
        [],
        "透過平台出貨、給你查得到的單號，是正常的賣家。",
    ),
]

# 舊版有、新版拿掉的卡片。同步時刪掉,不然它們沒有 seed_key、會一直留在牌堆裡。
# 滑卡沒有其他表引用(作答紀錄只存類型),刪除是安全的。
RETIRED_SWIPE_TEXTS = [
    "限時 48 小時！金管會核准的海外 ETF，保本保息、年化 15%，超過限額就關閉申購，現在轉帳就能鎖定。",
]


def seed_swipe_cards(session: Session) -> None:
    """把滑卡題庫同步到資料庫(每次啟動都跑,重複執行不會重複新增)。

    依 seed_key 找到就更新;找不到就用 legacy_text 認出舊版那一列並改寫;都沒有才新增。
    """
    existing = session.exec(select(SwipeCard)).all()
    for card in existing:
        if card.seed_key is None and card.scenario in RETIRED_SWIPE_TEXTS:
            session.delete(card)
    by_key = {c.seed_key: c for c in existing if c.seed_key}
    by_text = {c.scenario: c for c in existing if not c.seed_key}
    for data in SWIPE_CARDS_SEED:
        fields = {k: v for k, v in data.items() if k != "legacy_text"}
        row = by_key.get(data["seed_key"]) or by_text.get(data["legacy_text"] or "")
        if row is None:
            session.add(SwipeCard(**fields))
            continue
        for key, value in fields.items():
            setattr(row, key, value)
        session.add(row)
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
