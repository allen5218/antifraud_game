"""聊天式反詐劇本目錄（C1, C2, C3, C4, R1, R3, R4, R7）。

五位固定成年聯絡人：
1. 薇姐 (wei_jie): 富有直率
2. 梨梨 (li_li): 地雷系穿搭
3. 豪哥 (hao_ge): 人脈王
4. 房東阿姨 (landlady): 老舊物業房東
5. 阿燦 (a_can): 過氣直播主

每人三條獨立事件，共 15 事件，涵蓋合法、詐騙、合理暫停待補件。
包含三條怪異故事（活人的告別活動、相似人偶、空屋住戶群）及正常對照（排程晚安專線、三家共養一貓）。
所有題目均為中性名稱，無「假X」或「詐騙陷阱」。
所有金額、事實與管道均嚴格對齊，無默認發明金額（杜絕預設 1,000 元）。
"""

from __future__ import annotations

import copy
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class ContactInfo:
    id: str
    name: str
    avatar: str
    persona_desc: str
    initial_trust: int = 50
    initial_reliability: int = 50


CONTACTS: dict[str, ContactInfo] = {
    "wei_jie": ContactInfo(
        id="wei_jie",
        name="薇姐",
        avatar="WEI",
        persona_desc="身家豐厚、個性直率豪爽的資深投資客，說話直來直往，重視契約精神與時間效率。",
        initial_trust=55,
        initial_reliability=60,
    ),
    "li_li": ContactInfo(
        id="li_li",
        name="梨梨",
        avatar="LILI",
        persona_desc="喜愛地雷系穿搭與手作次文化的年輕創作者，重視隱私與原創性，對同好熱情但對外部施壓敏感。",
        initial_trust=45,
        initial_reliability=50,
    ),
    "hao_ge": ContactInfo(
        id="hao_ge",
        name="豪哥",
        avatar="HAO",
        persona_desc="活躍於商務社團與展會的人脈王，熱心引薦各路商業機會，重視業界聲譽與體面。",
        initial_trust=50,
        initial_reliability=50,
    ),
    "landlady": ContactInfo(
        id="landlady",
        name="房東阿姨",
        avatar="LAND",
        persona_desc="管理多處老舊公寓與出租套房的房東，熱心鄰里事務但對法規與新科技較不熟悉，重視產權與安全。",
        initial_trust=55,
        initial_reliability=55,
    ),
    "a_can": ContactInfo(
        id="a_can",
        name="阿燦",
        avatar="CAN",
        persona_desc="力圖轉型的過氣直播主與社區志工，性格樂觀健談，常在社群平台嘗試各種新興帶貨與企劃。",
        initial_trust=50,
        initial_reliability=45,
    ),
}


@dataclass
class StoryDefinition:
    story_id: str
    contact_id: str
    title: str
    learning_objective: str
    truth: str  # "scam" | "legit" | "pause_pending"
    source_adaptation_mark: str
    fixed_facts: dict[str, Any]
    npc_claims: dict[str, str]
    discloseable_facts: list[str]
    forbidden_facts: list[str]
    tool_results: dict[str, dict[str, Any]]
    prerequisites: dict[str, Any]
    branches: dict[str, Any]
    outcomes: dict[str, Any]
    is_weird_story: bool = False
    is_chapter_finale: bool = False


