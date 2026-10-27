from typing import Any

from sqlmodel import Session, col, select

from app.economy.service import adjust_cash, lock_user
from app.models import FraudType, MascotItem, PretestQuestion, User, UserMascotItem

# 前測題庫。每類 6 題:詐騙情境 3 題、正常情境 3 題,每次每類各抽 2 題(routes/pretest.py)。
#
# 出題規則(改題前先讀):
# - 三個選項都只寫「做法」,不寫理由,長度與句型盡量一致。
#   舊版的正解常寫成「不理會，這很可能是詐騙」,答案寫在選項裡,不懂防詐也挑得中。
# - 正常情境的錯誤選項是「過度懷疑」或「多做一件有風險的事」,
#   不能把「自己打官方電話查證」當成錯的 —— 那在任何情況下都是對的。
# - 解說用白話,一兩句講清楚為什麼。
#
# legacy_text:舊版題目的原文,用來把既有資料庫裡的那一列認出來、改寫成新版。
# seed_key 一旦上線就不要改,改了會變成新增一題。


def _q(
    seed_key: str,
    fraud_type: str,
    is_scam: bool,
    text: str,
    options: list[str],
    correct: str,
    explanation: str,
    difficulty: int = 1,
    legacy_text: str | None = None,
) -> dict[str, Any]:
    return {
        "seed_key": seed_key,
        "fraud_type": fraud_type,
        "is_scam": is_scam,
        "question_text": text,
        "options": [
            {"key": key, "text": option, "is_correct": key == correct}
            for key, option in zip("ABC", options, strict=True)
        ],
        "explanation": explanation,
        "difficulty": difficulty,
        "legacy_text": legacy_text,
    }


_INV = FraudType.INVESTMENT.value
_SALE = FraudType.FAKE_SALE.value
_SHOP = FraudType.SHOPPING.value
_ROM = FraudType.ROMANCE.value
_ATM = FraudType.ATM.value

