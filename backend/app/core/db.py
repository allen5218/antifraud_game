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
    pool: str = "practice",
) -> dict[str, Any]:
    return {
        "seed_key": seed_key,
        "pool": pool,
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
    # ── 2026-10 新增的練習卡（每類 6 → 12）──
    # 投資詐騙
    _card(
        "swipe-inv-07",
        "investment",
        True,
        "IG·理財網紅",
        "我私訊幾位粉絲送免費 VIP 訊號試用，只有 20 個名額，今天報名再送一支明牌。",
        ["greed", "time_pressure"],
        "網紅私訊送「明牌」和限量名額，是拉你進投資詐騙群組的常見開頭。",
    ),
    _card(
        "swipe-inv-08",
        "investment",
        True,
        "LINE 群組·助理小雅",
        "恭喜您抽中老師的保本方案，虧損公司全額賠。只要先下載這個 App 開戶，入金就能開始。",
        ["greed", "authority"],
        "保證不虧、要你下載指定 App 入金，是假投資平台。合法的投資不會保證賠你本金。",
    ),
    _card(
        "swipe-inv-09",
        "investment",
        True,
        "電話·投顧業務",
        "上次跟您聊得很愉快，這個案子我只告訴老客戶。先轉 5 萬到公司帳戶，下個月保證配息 8%。",
        ["trust_building", "greed"],
        "拉交情、說只給老客戶，再要你把錢轉到公司帳戶、保證配息，是投資詐騙。",
        difficulty=2,
    ),
    _card(
        "swipe-inv-10",
        "investment",
        False,
        "證券 App·成交回報",
        "您委託買進的 ETF 已成交 1 張，成交價 85.2 元，交割款會在成交後第二個營業日從您的交割帳戶扣款。",
        [],
        "自己下單的成交回報，錢從自己的交割帳戶扣，是正常通知。",
    ),
    _card(
        "swipe-inv-11",
        "investment",
        False,
        "銀行·理財專員",
        "這檔基金有風險，我先把公開說明書寄到您的信箱，您看完再決定，要買的話在 App 或來分行都可以。",
        [],
        "理專說明風險、讓你看完文件再決定，從 App 或分行購買，是正常流程。",
    ),
    _card(
        "swipe-inv-12",
        "investment",
        False,
        "LINE·姊姊",
        "公司本季員工持股開始了，每個月從薪水扣 2,000，是人資系統設定的，明細在薪資單上。你公司有這一種嗎？",
        [],
        "家人分享公司的員工持股，錢從自己的薪水扣、明細在薪資單上，沒有要你把錢交給誰。",
    ),
    # 假交友
    _card(
        "swipe-rom-07",
        "romance",
        True,
        "臉書·Captain Lee",
        "我退休後想在台灣定居，已經把 20 萬美元寄到你名下，但海關要你先繳 5 萬手續費才能領。",
        ["greed", "authority"],
        "陌生人說要寄大錢給你、要你先付手續費，是假交友和包裹詐騙常見的組合。",
    ),
    _card(
        "swipe-rom-08",
        "romance",
        True,
        "交友 App·Leo",
        "我好想見你，可是我的卡被鎖了，機票錢不夠。你能先借我 2 萬嗎？見面那天就還你。",
        ["trust_building"],
        "還沒見過面就要借錢，用「見面」當理由，是假交友要錢的常見藉口。",
    ),
    _card(
        "swipe-rom-09",
        "romance",
        True,
        "交友 App·Sophia",
        "我們的網路商店一個月可以賺十幾萬，平台上很多情侶一起經營。你先開一間店，進貨的錢我教你怎麼匯。",
        ["social_proof", "greed", "trust_building"],
        "拉你一起開網路商店，再教你把進貨的錢匯出去，是假交友後面接假網店。錢匯出去通常沒有店，也沒有貨。",
        difficulty=2,
    ),
    _card(
        "swipe-rom-10",
        "romance",
        False,
        "交友 App·Amy",
        "你說你在竹科上班，我也在附近。週三午休要不要一起吃個飯？在園區旁邊的餐廳就好。",
        [],
        "約平日午餐、公開場所，沒有提到錢，是正常交友。",
    ),
    _card(
        "swipe-rom-11",
        "romance",
        False,
        "交友 App·俊宏",
        "我們聊三個月了，想帶你見我朋友。週六大家約在火鍋店聚餐，你想來嗎？",
        [],
        "願意介紹朋友、約在公開場所，是正常的交往。",
    ),
    _card(
        "swipe-rom-12",
        "romance",
        False,
        "LINE·男友",
        "這次出國的機票我訂好了，我們各付各的。我把訂單截圖傳給你，你直接在航空公司 App 付你那張就好。",
        [],
        "交往中、各付各的，你自己在航空公司 App 付款，沒有要你把錢匯給他。",
        difficulty=2,
    ),
    # 假網拍
    _card(
        "swipe-sale-07",
        "fake-sale",
        True,
        "臉書社團·買家",
        "我同事也想買，我們一次買兩台。我用超商的賣貨服務下單了，你收到簡訊後點連結填銀行資料就能拿到款。",
        ["authority"],
        "買家自己下單，卻要你點簡訊連結填銀行資料才能收款，是假買家騙帳戶資料。",
        difficulty=2,
    ),
    _card(
        "swipe-sale-08",
        "fake-sale",
        True,
        "電話·二手平台客服",
        "您的賣場被檢舉暫停，要恢復需要繳保證金。我先在您帳戶匯一筆小額，您核對後照指示操作網路銀行。",
        ["authority"],
        "平台不會打電話要你繳保證金或操作網路銀行。「核對金額」其實是要你轉帳。",
        difficulty=2,
    ),
    _card(
        "swipe-sale-09",
        "fake-sale",
        True,
        "拍賣網·賣家",
        "這批是公司尾貨，原價 1 萬 2 只賣 3 千。平台抽成太高，你直接匯到我的帳戶，我多送一個。",
        ["greed"],
        "價格低得離譜、要你離開平台私下匯款，買了很可能收不到貨。",
    ),
    _card(
        "swipe-sale-10",
        "fake-sale",
        False,
        "二手平台·買家",
        "請問可以便宜 200 嗎？可以的話我直接在平台下單，用平台的付款就好。",
        [],
        "一般殺價，付款走平台，是正常的買家。",
    ),
    _card(
        "swipe-sale-11",
        "fake-sale",
        False,
        "拍賣網·系統通知",
        "買家已完成付款，款項由平台保管。請在 3 天內出貨並上傳寄件單號，買家確認收貨後撥款到你綁定的帳戶。",
        [],
        "款項由平台保管、出貨後撥款，是正常的交易流程，沒有要你另外驗證或付錢。",
        difficulty=2,
    ),
    _card(
        "swipe-sale-12",
        "fake-sale",
        False,
        "二手平台·賣家",
        "這件外套有一點小污漬，我拍給你看。介意的話不要買沒關係，下單前都可以再問我。",
        [],
        "主動說明瑕疵、不催你買，是正常的賣家。",
    ),
    # 購物詐騙
    _card(
        "swipe-shop-07",
        "shopping",
        True,
        "臉書社團·賣家",
        "原價 28,000 的吸塵器工廠價 1,500。貨在外縣市，不能貨到付款也不能刷卡，私訊匯到我個人帳戶，兩週後從海外寄出，寄出不退。",
        ["greed"],
        "價差大到不合理，又只收個人匯款、不給刷卡和貨到付款，錢匯出去很可能收不到貨。",
    ),
    _card(
        "swipe-shop-08",
        "shopping",
        True,
        "網路廣告·精品特賣",
        "官方授權清倉，所有包款 1 折起，倒數 3 小時。結帳頁只能用轉帳，訂單成立後寄出。",
        ["authority", "greed", "time_pressure"],
        "1 折、倒數計時、只能轉帳，是假購物網站常見的組合。",
    ),
    _card(
        "swipe-shop-09",
        "shopping",
        True,
        "LINE·賣家",
        "好評有幾千則，你查不到也沒關係。這筆我不走平台，你今晚先匯全額到我個人帳戶，我明天寄出，寄出後不退。",
        ["social_proof", "time_pressure"],
        "說好評很多卻不讓你查，不走平台、只收先匯款，買了很可能收不到貨。",
        difficulty=2,
    ),
    _card(
        "swipe-shop-10",
        "shopping",
        False,
        "網路商店·出貨通知",
        "您的訂單因缺貨延後出貨，不想等可以在訂單頁直接取消，款項會退回原付款方式。",
        [],
        "延後出貨、讓你自己在訂單頁取消、退回原付款方式，是正常處理。",
    ),
    _card(
        "swipe-shop-11",
        "shopping",
        False,
        "電話·購物網客服",
        "您好，您訂的冰箱明天安裝，師傅大約下午兩點到。尾款已經在網站付清，當天不用再付費用。",
        [],
        "店家打來確認安裝時間，沒有要你付錢或提供資料，是正常聯絡。",
    ),
    _card(
        "swipe-shop-12",
        "shopping",
        False,
        "社群·朋友",
        "我昨天收到了，顏色跟照片有一點落差，不過還可以。你要的話我把賣場名稱給你，你自己下單。",
        [],
        "朋友分享自己的購物經驗，請你自己去賣場下單，沒有要你付錢給誰。",
    ),
    # 解除分期
    _card(
        "swipe-atm-07",
        "atm",
        True,
        "簡訊·銀行通知",
        "您的帳戶今日將扣款 12 期會員費，若非本人申請，請在 1 小時內回撥本簡訊的客服專線辦理取消。",
        ["authority", "time_pressure"],
        "要你回撥簡訊裡的電話，接起來的就是詐騙集團。要確認扣款，請打卡片背面的電話或看銀行 App。",
    ),
    _card(
        "swipe-atm-08",
        "atm",
        True,
        "LINE·銀行客服",
        "為了解除重複扣款，請把網路銀行的帳號、密碼和等一下收到的驗證碼傳給我，我直接幫您在後台處理。",
        ["authority"],
        "銀行有的會用官方帳號傳通知，但不會跟你要網路銀行的帳號、密碼和驗證碼。這三樣一給，帳戶就等於交出去。",
    ),
    _card(
        "swipe-atm-09",
        "atm",
        True,
        "電話·銀行專員",
        "解除程序要用遊戲點數驗證身分，請您到便利商店買 2 萬元點數，把卡片背面的序號拍給我。今天沒處理完，明天又會再扣一期。",
        ["authority", "time_pressure"],
        "沒有任何銀行用遊戲點數驗證身分。序號一拍出去，點數就被拿走了。",
    ),
    _card(
        "swipe-atm-10",
        "atm",
        False,
        "銀行 App·訊息中心",
        "您申請的帳單分期 6 期已生效，每期 2,150 元，明細可在「信用卡帳務」查看，要提前清償請洽本行客服。",
        [],
        "這是你自己申請的分期，通知在銀行 App 裡、請你自己查明細，是正常通知。",
    ),
    _card(
        "swipe-atm-11",
        "atm",
        False,
        "電話·銀行信用卡中心",
        "提醒您本期帳單 5,600 元明天到期，可以在 App 繳費，或照原本設定的自動扣款。",
        [],
        "主動來電、有期限，但只提醒你繳自己的帳單，用的是你自己的 App 或自動扣款，沒有要你轉到別的帳戶。",
        difficulty=2,
    ),
    _card(
        "swipe-atm-12",
        "atm",
        False,
        "購物網·客服信箱",
        "您反映的重複扣款，我們查過是同一筆預先授權，3 到 5 個工作天會自動消失，不需要做任何操作。",
        [],
        "信用卡的預先授權本來就會自動取消，客服請你不用做任何事，是正常回覆。",
        difficulty=2,
    ),
    # ── 檢測專用（pool=exam，只在檢測出現，練習發牌讀不到）──
    # 投資詐騙
    _card(
        "swipe-exam-inv-01",
        "investment",
        True,
        "LINE·講座助理",
        "老師下週的線下講座免費參加。今天先幫你加入學員群組，裡面每天報內部飆股，跟單的學員這個月都翻倍了。",
        ["authority", "social_proof", "greed"],
        "免費講座先拉你進群、說跟單的人都翻倍，是投資詐騙的開頭。真的投資不會保證翻倍。",
        pool="exam",
    ),
    _card(
        "swipe-exam-inv-02",
        "investment",
        True,
        "簡訊·證券分析師",
        "恭喜您中籤！請在今天下午三點前把認股款 12 萬匯到指定專戶完成認購，逾時視同放棄。",
        ["authority", "greed", "time_pressure"],
        "新股申購的款項從你自己的交割帳戶扣，不會叫你匯到「指定專戶」。",
        difficulty=2,
        pool="exam",
    ),
    _card(
        "swipe-exam-inv-03",
        "investment",
        True,
        "LINE·投資平台客服",
        "你上次放的 2,000 已經提出來了。這次額度開到 30 萬，同一套做法，你看到錢入帳再加碼就好。",
        ["trust_building", "greed"],
        "先讓你小額提領成功，再勸你放大筆錢，是假投資平台的套路。大筆錢放進去就領不出來。",
        difficulty=2,
        pool="exam",
    ),
    _card(
        "swipe-exam-inv-04",
        "investment",
        False,
        "電話·證券營業員",
        "您好，您上週申請的信用戶還缺一份財力證明，本週可以帶到分公司補件，或從 App「開戶進度」上傳，不用急。",
        [],
        "券商主動聯絡，補的是你自己申請的信用戶文件，到分公司或從自己的 App 上傳，沒有要你匯款。",
        difficulty=2,
        pool="exam",
    ),
    _card(
        "swipe-exam-inv-05",
        "investment",
        False,
        "投信·活動通知",
        "定期定額申購手續費 0 元，活動到月底。基金的風險等級寫在本公司活動頁，要參加請從官網進入 App。",
        [],
        "有優惠期限，但請你自己從官網進 App 申購，風險等級也公開寫出，是正常的推銷。",
        difficulty=2,
        pool="exam",
    ),
    _card(
        "swipe-exam-inv-06",
        "investment",
        False,
        "LINE·同事",
        "公司福委會辦了一場理財講座，報名明天中午截止，名額快滿了。講者是銀行理專，講基金的風險，現場不收錢也不推銷，要不要一起報名？",
        [],
        "有截止時間，但只是公司辦的講座，不收錢、不推銷，也沒有要你把錢交給誰。",
        pool="exam",
    ),
    # 假交友
    _card(
        "swipe-exam-rom-01",
        "romance",
        True,
        "交友 App·Jason",
        "寶貝，我在遠洋貨輪上工作，訊號不好沒辦法視訊。公司要我先付 3 萬保管費，才能把薪水寄回台灣，你能先幫我嗎？",
        ["trust_building"],
        "不能視訊、人在海上或國外、要你先幫忙付錢，是假交友要錢的典型說法。",
        pool="exam",
    ),
    _card(
        "swipe-exam-rom-02",
        "romance",
        True,
        "IG·Andy",
        "認識你之後我才相信緣分。我有一個黃金交易平台，你先放 3 萬，我幫你操作，我們一起存結婚基金。",
        ["trust_building", "greed"],
        "先談感情，再帶你去投資平台，是假交友結合投資詐騙。錢放進去就領不出來。",
        difficulty=2,
        pool="exam",
    ),
    _card(
        "swipe-exam-rom-03",
        "romance",
        True,
        "交友 App·醫生 Ryan",
        "我在戰地醫院服務，寄了一箱禮物給你。快遞說關稅 2 萬要先匯給我，我再轉給他們，今天不付就退回。",
        ["authority", "time_pressure"],
        "關稅要匯給寄件人就是破綻。真的要繳稅，物流業者會給正式繳款單，錢付給海關或物流公司。",
        difficulty=2,
        pool="exam",
    ),
    _card(
        "swipe-exam-rom-04",
        "romance",
        False,
        "交友 App·小婷",
        "我們都見過兩次了。下週六那個展覽票只剩零星位置，一張 350，我先刷兩張卡位。你人來就好，票在我這。",
        [],
        "見過面、她自己先付、沒有要你匯款，是一般朋友之間的安排。",
        difficulty=2,
        pool="exam",
    ),
    _card(
        "swipe-exam-rom-05",
        "romance",
        False,
        "交友 App·志明",
        "這週六我人在高雄，沒辦法約。下下週你有空的話，想約在你方便的捷運站，咖啡或書店都行，時間你定。",
        [],
        "改期但主動提出見面、讓你決定時間地點，也沒提到錢，是正常交友。",
        pool="exam",
    ),
    _card(
        "swipe-exam-rom-06",
        "romance",
        False,
        "LINE·剛認識的朋友",
        "這陣子跟你聊天很開心。我手機鏡頭有裂痕，畫面可能很暗很糊，但今晚九點還是想跟你視訊十分鐘，讓你看看我本人。",
        [],
        "鏡頭壞了還是主動約視訊，願意露臉，是正常交友的樣子。詐騙的人通常拿鏡頭壞當作不視訊的理由。",
        pool="exam",
    ),
    # 假網拍
    _card(
        "swipe-exam-sale-01",
        "fake-sale",
        True,
        "二手平台·買家",
        "我已經下單付款了，可是平台說你的帳戶還沒開通金流。我把客服的 LINE 給你，你加了照指示驗證就能收款。",
        ["authority"],
        "買家說款項卡住、要你加「客服 LINE」驗證，是假網拍。真的收款只在 App 訂單頁和錢包設定處理。",
        difficulty=2,
        pool="exam",
    ),
    _card(
        "swipe-exam-sale-02",
        "fake-sale",
        True,
        "簡訊·拍賣網得標通知",
        "您已得標，因系統升級改用超商代碼繳費，請點連結取得代碼，今晚 12 點前未繳視同棄標。",
        ["authority", "time_pressure"],
        "得標付款在拍賣網站的訂單頁處理。用簡訊連結要你繳代碼、還限時，是假得標通知。",
        difficulty=2,
        pool="exam",
    ),
    _card(
        "swipe-exam-sale-03",
        "fake-sale",
        True,
        "社群拍賣·賣家",
        "這台遊戲機只剩一台，好幾個人在排。訂金請匯到我朋友的帳戶，我自己的帳戶被凍結了。不能面交，也不走平台。",
        ["social_proof", "time_pressure"],
        "匯到別人的帳戶、不能面交、不走平台，三件事加在一起，錢匯出去就追不回來。",
        difficulty=2,
        pool="exam",
    ),
    _card(
        "swipe-exam-sale-04",
        "fake-sale",
        False,
        "拍賣網·訂單通知",
        "昨日得標的電競椅還沒付款。賣家把期限設到明晚 23:59，逾時會取消訂單，並在帳號記一筆未付款。付款請到 App 的得標清單完成。",
        [],
        "有期限、會記錄未付款，但付款在拍賣 App 的得標清單完成，是正常的得標通知。",
        difficulty=2,
        pool="exam",
    ),
    _card(
        "swipe-exam-sale-05",
        "fake-sale",
        False,
        "二手平台·買家",
        "我這週只週三晚上有空，想看那台腳踏車。市政府捷運站 2 號出口可以嗎？我要試騎，沒問題再現場付現。",
        [],
        "約在公開場所、試騎過才付現，對雙方都有保障，是正常的買家。",
        pool="exam",
    ),
    _card(
        "swipe-exam-sale-06",
        "fake-sale",
        False,
        "二手平台·買家",
        "我已經在平台付款了，麻煩今天寄出。你看一下訂單頁，應該是待出貨。單號填在訂單裡就好，我確認收到，平台才會把錢撥給你。",
        [],
        "買家催出貨，但付款、出貨、撥款都在平台的訂單頁，沒有要你加客服或付錢。",
        difficulty=2,
        pool="exam",
    ),
    # 購物詐騙
    _card(
        "swipe-exam-shop-01",
        "shopping",
        True,
        "IG·代購小舖",
        "你要的日本限定模型我問到了，店家賣 9,800，我這只要 1,200。請匯到我傳的無卡存款帳號，今晚十二點前要入帳，不能貨到付款，也不能退。",
        ["greed", "time_pressure"],
        "價差大到不合理、只收無卡存款、不能貨到付款也不能退，錢匯出去就沒有任何保障。",
        pool="exam",
    ),
    _card(
        "swipe-exam-shop-02",
        "shopping",
        True,
        "臉書廣告·家電出清",
        "倉庫結束營業，掃地機器人一台 990 元，只接受轉帳付款，付款後 7 天內出貨。",
        ["greed"],
        "價格低得不合理、只收轉帳不給貨到付款，付了錢很可能收不到貨。",
        pool="exam",
    ),
    _card(
        "swipe-exam-shop-03",
        "shopping",
        True,
        "簡訊·物流通知",
        "您的包裹因地址不完整無法配送，請在 24 小時內點連結補填地址並支付 25 元補運費。",
        ["authority", "time_pressure"],
        "假物流簡訊用小額運費騙你輸入信用卡資料。真的物流問題，到你下單的網站或物流公司官網查。",
        difficulty=2,
        pool="exam",
    ),
    _card(
        "swipe-exam-shop-04",
        "shopping",
        False,
        "網路商店·會員通知",
        "您購物車裡的商品今晚 12 點結束 85 折，要結帳請回官網或 App。",
        [],
        "有期限的促銷，但要你自己回官網或 App 結帳，沒有連結、沒有要你轉帳，是正常廣告。",
        difficulty=2,
        pool="exam",
    ),
    _card(
        "swipe-exam-shop-05",
        "shopping",
        False,
        "購物網·客服",
        "您的訂單因為信用卡授權失敗沒有成立，若還要購買，請重新在官網下單，原本那筆不會扣款。",
        [],
        "訂單失敗請你自己重新下單，沒有要你提供卡號或付款到別處，是正常通知。",
        difficulty=2,
        pool="exam",
    ),
    _card(
        "swipe-exam-shop-06",
        "shopping",
        False,
        "超商·取件提醒",
        "您的包裹已到指定門市，取貨時付 2,460 元。請於 7 天內領取，逾期未取會取消訂單，並依賣場規則處理運費。",
        [],
        "取貨付款、逾期取消都是超商取貨的一般規則。取貨時核對金額和自己的訂單一樣，就是正常通知。",
        pool="exam",
    ),
    # 解除分期
    _card(
        "swipe-exam-atm-01",
        "atm",
        True,
        "電話·影音平台客服",
        "您申辦的影音會員被設成連扣 12 期。請帶提款卡到 ATM，選「解除代扣」，我報一組代碼給您。先不要掛斷，掛了代碼會失效。",
        ["authority", "time_pressure"],
        "ATM 沒有「解除代扣」的功能，照著輸入代碼就是轉帳。叫你不要掛電話，是不讓你自己查證。",
        pool="exam",
    ),
    _card(
        "swipe-exam-atm-02",
        "atm",
        True,
        "電話·銀行行員",
        "您的帳戶今天有一筆異常資金進出，為了保護您，請在下午四點前把存款轉到本行的監管專戶隔離，錢還是您的。逾時會先限制提領。",
        ["authority", "time_pressure"],
        "沒有「監管專戶」這種東西，銀行也不會叫你把錢轉走保護。照做就是把錢轉給詐騙集團。",
        difficulty=2,
        pool="exam",
    ),
    _card(
        "swipe-exam-atm-03",
        "atm",
        True,
        "電話·地方法院書記官",
        "我是地方法院的書記官。你的帳戶收進一筆問題款項，請現在到 ATM，把餘額轉進法院保管專戶。這件事不要跟家人說。",
        ["authority", "time_pressure"],
        "法院不會打電話叫你操作 ATM，也沒有「法院保管專戶」。叫你不要告訴家人，是怕有人攔住你。",
        difficulty=2,
        pool="exam",
    ),
    _card(
        "swipe-exam-atm-04",
        "atm",
        False,
        "你撥打的銀行客服",
        "您查的那筆分期，手續費是 180 元。為了核對身分，請說身分證後四碼。要取消分期，請到本行 App 的帳務頁送出申請。",
        [],
        "是你自己打官方電話過去，客服核對身分是正常流程，取消也是請你到自己的 App 辦。",
        difficulty=2,
        pool="exam",
    ),
    _card(
        "swipe-exam-atm-05",
        "atm",
        False,
        "購物網·App 推播",
        "您的訂單選了分 3 期付款，若要改成一次付清，請在 48 小時內到 App「訂單明細」修改。",
        [],
        "有分期、有期限，但只請你在自己的 App 裡修改，沒有電話、沒有 ATM，是正常通知。",
        difficulty=2,
        pool="exam",
    ),
    _card(
        "swipe-exam-atm-06",
        "atm",
        False,
        "銀行 App·推播",
        "您的帳戶今日有一筆約定轉帳 25,000 元。若非本人操作，請在 App 點選「暫停交易」或撥打卡片背面客服。",
        [],
        "這是你自己銀行 App 裡的交易通知，請你在 App 或打卡片背面的電話處理，沒有要你回撥陌生號碼。",
        pool="exam",
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
    # 比對要看全部的池：只看練習池的話，檢測卡每次啟動都比對不到、會被當成新卡再塞一次
    existing = session.exec(select(SwipeCard)).all()
    for card in existing:
        if (
            card.pool == "practice"
            and card.seed_key is None
            and card.scenario in RETIRED_SWIPE_TEXTS
        ):
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
