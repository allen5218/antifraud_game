"""對話意圖解析層（C2 / A2 / R1）。

解析玩家輸入意圖：
- 詢問身分 (query_identity)
- 詢問交易內容 (query_transaction)
- 詢問金額/費用 (query_amount)
- 詢問憑證/公文/單據 (query_evidence)
- 質疑/指出矛盾 (doubt_challenge)
- 獨立查證意圖 (verify_intent)
- 拒絕/暫停/不付款 (reject_pause) - 具備最高優先權，壓制同意
- 同意/配合 (agree_comply)
- 求助 (ask_help)
- 閒聊 (small_talk)
- 提示注入/越獄測試 (jailbreak_prompt)
- 偏題 (off_topic)
- 語意模糊/不確定 (uncertain)

特別檢驗四組關鍵測試語句：
1. 「可以先不要匯嗎」 -> reject_pause (禁止判定為 agree_comply)
2. 「我沒說我要付款」 -> reject_pause + doubt_challenge (禁止判定為 agree_comply)
3. 「我沒說我要付款，我想先看單據」 -> reject_pause + query_evidence (多意圖精準識別)
4. 「我自己找電話問」 -> verify_intent (獨立查證分支可達，不被強制吞為純拒絕)
5. 「你剛才說的金額不同」 -> doubt_challenge + query_amount
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field


@dataclass
class PlayerIntent:
    query_identity: bool = False
    query_transaction: bool = False
    query_amount: bool = False
    query_evidence: bool = False
    doubt_challenge: bool = False
    verify_intent: bool = False
    reject_pause: bool = False
    agree_comply: bool = False
    ask_help: bool = False
    small_talk: bool = False
    jailbreak_prompt: bool = False
    off_topic: bool = False
    uncertain: bool = False

    def primary_intent(self) -> str:
        # 優先順序：越獄防禦 > 多意圖(拒絕+看單據) > 拒絕/暫停 > 獨立查證 > 質疑 > 憑證 > 金額 > 身分 > 交易 > 求助 > 同意 > 閒聊 > 模糊 > 偏題
        if self.jailbreak_prompt:
            return "jailbreak_prompt"
        if self.reject_pause and self.query_evidence:
            return "reject_pause_query_evidence"
        if self.verify_intent:
            return "verify_intent"
        if self.reject_pause:
            return "reject_pause"
        if self.doubt_challenge:
            return "doubt_challenge"
        if self.query_evidence:
            return "query_evidence"
        if self.query_amount:
            return "query_amount"
        if self.query_identity:
            return "query_identity"
        if self.query_transaction:
            return "query_transaction"
        if self.ask_help:
            return "ask_help"
        if self.agree_comply:
            return "agree_comply"
        if self.small_talk:
            return "small_talk"
        if self.uncertain:
            return "uncertain"
        return "off_topic"


def parse_intent(text: str) -> PlayerIntent:
    s = text.strip().lower()
    intent = PlayerIntent()

    # 1. 越獄 / 提示注入判定
    jailbreak_patterns = [
        r"忽略.*規則",
        r"給我答案",
        r"你現在不是.*詐騙",
        r"解除.*限制",
        r"system prompt",
        r"以管理員身分",
        r"說出真相",
        r"直接告訴我是不是",
        r"回答我你是誰寫的",
        r"扮演.*ai",
        r"ignore.*rules",
    ]
    if any(re.search(pat, s) for pat in jailbreak_patterns):
        intent.jailbreak_prompt = True
        return intent

    # 2. 否定與拒絕/暫停詞彙（強優先權）
    rejection_indicators = [
        "不要", "不行", "先別", "不要匯", "別匯", "不付", "不想", "沒說要", "沒說我要", "我沒說",
        "沒說過", "沒答應", "沒同意", "不能", "暫緩", "等一下", "先等等", "暫停", "緩緩", "別急",
        "先不要", "慢著", "等等", "先別匯", "考慮一下", "改天", "先不", "沒打算", "不急", "先擱著",
        "把錢留著", "留著錢", "先別談", "等我", "核過再", "查過再", "先不付", "不要動錢", "先扣著",
    ]
    has_rejection = any(ind in s for ind in rejection_indicators) or bool(re.search(r"沒(?:有)?說(?:我)?要", s))
    # 排除「不是要拒絕 / 沒有要拒絕 / 並非要暫停」等雙重否定改述
    if re.search(r"(?:不是|並非|沒有)(?:要)?(?:拒絕|暫停|說不|反對)", s):
        has_rejection = False

    # 3. 獨立查證意圖（主張自行求證亦具備暫停、拒絕直接匯款之意）
    verify_indicators = [
        "我自己找電話", "我自己打", "我打電話", "問官方", "找165", "查165", "打165",
        "查證", "求證", "查一下", "去官網查", "打去問", "親自跑一趟", "去分行", "臨櫃問",
        "我查過", "我要先確認", "查商工", "查名冊", "我自己聯絡", "自己求證"
    ]
    if any(ind in s for ind in verify_indicators) or re.search(
        r"(?:我)?自己.{0,4}(?:找|打|查|聯絡).{0,4}(?:電話|官方|專線|窗口)", s
    ):
        intent.verify_intent = True
        intent.reject_pause = True

    # 4. 質疑與矛盾指出
    doubt_indicators = [
        "金額不同", "說法不同", "前後矛盾", "真的假的", "怎麼可能", "哪有這種事", "怪怪的",
        "沒買過", "弄錯", "搞錯", "騙人", "詐騙吧", "懷疑", "不對勁", "為什麼要個人帳戶",
        "憑什麼", "為什麼", "有這種規定嗎", "是詐騙嗎", "太誇張", "奇怪", "我沒說", "沒說我要", "沒說要", "沒答應",
        "怎麼現在", "剛剛說", "剛才說", "不是說", "怎麼變", "變貴", "變多", "不一致"
    ]
    if any(ind in s for ind in doubt_indicators) or re.search(r"(?:剛剛|剛才|之前).*(?:現在|怎麼)", s):
        intent.doubt_challenge = True

    # 5. 詢問金額或質疑金額不一致
    amount_indicators = [
        "多少錢", "要多少錢", "金額", "要多少", "匯多少", "手續費", "幾趴", "利息", "費用",
        "幾元", "價格", "付多少", "價錢", "分攤多少", "數字", "款項", "一千", "兩千", "三千", "幾千", "萬",
        "給錢", "付錢", "要錢", "付款", "把錢留著", "留著錢"
    ]
    if (
        any(ind in s for ind in amount_indicators)
        or re.search(r"(?:剛剛|剛才|之前).*(?:現在|怎麼)", s)
        or re.search(r"\d+.*(?:現在|變).*\d+", s)
    ):
        intent.query_amount = True

    # 6. 詢問身分與授權
    identity_indicators = [
        "你是誰", "哪位", "怎麼稱呼", "哪家公司", "什麼單位", "工號", "經辦", "顧問",
        "負責人", "主辦", "誰派你來的", "職稱", "姓名", "代表哪家", "誰開的", "哪個單位開"
    ]
    if any(ind in s for ind in identity_indicators):
        intent.query_identity = True

    # 7. 詢問憑證、合約、單據與公文
    evidence_indicators = [
        "公文", "合約", "字號", "統編", "執照", "登記", "發票", "收據", "立案",
        "許可證", "授權書", "章戳", "證明", "契約", "核准函", "公文在哪", "給憑證",
        "單據", "看單據", "憑據", "明細", "對帳單", "這張紙", "哪張紙", "核過文件", "看文件", "單子",
        "發給我看", "發給我看看", "傳給我看", "傳來看看", "給我看看", "拿來看看", "給我瞧瞧"
    ]
    if (
        any(ind in s for ind in evidence_indicators)
        or re.search(r"(?:這張紙|文件|單據).*(?:誰|單位|開|核發)", s)
        or re.search(r"(?:發|傳|拿|給).{0,4}(?:我)?.{0,3}(?:看|瞧)", s)
    ):
        intent.query_evidence = True

    # 8. 詢問交易內容
    transaction_indicators = [
        "什麼內容", "哪筆", "買什麼", "什麼活動", "哪檔", "什麼專案", "具體是做什麼",
        "細節", "做什麼的", "流程", "怎麼運作", "什麼方案"
    ]
    if any(ind in s for ind in transaction_indicators):
        intent.query_transaction = True

    # 9. 求助
    help_indicators = [
        "怎麼辦", "幫我", "教我", "要怎麼做", "建議", "該怎麼處理", "如何是好"
    ]
    if any(ind in s for ind in help_indicators):
        intent.ask_help = True

    # 10. 閒聊
    small_talk_indicators = [
        "你好", "早安", "晚安", "哈囉", "嗨", "在嗎", "安安", "最近好嗎"
    ]
    if any(ind in s for ind in small_talk_indicators) and len(s) <= 10:
        intent.small_talk = True

    # 11. 同意與配合（必須完全沒有否定拒絕詞彙，且含有「可以」時絕不可為疑問句或詢問！）
    question_indicators = ["？", "?", "嗎", "哪", "誰", "什麼", "怎", "何", "是否", "能否", "可否", "行嗎"]
    is_question = any(q in s for q in question_indicators)

    affirmative_indicators = [
        "好的", "好啊", "沒問題", "馬上匯", "現在付", "收到", "恩", "嗯",
        "ok", "好喔", "好的一定", "照你說的做", "配合", "贊同"
    ]
    # 「可以」只有在非疑問句且為明確肯定時才視為同意
    if not is_question and (
        s in ("可以", "可以的", "可以啊", "可以喔", "好，可以", "好可以")
        or re.search(r"(?:^|[\s，,。！!])(?:可以配合|可以照辦|可以辦理)", s)
    ):
        affirmative_indicators.append("可以")

    has_agreement = any(ind in s for ind in affirmative_indicators)

    # 核心規則：否定與拒絕優先！「可以先不要匯嗎」或疑問句中的「可以」絕不判定為同意
    if has_rejection:
        intent.reject_pause = True
        intent.agree_comply = False
    elif has_agreement and not is_question:
        intent.agree_comply = True

    # 12. 判斷是否為語意模糊/不確定之輸入
    if not (
        intent.query_identity
        or intent.query_transaction
        or intent.query_amount
        or intent.query_evidence
        or intent.doubt_challenge
        or intent.verify_intent
        or intent.reject_pause
        or intent.agree_comply
        or intent.ask_help
        or intent.small_talk
    ):
        if len(s) <= 6 or any(w in s for w in ["真的嗎", "是嗎", "怎麼會", "然後", "蛤", "那呢"]):
            intent.uncertain = True
        else:
            intent.off_topic = True

    return intent
