from sqlmodel import Session, select

from app.models import FraudType, MascotItem, PretestQuestion

PRETEST_QUESTIONS = [
    # ── 投資詐欺 ──
    {
        "fraud_type": FraudType.INVESTMENT.value,
        "question_text": (
            "你在 LINE 群組收到一則訊息：「老師帶單，月報酬 30%，"
            "已有 500 人獲利！」你會怎麼做？"
        ),
        "options": [
            {"key": "A", "text": "加入群組跟單", "is_correct": False},
            {"key": "B", "text": "先投小額試試看", "is_correct": False},
            {"key": "C", "text": "不理會，這很可能是詐騙", "is_correct": True},
        ],
        "explanation": (
            "「保證獲利」和「高報酬」是投資詐騙的典型話術。合法投資不會保證收益。"
        ),
        "difficulty": 1,
    },
    {
        "fraud_type": FraudType.INVESTMENT.value,
        "question_text": (
            "朋友分享他在某平台投資加密貨幣，已小賺了 5 萬元並成功提領。"
            "他推薦你加入。你會？"
        ),
        "options": [
            {"key": "A", "text": "跟著投入，朋友已經賺到了", "is_correct": False},
            {"key": "B", "text": "先查證平台是否有金管會核准", "is_correct": True},
            {"key": "C", "text": "投入但只用閒錢", "is_correct": False},
        ],
        "explanation": (
            "「小額獲利再加碼」是殺豬盤常見手法。先讓你賺小錢建立信任，"
            "再誘導大額投入。務必查證平台合法性。"
        ),
        "difficulty": 2,
    },
    {
        "fraud_type": FraudType.INVESTMENT.value,
        "question_text": (
            "你的銀行理專推薦一檔年化報酬約 4% 的定存方案，並詳細說明風險。這是詐騙嗎？"
        ),
        "options": [
            {"key": "A", "text": "是詐騙，報酬太高了", "is_correct": False},
            {"key": "B", "text": "不是詐騙，這是合法的銀行服務", "is_correct": True},
            {"key": "C", "text": "可能是詐騙，需要再確認", "is_correct": False},
        ],
        "explanation": (
            "銀行理專推薦定存方案並說明風險，是正常的金融服務。"
            "4% 的定存報酬在合理範圍內。"
        ),
        "difficulty": 2,
    },
    # ── 假網路購物 ──
    {
        "fraud_type": FraudType.SHOPPING.value,
        "question_text": (
            "你在 Facebook 看到一頁式廣告，名牌包只要原價一折，僅接受貨到付款。你會？"
        ),
        "options": [
            {"key": "A", "text": "下單，貨到付款很安全", "is_correct": False},
            {
                "key": "B",
                "text": "不買，一頁式廣告加超低價是詐騙特徵",
                "is_correct": True,
            },
            {"key": "C", "text": "先買再說，不滿意可以退", "is_correct": False},
        ],
        "explanation": (
            "一頁式廣告 + 超低價 + 僅貨到付款，是假購物詐騙三大特徵。"
            "收到的通常是仿冒品或空盒。"
        ),
        "difficulty": 1,
    },
    {
        "fraud_type": FraudType.SHOPPING.value,
        "question_text": (
            "你在 momo 購物網的官方 App 上看到一款電視特價 6 折，"
            "並標示「品牌直送、七天鑑賞」。這是詐騙嗎？"
        ),
        "options": [
            {"key": "A", "text": "是詐騙，折扣太多了", "is_correct": False},
            {
                "key": "B",
                "text": "不是詐騙，這是正規購物平台的促銷",
                "is_correct": True,
            },
            {"key": "C", "text": "可能是詐騙，需要打電話確認", "is_correct": False},
        ],
        "explanation": ("momo 是合法購物平台，在官方 App 內的特價活動是正常促銷行為。"),
        "difficulty": 2,
    },
    {
        "fraud_type": FraudType.SHOPPING.value,
        "question_text": (
            "你接到一通電話，對方自稱是購物平台客服，說你的訂單被設為分期付款，"
            "需要到 ATM 操作取消。你會？"
        ),
        "options": [
            {"key": "A", "text": "照指示去 ATM 操作", "is_correct": False},
            {"key": "B", "text": "掛電話，自行登入平台確認訂單", "is_correct": True},
            {"key": "C", "text": "請對方提供員工編號再決定", "is_correct": False},
        ],
        "explanation": (
            "「誤設分期付款需到 ATM 操作」是經典的解除分期詐騙。"
            "正規平台不會要求你到 ATM 操作。"
        ),
        "difficulty": 1,
    },
    # ── 偽稱買賣 ──
    {
        "fraud_type": FraudType.FAKE_SALE.value,
        "question_text": (
            "你在蝦皮看到一台 iPhone 只要市價五折，賣家說「搬家急售」"
            "並要求加 LINE 私下交易。你會？"
        ),
        "options": [
            {"key": "A", "text": "加 LINE 議價，看起來很划算", "is_correct": False},
            {
                "key": "B",
                "text": "不買，低於市價太多且要求平台外交易是警訊",
                "is_correct": True,
            },
            {"key": "C", "text": "請賣家提供更多照片再決定", "is_correct": False},
        ],
        "explanation": (
            "超低價 + 要求脫離平台私下交易，是假賣家的典型手法。"
            "脫離平台後買家失去保障。"
        ),
        "difficulty": 1,
    },
    {
        "fraud_type": FraudType.FAKE_SALE.value,
        "question_text": (
            "你在正規拍賣平台賣二手相機，買家透過平台下單"
            "並使用平台的安全交易機制付款。這是正常交易嗎？"
        ),
        "options": [
            {"key": "A", "text": "不正常，可能是詐騙", "is_correct": False},
            {
                "key": "B",
                "text": "正常，使用平台安全交易機制是安全的",
                "is_correct": True,
            },
            {"key": "C", "text": "要再觀察買家的行為", "is_correct": False},
        ],
        "explanation": (
            "透過正規平台的安全交易機制進行買賣是正常的，平台會提供買賣雙方的保障。"
        ),
        "difficulty": 2,
    },
    {
        "fraud_type": FraudType.FAKE_SALE.value,
        "question_text": (
            "你賣東西時，買家傳了一個連結說是「付款確認頁面」，"
            "要你點進去填寫銀行帳號以接收款項。你會？"
        ),
        "options": [
            {"key": "A", "text": "點進去填寫，趕快完成交易", "is_correct": False},
            {"key": "B", "text": "不點，這是釣魚連結的典型手法", "is_correct": True},
            {"key": "C", "text": "先問朋友這個連結是否安全", "is_correct": False},
        ],
        "explanation": (
            "買家傳「付款確認連結」要求填寫銀行資料，是假買家的釣魚手法。"
            "正規交易不需要點擊外部連結。"
        ),
        "difficulty": 1,
    },
    # ── 假愛情交友 ──
    {
        "fraud_type": FraudType.ROMANCE.value,
        "question_text": (
            "你在交友 App 上認識一位自稱在海外當軍醫的對象，"
            "交往兩個月後對方說需要 5 萬元才能回國見你。你會？"
        ),
        "options": [
            {"key": "A", "text": "匯款，幫助對方回國", "is_correct": False},
            {
                "key": "B",
                "text": "拒絕匯款，這是感情詐騙的典型手法",
                "is_correct": True,
            },
            {"key": "C", "text": "先匯一半看對方是否真的回來", "is_correct": False},
        ],
        "explanation": (
            "「海外軍人/醫生 + 需要錢才能回國」是假愛情詐騙的經典劇本。"
            "真正的軍人不需要對象匯機票錢。"
        ),
        "difficulty": 1,
    },
    {
        "fraud_type": FraudType.ROMANCE.value,
        "question_text": (
            "你透過朋友介紹認識一位新朋友，見過幾次面後"
            "對方邀你一起參加社區志工活動。這是詐騙嗎？"
        ),
        "options": [
            {"key": "A", "text": "是詐騙，要小心", "is_correct": False},
            {"key": "B", "text": "不是詐騙，這是正常的社交互動", "is_correct": True},
            {"key": "C", "text": "先觀察再說", "is_correct": False},
        ],
        "explanation": (
            "透過朋友介紹認識並面對面互動的社交活動是正常的，"
            "沒有金錢要求也沒有詐騙跡象。"
        ),
        "difficulty": 2,
    },
    {
        "fraud_type": FraudType.ROMANCE.value,
        "question_text": (
            "網路上認識三個月的對象突然說家人住院需要醫藥費，"
            "希望你借 10 萬元，並保證下個月還。你會？"
        ),
        "options": [
            {"key": "A", "text": "借錢，對方一定很需要幫助", "is_correct": False},
            {
                "key": "B",
                "text": "婉拒，未見過面就要求大筆借款是詐騙警訊",
                "is_correct": True,
            },
            {"key": "C", "text": "先借一部分表示心意", "is_correct": False},
        ],
        "explanation": (
            "「假急難」是感情詐騙的常見手法。從未見過面就要求借大筆款項，極可能是詐騙。"
        ),
        "difficulty": 1,
    },
    # ── 解除分期付款（ATM） ──
    {
        "fraud_type": FraudType.ATM.value,
        "question_text": (
            "你接到電話，對方準確說出你上週在網路上買的東西和金額，"
            "並說系統出錯要幫你退款。你會？"
        ),
        "options": [
            {
                "key": "A",
                "text": "配合操作，對方知道我的訂單應該是真的客服",
                "is_correct": False,
            },
            {
                "key": "B",
                "text": "掛電話，個資外洩不代表對方是真客服",
                "is_correct": True,
            },
            {"key": "C", "text": "請對方稍等，自己去查訂單", "is_correct": False},
        ],
        "explanation": (
            "詐騙者常透過外洩的個資取得你的購物紀錄來建立信任。"
            "知道你的訂單不代表是真客服，應掛電話自行查證。"
        ),
        "difficulty": 2,
    },
    {
        "fraud_type": FraudType.ATM.value,
        "question_text": (
            "銀行官方 App 推播通知你有一筆信用卡消費異常，"
            "要你進入 App 確認。這是詐騙嗎？"
        ),
        "options": [
            {"key": "A", "text": "是詐騙，不要點", "is_correct": False},
            {
                "key": "B",
                "text": "不是詐騙，銀行 App 的推播通知是正常功能",
                "is_correct": True,
            },
            {"key": "C", "text": "先打電話給銀行確認", "is_correct": False},
        ],
        "explanation": (
            "銀行官方 App 的推播通知是正常的風控功能，"
            "透過 App 內確認交易是安全的操作方式。"
        ),
        "difficulty": 2,
    },
    {
        "fraud_type": FraudType.ATM.value,
        "question_text": (
            "有人打電話自稱是「165 反詐騙專線」，說你的帳戶涉及洗錢案件，"
            "需要把錢轉到安全帳戶。你會？"
        ),
        "options": [
            {"key": "A", "text": "照做，165 是政府機構應該可信", "is_correct": False},
            {
                "key": "B",
                "text": "掛電話，165 不會主動打來要求轉帳",
                "is_correct": True,
            },
            {"key": "C", "text": "先確認對方身份再決定", "is_correct": False},
        ],
        "explanation": (
            "165 反詐騙專線不會主動致電要求轉帳到「安全帳戶」。"
            "世界上不存在「安全帳戶」這種東西。"
        ),
        "difficulty": 1,
    },
]