PRETEST_QUESTIONS = [
    # ── 投資詐騙 ──
    _q(
        "pre-inv-01",
        _INV,
        True,
        "你被拉進一個 LINE 投資群組，「老師」每天報明牌，說跟單每月賺 30%，群裡很多人貼獲利截圖。你會怎麼做？",
        ["退出群組，不跟單", "先跟一次小額試試看", "私訊老師問怎麼加入"],
        "A",
        "保證高報酬、一堆人貼獲利截圖，是投資詐騙最常見的開場。截圖可以造假，說自己賺錢的群友也可能是同一夥人。",
        legacy_text="你在 LINE 群組收到一則訊息：「老師帶單，月報酬 30%，已有 500 人獲利！」你會怎麼做？",
    ),
    _q(
        "pre-inv-02",
        _INV,
        True,
        "朋友說他在一個加密貨幣平台賺了 5 萬，還成功領出來，拉你一起加入。你會怎麼做？",
        ["先投一萬，領得出來再加碼", "查平台有沒有在金管會登記", "請朋友直接幫你操作"],
        "B",
        "先讓你小賺、順利出金，等你放了大筆錢就領不出來，是假投資平台的做法。朋友也可能被騙了。",
        difficulty=2,
        legacy_text="朋友分享他在某平台投資加密貨幣，已小賺了 5 萬元並成功提領。他推薦你加入。你會？",
    ),
    _q(
        "pre-inv-03",
        _INV,
        False,
        "你在銀行臨櫃辦事，理專介紹一檔債券基金，說過去五年平均年報酬約 3%、有虧損的可能，給你說明書帶回家看。你會怎麼做？",
        ["請理專保證不會虧再買", "帶回家看完說明書再決定", "當作詐騙，拒絕後離開"],
        "B",
        "在銀行臨櫃、主動說有虧損風險、讓你帶回家考慮，是正常的理財推銷。反過來，敢保證不虧的才要小心。",
        difficulty=2,
        legacy_text="你的銀行理專推薦一檔年化報酬約 4% 的定存方案，並詳細說明風險。這是詐騙嗎？",
    ),
    _q(
        "pre-inv-04",
        _INV,
        True,
        "你在 YouTube 看到財經名人代言的投資廣告，點進去後有位「助理」加你 LINE，說要教你用一個 App 搶股票。你會怎麼做？",
        [
            "先下載 App 看介面正不正規",
            "到名人的官方粉專看有沒有這則廣告",
            "查這家業者在不在金管會名單上",
        ],
        "C",
        "冒用名人照片的投資廣告很多。就算粉專真的有這則廣告，也不代表那個 App 能投資；要你下載 App 投資，先查業者有沒有在金管會登記。",
    ),
    _q(
        "pre-inv-05",
        _INV,
        False,
        "同事說他每個月用自己的券商帳戶定期定額買 ETF，建議你也可以自己去開戶研究看看。你會怎麼做？",
        ["把錢交給同事幫你買", "認定是詐騙並封鎖他", "自己去券商開戶研究"],
        "C",
        "同事分享自己的做法，錢留在你自己名下的帳戶，沒有要你把錢交給他，是正常的聊天。",
    ),
    _q(
        "pre-inv-06",
        _INV,
        False,
        "你在投信官網看上一檔基金，頁面寫著募集只到這週五，扣款前列出手續費，也寫了過去績效不代表未來。你會怎麼做？",
        [
            "看完說明，照官網流程申購",
            "改匯到客服視窗給的帳戶",
            "覺得截止日在催你，當作詐騙",
        ],
        "A",
        "基金本來就有募集期限，官網寫明截止日、先列出費用和風險、從自己的帳戶扣款，是正常的申購流程。要你改匯到別的帳戶才有問題。",
        difficulty=2,
    ),
    # ── 假網拍 ──
    _q(
        "pre-sale-01",
        _SALE,
        True,
        "你在二手社團看到一支 iPhone 只要市價一半，賣家說搬家急售，要你加 LINE 私下交易。你會怎麼做？",
        ["要求改在平台上下單", "加 LINE 付訂金保留", "請賣家寄照片再匯款"],
        "A",
        "價格低得離譜、又要你離開平台私下交易，錢匯出去就沒有任何保障。在平台下單，出問題才有人處理。",
        legacy_text="你在蝦皮看到一台 iPhone 只要市價五折，賣家說「搬家急售」並要求加 LINE 私下交易。你會？",
    ),
    _q(
        "pre-sale-02",
        _SALE,
        False,
        "你在拍賣平台賣二手相機，買家直接在平台下單，也用平台的付款方式付了錢。你會怎麼做？",
        ["要買家改成私下匯款", "照平台流程出貨", "取消訂單，當作詐騙"],
        "B",
        "買家在平台下單、用平台付款，錢由平台代收，照流程出貨就好。改成私下匯款反而失去保障。",
        legacy_text="你在正規拍賣平台賣二手相機，買家透過平台下單並使用平台的安全交易機制付款。這是正常交易嗎？",
    ),
    _q(
        "pre-sale-03",
        _SALE,
        True,
        "你在二手平台賣東西，買家說他付款了，傳來一個「收款確認」連結，要你點進去填銀行帳號。你會怎麼做？",
        ["先看連結網址像不像平台", "回平台 App 看這筆訂單", "請買家改傳轉帳截圖"],
        "B",
        "買家付的錢會出現在平台的訂單裡，不需要你點外部連結填資料。網址可以做得很像，截圖也能假造，回自己的 App 看訂單才準。",
        difficulty=2,
        legacy_text="你賣東西時，買家傳了一個連結說是「付款確認頁面」，要你點進去填寫銀行帳號以接收款項。你會？",
    ),
    _q(
        "pre-sale-04",
        _SALE,
        True,
        "你在平台賣東西，有人自稱「平台客服」，說你的帳號還沒完成認證，錢卡在系統裡，要你加 LINE 處理。你會怎麼做？",
        [
            "加 LINE，請他報訂單編號核對",
            "請他把認證步驟寄到你的信箱",
            "從 App 的客服中心詢問",
        ],
        "C",
        "平台客服只會在 App 裡聯絡你，不會要你加 LINE。對方報得出訂單編號、寄來的信看起來很正式，都不代表他是客服。",
        difficulty=2,
    ),
    _q(
        "pre-sale-05",
        _SALE,
        False,
        "你在二手平台買一台單眼相機，賣家約在捷運站面交，讓你當場試拍，確認沒問題再付錢。你會怎麼做？",
        ["先匯全額再去面交", "取消交易並檢舉賣家", "當場檢查沒問題就付款"],
        "C",
        "面交、當場驗貨再付錢，對雙方都有保障，是很安全的交易方式。",
    ),
    _q(
        "pre-sale-06",
        _SALE,
        False,
        "你在拍賣平台得標一件商品，平台寄來站內通知，提醒你三天內在 App 裡完成付款。你會怎麼做？",
        ["在 App 的訂單頁付款", "回覆要求改用匯款", "當作詐騙，不理會"],
        "A",
        "得標通知出現在平台裡、請你在訂單頁付款，是正常流程。不付款的話，訂單會被取消。",
    ),
    # ── 購物詐騙 ──
    _q(
        "pre-shop-01",
        _SHOP,
        True,
        "你在臉書看到一頁式廣告，名牌包只要原價一折，只接受貨到付款。你會怎麼做？",
        ["先搜尋這家店的資料和評價", "下單，反正貨到付款", "先私訊客服問是不是正品"],
        "A",
        "一頁式廣告、價格低得離譜，貨到付款也擋不住空盒和假貨。先搜這家店的資料和評價，好評也可能是假的，查不到公司和退貨方式就不要買。",
        legacy_text="你在 Facebook 看到一頁式廣告，名牌包只要原價一折，僅接受貨到付款。你會？",
    ),
    _q(
        "pre-shop-02",
        _SHOP,
        False,
        "你在 momo 官方 App 看到電視打六折，頁面寫著品牌直送、七天鑑賞期。你會怎麼做？",
        ["改加客服 LINE 私下買", "在 App 裡照流程下單", "認定是詐騙並檢舉商品"],
        "B",
        "在大型購物網站的官方 App 下單、有鑑賞期，是正常的促銷。私下交易反而沒有保障。",
        legacy_text="你在 momo 購物網的官方 App 上看到一款電視特價 6 折，並標示「品牌直送、七天鑑賞」。這是詐騙嗎？",
    ),
    _q(
        "pre-shop-03",
        _SHOP,
        True,
        "你在 IG 看到代購帳號說明天飛日本，可以幫你帶限量球鞋，要先匯全額，今晚截止。你會怎麼做？",
        ["看他追蹤人數夠多再匯", "改在有保障的平台買", "請他傳機票照片再匯"],
        "B",
        "個人代購先收全額、又限時截止，錢匯出去沒有任何保障。追蹤人數可以買，機票照片也能假造，這類帳號收完錢就消失的很多。",
    ),
    _q(
        "pre-shop-04",
        _SHOP,
        True,
        "你收到簡訊：「您的包裹地址不完整，請點連結補繳 25 元運費。」你會怎麼做？",
        ["點連結看是哪家物流", "回簡訊補上地址", "到物流官方 App 查"],
        "C",
        "補繳運費的簡訊連結會騙你輸入信用卡資料。包裹有問題就到物流或購物網站的官方 App 查。",
        difficulty=2,
    ),
    _q(
        "pre-shop-05",
        _SHOP,
        False,
        "你在超商取貨，店員說包裹要付 890 元，跟你自己下單時的金額一樣。你會怎麼做？",
        ["拒絕取貨並報警", "先付款，回家再查", "核對訂單後付款取貨"],
        "C",
        "金額和你自己下的訂單一樣，就是正常的取貨付款。養成先核對再付款的習慣，就不怕被寄來沒買的東西。",
    ),
    _q(
        "pre-shop-06",
        _SHOP,
        False,
        "你網購的衣服尺寸不合，從網站的「退換貨」頁面申請退貨，客服回覆退貨單號和寄回地址。你會怎麼做？",
        ["照流程把衣服寄回", "要客服先轉錢給你", "當作詐騙，不寄回"],
        "A",
        "你自己申請的退貨，照網站的流程寄回，退款會退到原本的付款方式，是正常流程。",
    ),
    # ── 假交友 ──
    _q(
        "pre-rom-01",
        _ROM,
        True,
        "你在交友 App 認識一位自稱在國外當軍醫的人，聊了兩個月，他說要 5 萬元手續費才能回台灣見你。你會怎麼做？",
        [
            "先匯一半，說好視訊再匯剩下的",
            "請他先視訊，錢一毛都不匯",
            "請他傳部隊的證件照片",
        ],
        "B",
        "沒見過面、人在國外、需要錢才能回來見你，是假交友最常見的說法。不管他給不給視訊、傳什麼證件，錢都不要匯，真的軍人回國不用你付錢。",
        legacy_text="你在交友 App 上認識一位自稱在海外當軍醫的對象，交往兩個月後對方說需要 5 萬元才能回國見你。你會？",
    ),
    _q(
        "pre-rom-02",
        _ROM,
        False,
        "朋友介紹你認識一位新朋友，見過幾次面，對方邀你週末一起去當社區志工。你會怎麼做？",
        ["直接封鎖對方", "照常赴約一起參加", "只在網路上聊，不見面"],
        "B",
        "透過朋友認識、見過面、邀你參加公開活動，也沒有提到錢，是正常的交友。",
        legacy_text="你透過朋友介紹認識一位新朋友，見過幾次面後對方邀你一起參加社區志工活動。這是詐騙嗎？",
    ),
    _q(
        "pre-rom-03",
        _ROM,
        True,
        "網路上聊了三個月、從沒見過面的對象說，家人住院急需 10 萬，保證下個月還你。你會怎麼做？",
        ["先借一部分應急", "拒絕，先見面再說", "匯到他給的醫院帳戶"],
        "B",
        "從沒見過面就開口借大錢，還說得很急，是假交友的做法。他給的帳戶是不是醫院的，你沒辦法確認，不能因為他說是醫院帳戶就匯款。",
        difficulty=2,
        legacy_text="網路上認識三個月的對象突然說家人住院需要醫藥費，希望你借 10 萬元，並保證下個月還。你會？",
    ),
    _q(
        "pre-rom-04",
        _ROM,
        True,
        "交友 App 認識的對象說他靠一個投資平台賺很多，要教你一起操作，還說賺了可以一起買房。你會怎麼做？",
        [
            "先投一點，領得出來再加碼",
            "請他截圖給你看他賺的錢",
            "查這個平台有沒有在金管會登記",
        ],
        "C",
        "先談感情、再帶你去投資，是「殺豬盤」的做法。先讓你小額領出來、傳賺錢截圖，都是讓你放心加碼的手段；查得到登記之前，一毛錢都不要放進去。",
        difficulty=2,
    ),
    _q(
        "pre-rom-05",
        _ROM,
        False,
        "交友 App 上聊了幾週的人，主動提議視訊，接著約你週末在熱鬧的咖啡廳見面。你會怎麼做？",
        ["先匯車資給對方", "封鎖對方，不再聯絡", "約在公開場所見面"],
        "C",
        "願意視訊、約在公開場所見面、沒有要錢，是正常的交友。第一次見面選人多的地方就好。",
    ),
    _q(
        "pre-rom-06",
        _ROM,
        False,
        "交往半年、見過彼此朋友的男友說想一起出國玩，提議各自用自己的信用卡訂機票。你會怎麼做？",
        ["各自訂票，一起排行程", "把卡號給他代訂", "認定是詐騙，提分手"],
        "A",
        "交往一段時間、見過彼此的朋友、各付各的，是正常的交往。就算是伴侶，信用卡號也不要交給別人。",
    ),
    # ── 解除分期 ──
    _q(
        "pre-atm-01",
        _ATM,
        True,
        "你接到自稱網購客服的電話，對方說得出你上週買的東西和金額，說系統出錯被設成分期，要你現在去 ATM 取消。你會怎麼做？",
        ["掛掉，自己到購物 App 查訂單", "請他報員工編號再照做", "先去 ATM，到了再決定"],
        "A",
        "你的訂單資料可能已經外洩，對方說得出來不代表他是真客服，員工編號也能隨口編。ATM 沒有取消分期的功能，掛掉後自己到購物 App 查。",
        legacy_text="你接到電話，對方準確說出你上週在網路上買的東西和金額，並說系統出錯要幫你退款。你會？",
    ),
    _q(
        "pre-atm-02",
        _ATM,
        False,
        "銀行 App 推播通知你有一筆刷卡消費，金額你沒印象，請你打開 App 確認。你會怎麼做？",
        ["當作詐騙，不理會", "打開銀行 App 查這筆", "把卡號傳給客服 LINE"],
        "B",
        "銀行 App 的推播是正常的刷卡通知，在自己的 App 裡查就好。不理會的話，盜刷可能會繼續。",
        legacy_text="銀行官方 App 推播通知你有一筆信用卡消費異常，要你進入 App 確認。這是詐騙嗎？",
    ),
    _q(
        "pre-atm-03",
        _ATM,
        True,
        "有人打來自稱「165 反詐騙專線」，說你的帳戶涉及洗錢，要你把錢轉到安全帳戶。你會怎麼做？",
        [
            "掛掉，打卡片背面的電話問銀行",
            "掛掉，自己撥 165 問",
            "打開銀行 App 看帳戶有沒有異常",
        ],
        "B",
        "165 不會打電話叫你轉帳，也沒有「安全帳戶」這種東西。對方冒用的是 165，就掛掉自己撥 165 問最直接；銀行和 App 只看得到你的帳戶，查不了這通電話。",
        legacy_text="有人打電話自稱是「165 反詐騙專線」，說你的帳戶涉及洗錢案件，需要把錢轉到安全帳戶。你會？",
    ),
    _q(
        "pre-atm-04",
        _ATM,
        True,
        "有人打來自稱銀行人員，說你的帳戶被盜用，要你到 ATM 照指示「設定安全防護」，還說不能掛電話。你會怎麼做？",
        ["照指示到 ATM 操作", "先去 ATM 查餘額再說", "掛掉，打卡片背面的電話"],
        "C",
        "ATM 沒有「設定安全防護」這種功能，照做就是把錢轉出去。對方不讓你掛電話，是怕你自己打卡片背面的電話去問。",
        difficulty=2,
        legacy_text="你接到一通電話，對方自稱是購物平台客服，說你的訂單被設為分期付款，需要到 ATM 操作取消。你會？",
    ),
    _q(
        "pre-atm-05",
        _ATM,
        False,
        "你網購下單後，購物 App 通知：「付款方式：信用卡一次付清」，跟你下單時選的一樣。你會怎麼做？",
        ["打給客服改付款設定", "去 ATM 取消付款設定", "確認無誤，不用處理"],
        "C",
        "通知內容和你自己選的一樣，就不需要做任何事。ATM 沒有任何「付款設定」可以改。",
    ),
    _q(
        "pre-atm-06",
        _ATM,
        False,
        "你打信用卡背面的客服電話問分期手續費，客服請你報身分證字號核對身分。你會怎麼做？",
        ["照客服要求核對身分", "立刻掛斷，當作詐騙", "改把資料傳到客服 LINE"],
        "A",
        "是你自己打官方電話過去，客服核對身分是正常流程。要小心的是對方主動打來要你做事。",
    ),
]


