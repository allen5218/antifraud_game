"""情境對話 RAG (Retrieval-Augmented Generation) 知識檢索與反制引擎。

核心職責：
1. 建立涵蓋 5 大詐騙類型（投資、假網拍、解除分期、購物、交友）之破綻話術庫、抗辯劇本庫、心理反打策略與主管機關查證知識。
2. 以 BM25 / TF-IDF 與語意標籤為基礎之語意檢索器（Semantic Retriever），即時比對玩家發送之詞彙、疑點、執照質疑與工具查驗結果。
3. 知識增強生成器（Augmented Generator）：精準對齊玩家所說的具體詞彙（如金管會執照、營業字號、釣魚網址、165通報、個人戶頭、面交），
   生成緊扣脈絡且符合騙子/合規角色人格的極致真實回應，並支援將檢索脈絡無縫注入大語言模型（Gemini）。
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from app.scenario.evidence import FACTS_MAP


@dataclass(frozen=True)
class KnowledgeChunk:
    id: str
    category: str  # investment, shopping, fake-sale, romance, atm
    role: str      # scam, legit
    topic: str     # license, money, meet, police_165, order, account, urgency, identity
    keywords: list[str]
    context_fact: str
    tactics: list[str]
    rebuttal_responses: list[str]


# ── RAG 專業話術與反制知識庫 ──────────────────────────────────────────────────
KNOWLEDGE_BASE: list[KnowledgeChunk] = [
    # ── 1. 投資詐欺 (investment) ──
    KnowledgeChunk(
        id="inv_scam_license_denial",
        category="investment",
        role="scam",
        topic="license",
        keywords=[
            "金管會", "執照", "登記", "營業字號", "特許", "證券期貨局", "證期局", "投顧",
            "核准", "查無", "合法", "牌照", "立案", "監管", "公會", "統編", "商工登記"
        ],
        context_fact="金管會證期局查無特許執照；宏盛資本宣稱受海外開曼與塞浦路斯離岸監管以規避境內稽查。",
        tactics=["authority", "time_pressure"],
        rebuttal_responses=[
            "您去查台灣金管會名冊當然查不到！我們宏盛資本走的是開曼群島頂級離岸對沖私募基金結構，受塞浦路斯 CySEC 離岸監管，根本不受台灣境內繁瑣法規限制。台灣一般投顧怎麼可能拿到日化 15% 的內線額度？名額只保留到下午 3:30 前，您如果一直懷疑沒魄力，我現在就把這席位讓給排隊候補的學員了！",
            "內線私募走的是境外專用機構代操通道，台灣證期局名冊上只會有那些賺不到 5% 通膨的平庸券商。我們操盤團隊受海外離岸信託基金監管，合約具備國際仲裁效力。VIP 席位只剩最後一位，您若要因為查境內名冊而放棄翻倍機會，我也只能尊重。",
        ],
    ),
    KnowledgeChunk(
        id="inv_scam_personal_account",
        category="investment",
        role="scam",
        topic="account",
        keywords=[
            "個人戶頭", "人頭戶", "帳號", "人頭", "為什麼是個人", "私人口座", "受款人", "指定帳戶",
            "匯到哪", "轉帳帳號", "匯款帳號", "約定帳號", "特別戶頭", "入金帳戶"
        ],
        context_fact="要求匯款至個人戶頭，狡辯為跨國券商在台特約結算代收專員通道。",
        tactics=["authority", "greed"],
        rebuttal_responses=[
            "那是我們合作券商在台灣的『授權結算代收專用通道』！因為國際外匯申報上限管制，大額私募進場必須透過境內特約子帳戶進行資金集中造冊，完成建倉後系統會直接把額度全數撥入您的專屬交易子帳號，群裡幾百位學員每週出金都是走這套合規結算路徑！",
            "您放心，這是特約信託監管代收人名額，每一筆入金都有系統即時金流序號與保本憑證核對，絕非私人帳號，只要您完成約定轉帳截圖回傳，老師馬上替您啟用首期對沖保證權益！",
        ],
    ),
    KnowledgeChunk(
        id="inv_scam_guaranteed_profit",
        category="investment",
        role="scam",
        topic="profit",
        keywords=[
            "保證獲利", "穩賺", "保本", "零風險", "違法", "不可能", "投報率", "幾趴", "利息",
            "獲利幾趴", "賺多少", "怎麼保證", "天上掉餡餅", "騙局"
        ],
        context_fact="標榜高額保證獲利與零風險保本，以量化對沖套利與假合約掩飾違法吸金本質。",
        tactics=["greed", "social_proof"],
        rebuttal_responses=[
            "市面上的普通散戶投資當然不敢喊保證，但我們團隊採用的是全球高頻量化跨市場期現套利！我們鎖定的是買賣價差與瞬時造市利差，無論大盤漲跌都能保持日均 12%~15% 的無風險淨收益，合約內直接附帶第三方資金保本承諾！",
            "群裡每天上傳的都是學員真實出金入帳的網銀截圖！我們過去三年在國際市場的勝率高達 94.8%，若沒有這樣的底氣，怎麼可能吸引上千位高資產學員長期追隨？",
        ],
    ),
    KnowledgeChunk(
        id="inv_scam_meet_offline",
        category="investment",
        role="scam",
        topic="meet",
        keywords=["面交", "簽約", "見面", "實體門市", "臨櫃", "公司地址", "公司在哪", "辦公室", "去你們公司"],
        context_fact="拒絕線下接觸與面交簽約，藉口大戶隱私與跨國操盤保密條款。",
        tactics=["authority", "trust_building"],
        rebuttal_responses=[
            "我們是封閉式私人操盤機構，涉及多位上市櫃政商大戶的持倉機密，依跨國保密協定嚴格禁止任何線下公開接觸！所有資金交易與法規清算全部在雲端金融安全通道完成，這才是頂級對沖圈的運作常態。",
            "若要線下面對面諮詢，依合約規定最低資產門檻需達新台幣 2,000 萬元並經由海外董事會審核。線上體驗名額是老師特別開放給一般學員的福利，請把握這難得的破格機會！",
        ],
    ),
    KnowledgeChunk(
        id="inv_scam_police_165",
        category="investment",
        role="scam",
        topic="police_165",
        keywords=["165", "警察", "報警", "詐騙", "被騙", "黑名單", "受害", "165反詐騙", "報案"],
        context_fact="遭 165 通報為高風險，狡辯為同業惡意檢舉競爭與黑函抹黑。",
        tactics=["authority", "fear"],
        rebuttal_responses=[
            "165 那種大眾通報系統只要被少數同行惡意檢舉就會上榜！我們團隊績效太好，經常遭到傳統平庸券商動員網軍惡意抹黑。我們幾百位學員每天都能自由全額提領獲利，如果真是詐騙，我們怎麼可能還能在線上公開帶單？請您相信親眼所見的真實績效！",
            "您如果因為未經查證的網路流言而錯過主力建倉時機，損失的是您自己的資產翻倍機會！我們每一筆出金都有完整清算明細，您若心存疑慮，可以先用三萬元小額體驗一次出金流程！",
        ],
    ),
    KnowledgeChunk(
        id="inv_legit_credentials",
        category="investment",
        role="legit",
        topic="license",
        keywords=["金管會", "執照", "登記", "核准", "合法", "營業字號", "證照", "手續費"],
        context_fact="合法金融從業人員具有金管會合格登錄字號，主動揭露公開說明書並強調無保證獲利。",
        tactics=["trust_building"],
        rebuttal_responses=[
            "您好！本行理財專員均具備合格證券投顧與信託從業證照，登錄字號均可在金管會證期局網站公開查驗。金融法規嚴格規定不得宣稱『保證獲利』或『零風險』，本行所有架上產品均備有正式公開說明書，請您務必詳閱風險評估。",
            "感謝您的謹慎查驗！合規金融交易絕不會要求客戶匯款至個人或不明私人帳戶，所有申購手續均由您本人名下之同名交割帳戶扣繳，保障完全透明且受台灣法律保護。",
        ],
    ),

    # ── 2. 假拍賣與購物詐欺 (fake-sale, shopping) ──
    KnowledgeChunk(
        id="shop_scam_fake_system_error",
        category="fake-sale",
        role="scam",
        topic="order",
        keywords=[
            "沒買", "沒下單", "查無訂單", "後台沒紀錄", "後台", "訂單", "沒這筆", "搞錯", "什麼商品",
            "買什麼", "哪一筆", "賣家後台"
        ],
        context_fact="買家宣稱已付款但賣家後台無紀錄，詐稱賣家未簽署誠信保證協定導致款項凍結中繼站。",
        tactics=["authority", "time_pressure"],
        rebuttal_responses=[
            "因為您尚未完成我們拍賣平台的『賣家誠信擔保協定』簽署！金流系統為了保護雙方價金，已自動將我的結帳款項 $28,500 暫扣在官方安全中繼帳戶，您後台當然還看不到已撥款！必須透過客服傳送的安全認證通道完成授權，訂單才會即時同步顯現！",
            "我這邊扣款通知跟結帳訂單編號都已經產生了！平台客服剛才警告說，如果賣家在 15 分鐘內未完成賣場金流協議綁定，將會判定為惡意詐領，我的銀行會直接通報凍結您的賣場！請您快點點擊認證專區完成驗證！",
        ],
    ),
    KnowledgeChunk(
        id="shop_scam_phishing_link",
        category="fake-sale",
        role="scam",
        topic="license",
        keywords=[
            "釣魚", "網址", "twnic", "不是官方", "假網址", "域名", "境外", "假的", "外部連結",
            "連結", "怪怪的", "為什麼不是官網"
        ],
        context_fact="提供仿冒釣魚認證網址，狡辯為雙十一高負載專用跨境 SSL 加密備援站點。",
        tactics=["authority", "fear"],
        rebuttal_responses=[
            "那是因為雙十一與例行金流結算流量過大，平台工程部啟用的『跨境負載均衡 SSL 專用鏡像站點』！完全通過國際 VeriSign 256 位元金融安全認證，專門處理即時協議簽署與退款審核，絕非普通一般外部網址，請您立即點擊完成綁定！",
            "您放心，此連結直通官方金流驗證中樞，只要您在安全頁面輸入手機與身分核對碼，系統便會自動簽發核銷憑證，10 分鐘內解除您賣場的一切限制並立即放行訂單款項！",
        ],
    ),
    KnowledgeChunk(
        id="shop_scam_order_amount",
        category="shopping",
        role="scam",
        topic="money",
        keywords=["多少錢", "金額", "多少", "扣款", "重複扣款", "分期", "12期", "手續費", "費用"],
        context_fact="謊稱訂單條碼誤刷設定為連續 12 期自動扣款，需依指示操作撤銷。",
        tactics=["time_pressure", "fear"],
        rebuttal_responses=[
            "您的訂單總額是新台幣 2,980 元，但因為超商條碼掃描時系統發生雙重入帳異常，後台誤將您的款項設定為『每個月固定自網銀扣款 2,980 元，連續扣款 12 期』！若今晚 12 點前未完成跨行撤銷授權，銀行結算中心就會自動扣除第一期款項！",
            "我們客服專員也是緊急加班協助您處理，這筆重複分期扣款若不及時在線上金流終端註銷，日後要向總公司申訴退款手續繁瑣且需耗時三個月，請您務必配合現在完成撤銷核銷！",
        ],
    ),
    KnowledgeChunk(
        id="shop_legit_protection",
        category="shopping",
        role="legit",
        topic="order",
        keywords=["訂單", "發票", "退貨", "統編", "查驗", "金流", "詐騙", "官方"],
        context_fact="合法電商透過站內系統保障履約，絕不要求私下加 LINE 或提供金融驗證碼。",
        tactics=["trust_building"],
        rebuttal_responses=[
            "您好！官方商城所有交易均開立財政部電子發票，且所有訂單進度、退換貨與款項處理一律於平台 App 內操作完成。官方客服絕不會要求您加 LINE、點擊外部未知連結或指示操作網銀退款，請安心在平台站內查閱即可！",
            "感謝您的細心！如您發現任何異常簡訊或自稱商城客服之外部來電，請切勿點擊其提供之外部網址，您可隨時至商城『幫助中心』提交線上客服工單，我們將由專責人員為您守護交易安全。",
        ],
    ),

    # ── 3. 交友愛情與殺豬盤 (romance) ──
    KnowledgeChunk(
        id="rom_scam_customs_fee",
        category="romance",
        role="scam",
        topic="account",
        keywords=[
            "海關", "保證金", "外匯", "包裹", "代墊", "借錢", "匯款", "寄送", "黃金", "獎金",
            "扣留", "清關", "代收"
        ],
        context_fact="藉口高額海外外匯或貴重禮品遭海關扣押，以深厚感情為籌碼情感勒索要求代墊手續費。",
        tactics=["trust_building", "greed", "time_pressure"],
        rebuttal_responses=[
            "親愛的，這箱包裹裡裝著我這五年在外海探勘所攢下的全部外幣存單與我們未來在台灣置產的創業資金！海關說因為涉及大額跨國資產申報，必須有一位直系親屬或配偶擔保人代繳清關規費 $65,000。我現在人在外海鑽油平台根本無法使用個人網銀，除了你我真的不知道還能信任誰了！",
            "只要你幫我這一次墊付清關保證金，等下週包裹放行到了台北，裡面的資金全部由你保管！我愛你，我的一切未來都寄託在你身上了，你忍心看著我們一輩子的幸福毀在這最後一哩路嗎？",
        ],
    ),
    KnowledgeChunk(
        id="rom_scam_video_call_refusal",
        category="romance",
        role="scam",
        topic="meet",
        keywords=["視訊", "電話", "照片", "見面", "打電話", "開鏡頭", "通話", "聲音", "本尊"],
        context_fact="拒絕視訊與見面，藉口軍事基地、外海鑽井平台訊號管制或國防保密條約。",
        tactics=["trust_building", "authority"],
        rebuttal_responses=[
            "我也多麼渴望能看見你的笑容！但我們這座深海鑽探基地屬於中東跨國能源管制特區，出於防恐與商業防諜條約，所有工作人員的智慧型手機鏡頭全部貼上了防拆封條，頻寬也受到嚴格監聽限制，根本無法開啟雙向視訊串流！",
            "請你再等等我，再過 45 天我的駐外合約就圓滿結束了。到時候我會帶著所有的積蓄搭機直飛桃園機場，親手把戒指戴在你的手上，好嗎？",
        ],
    ),

    # ── 4. 假檢警與司法監管 (atm, authority) ──
    KnowledgeChunk(
        id="atm_scam_subpoena_threat",
        category="atm",
        role="scam",
        topic="license",
        keywords=[
            "公文", "地檢署", "檢察官", "刑事", "警察", "133條", "洗錢", "拘票", "傳票", "分行",
            "監管帳戶", "清查", "監管"
        ],
        context_fact="冒充特偵檢察官出示假公文，恐嚇涉入跨國特大洗錢案，威脅凍結名下所有財產。",
        tactics=["authority", "fear", "time_pressure"],
        rebuttal_responses=[
            "這裡是新北地檢署特偵指揮中心！刑事訴訟法第 133 條之規定清楚明瞭，主嫌張宏圖名下查扣的地下洗錢人頭帳戶就是用您的身分證號開立！若您在今天下午三點前未配合司法專案清查，本庭將直接簽發拘票將您列為共犯收押禁見，並依法凍結您在各金融機構名下的全部動產與不動產！",
            "現在全案依法進入『偵查不公開』程序，不得洩漏給任何第三方包括家人或行員！您現在必須立刻開啟通話保持連線，前往鄰近金融機構或透過網銀將可疑資金全數轉入國家金融安全公證帳戶進行金流比對，查明清白後 24 小時內連同結案證明全數發還！",
        ],
    ),
    KnowledgeChunk(
        id="atm_scam_refuse_165",
        category="atm",
        role="scam",
        topic="police_165",
        keywords=["165", "律師", "親自去地檢署", "去派出所", "臨櫃問", "查問", "求證", "打165"],
        context_fact="嚴禁撥打 165 或臨櫃查核，以妨害司法公正與洩密重罪威嚇受害者。",
        tactics=["fear", "authority"],
        rebuttal_responses=[
            "荒唐！165 只是警政署的民意諮詢接線外包窗口，根本無權調閱高檢署特偵核心公文！你現在擅自向外界洩漏案情，已經構成刑法第 132 條洩漏國防以外秘密罪，最重可處三年有期徒刑！地檢署執法人員當前正與你依法通話，你竟敢輕信民間客服延誤司法調查？",
            "若你要親自前往地檢署，現在立刻派法警前往您戶籍地實施強制拘提！您只要敢掛斷電話或向銀行櫃員走漏半點風聲，檢察官將立刻視同畏罪潛逃，請您切莫自誤前程！",
        ],
    ),
]


class ScenarioRagEngine:
    """高效語意檢索與上下文知識增強生成器。"""

    def __init__(self, corpus: list[KnowledgeChunk] | None = None) -> None:
        self.corpus = corpus or KNOWLEDGE_BASE

    def retrieve(
        self,
        fraud_type: str,
        persona_role: str,
        player_text: str,
        unlocked_evidence: list[str] | None = None,
    ) -> tuple[KnowledgeChunk | None, float]:
        """檢索與玩家輸入或已解鎖證據最相關之反制知識塊。"""
        tokens = self._tokenize(player_text)
        evidence_tokens: set[str] = set()
        if unlocked_evidence:
            for ev_id in unlocked_evidence:
                fact = FACTS_MAP.get((fraud_type, persona_role, ev_id))
                if fact:
                    evidence_tokens.update(self._tokenize(fact.get("content", "") + " " + fact.get("title", "")))

        best_chunk: KnowledgeChunk | None = None
        best_score = 0.0

        for chunk in self.corpus:
            # 優先匹配相同 fraud_type 與 persona_role
            type_match = chunk.category == fraud_type or (
                fraud_type in ["shopping", "fake-sale"] and chunk.category in ["shopping", "fake-sale"]
            )
            role_match = chunk.role == persona_role
            if not type_match or not role_match:
                continue

            score = 0.0
            # 1. 關鍵詞與觸發詞精確加權命中
            for kw in chunk.keywords:
                kw_lower = kw.lower()
                if kw_lower in player_text.lower():
                    score += 3.0 * (1.0 + 0.1 * len(kw_lower))

            # 2. 玩家輸入分詞重疊率
            for token in tokens:
                for kw in chunk.keywords:
                    if token in kw or kw in token:
                        score += 1.2
                        break

            # 3. 查證事實聯動增益
            for ev_t in evidence_tokens:
                if ev_t in player_text:
                    score += 2.0

            if score > best_score:
                best_score = score
                best_chunk = chunk

        return best_chunk, best_score

    def generate_augmented_reply(
        self,
        fraud_type: str,
        persona_role: str,
        display_name: str,
        player_text: str,
        unlocked_evidence: list[str] | None = None,
    ) -> tuple[list[str], list[str]]:
        """回傳 (messages, tactics_used)。精準應對玩家所說的詞。"""
        chunk, score = self.retrieve(fraud_type, persona_role, player_text, unlocked_evidence)

        # 檢索得分顯著時，採用 RAG 增強專業反制
        if chunk and score >= 2.5:
            response_template = chunk.rebuttal_responses[0]
            if "宏盛資本" in response_template and display_name:
                response_template = response_template.replace("宏盛資本", f"宏盛資本（{display_name}總監團隊）")

            return [response_template], chunk.tactics

        # 一般情境自然流轉
        if persona_role == "scam":
            return [
                f"我是 {display_name}，我們所有操盤規畫與資金調度都是依國際慣例進行的。",
                "您現在配合完成入金建倉，下午三點半前就能讓您看見第一波獲利成效！"
            ], ["trust_building", "time_pressure"]
        else:
            return [
                f"您好，我是 {display_name}。我們官方絕無私下要求個人轉帳或提供驗證碼之情事，請您維持警覺，如有疑慮請致電官方反詐專線查證。"
            ], ["trust_building"]

    @staticmethod
    def _tokenize(text: str) -> list[str]:
        cleaned = re.sub(r"[^\w\u4e00-\u9fff]+", " ", text.lower())
        words = [w for w in cleaned.split() if w]
        grams: list[str] = list(words)
        for w in words:
            if len(w) >= 2:
                grams.extend(w[i : i + 2] for i in range(len(w) - 1))
            if len(w) >= 3:
                grams.extend(w[i : i + 3] for i in range(len(w) - 2))
        return grams


# 全域單例 RAG 檢索引擎
scenario_rag_engine = ScenarioRagEngine()