STORIES_CATALOG: dict[str, StoryDefinition] = {
    # ── 薇姐 (wei_jie) ──
    "living_farewell": StoryDefinition(
        story_id="living_farewell",
        contact_id="wei_jie",
        title="生前告別狂歡派對企劃",
        learning_objective="查證新創禮儀顧問登記資質與場地租賃真偽，防範高額預付訂金與私人海外帳戶匯款陷阱。",
        truth="scam",
        source_adaptation_mark="教學原創",
        is_weird_story=True,
        fixed_facts={
            "vendor_name": "星辰永恆生命禮儀策劃所",
            "contact_person": "特約顧問 沈專員",
            "amount": 80000,
            "amount_desc": "80,000 元（場地預付訂金）",
            "bank_account": "境外個人託管帳戶（非公司對公戶頭）",
            "venue": "松山文創園區多功能展演廳",
            "claim": "要求今日下午四點前預付 8 萬元場地保留金，宣稱名額有限且可享早鳥專屬禮儀攝影贊助。",
        },
        npc_claims={
            "initial": "我打算在我還健康的時候辦一場生前告別狂歡派對！有家新創生命禮儀顧問給了企劃，你幫我看看這件事靠不靠譜？",
            "doubt": "沈專員說這是海外私募基金贊助的新型態生命藝術節，所以款項才由海外專用帳戶代收。",
            "amount": "總預算 30 萬，對方要求今天下午四點前先付 8 萬場地保留金，說是松菸展演廳的檔期訂金。",
            "evidence": "沈專員只傳了一份電子合約草案，上面沒有公司統編跟用印，只有一個個人英文戶名。",
            "vendor": "跟我接洽的是『星辰永恆生命禮儀策劃所』的沈專員，收款要匯到海外個人託管帳戶。",
            "pause_reaction": "你說得對，不管對方怎麼催促，我們先慢下來把事情確認清楚。你覺得要先從哪項資料開始查？",
        },
        discloseable_facts=[
            "顧問公司名稱為星辰永恆生命禮儀策劃所",
            "要求匯款至境外個人託管帳戶，非公司專戶",
            "要求金額 80,000 元，期限為今天下午四點",
            "宣稱已包下松山文創園區展演廳",
        ],
        forbidden_facts=[
            "這是虛構幽靈公司與釣魚洗錢帳戶",
            "松菸管理處根本沒有這筆檔期登記",
            "底層真實身分是 scam",
        ],
        tool_results={
            "check_personal_records": {
                "title": "通聯與合約草案檢視",
                "content": "【遊戲模擬查證】檢視對方傳送之合約電子檔：文件未用印正式法人印鑑，受款人為個人戶名，無統一編號且無退款條款。",
                "is_independent": True,
                "source_id": "contract_paper",
                "claim_addressed": "contract_terms",
            },
            "check_official_registry": {
                "title": "全國殯葬資訊網與商工登記查詢",
                "content": "【遊戲模擬查證】經內政部全國殯葬資訊網與經濟部商業司登記檢索：查無『星辰永恆生命禮儀策劃所』之立案登記或營業許可字號。",
                "is_independent": True,
                "source_id": "official_registry_db",
                "claim_addressed": "legal_registration",
            },
            "check_independent_service": {
                "title": "松山文創園區場地組求證",
                "content": "【遊戲模擬查證】自行致電松菸展演組官方電話核實：檔期承辦人表示該展廳該週末已由公部門預訂，從未接獲該策劃所之租借申請。",
                "is_independent": True,
                "source_id": "independent_hotline",
                "claim_addressed": "venue_reservation",
            },
            "use_document_scanner": {
                "title": "合約草案光學高精掃描存證",
                "content": "【遊戲模擬查證】使用掃描器清晰留存合約紙本細節：該合約印文為修圖軟體合成邊緣，與正規商業合約樣式嚴重不符。",
                "is_independent": True,
                "source_id": "contract_paper",
                "claim_addressed": "contract_terms",
            },
        },
        prerequisites={"min_cash": 0, "required_flags": [], "required_stories": []},
        branches={
            "has_document_scanner": "可使用文件掃描器仔細留存合約印文細節",
            "high_trust": "薇姐願意耐心等待松菸官方電話核實結果",
            "low_trust": "薇姐態度急躁催促快點給結論",
        },
        outcomes={
            "report": "及時揭發幽靈禮儀機構與虛假場地租約，成功為薇姐保全 80,000 元資金。",
            "comply": "誤信其言貿然匯款，款項匯出後對方隨即失聯，造成重大金錢損失。",
            "safe_exit": "建議薇姐暫停匯款並親赴松菸管委會現場確認，穩健規避詐騙陷阱。",
        },
    ),
    "art_auction_consignment": StoryDefinition(
        story_id="art_auction_consignment",
        contact_id="wei_jie",
        title="當代藝術品拍賣代銷委託",
        learning_objective="辨識假拍賣預收高額鑑定費、圖錄費與海外展覽保證金之詐騙模式。",
        truth="scam",
        source_adaptation_mark="教學原創",
        fixed_facts={
            "gallery_name": "蘇菲亞當代國際拍賣行",
            "artwork_title": "當代抽象版畫三件組",
            "amount": 25000,
            "amount_desc": "25,000 元（鑑定費與圖錄保險費）",
            "claim": "宣稱買家已出價 60 萬元收購，但依國際藝術拍賣規約，賣方需先自費委託指定機構出具鑑定書與保險 25,000 元。",
        },
        npc_claims={
            "initial": "我五年前在藝博會收的那批版畫，剛才突然有拍賣行專員聯繫我，說有大買家看上想整批收購。你幫我掌掌眼，看看這交易能接嗎？",
            "doubt": "對方說這家拍賣行在倫敦有辦事處，國際買家指名要這份專屬防偽鑑定卡。",
            "amount": "買家開價 60 萬，但拍賣行說要賣方先匯 25,000 元的鑑定與圖錄印製保險費，下週才安排海外交割。",
            "evidence": "拍賣行只傳了英文合約草案，說繳費後會寄防偽鑑定卡，查不到在台灣的立案公文。",
            "vendor": "接洽人自稱是『蘇菲亞當代國際拍賣行』的海外藝術經紀人。",
            "pause_reaction": "行！你說得對，做買賣絕不能盲目配合。我們先暫緩，把拍賣行資質和行規查清楚再說！",
        },
        discloseable_facts=[
            "拍賣行名稱為蘇菲亞當代國際拍賣行",
            "要求賣方預先繳納 25,000 元鑑定與圖錄費",
            "宣稱有買家出價 60 萬元",
        ],
        forbidden_facts=[
            "買家為拍賣行自導自演之虛假買家",
            "該拍賣行以騙取前置鑑定費為主要獲利手段",
            "底層真相為 scam",
        ],
        tool_results={
            "check_personal_records": {
                "title": "藝術品原始購買憑證與合約草案核對",
                "content": "【遊戲模擬查證】檢視五年前原始購買發票：該版畫為限量複製品市價約 8,000 元，對方開價 60 萬明顯脫離常理。",
                "is_independent": True,
                "source_id": "contract_paper",
                "claim_addressed": "valuation_reality",
            },
            "check_official_registry": {
                "title": "商工登記與文化部拍賣業務查詢",
                "content": "【遊戲模擬查證】至經濟部商工登記與文化部系統檢索：查無該拍賣行在台灣之公司法人設立登記。",
                "is_independent": True,
                "source_id": "official_registry_db",
                "claim_addressed": "legal_registration",
            },
            "check_independent_service": {
                "title": "中華民國畫廊協會防詐諮詢",
                "content": "【遊戲模擬查證】致電畫廊協會諮詢：專員說明合規拍賣行均由成交價款後扣佣金，絕無要求賣方預先匯款前置鑑定費之慣例。",
                "is_independent": True,
                "source_id": "independent_hotline",
                "claim_addressed": "industry_practice",
            },
            "use_second_phone": {
                "title": "使用獨立線路撥打畫廊公會求證",
                "content": "【遊戲模擬查證】使用獨立線路外撥公會代表號：確認近期有多起冒充海外拍賣行收取版畫鑑定費後失聯之手法通報。",
                "is_independent": True,
                "source_id": "independent_hotline",
                "claim_addressed": "industry_practice",
            },
        },
        prerequisites={"min_cash": 0, "required_flags": [], "required_stories": ["living_farewell"]},
        branches={
            "has_second_phone": "使用獨立專線外撥畫廊協會直接取得權威行規說明",
            "high_cash": "薇姐認為 2 萬 5 只是小錢差點直接刷卡",
        },
        outcomes={
            "report": "指認假拍賣高估價誘騙前置費用之手法，保全 25,000 元。",
            "comply": "匯出鑑定費後拍賣行百般推託流標，無法追回款項。",
            "safe_exit": "建議薇姐堅持『由買方自費鑑定或成交後扣款』，對方知難而退。",
        },
    ),
    "scheduled_goodnight": StoryDefinition(
        story_id="scheduled_goodnight",
        contact_id="wei_jie",
        title="排程晚安長者陪伴專線訂閱",
        learning_objective="辨別合規公益社福服務與合法定期扣款，理解提供公開統編、隨時可取消與正規刷卡金流之正當訊號。",
        truth="legit",
        source_adaptation_mark="教學原創",
        fixed_facts={
            "service_name": "銀髮暖心排程語音陪伴網",
            "org_name": "社團法人台灣高齡關懷發展協會",
            "amount": 600,
            "amount_desc": "每月 600 元（定期信用卡扣款，可隨時解約）",
            "payment_method": "合規第三方金流信用卡定期扣款，提供線上單鍵解約與電子發票",
            "claim": "提供獨居長者每晚排程問安與心理支持，收費透明且公開立案核備文號。",
        },
        npc_claims={
            "initial": "我想替社區幾位獨居長輩找個晚安關懷電話服務，剛好看到一個協會推出的排程陪伴專案。你幫我審核看看這服務規不正規？",
            "doubt": "我查過他們官網有列出理事長姓名跟內政部立案字號，繳費也是直接連到銀行信用卡授權頁面。",
            "amount": "費用是每月 600 元，走信用卡定期扣款，隨時可在線上解約，發票可開三聯式或捐贈碼。",
            "evidence": "協會官網公開了理監事名單、內政部立案字號與公益勸募許可文號。",
            "vendor": "服務機構是『社團法人台灣高齡關懷發展協會』，由受訓志工電話問候。",
            "pause_reaction": "沒問題！訂閱長輩關懷服務本來就不用急於一時。我們先仔細看他們的立案證書跟信用卡合約條款！",
        },
        discloseable_facts=[
            "機構全銜為社團法人台灣高齡關懷發展協會",
            "收費為每月 600 元，走正式信用卡線上金流",
            "官網公開內政部立案證書與公益勸募核准字號",
        ],
        forbidden_facts=[
            "本案為完全合法公益服務",
            "無任何詐騙或冒名情事",
        ],
        tool_results={
            "check_personal_records": {
                "title": "刷卡授權網頁與解約條款查閱",
                "content": "【遊戲模擬查證】檢視線上合約條款：金流為藍新科技合法第三方金流，明確載明『可隨時線上取消次期扣款』，合約權利義務清晰。",
                "is_independent": True,
                "source_id": "contract_paper",
                "claim_addressed": "payment_terms",
            },
            "check_official_registry": {
                "title": "內政部合作及人民團體司登記查詢",
                "content": "【遊戲模擬查證】查詢內政部全國人民團體名冊：該協會確實合法立案（台內團字第 1100012345 號），理監事名冊與財務報表依法備查。",
                "is_independent": True,
                "source_id": "official_registry_db",
                "claim_addressed": "legal_registration",
            },
            "check_independent_service": {
                "title": "直撥協會登記市話與社會局核實",
                "content": "【遊戲模擬查證】依登記代表號求證：秘書處專員清楚說明服務流程，並出示志工長照關懷基礎培訓證書，資訊完全一致。",
                "is_independent": True,
                "source_id": "independent_hotline",
                "claim_addressed": "operational_reality",
            },
        },
        prerequisites={"min_cash": 0, "required_flags": [], "required_stories": ["art_auction_consignment"]},
        branches={
            "has_pet_supplies": "可洽談社區寵物探訪複合關懷志工活動",
            "regular": "依合規透明程序正常訂閱",
        },
        outcomes={
            "trust": "確認協會資質完備透明，放心支持社區長者關懷排程服務。",
            "report": "草率指責正當社福組織，損害互信並錯失優質公益服務。",
            "safe_exit": "保留評估彈性，日後再行決定是否贊助訂閱。",
        },
    ),

    # ── 梨梨 (li_li) ──
    "lookalike_doll": StoryDefinition(
        story_id="lookalike_doll",
        contact_id="li_li",
        title="手工訂製人偶版權索賠事件",
        learning_objective="辨別著作權侵權恐嚇與私訊勒索手法，堅持透過正規存證信函與實體著作權證明查證，不私下匯款和解。",
        truth="scam",
        source_adaptation_mark="教學原創",
        is_weird_story=True,
        fixed_facts={
            "demander_name": "暗影模型工作室 代理法務",
            "amount": 15000,
            "amount_desc": "15,000 元（私下和解賠償金）",
            "claim": "指控梨梨市集展示之人偶臉模侵權，宣稱若今日不透過超商代碼匯款 15,000 元和解即提起訴訟並上網公審。",
            "bank_account": "超商代碼繳費 / 虛擬電子錢包",
        },
        npc_claims={
            "initial": "我快嚇哭了…剛才有人私訊指控我市集展出的人偶模具侵權，態度好兇說要去告我還要網路上公審我…我好慌，怎麼辦？",
            "doubt": "他傳了一張對比圖，但那個人偶根本是我自己用黏土一點一滴捏出來的！但他口氣好兇好專業…",
            "amount": "他說今天下午五點前要用超商代碼繳 15,000 元私下和解，不然就要叫律師提告。",
            "evidence": "對方私訊只傳了一張模糊的日本專利登記書截圖，根本沒有台灣智財局的有效專利案號。",
            "vendor": "對方帳號自稱是『暗影模型工作室代理法務』，連真實姓名跟律師證號都沒給。",
            "pause_reaction": "好…聽你的，我先不要理那個代碼。對方口氣真的好兇，我把警告截圖和我的原創草稿都整理出來了，你幫我看看！",
        },
        discloseable_facts=[
            "對方自稱暗影模型工作室法務代理人",
            "指控手工人偶臉模抄襲專利，要求 15,000 元和解金",
            "要求透過超商代碼或虛擬錢包匯款，時間要求緊迫",
        ],
        forbidden_facts=[
            "對方為網路亂槍打鳥之專利流氓與恐嚇勒索者",
            "根本未在智慧財產局登記任何有效外觀專利",
            "底層真實身分是 scam",
        ],
        tool_results={
            "check_personal_records": {
                "title": "原創黏土捏塑歷程與發布時間戳",
                "content": "【遊戲模擬查證】調閱梨梨個人創作相簿：存有清晰創作縮時影片與社群原始發布時間戳記，創作時間遠早於對方指控之時間點。",
                "is_independent": True,
                "source_id": "creation_evidence",
                "claim_addressed": "originality_proof",
            },
            "check_official_registry": {
                "title": "智慧財產局專利商標檢索系統",
                "content": "【遊戲模擬查證】檢索經濟部智財局系統：查無該工作室之外觀專利登記案號，對方出示之圖檔實為公版網路圖樣修改而成。",
                "is_independent": True,
                "source_id": "official_registry_db",
                "claim_addressed": "patent_validity",
            },
            "check_independent_service": {
                "title": "保二總隊刑事警察大隊諮詢",
                "content": "【遊戲模擬查證】致電保二總隊諮詢：警官說明近期多起鎖定手作者恐嚇之假侵權和解勒索，提醒切勿私下超商代碼匯款。",
                "is_independent": True,
                "source_id": "independent_hotline",
                "claim_addressed": "legal_process",
            },
            "use_secondhand_polaroid": {
                "title": "使用拍立得留存展品現場影像存證",
                "content": "【遊戲模擬查證】使用二手拍立得拍攝展品細部特徵留存時間照片：人偶切刀刻痕清晰，保留物理影像留存紀錄。",
                "is_independent": True,
                "source_id": "creation_evidence",
                "claim_addressed": "originality_proof",
            },
        },
        prerequisites={"min_cash": 0, "required_flags": [], "required_stories": ["underground_idol_goods"]},
        branches={
            "has_collectible_doll": "限定同好玩偶給予梨梨極大心理支持，穩定其情緒不慌張",
            "has_secondhand_polaroid": "可使用二手拍立得拍攝現場照片留存實體特徵",
        },
        outcomes={
            "report": "確認對方為空頭勒索，協助梨梨封鎖對方並報警存證，保全 15,000 元。",
            "comply": "因恐懼破財匯款，對方食髓知味繼續索討更多封口費。",
            "safe_exit": "請梨梨要求對方寄發正式存證信函並暫停對話，對方隨即放棄糾纏。",
        },
    ),
    "underground_idol_goods": StoryDefinition(
        story_id="underground_idol_goods",
        contact_id="li_li",
        title="地下偶像聯名週邊寄賣合作",
        learning_objective="確認實體演藝經紀法人登記與授權條約完整性，認識合規文化商業合作之透明流程。",
        truth="legit",
        source_adaptation_mark="教學原創",
        fixed_facts={
            "company_name": "幻月娛樂經紀股份有限公司",
            "idol_group": "星光稜鏡 PrismGirls",
            "amount": 0,
            "amount_desc": "0 元（無前置保證金，為實銷實結 7:3 拆帳）",
            "cooperation_type": "手作痛包與聯名徽章授權寄賣，提供實體授權證書與三聯式合約",
            "financial_terms": "無需預付任何保證金，採每月實銷實結拆帳 7:3，走銀行匯入梨梨本人戶頭",
        },
        npc_claims={
            "initial": "我推的地下偶像經紀公司，剛才主辦人主動聯繫我，說想把我做的手作痛包列為演唱會官方週邊寄賣！合約看起來好正式，你幫我看看有坑嗎？",
            "doubt": "他們沒跟我要任何保證金，說等活動結束後依銷售報表對帳直接匯給我。",
            "amount": "完全不用預付任何保證金！條款寫實銷實結 7:3 拆帳，款項直接匯到我的銀行帳戶。",
            "evidence": "經紀公司寄了合作備忘錄與授權意向書，上面有公司大小章與統一編號。",
            "vendor": "接洽窗口是『幻月娛樂經紀股份有限公司』的周製作人。",
            "pause_reaction": "嗯！合作合約雖然看起來很棒，但我也覺得仔細審閱智慧財產權條款最重要。我們先不急著簽字！",
        },
        discloseable_facts=[
            "經紀公司名稱為幻月娛樂經紀股份有限公司",
            "合作模式為週邊寄賣實銷實結，無需預繳任何保證金",
            "提供完整紙本合約與經紀公司大小章",
        ],
        forbidden_facts=[
            "此合作為真實合法之商業聯名",
            "經紀公司資質完整無詐騙情事",
        ],
        tool_results={
            "check_personal_records": {
                "title": "合約草案與智財歸屬條款審閱",
                "content": "【遊戲模擬查證】檢視合作協議書草案：條款明確載明智財權仍屬創作者梨梨所有，僅授權演唱會當日限量寄售，權責合理分明。",
                "is_independent": True,
                "source_id": "contract_paper",
                "claim_addressed": "contract_terms",
            },
            "check_official_registry": {
                "title": "經濟部商工登記核驗",
                "content": "【遊戲模擬查證】查詢商業司登記資料：該公司資本額 500 萬元，實體營業登記地址明確，登記營業項目包含演藝經紀與文創展售。",
                "is_independent": True,
                "source_id": "official_registry_db",
                "claim_addressed": "legal_registration",
            },
            "check_independent_service": {
                "title": "售票平台與主辦單位官方求證",
                "content": "【遊戲模擬查證】查核演唱會售票系統公告：主辦單位確實為該經紀公司，官方粉專亦同步刊登週邊合作招募公告，資訊相符。",
                "is_independent": True,
                "source_id": "independent_hotline",
                "claim_addressed": "event_verification",
            },
        },
        prerequisites={"min_cash": 0, "required_flags": [], "required_stories": []},
        branches={
            "has_workbench": "在工作桌上整齊歸納合約條款與拆帳明細表格",
            "regular": "依合規條約順利推進合作",
        },
        outcomes={
            "trust": "確認合作合規透明，梨梨成功展開首次官方週邊合作並獲得良好收益。",
            "report": "誤認合規經紀公司為詐騙而粗暴拒絕，錯失正當商業發展機會。",
            "safe_exit": "建議梨梨先簽署單場試賣備忘錄，穩紮穩打建立長期合作。",
        },
    ),
    "cosplay_custom_import": StoryDefinition(
        story_id="cosplay_custom_import",
        contact_id="li_li",
        title="客製服飾海外代購海關留置單",
        learning_objective="辨認海關正式進口補件通知與冒名假快遞詐騙之差異，掌握合規報關行正式稅單查驗與暫停補件處置流程。",
        truth="pause_pending",
        source_adaptation_mark="教學原創",
        fixed_facts={
            "customs_notice_no": "關字第 11309876 號待補正通知",
            "broker_name": "順達國際報關行",
            "amount": 0,
            "amount_desc": "0 元（海關補正發票程序，未收取任何款項）",
            "issue": "因布料材質代碼需核實，通知於 14 日內補正原廠商業發票，不收解鎖規費，逾期退運",
            "solution": "需向海外原廠索取完整商業發票與規格證明補件給報關行，而非線上直接付款解鎖",
        },
        npc_claims={
            "initial": "我訂做的一套動漫 Cosplay 洋裝卡在海關了！報關行傳訊來說要辦理留置審驗，我好擔心包裹被退運或銷毀…現在該怎麼辦？",
            "doubt": "對方簡訊裡沒有附任何轉帳帳號，只說要我回傳購買發票跟委任書，但網路上好多假海關詐騙，我不敢隨便給個資…",
            "amount": "目前通知完全不涉及款項支付（0 元），但要在 14 天內補齊文件，逾期會被退運。",
            "evidence": "報關行傳來基隆關的待補正通知單（關字第 11309876 號），要求補附材質說明與原始發票。",
            "vendor": "通知單位是基隆關委任之『順達國際報關行』，負責快遞貨物查驗業務。",
            "pause_reaction": "好！我們先不慌，海關既然有給補正期限，我們就先向海外原廠要發票跟材質證明，一步一步補正！",
        },
        discloseable_facts=[
            "案件性質為海關正式待補件程序",
            "負責報關行為順達國際報關行",
            "未要求任何款項支付，僅要求依法補正商業發票與型錄",
        ],
        forbidden_facts=[
            "本案並非詐騙，但屬待補正法定程序",
            "不可要求玩家立刻下結案判斷，應採取暫停補件查證",
        ],
        tool_results={
            "check_personal_records": {
                "title": "海外購物平台訂單與商品明細",
                "content": "【遊戲模擬查證】登入海外購物網站調閱交易紀錄：訂單確實載有工房出具之成分標籤（100% 聚酯纖維），可作為補件憑據。",
                "is_independent": True,
                "source_id": "contract_paper",
                "claim_addressed": "invoice_match",
            },
            "check_official_registry": {
                "title": "關務署『易利委 EZ WAY』實名認證查詢",
                "content": "【遊戲模擬查證】開啟關務署官方 EZ WAY App：該筆分提單號確實處於『海關審驗待補文件』狀態，案件號碼與簡訊完全一致。",
                "is_independent": True,
                "source_id": "official_registry_db",
                "claim_addressed": "customs_status",
            },
            "check_independent_service": {
                "title": "致電基隆關業務組專線核對",
                "content": "【遊戲模擬查證】直撥海關官網總機轉業務課：海關人員說明只需在官方 App 補附材質說明即可，絕無私下要求點擊未知連結付款。",
                "is_independent": True,
                "source_id": "independent_hotline",
                "claim_addressed": "customs_procedure",
            },
            "use_document_scanner": {
                "title": "使用掃描器清晰留存原廠發票影本",
                "content": "【遊戲模擬查證】以文件掃描器清晰留存發票與材質說明數位檔，便於上傳官方補件平台。",
                "is_independent": True,
                "source_id": "contract_paper",
                "claim_addressed": "invoice_match",
            },
        },
        prerequisites={"min_cash": 0, "required_flags": [], "required_stories": ["lookalike_doll"]},
        branches={
            "has_document_scanner": "使用文件掃描器清晰掃描原廠證明文件上傳報關",
            "regular": "按法定途徑在 EZ WAY 上傳補件憑據",
        },
        outcomes={
            "safe_exit": "指導梨梨透過官方 EZ WAY 補件切結，未盲信未知網址亦未輕忽法規，平安順利取貨。",
            "report": "誤將法定海關補件程序當成詐騙向警方檢舉，導致貨物逾期退運產生額外運費。",
            "comply": "未補件即草率確認，無法解決海關留置問題。",
        },
    ),

    # ── 豪哥 (hao_ge) ──
    "vip_cross_border_fund": StoryDefinition(
        story_id="vip_cross_border_fund",
        contact_id="hao_ge",
        title="跨境商務俱樂部專屬基金",
        learning_objective="防範熟人引薦之未核准跨境私募基金與保證獲利騙局，查證金管會特許執照與合規受監管通路。",
        truth="scam",
        source_adaptation_mark="教學原創",
        fixed_facts={
            "fund_name": "杜拜阿布達比聯合能源產業基金",
            "promoter": "商會李總裁",
            "amount": 100000,
            "amount_desc": "100,000 元（最低進場投資門檻）",
            "guaranteed_return": "月息 8%（年化接近 100%）",
            "entry_method": "指定轉入境外冷錢包或特定私人代收帳戶，宣稱保本保息",
        },
        npc_claims={
            "initial": "兄弟！我上週在商會聚會認識一位大老闆，私下幫我爭取到一個海外能源基金的內部投資名額，機會難得，我找你一起研究看看！",
            "doubt": "李總開豪車出入體面，群組裡還有好多老闆每天貼分紅截圖，這應該很穩吧？",
            "amount": "宣稱保證月息 8%，最低進場門檻是 10 萬元，他自己投了 50 萬，要我把錢匯到指定的海外私人帳戶。",
            "evidence": "李總只給我看海外基金英文簡報跟高額對帳單截圖，問他有沒有金管會核准函，他只說是境外私募基金不用在台灣登記。",
            "vendor": "推介人是商會認識的李總裁，宣稱代表『杜拜阿布達比聯合能源產業基金』。",
            "pause_reaction": "兄弟你說得對！做生意最忌諱衝動，就算獲利再誘人，我們先把基金合法立案跟帳戶搞清楚！",
        },
        discloseable_facts=[
            "基金宣稱為杜拜能源產業基金",
            "宣稱保證月獲利 8%，由李總裁私下引薦",
            "要求資金轉換為加密貨幣或轉入特定未監管帳戶",
        ],
        forbidden_facts=[
            "標準龐氏騙局，利用熟人人脈與群組分紅截圖造假吸金",
            "未受金管會監管亦未在阿聯酋正式登記",
            "底層真相為 scam",
        ],
        tool_results={
            "check_personal_records": {
                "title": "豪哥出示之英文合約細閱",
                "content": "【遊戲模擬查證】審閱合約條款：立約方為海外免稅島空殼公司，內文載有小字免責條款『投資人需承擔所有本金損失』，與保本口頭宣稱矛盾。",
                "is_independent": True,
                "source_id": "contract_paper",
                "claim_addressed": "contract_guarantee",
            },
            "check_official_registry": {
                "title": "金管會證期局特許境外基金名單查詢",
                "content": "【遊戲模擬查證】至金管會證券期貨局檢驗：該基金未在台獲准募集與銷售，亦未取得合法資產管理特許業務牌照。",
                "is_independent": True,
                "source_id": "official_registry_db",
                "claim_addressed": "license_check",
            },
            "check_independent_service": {
                "title": "投信投顧公會諮詢專線",
                "content": "【遊戲模擬查證】致電投信投顧公會查證：公會明確提醒，凡未經核准以保證高獲利在台招攬境外基金者，均屬高度吸金套牢風險。",
                "is_independent": True,
                "source_id": "independent_hotline",
                "claim_addressed": "regulatory_compliance",
            },
        },
        prerequisites={"min_cash": 0, "required_flags": [], "required_stories": []},
        branches={
            "high_cash": "玩家手頭充裕，豪哥力勸跟單 10 萬獲利",
            "has_display_cabinet": "豪哥在展示櫃前看到正派證照，願意認真聽你分析監管風險",
        },
        outcomes={
            "report": "徹底戳破無牌非法吸金假面，拉住豪哥並保全大筆資金。",
            "comply": "跟進投款，前兩月拿到假利息後平台隨即無法出金崩盤。",
            "safe_exit": "要求李總提出金管會核准公文，對方藉故閃爍其詞，成功脫身。",
        },
    ),
    "industry_summit_exhibition": StoryDefinition(
        story_id="industry_summit_exhibition",
        contact_id="hao_ge",
        title="國際供應鏈創新論壇參展",
        learning_objective="查驗實體大型展會標案主管機關公告、展覽館排程與合法三聯式發票之透明商業交易特徵。",
        truth="legit",
        source_adaptation_mark="教學原創",
        fixed_facts={
            "organizer": "中華民國對外貿易發展協會（外貿協會）共同指導",
            "event_title": "2026 亞洲綠色智慧供應鏈高峰會",
            "venue": "台北世界貿易中心展覽大樓一樓 A 區",
            "amount": 19000,
            "amount_desc": "攤位費 38,000 元，合租平攤 19,000 元（開立正式發票）",
            "payment": "土地銀行外貿協會專屬公庫帳號，開立財政部三聯式電子發票",
        },
        npc_claims={
            "initial": "兄弟！我拿到下個月世貿一館國際供應鏈高峰會的聯展攤位資格，能見度超高！我想找你一起合租展位，你覺得如何？",
            "doubt": "報名表都是外貿協會官網標準表單，繳款也是直接匯到世貿官方的公庫戶頭。",
            "amount": "標準攤位總租金 38,000 元，我們合租平攤一人 19,000 元，會開立財政部三聯式電子發票。",
            "evidence": "主辦方給了正式繳款通知單與展位配置圖，受款帳號是土地銀行的外貿協會專用公庫帳戶。",
            "vendor": "主辦單位是中華民國對外貿易發展協會（外貿協會），活動是『2026 亞洲綠色智慧供應鏈高峰會』。",
            "pause_reaction": "沒問題！合租參展本來就要雙方確認好預算跟合約。我們先核對繳款帳號跟展位位置！",
        },
        discloseable_facts=[
            "主辦方包含外貿協會與正式產業公會",
            "展出地點為台北世貿一館實體展區",
            "繳費走正式銀行公庫帳號並開立三聯式發票",
        ],
        forbidden_facts=[
            "本活動為合規實體展會",
            "完全真實，無欺詐成分",
        ],
        tool_results={
            "check_personal_records": {
                "title": "展位規章與參展手冊檢閱",
                "content": "【遊戲模擬查證】審閱參展手冊：明確記載展館公共意外保險、進退場標準時間表與正式發票開立規定，格式合規完備。",
                "is_independent": True,
                "source_id": "contract_paper",
                "claim_addressed": "exhibition_terms",
            },
            "check_official_registry": {
                "title": "台北世貿展覽大樓公開排程查核",
                "content": "【遊戲模擬查證】查詢世貿展館官方檔期表：該週確實排定該高峰會展期，承辦公會統編與活動名稱完全吻合。",
                "is_independent": True,
                "source_id": "official_registry_db",
                "claim_addressed": "schedule_reality",
            },
            "check_independent_service": {
                "title": "外貿協會展覽業務組代表號確認",
                "content": "【遊戲模擬查證】致電外貿協會總機轉展覽組：專員查對確認豪哥之企業統編已登記候補與正取攤位，款項確入世貿專戶。",
                "is_independent": True,
                "source_id": "independent_hotline",
                "claim_addressed": "registration_verification",
            },
        },
        prerequisites={"min_cash": 0, "required_flags": [], "required_stories": ["vip_cross_border_fund"]},
        branches={
            "has_dashcam": "可安排載運大型樣品前往世貿佈展並留存影音紀錄",
            "regular": "依合約共同參展拓展業務人脈",
        },
        outcomes={
            "trust": "確認實體展會真實可靠，合租攤位提升品牌知名度與業務接單。",
            "report": "因疑心過重誤指控官方主辦展會，破壞與豪哥之商業信賴關係。",
            "safe_exit": "因預算考量本次暫不參展，向主辦單位辦理正式候補保留。",
        },
    ),
    "influencer_mcn_contract": StoryDefinition(
        story_id="influencer_mcn_contract",
        contact_id="hao_ge",
        title="新媒體經紀人孵化專案合約",
        learning_objective="行使商業經紀合約法定審閱期，防範以模糊保證包裹霸王條款或高額違約金之法律陷阱。",
        truth="pause_pending",
        source_adaptation_mark="教學原創",
        fixed_facts={
            "mcn_company": "星潮數位娛樂媒體",
            "contract_type": "自媒體創作者全經紀授權代理合約",
            "amount": 0,
            "amount_desc": "0 元（簽約不收費，但含五年 200 萬違約金條款）",
            "issue": "合約承諾流量曝光但附帶『外部收入抽成 50%』及『提前解約需支付懲罰性違約金 200 萬元』，缺乏對等義務",
            "correct_action": "依法主張七日合約審閱期，要求由專業法務修改對等條款或暫停簽約",
        },
        npc_claims={
            "initial": "兄弟！有家網紅經紀公司看中我的商務人脈，想簽我當帶貨經紀合夥人，合約剛送過來，催得有點急，你幫我翻翻看有沒有問題？",
            "doubt": "經紀人一直說名額搶手，今天不簽明天就給別人了，但裡面違約金寫得好可怕…",
            "amount": "簽約本身不收保證金（0 元），但條款裡藏著一條若提前解約要賠償 200 萬違約金的巨額罰則！",
            "evidence": "對方給了一份六十多頁的紙本合約，承諾流量曝光但義務極不對等，也沒有律師見證用印。",
            "vendor": "對方是『星潮數位娛樂媒體』的簽約代表。",
            "pause_reaction": "兄弟你提醒得及時！合約不能草率簽字，我們依法主張七日審閱期，先找法務或專業人士看過再決定。",
        },
        discloseable_facts=[
            "經紀公司名稱為星潮數位娛樂媒體",
            "宣稱提供流量支援但合約含有高額解約罰款條款",
            "對方催促當日簽署，規避契約審閱期",
        ],
        forbidden_facts=[
            "非單純詐騙，屬不平等霸王條款陷阱",
            "正確策略為行使審閱期暫停簽約與要求修約",
        ],
        tool_results={
            "check_personal_records": {
                "title": "合約關鍵權益與違約罰則拆解",
                "content": "【遊戲模擬查證】細看條文：經紀公司對流量承諾僅有『盡力而為』無保證條款，創作者若解約卻需承擔 200 萬元懲罰性違約金，權責顯失公平。",
                "is_independent": True,
                "source_id": "contract_paper",
                "claim_addressed": "clause_balance",
            },
            "check_official_registry": {
                "title": "司法院裁判書同名公司糾紛查詢",
                "content": "【遊戲模擬查證】至司法院裁判書公開系統查詢：該公司過去兩年有四起與旗下創作者之合約訴訟，多涉及高額違約金求償爭議。",
                "is_independent": True,
                "source_id": "official_registry_db",
                "claim_addressed": "litigation_history",
            },
            "check_independent_service": {
                "title": "法律扶助基金會諮詢",
                "content": "【遊戲模擬查證】向法律扶助專線諮詢：律師建議嚴格主張合約審閱期，切勿當日匆忙簽署，並應刪除不對等巨額懲罰條款。",
                "is_independent": True,
                "source_id": "independent_hotline",
                "claim_addressed": "legal_advice",
            },
            "use_document_scanner": {
                "title": "使用掃描器標記合約爭議條文",
                "content": "【遊戲模擬查證】以掃描器將六十頁合約歸檔並比對不合理條款，留存律師修約底稿。",
                "is_independent": True,
                "source_id": "contract_paper",
                "claim_addressed": "clause_balance",
            },
        },
        prerequisites={"min_cash": 0, "required_flags": [], "required_stories": ["industry_summit_exhibition"]},
        branches={
            "has_document_scanner": "掃描合約關鍵字標註風險條款交由律師修訂",
            "regular": "主張審閱期並要求修改條文",
        },
        outcomes={
            "safe_exit": "指導豪哥行使法定契約審閱期要求修改條款，對方自知理虧主動修改，成功避開霸王條約陷阱。",
            "report": "直接檢舉該公司為詐騙集團，因屬民事契約範疇警察無法受理且引發無謂口舌。",
            "comply": "倉促簽字受制於人，日後難以擺脫五年長約與巨額違約金威脅。",
        },
    ),

    # ── 房東阿姨 (landlady) ──
    "vacant_house_group": StoryDefinition(
        story_id="vacant_house_group",
        contact_id="landlady",
        title="公寓頂樓防水工程公費分攤",
        learning_objective="防範冒名假管委會總幹事私設帳戶催繳修繕公費，掌握查驗區分所有權人會議紀錄與合法管委會專戶之途徑。",
        truth="scam",
        source_adaptation_mark="教學原創",
        is_weird_story=True,
        fixed_facts={
            "alleged_role": "和平新村公寓大廈管理委員會 新任總幹事 趙先生",
            "amount": 12000,
            "amount_desc": "12,000 元（頂樓修繕每戶分攤公費）",
            "project": "頂樓防水隔熱工程每戶平攤公費",
            "payment_account": "某個人銀行帳戶（非大樓管委會對公帳戶）",
        },
        npc_claims={
            "initial": "阿姨那間空著的老公寓，社區群組突然有人自稱新總幹事，說頂樓漏水很嚴重急著要修，催大家趕快配合繳錢，真有這回事嗎？",
            "doubt": "那棟老公寓以前從來沒有成立過正式管委會，都是我們三樓的老李在收清潔費，怎麼突然跑出個趙總幹事？",
            "amount": "那個趙先生要求每戶今天之內平攤 12,000 元修繕公費，匯到他的個人帳戶，還說不繳就要斷水。",
            "evidence": "趙先生只在 LINE 群組貼了一張手寫估價單跟幾張漏水照片，管委會開會紀錄或正式工程合約連一張都沒看到。",
            "vendor": "對方自稱是社區新成立管委會的趙總幹事。",
            "pause_reaction": "好喔，阿姨聽你的，先把錢按住不匯！大樓修繕要有管委會正式規矩，我們先找里長跟 3 樓老李問清楚！",
        },
        discloseable_facts=[
            "對方自稱新任管委會總幹事趙先生",
            "要求匯款 12,000 元修繕公費至其個人銀行帳號",
            "威脅逾期斷水與加收滯納金",
        ],
        forbidden_facts=[
            "趙先生為外部閒雜人士冒名混入社區群組行騙",
            "大樓根本未曾召開正式所有權人會議成立管委會",
            "底層真實真相為 scam",
        ],
        tool_results={
            "check_personal_records": {
                "title": "過往清潔收據與住戶名冊核對",
                "content": "【遊戲模擬查證】檢視過往收據與名冊：大樓一直由 3 樓李先生協助代收微薄清潔費，住戶名單中查無趙姓住戶或所有權人紀錄。",
                "is_independent": True,
                "source_id": "contract_paper",
                "claim_addressed": "resident_history",
            },
            "check_official_registry": {
                "title": "建管處公寓大廈組織報備名冊查詢",
                "content": "【遊戲模擬查證】查詢台北市建管處公寓大廈報備系統：該棟地址查無任何合法報備立案之管理委員會或負責人備查紀錄。",
                "is_independent": True,
                "source_id": "official_registry_db",
                "claim_addressed": "committee_registration",
            },
            "check_independent_service": {
                "title": "親訪 3 樓住戶李先生與在地里長查核",
                "content": "【遊戲模擬查證】向里長與 3 樓老李核實：老李說明頂樓日前剛檢查過完好無漏水，此人為冒名混進群組的不明人士，提醒大家切勿匯款！",
                "is_independent": True,
                "source_id": "independent_hotline",
                "claim_addressed": "onsite_reality",
            },
            "use_second_phone": {
                "title": "使用獨立電話撥打估價單廠商號碼",
                "content": "【遊戲模擬查證】撥打估價單上印製之水電工程行電話：發話提示為暫停使用空號，顯為偽造之報價單據。",
                "is_independent": True,
                "source_id": "independent_hotline",
                "claim_addressed": "onsite_reality",
            },
        },
        prerequisites={"min_cash": 0, "required_flags": [], "required_stories": ["fire_safety_inspection"]},
        branches={
            "has_second_phone": "使用第二支手機外撥施工廠商迅速確認空號偽造",
            "has_property": "房東阿姨見你擁有個人物業經驗，非常信賴你的物業處置建議",
        },
        outcomes={
            "report": "及時在住戶群踢爆假總幹事，並通報里長報警，保護全棟住戶免遭冒名斂財。",
            "comply": "因畏懼斷水威脅匯出 12,000 元，事後發現受騙求償無門。",
            "safe_exit": "指導房東阿姨要求召開實體住戶大會並當面核對帳目，冒牌者立即退群潛逃。",
        },
    ),
    "subsidized_social_housing": StoryDefinition(
        story_id="subsidized_social_housing",
        contact_id="landlady",
        title="社會住宅包租代管計畫合作",
        learning_objective="確認國家住宅中心認可特許業者執照、公證租賃保障與合法稅賦減免流程。",
        truth="legit",
        source_adaptation_mark="教學原創",
        fixed_facts={
            "agent_company": "安居永續租賃住宅服務股份有限公司",
            "license_no": "北市地房特字第 1090888 號",
            "program": "內政部第四期社會住宅包租代管計畫",
            "amount": 0,
            "amount_desc": "0 元（政府特許專案，房東免付代辦規費）",
            "benefits": "提供房東每年修繕補助最高 1 萬元、地價稅房屋稅合規減免",
            "process": "由特許專員陪同現場會勘，簽約全程至法院或民間公證人處公證，房東免付任何手續費",
        },
        npc_claims={
            "initial": "有家租賃公司找上門，說可以把阿姨二樓套房加入政府的包租代管計畫，省得我自己招租。但現在詐騙這麼多，你幫阿姨看看這政策是真的嗎？",
            "doubt": "專員說簽約都要去地方法院公證，而且我完全不用付仲介費跟手續費，政府會全額補助業者。",
            "amount": "房東完全免收代辦規費（0 元），政府還提供每年最高 1 萬元的修繕補助和稅務減免。",
            "evidence": "對方出示了台北市地政局租賃住宅特許證照，簽約全程安排到地方法院公證處辦理公證。",
            "vendor": "接洽業者是『安居永續租賃住宅服務股份有限公司』，領有北市地房特字第 1090888 號。",
            "pause_reaction": "對對對，阿姨也是這麼想！雖然是政府政策，但把房子交出去可不能大意，我們先看公證合約跟證照！",
        },
        discloseable_facts=[
            "租賃公司全銜為安居永續租賃住宅服務股份有限公司",
            "合作專案為內政部第四期社會住宅包租代管計畫",
            "簽約全程採公證制度，房東不需支付任何代辦規費",
        ],
        forbidden_facts=[
            "本案為國家住宅及都市更新中心合法特許專案",
            "絕無任何私下收費或產權侵占風險",
        ],
        tool_results={
            "check_personal_records": {
                "title": "內政部公版租賃契約與公證協議草案",
                "content": "【遊戲模擬查證】檢閱合約文件：條款引用內政部租賃住宅市場發展及管理條例之公版範本，公證費用依法載明由公部門專款補助。",
                "is_independent": True,
                "source_id": "contract_paper",
                "claim_addressed": "contract_terms",
            },
            "check_official_registry": {
                "title": "內政部不動產資訊平台特許業者查詢",
                "content": "【遊戲模擬查證】查詢不動產資訊平台合格廠商名冊：該公司確實名列公部門第四期得標執行廠商，租賃住宅管理人員執照有效。",
                "is_independent": True,
                "source_id": "official_registry_db",
                "claim_addressed": "license_check",
            },
            "check_independent_service": {
                "title": "國家住宅及都市更新中心專線核實",
                "content": "【遊戲模擬查證】撥打住都中心官方客服電話：專員核實該公司為簽約特許代管業者，承辦專員姓名工號查對無誤。",
                "is_independent": True,
                "source_id": "independent_hotline",
                "claim_addressed": "agency_verification",
            },
        },
        prerequisites={"min_cash": 0, "required_flags": [], "required_stories": ["vacant_house_group"]},
        branches={
            "has_guestroom_decor": "提供房東阿姨客房佈置參考範例提升租金收益",
            "regular": "依政府正規管道完成加入包租代管",
        },
        outcomes={
            "trust": "確認為政府合法特許專案，房東阿姨安心加入社會住宅並享有稅賦減免與修繕津貼。",
            "report": "草率將政府公信專案舉報為詐騙，浪費行政資源並錯失合法補助。",
            "safe_exit": "建議先約在公證處當面審核合約，循序漸進安心完成簽約。",
        },
    ),
    "fire_safety_inspection": StoryDefinition(
        story_id="fire_safety_inspection",
        contact_id="landlady",
        title="公寓消防安全設備限期改善單",
        learning_objective="辨認假借消防安全名義強迫推銷高價器材之不肖手法，掌握官方消防會勘流程與合規查證程序。",
        truth="pause_pending",
        source_adaptation_mark="教學原創",
        fixed_facts={
            "letter_title": "消防安全設備自主維護宣導會勘通知單",
            "amount": 7000,
            "amount_desc": "7,000 元（指定廠商兩支滅火器費用）",
            "alleged_penalty": "函文提及若未依限購置設備恐有裁罰風險，附帶民間器材訂購單每支 3,500 元",
            "correct_action": "向在地消防分隊預防專線核對發文字號，依合格通路選購合規認可器材，切勿逕行向指定帳戶匯款",
        },
        npc_claims={
            "initial": "阿姨信箱收到一張大紅色的消防安檢改善通知，說公寓滅火器不合格要限期處理，還夾著器材劃撥單，這公文是真的假的？",
            "doubt": "通知單印得滿紙紅字好嚇人，寫什麼違規要重罰，阿姨差點就被嚇到去郵局劃撥了。",
            "amount": "後面夾的民間器材訂購單開價兩支滅火器 7,000 元（每支 3,500 元），比市價貴了好幾倍！",
            "evidence": "信箱裡只放了一張宣導會勘通知單與訂購單，沒有主管消防機關的正式查驗處分書發文字號。",
            "vendor": "寄件單位寫得像公家機關，但下面的訂購專線是一家民間消防器材設備行。",
            "pause_reaction": "阿姨懂了！先把劃撥單收起來不繳。我們先打電話去轄區消防分隊問清楚改善規定，免得花冤枉錢！",
        },
        discloseable_facts=[
            "收到消防安全檢查宣導改善單",
            "函文隨附特定民間器材廠商訂購單要求匯款 7,000 元",
            "正確流程應先查核消防分隊紀錄，不應立即匯款",
        ],
        forbidden_facts=[
            "民間器材廠商印製類似公文之強迫推銷手法",
            "消防局依法絕不會隨函附帶特定民間帳號強制收費",
        ],
        tool_results={
            "check_personal_records": {
                "title": "通知單發文字號與排版細閱",
                "content": "【遊戲模擬查證】審視通知單：公文雖印有宣導紅印，但文號缺少正式機關代碼，底部訂購電話為民間企業專線，非政府公庫。",
                "is_independent": True,
                "source_id": "contract_paper",
                "claim_addressed": "letter_format",
            },
            "check_official_registry": {
                "title": "消防署器材認可檢驗標章規範查詢",
                "content": "【遊戲模擬查證】查詢消防署認可規定：合規滅火器均貼有銀色雷射防偽認可標籤，市售常態均價約 800 至 1,200 元，無強制向指定廠商採購規定。",
                "is_independent": True,
                "source_id": "official_registry_db",
                "claim_addressed": "equipment_standards",
            },
            "check_independent_service": {
                "title": "直撥轄區消防分隊預防課查證",
                "content": "【遊戲模擬查證】撥打在地消防分隊電話：隊員說明消防隊絕不會寄送附帶廠商收費帳號之訂購單，此為民間業者推銷手法，請至正規通路購置。",
                "is_independent": True,
                "source_id": "independent_hotline",
                "claim_addressed": "official_clarification",
            },
            "use_second_phone": {
                "title": "以獨立電話向消防分隊求證",
                "content": "【遊戲模擬查證】外撥消防分隊值勤台：值班員警叮嚀注意假借安檢名義之推銷，若遭騷擾可通報轄區警員。",
                "is_independent": True,
                "source_id": "independent_hotline",
                "claim_addressed": "official_clarification",
            },
        },
        prerequisites={"min_cash": 0, "required_flags": [], "required_stories": []},
        branches={
            "has_second_phone": "使用獨立專線外撥消防分隊預防課直接核實",
            "regular": "依正規消防規範由合格通路採購器材",
        },
        outcomes={
            "safe_exit": "指導房東阿姨先向在地消防分隊核對發文字號，拆穿民間器材行假借安檢名義之強銷手法，改由合規通路選購合格滅火器，審慎化解爭議並達成自主維護防護目標。",
            "report": "確認民間廠商假冒公務名義並檢附不實公文後向主管機關與消保官申訴檢舉，有效遏止不肖業者在社區散布假公文強銷器材之行為。",
            "comply": "未經查證即依未具公信力之劃撥單匯款 7,000 元購買來路不明器材，蒙受金錢損失且恐獲不合格滅火設備。",
        },
    ),

    # ── 阿燦 (a_can) ──
    "streamer_traffic_booster": StoryDefinition(
        story_id="streamer_traffic_booster",
        contact_id="a_can",
        title="直播帶貨智能流量增長工具",
        learning_objective="辨別假借外掛工具竊取後台帳密之資安風險，防範未經官方認證之外部程式與非正常刷榜軟體。",
        truth="scam",
        source_adaptation_mark="教學原創",
        fixed_facts={
            "software_name": "極速流光 AI 萬人在線推流引擎",
            "developer": "雲端極致科技有限公司 銷售經理",
            "amount": 6800,
            "amount_desc": "6,800 元（外掛開通軟體費）",
            "installation": "要求提供頻道主帳號密碼，或在電腦安裝包含未知來源之執行安裝包",
        },
        npc_claims={
            "initial": "兄弟！阿燦我這陣子直播人數真的很慘…剛才有人私訊說有黑科技 AI 推流軟體可以幫我衝人氣，我好心動，你幫我把把關？",
            "doubt": "對方傳了好多其他直播主的後台截圖，人數真的都是幾萬人在線耶！但要我把直播頻道帳號密碼給他綁定…",
            "amount": "對方說一套開通費 6,800 元，保證今晚開播常駐 5,000 人在線，但要先轉帳或交出頻道管理帳密。",
            "evidence": "對方只傳了幾張修圖軟體做出來的假流量後台截圖，沒有任何軟體著作權證明或合法登記統編。",
            "vendor": "私訊對方自稱是『雲端極致科技』的銷售總監。",
            "pause_reaction": "兄弟你說得對！阿燦我雖然急著衝流量，但也不能病急亂投醫。我們先查查這家公司跟軟體到底有沒有鬼！",
        },
        discloseable_facts=[
            "軟體宣稱能保證直播間數千人在線",
            "收費 6,800 元並要求交出頻道後台管理員帳密",
            "提供外部未知來源之執行安裝檔",
        ],
        forbidden_facts=[
            "所謂推流軟體含有竊密後門程式，會盜取頻道所有權與憑證",
            "底層真實身分是 scam",
        ],
        tool_results={
            "check_personal_records": {
                "title": "官方平台社群服務條款查閱",
                "content": "【遊戲模擬查證】檢閱平台服務條款：明文禁止使用任何非官方機器人或未授權外部外掛，偵測到將面臨永久停權。",
                "is_independent": True,
                "source_id": "contract_paper",
                "claim_addressed": "terms_of_service",
            },
            "check_official_registry": {
                "title": "資安檢驗沙盒軟體行為分析",
                "content": "【遊戲模擬查證】使用檢驗沙盒分析安裝包：程式含有嘗試提取瀏覽器 Cookie 與帳號憑證之後門行為，具備高度安全風險。",
                "is_independent": True,
                "source_id": "security_sandbox",
                "claim_addressed": "software_safety",
            },
            "check_independent_service": {
                "title": "直播平台官方創作者支援專線",
                "content": "【遊戲模擬查證】致電官方創作者支援中心：專員強調官方絕未授權任何保證推流之外掛軟體，請勿交出後台權限。",
                "is_independent": True,
                "source_id": "independent_hotline",
                "claim_addressed": "platform_policy",
            },
            "use_second_phone": {
                "title": "使用備用設備隔離檢視安裝包細節",
                "content": "【遊戲模擬查證】使用未登入主要帳號之備用設備檢視：確認該檔案權限清單包含讀取所有儲存空間與通聯記錄，風險極高。",
                "is_independent": True,
                "source_id": "security_sandbox",
                "claim_addressed": "software_safety",
            },
        },
        prerequisites={"min_cash": 0, "required_flags": [], "required_stories": []},
        branches={
            "has_second_phone": "使用備用設備進行隔離檢視避免主要工作設備受威脅",
            "regular": "拒絕安裝未認證外掛保護頻道安全",
        },
        outcomes={
            "report": "及時阻止安裝木馬，保護阿燦的直播頻道所有權免遭盜用封鎖。",
            "comply": "交付帳密並匯款，當晚頻道被盜用於詐騙虛擬幣，慘遭官方永久封停。",
            "safe_exit": "建議阿燦專注內容創作並透過官方合法廣告投放，遠離非法外掛危險。",
        },
    ),
    "co_parenting_cat": StoryDefinition(
        story_id="co_parenting_cat",
        contact_id="a_can",
        title="三家共養社區流浪橘貓分攤",
        learning_objective="辨識鄰里正常互助共照機制，查驗合法獸醫診療機構收據與微晶片登記資料之正當流程。",
        truth="legit",
        source_adaptation_mark="教學原創",
        fixed_facts={
            "cat_name": "橘子（社區共養街貓）",
            "clinic_name": "康和動物醫院",
            "vet_name": "林院長（具合法獸醫師證書）",
            "amount": 1200,
            "amount_desc": "醫療費 3,600 元，三家均攤每戶 1,200 元（附動物醫院收據）",
            "procedure": "年度三合一疫苗接種、晶片植入與體內外驅蟲",
            "payment": "三家鄰居均攤每戶 1,200 元，提供正式診療收據與晶片登記證",
        },
        npc_claims={
            "initial": "我們這棟樓三家一起照顧的那隻大橘貓，阿燦我剛帶牠從動物醫院做完檢查回來！有醫療費要跟大家均攤，我傳收據給你看好嗎？",
            "doubt": "康和動物醫院就在我們巷口，林醫師大家都很熟，收據上還有印晶片號碼。",
            "amount": "動物醫院醫療費總共 3,600 元，我們三家鄰居均攤，每戶是 1,200 元。",
            "evidence": "阿燦手上有康和動物醫院開立的正式診療收據、三合一疫苗注射證明與晶片登記證書。",
            "vendor": "診療院所是巷口的康和動物醫院林院長，由林獸醫師親自看診。",
            "pause_reaction": "沒問題！三家分攤橘子的醫藥費本來就要明細公開，我們先把醫院收據跟晶片登記證對一下！",
        },
        discloseable_facts=[
            "項目為鄰里共照流浪貓之常態醫療分攤",
            "由合法立案康和動物醫院出具明細收據",
            "每戶均攤 1,200 元，收據載明晶片條碼",
        ],
        forbidden_facts=[
            "本案為完全真實友善鄰里共照互助",
            "無任何詐騙情節",
        ],
        tool_results={
            "check_personal_records": {
                "title": "動物醫院醫療明細收據審閱",
                "content": "【遊戲模擬查證】檢視醫療收據：載明診療機構執照字號，晶片號碼（900012345678901）清楚列印，疫苗批號透明完整。",
                "is_independent": True,
                "source_id": "contract_paper",
                "claim_addressed": "clinic_receipt",
            },
            "check_official_registry": {
                "title": "農業部寵物登記管理資訊網核驗",
                "content": "【遊戲模擬查證】至農業部動植物防疫檢疫署系統查詢：晶片號碼確實登記於該社區共同照護名下，獸醫登記資料相符。",
                "is_independent": True,
                "source_id": "official_registry_db",
                "claim_addressed": "pet_registry",
            },
            "check_independent_service": {
                "title": "親訪康和動物醫院林院長核實",
                "content": "【遊戲模擬查證】直接向動物醫院核對：林院長確認日前確實由阿燦與鄰居帶貓前往施打疫苗，醫療開支實報實銷無虛報。",
                "is_independent": True,
                "source_id": "independent_hotline",
                "claim_addressed": "vet_confirmation",
            },
        },
        prerequisites={"min_cash": 0, "required_flags": [], "required_stories": ["streamer_traffic_booster"]},
        branches={
            "has_pet_supplies": "提供高級寵物用品組作為貓咪照護禮物，阿燦好感與信任大幅提升",
            "regular": "依明細收據順利分攤支出完成善舉",
        },
        outcomes={
            "trust": "確認醫療開支真實合理，支持友善鄰里共照，增進社區情誼與互信。",
            "report": "無端懷疑鄰里共照為詐騙斂財，傷了鄰居熱情並破壞社區和諧。",
            "safe_exit": "建議至動物醫院現場確認後再付款，穩健完成分攤。",
        },
    ),
    "cross_brand_charity_finale": StoryDefinition(
        story_id="cross_brand_charity_finale",
        contact_id="a_can",
        title="跨界品牌聯合慈善音樂會",
        learning_objective="跨角色多方利害關係人合作查核：落實文化部立案核備、募款專戶透明性與公益演出審批查驗，符合首度通關之 2.5 倍獎勵里程碑。",
        truth="legit",
        source_adaptation_mark="教學原創",
        is_chapter_finale=True,
        fixed_facts={
            "event_title": "2026 曙光重現跨界慈善巡迴音樂節",
            "participants": "阿燦（直播主辦）、薇姐（贊助會場押金）、豪哥（媒合展演設備）",
            "amount": 0,
            "amount_desc": "0 元（多方公信公益信託與衛福部核備勸募，無私人索款）",
            "charity_target": "支持偏鄉孩童音樂與反詐通識教育計畫",
            "permit_no": "文化部文藝字第 11305432 號公開展演核准函",
            "mohw_permit_no": "衛部救字第 1130123456 號公益勸募許可",
            "fundraising_period": "2026/10/01 - 2026/12/31",
            "bank_account": "台灣銀行公益專用託管信託專戶（由會計師事務所查核簽證，專款專用）",
        },
        npc_claims={
            "initial": "這是我們大家的心血！我和豪哥、薇姐打算聯合辦一場大型反詐慈善音樂會，所有政府核備跟信託都辦好了，請你以總顧問身分幫我們做最後審核！",
            "doubt": "豪哥贊助燈光音響，薇姐贊助會場押金，我負責線上推廣，款項完全透明公開！",
            "amount": "全程公開信託，由會計師每週簽證財務報表，無任何私人口袋資金！",
            "evidence": "三方共同出具了文化部展演許可函、衛福部公益勸募許可文號、會計師查核報告與台銀信託公文。",
            "vendor": "由阿燦、薇姐、豪哥三方共同聯合主辦，由台灣銀行擔任信託保管人。",
            "pause_reaction": "太好了！慈善音樂會本來就該最高規格透明公開，我們先把衛福部勸募許可文號、勸募期間與台銀信託公文逐項查對清楚！",
        },
        discloseable_facts=[
            "本案為阿燦、豪哥、薇姐共同發起之跨角色聯合專案",
            "取得文化部展演核准與衛福部公益勸募許可文號（衛部救字第 1130123456 號）",
            "勸募期間、專戶名稱與財務簽證經獨立監管，無私人匯款路徑",
        ],
        forbidden_facts=[
            "此為章末里程碑正式合格多方公益專案",
            "完全合法，結算適用 2.5 倍特殊結算加成",
        ],
        tool_results={
            "check_personal_records": {
                "title": "三方合作備忘錄與會計師簽證文件",
                "content": "【遊戲模擬查證】檢閱跨角色合作契約：載明阿燦、豪哥、薇姐各自權責，款項全數由台灣銀行信託財產專戶保管，動支需會計師共同簽署。",
                "is_independent": True,
                "source_id": "contract_paper",
                "claim_addressed": "trust_agreement",
            },
            "check_official_registry": {
                "title": "衛福部公益勸募管理系統核驗",
                "content": "【遊戲模擬查證】查詢衛福部公益勸募管理系統：衛部救字第 1130123456 號立案有效，活動名稱、主辦團體、勸募期間與台銀信託專戶完全相符，專款專用。",
                "is_independent": True,
                "source_id": "official_registry_db",
                "claim_addressed": "charity_permit",
            },
            "check_independent_service": {
                "title": "台灣銀行信託部專線查核",
                "content": "【遊戲模擬查證】致電台灣銀行總行信託部：行員核對信託契約統一編號，確認該專戶屬合規公益信託，受主管機關監管。",
                "is_independent": True,
                "source_id": "independent_hotline",
                "claim_addressed": "trust_account_status",
            },
            "use_commemorative_plaque": {
                "title": "出示防詐紀念桌牌（象徵信物）",
                "content": "【遊戲模擬查證】出示防詐紀念桌牌作為交流信物（紀念裝飾性質，非獨立法定查證管道）。",
                "is_independent": False,
                "source_id": None,
                "claim_addressed": None,
            },
        },
        prerequisites={
            "min_cash": 0,
            "required_flags": [],
            "required_stories": [
                "scheduled_goodnight",
                "cosplay_custom_import",
                "influencer_mcn_contract",
                "subsidized_social_housing",
                "co_parenting_cat",
            ],
        },
        branches={
            "has_commemorative_plaque": "擺放紀念桌牌見證簽署，凝聚最高情誼",
            "regular": "按法定程序查驗三方信託順利結案",
        },
        outcomes={
            "trust": "成功完成跨角色多方慈善音樂會查核！樹立社區反詐合作典範，並獲得 2.5 倍章末特殊高額加成！",
            "report": "無端誣指合規透明之多方公益行動為詐騙，破壞所有人脈牽絆。",
            "safe_exit": "建議增加線上即時對帳公開網頁後再全面推廣，促成更完善之公益管理。",
        },
    ),
}