def seed_pretest_questions(session: Session) -> None:
    """把前測題庫同步到資料庫(每次啟動都跑,重複執行不會重複新增)。

    依 seed_key 找到就更新;找不到就用 legacy_text 認出舊版那一列並改寫;都沒有才新增。
    舊版只在空表時灌一次,改寫措詞、新增題目都到不了已上線的資料庫。

    舊列就地改寫(沿用 id),pretest_result 的外鍵才不會斷。代價是歷史作答的
    selected_option 會對到新版選項;那張表目前只寫不讀,實際受影響的只有
    部署當下正在作答、用舊題目交卷的人。之後若要讀歷史作答,改題就要換新 seed_key。
    """
    existing = session.exec(select(PretestQuestion)).all()
    by_key = {q.seed_key: q for q in existing if q.seed_key}
    by_text = {q.question_text: q for q in existing if not q.seed_key}
    for data in PRETEST_QUESTIONS:
        fields = {k: v for k, v in data.items() if k != "legacy_text"}
        row = by_key.get(data["seed_key"]) or by_text.get(data["legacy_text"] or "")
        if row is None:
            session.add(PretestQuestion(**fields))
            continue
        for key, value in fields.items():
            setattr(row, key, value)
        session.add(row)
    session.commit()


# 舊配件下架時退回原價，購買紀錄與商品在同一筆交易中刪除。
RETIRED_MASCOT_ITEM_NAMES: list[str] = [
    "防詐警徽",
    "金色盾牌",
    "偵探帽",
    "紅色披風",
    "放大鏡",
    "警報器",
    "寶石項鍊",
    "星星眼鏡",
]