def seed_pretest_questions(session: Session) -> None:
    """若題庫為空，插入預設前測題目。"""
    existing = session.exec(select(PretestQuestion).limit(1)).first()
    if existing:
        return

    for q_data in PRETEST_QUESTIONS:
        question = PretestQuestion(**q_data)
        session.add(question)
    session.commit()


MASCOT_ITEMS = [
    {
        "name": "防詐警徽",
        "category": "徽章",
        "cost": 50,
        "emoji": "🔰",
        "description": "新手防詐達人的起步徽章",
    },
    {
        "name": "金色盾牌",
        "category": "徽章",
        "cost": 150,
        "emoji": "🛡️",
        "description": "進階防詐衛士的榮譽徽章",
    },
    {
        "name": "偵探帽",
        "category": "帽子",
        "cost": 100,
        "emoji": "🎩",
        "description": "頂尖詐騙偵探的標配",
    },
    {
        "name": "紅色披風",
        "category": "披風",
        "cost": 200,
        "emoji": "🦸",
        "description": "正義使者的象徵",
    },
    {
        "name": "放大鏡",
        "category": "道具",
        "cost": 75,
        "emoji": "🔍",
        "description": "用來識破詐騙話術的神器",
    },
    {
        "name": "警報器",
        "category": "道具",
        "cost": 120,
        "emoji": "🚨",
        "description": "遇到可疑訊息時的警報裝置",
    },
    {
        "name": "寶石項鍊",
        "category": "飾品",
        "cost": 250,
        "emoji": "💎",
        "description": "頂級防詐大師的專屬飾品",
    },
    {
        "name": "星星眼鏡",
        "category": "飾品",
        "cost": 80,
        "emoji": "⭐",
        "description": "看穿謊言的魔法眼鏡",
    },
]


def seed_mascot_items(session: Session) -> None:
    """若裝飾品表為空，插入預設裝飾品。"""
    existing = session.exec(select(MascotItem).limit(1)).first()
    if existing:
        return

    for item_data in MASCOT_ITEMS:
        item = MascotItem(**item_data)
        session.add(item)
    session.commit()