def validate_story_catalog() -> dict[str, Any]:
    """驗證故事目錄之完整性與無循環依賴（滿足 C1, R1, R3 驗收）。

    檢查點：
    1. 恰好或至少 5 個聯絡人，且每人至少 3 個獨立事件（共 >= 15）。
    2. 包含至少 3 個怪異故事（is_weird_story=True）。
    3. 涵蓋合法、詐騙、合理暫停待補件三種真相。
    4. 無循環依賴或無法滿足之先決條件（DAG 拓撲排序檢查）。
    5. 每個故事均具備至少 2 種實質處置路徑。
    6. 所有故事具備 fixed_facts, npc_claims, tool_results, learning_objective。
    7. 所有故事具備明確認證金額（0 或具體金額，杜絕發明 $1000）。
    """
    errors: list[str] = []

    # 1. 聯絡人與故事數量
    contacts_in_catalog: dict[str, list[str]] = {cid: [] for cid in CONTACTS}
    for sid, s in STORIES_CATALOG.items():
        if s.contact_id not in CONTACTS:
            errors.append(f"Story {sid} has invalid contact_id {s.contact_id}")
        else:
            contacts_in_catalog[s.contact_id].append(sid)

    for cid, stories in contacts_in_catalog.items():
        if len(stories) < 3:
            errors.append(f"Contact {cid} has fewer than 3 stories ({len(stories)})")

    total_stories = len(STORIES_CATALOG)
    if total_stories < 15:
        errors.append(f"Total stories in catalog {total_stories} < 15")

    # 2. 怪異故事檢驗
    weird_stories = [s for s in STORIES_CATALOG.values() if s.is_weird_story]
    if len(weird_stories) < 3:
        errors.append(f"Fewer than 3 weird stories ({len(weird_stories)})")

    # 3. 真相分佈檢驗（全目錄與初始開放集）
    truths = {s.truth for s in STORIES_CATALOG.values()}
    for required_truth in ["scam", "legit", "pause_pending"]:
        if required_truth not in truths:
            errors.append(f"Missing required truth type {required_truth}")

    initial_stories = [s for s in STORIES_CATALOG.values() if not s.prerequisites.get("required_stories")]
    initial_truths = {s.truth for s in initial_stories}
    for required_truth in ["scam", "legit", "pause_pending"]:
        if required_truth not in initial_truths:
            errors.append(f"Initial accessible stories missing truth type {required_truth}")

    # 4. 先決條件無循環檢驗 (DAG Cycle Detection)
    visited: set[str] = set()
    visiting: set[str] = set()

    def check_cycle(sid: str) -> None:
        visiting.add(sid)
        s = STORIES_CATALOG.get(sid)
        if s and s.prerequisites and "required_stories" in s.prerequisites:
            for req in s.prerequisites["required_stories"]:
                if req not in STORIES_CATALOG:
                    errors.append(f"Story {sid} has nonexistent prerequisite story: {req}")
                elif req in visiting:
                    errors.append(f"Cycle detected in story prerequisites: {sid} -> {req}")
                elif req not in visited:
                    check_cycle(req)
        visiting.remove(sid)
        visited.add(sid)

    for sid in STORIES_CATALOG:
        if sid not in visited:
            check_cycle(sid)

    # 5. 處置路徑、內容與客觀事實
    for sid, s in STORIES_CATALOG.items():
        if len(s.outcomes) < 2:
            errors.append(f"Story {sid} has fewer than 2 outcomes ({len(s.outcomes)})")
        if not s.tool_results:
            errors.append(f"Story {sid} has empty tool_results")
        if not s.learning_objective:
            errors.append(f"Story {sid} missing learning_objective")
        if not s.fixed_facts:
            errors.append(f"Story {sid} missing fixed_facts")
        if "amount" not in s.fixed_facts:
            errors.append(f"Story {sid} missing explicit amount in fixed_facts")
        if "pause_reaction" not in s.npc_claims:
            errors.append(f"Story {sid} missing pause_reaction in npc_claims")

        # 檢查中性標題（不叫「假X」或「詐騙」）
        if "假" in s.title or "詐騙" in s.title or "陷阱" in s.title:
            errors.append(f"Story {sid} title '{s.title}' is not neutral")

    return {
        "is_valid": len(errors) == 0,
        "total_stories": total_stories,
        "total_contacts": len(CONTACTS),
        "weird_stories_count": len(weird_stories),
        "errors": errors,
    }


def get_story(story_id: str) -> StoryDefinition | None:
    return STORIES_CATALOG.get(story_id)


def get_stories_for_contact(contact_id: str) -> list[StoryDefinition]:
    return [s for s in STORIES_CATALOG.values() if s.contact_id == contact_id]


def pick_story_for_contact(
    contact_id: str, completed_story_ids: list[str] | set[str]
) -> StoryDefinition:
    """為聯絡人挑選符合先決條件且尚未完成之事件；若全已完成則可循環重玩已合格故事。"""
    stories = get_stories_for_contact(contact_id)
    completed_set = set(completed_story_ids)
    available: list[StoryDefinition] = []
    qualified_stories: list[StoryDefinition] = []
    for s in stories:
        reqs = s.prerequisites.get("required_stories", [])
        if all(r in completed_set for r in reqs):
            qualified_stories.append(s)
            if s.story_id not in completed_set:
                available.append(s)

    if available:
        return available[0]
    if qualified_stories:
        return qualified_stories[0]
    return stories[0] if stories else list(STORIES_CATALOG.values())[0]