# 只是外觀、不帶收入，價格排在房產之下：每個階段都有可以存錢的目標，又不和買房搶錢。
# 每隻都要有 base／point／cheer／think 四張圖（tests/unit/test_mascot_assets.py 會檢查）。
MASCOT_ITEMS: list[dict[str, str | int]] = [
    {
        "name": "柴犬",
        "category": "mascot",
        "cost": 0,
        "image_url": "/assets/mascot/shiba/base.webp",
    },
    {
        "name": "倉鼠",
        "category": "mascot",
        "cost": 750,
        "image_url": "/assets/mascot/hamster/base.webp",
    },
    {
        "name": "兔子",
        "category": "mascot",
        "cost": 1000,
        "image_url": "/assets/mascot/rabbit/base.webp",
    },
    {
        "name": "貓",
        "category": "mascot",
        "cost": 1500,
        "image_url": "/assets/mascot/cat/base.webp",
    },
    {
        "name": "柯基",
        "category": "mascot",
        "cost": 2000,
        "image_url": "/assets/mascot/corgi/base.webp",
    },
    {
        "name": "企鵝",
        "category": "mascot",
        "cost": 3000,
        "image_url": "/assets/mascot/penguin/base.webp",
    },
    {
        "name": "水獺",
        "category": "mascot",
        "cost": 4000,
        "image_url": "/assets/mascot/otter/base.webp",
    },
    {
        "name": "狐狸",
        "category": "mascot",
        "cost": 5000,
        "image_url": "/assets/mascot/fox/base.webp",
    },
    {
        "name": "小熊貓",
        "category": "mascot",
        "cost": 7500,
        "image_url": "/assets/mascot/red_panda/base.webp",
    },
    {
        "name": "無尾熊",
        "category": "mascot",
        "cost": 10000,
        "image_url": "/assets/mascot/koala/base.webp",
    },
]


def seed_mascot_items(session: Session) -> None:
    """舊配件退款後同步角色；刪除紀錄讓重啟不會再次退款。"""
    existing = session.exec(
        select(MascotItem).order_by(col(MascotItem.id)).with_for_update()
    ).all()
    for item in existing:
        if item.name not in RETIRED_MASCOT_ITEM_NAMES:
            continue
        purchases = session.exec(
            select(UserMascotItem).where(UserMascotItem.item_id == item.id)
        ).all()
        for purchase in purchases:
            user = session.get(User, purchase.user_id)
            if user is not None:
                user = lock_user(session, user)
                adjust_cash(user, item.cost, reason="retired_mascot_refund")
                session.add(user)
            session.delete(purchase)
        # 先刪購買紀錄，避免商品的級聯刪除搶先移除尚未 flush 的列。
        session.flush()
        session.delete(item)
    by_name = {item.name: item for item in existing}
    for data in MASCOT_ITEMS:
        row = by_name.get(str(data["name"]))
        if row is None:
            session.add(MascotItem(**data))
            continue
        for key, value in data.items():
            setattr(row, key, value)
        session.add(row)
    session.commit()
