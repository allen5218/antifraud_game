/**
 * 前端情境 RAG (Retrieval-Augmented Generation) 知識檢索與反制引擎。
 *
 * 核心功能：
 * 1. 涵蓋真實防詐實境中玩家常提出的質疑（訂購商品確認、執照、金管會、營業字號、個人戶頭、面交、165通報、釣魚網址）。
 * 2. 透過語意分詞與關鍵詞權重即時檢索最貼切的反制策略（Scammer Rebuttal 或 Legit Response）。
 * 3. 精準對齊玩家具體輸入的詞句，絕不答非所問。
 */

export interface KnowledgeChunk {
  id: string
  category: "investment" | "shopping" | "fake-sale" | "romance" | "atm"
  role: "scam" | "legit"
  topic:
    | "license"
    | "account"
    | "profit"
    | "meet"
    | "police_165"
    | "order"
    | "urgency"
  keywords: string[]
  contextFact: string
  tactics: string[]
  rebuttalResponses: string[]
}

export const FRONTEND_KNOWLEDGE_BASE: KnowledgeChunk[] = [
  // ── 1. 假投資詐欺 (investment) ──
  {
    id: "inv_scam_license_denial",
    category: "investment",
    role: "scam",
    topic: "license",
    keywords: [
      "金管會",
      "執照",
      "登記",
      "營業字號",
      "特許",
      "證券期貨局",
      "證期局",
      "投顧",
      "核准",
      "查無",
      "合法",
      "牌照",
      "立案",
      "監管",
      "公會",
      "統編",
      "商工登記",
    ],
    contextFact:
      "金管會證期局查無特許執照；宏盛資本宣稱受海外開曼與塞浦路斯離岸監管以規避境內稽查。",
    tactics: ["authority", "time_pressure"],
    rebuttalResponses: [
      "您去查台灣金管會名冊當然查不到！我們宏盛資本走的是開曼群島頂級離岸對沖私募基金結構，受海外塞浦路斯 CySEC 離岸監管，根本不受台灣境內繁瑣法規限制。台灣一般投顧怎麼可能拿到日化 15% 的內線額度？名額只保留到下午 3:30 前，您如果一直懷疑沒魄力，我現在就把這席位讓給排隊候補的學員了！",
      "內線私募走的是境外專用機構代操通道，台灣證期局名冊上只會有那些賺不到 5% 通膨的平庸券商。我們操盤團隊受海外離岸信託基金監管，合約具備國際仲裁效力。VIP 席位只剩最後一位，您若要因為查境內名冊而放棄翻倍機會，我也只能尊重。",
    ],
  },
  {
    id: "inv_scam_personal_account",
    category: "investment",
    role: "scam",
    topic: "account",
    keywords: [
      "個人戶頭",
      "人頭戶",
      "帳號",
      "人頭",
      "為什麼是個人",
      "私人口座",
      "受款人",
      "指定帳戶",
      "匯到哪",
      "轉帳帳號",
      "匯款帳號",
      "約定帳號",
      "特別戶頭",
      "入金帳戶",
    ],
    contextFact: "要求匯款至個人戶頭，狡辯為跨國券商在台特約結算代收專員通道。",
    tactics: ["authority", "greed"],
    rebuttalResponses: [
      "那是我們合作券商在台灣的『授權結算代收專用通道』！因為國際外匯申報上限管制，大額私募進場必須透過境內特約子帳戶進行資金集中造冊，完成建倉後系統會直接把額度全數撥入您的專屬交易子帳號，群裡幾百位學員每週出金都是走這套合規結算路徑！",
    ],
  },
  {
    id: "inv_scam_guaranteed_profit",
    category: "investment",
    role: "scam",
    topic: "profit",
    keywords: [
      "保證獲利",
      "穩賺",
      "保本",
      "零風險",
      "違法",
      "不可能",
      "投報率",
      "幾趴",
      "利息",
      "獲利幾趴",
      "賺多少",
      "怎麼保證",
      "天上掉餡餅",
      "騙局",
    ],
    contextFact:
      "標榜高額保證獲利與零風險保本，以量化對沖套利與假合約掩飾違法吸金本質。",
    tactics: ["greed", "social_proof"],
    rebuttalResponses: [
      "市面上的普通散戶投資當然不敢喊保證，但我們團隊採用的是全球高頻量化跨市場期現套利！我們鎖定的是買賣價差與瞬時造市利差，無論大盤漲跌都能保持日均 12%~15% 的無風險淨收益，合約內直接附帶第三方資金保本承諾！",
    ],
  },
  {
    id: "inv_scam_meet_offline",
    category: "investment",
    role: "scam",
    topic: "meet",
    keywords: [
      "面交",
      "簽約",
      "見面",
      "實體門市",
      "臨櫃",
      "公司地址",
      "公司在哪",
      "辦公室",
      "去你們公司",
    ],
    contextFact: "拒絕線下接觸與面交簽約，藉口大戶隱私與跨國操盤保密條款。",
    tactics: ["authority", "trust_building"],
    rebuttalResponses: [
      "我們是封閉式私人操盤機構，涉及多位上市櫃政商大戶的持倉機密，依跨國保密協定嚴格禁止任何線下公開接觸！所有資金交易與法規清算全部在雲端金融安全通道完成，這才是頂級對沖圈的運作常態。",
    ],
  },
  {
    id: "inv_scam_police_165",
    category: "investment",
    role: "scam",
    topic: "police_165",
    keywords: [
      "165",
      "警察",
      "報警",
      "詐騙",
      "被騙",
      "黑名單",
      "受害",
      "165反詐騙",
      "報案",
    ],
    contextFact: "遭 165 通報為高風險，狡辯為同業惡意檢舉競爭與黑函抹黑。",
    tactics: ["authority", "fear"],
    rebuttalResponses: [
      "165 那種大眾通報系統只要被少數同行惡意檢舉就會上榜！我們團隊績效太好，經常遭到傳統平庸券商動員網軍惡意抹黑。我們幾百位學員每天都能自由全額提領獲利，如果真是詐騙，我們怎麼可能還能在線上公開帶單？請您相信親眼所見的真實績效！",
    ],
  },

  // ── 2. 拍賣與購物詐騙 (fake-sale, shopping) ──
  {
    id: "shop_scam_what_product",
    category: "fake-sale",
    role: "scam",
    topic: "order",
    keywords: [
      "訂了什麼",
      "買了什麼",
      "什麼商品",
      "什麼東西",
      "買什麼",
      "哪件",
      "什麼貨",
      "訂什麼",
      "什麼訂單",
      "哪筆",
      "商品名稱",
      "訂單編號",
      "內容",
      "我訂了",
      "我買了",
    ],
    contextFact:
      "玩家詢問具體購買明細，詐騙客服聲稱為昨日訂購之日本頂級美妝禮盒。",
    tactics: ["trust_building", "authority"],
    rebuttalResponses: [
      "系統紀錄顯示是您昨天在平台訂購的『日本頂級保濕美妝禮盒（訂單金額 $2,980 元）』呀！因為超商物流條碼掃描時重複入帳，系統轉入異常分期程序了，我們才趕快聯絡您核銷解除！",
    ],
  },
  {
    id: "shop_scam_how_to_cancel",
    category: "fake-sale",
    role: "scam",
    topic: "order",
    keywords: [
      "怎麼撤銷",
      "怎麼處理",
      "如何取消",
      "不要扣款",
      "怎麼辦",
      "怎麼做",
      "取消",
      "解除",
      "撤銷",
      "不要分期",
      "怎麼弄",
      "幫我取消",
      "如何解除",
    ],
    contextFact: "玩家詢問如何取消連續扣款，詐騙客服誘導點擊外部安全核銷連結。",
    tactics: ["time_pressure", "authority"],
    rebuttalResponses: [
      "請您不要慌！只要在今晚 12 點前，透過我們官方即時核銷專區完成身分驗證，系統 10 分鐘內就會全額註銷連續扣款紀錄，絕不會扣您半毛錢！我現在將安全通道連結發給您好嗎？",
    ],
  },
  {
    id: "shop_scam_who_are_you",
    category: "fake-sale",
    role: "scam",
    topic: "license",
    keywords: [
      "你是誰",
      "工號",
      "哪位",
      "客服編號",
      "哪家公司",
      "什麼單位",
      "叫什麼",
      "電話",
    ],
    contextFact: "玩家詢問客服身分與工號，詐稱商城特約物流客服小美。",
    tactics: ["authority", "trust_building"],
    rebuttalResponses: [
      "我是商城平台特約金流客服小美，工號是 CS-5842！我們剛才接獲超商物流中心通報您的異常重複扣款件，怕影響您的信用紀錄才特地私訊協助您緊急撤銷的！",
    ],
  },
  {
    id: "shop_scam_order_amount",
    category: "fake-sale",
    role: "scam",
    topic: "order",
    keywords: [
      "多少錢",
      "金額",
      "多少",
      "扣多少",
      "費用",
      "手續費",
      "價錢",
      "幾元",
    ],
    contextFact: "玩家詢問扣款金額，詐稱條碼誤設為 12 期連續扣款總額數萬元。",
    tactics: ["time_pressure", "fear"],
    rebuttalResponses: [
      "您原本的訂單金額是 2,980 元，但因為系統誤設成 12 期連續扣款，如果不趕快線上撤銷，銀行每個月都會自動扣款 2,980 元，總共會被多扣三萬多元！",
    ],
  },
  {
    id: "shop_scam_phishing_link",
    category: "fake-sale",
    role: "scam",
    topic: "license",
    keywords: [
      "釣魚",
      "網址",
      "twnic",
      "不是官方",
      "假網址",
      "域名",
      "境外",
      "假的",
      "外部連結",
      "連結",
      "怪怪的",
      "為什麼不是官網",
    ],
    contextFact:
      "提供仿冒釣魚認證網址，狡辯為雙十一高負載專用跨境 SSL 加密備援站點。",
    tactics: ["authority", "fear"],
    rebuttalResponses: [
      "那是因為例行金流結算流量過大，平台工程部啟用的『跨境負載均衡 SSL 專用鏡像站點』！完全通過國際 VeriSign 金融安全認證，專門處理即時協議簽署與退款審核，絕非普通一般外部網址，請您立即點擊完成綁定！",
    ],
  },

  // ── 3. ATM / 假檢警 (atm) ──
  {
    id: "atm_scam_subpoena_threat",
    category: "atm",
    role: "scam",
    topic: "license",
    keywords: [
      "公文",
      "地檢署",
      "檢察官",
      "刑事",
      "警察",
      "133條",
      "洗錢",
      "拘票",
      "傳票",
      "分行",
      "監管帳戶",
      "清查",
      "監管",
    ],
    contextFact:
      "冒充特偵檢察官出示假公文，恐嚇涉入跨國特大洗錢案，威脅凍結名下所有財產。",
    tactics: ["authority", "fear", "time_pressure"],
    rebuttalResponses: [
      "這裡是新北地檢署特偵指揮中心！刑事訴訟法第 133 條之規定清楚明瞭，主嫌名下查扣的地下洗錢人頭帳戶就是用您的身分證號開立！若您未配合清查，本庭將直接簽發拘票將您列為共犯收押禁見，並依法凍結您名下的全部資產！",
    ],
  },

  // ── 4. 假交友殺豬盤 (romance) ──
  {
    id: "rom_scam_customs_fee",
    category: "romance",
    role: "scam",
    topic: "account",
    keywords: [
      "海關",
      "保證金",
      "外匯",
      "包裹",
      "代墊",
      "借錢",
      "匯款",
      "寄送",
      "黃金",
      "獎金",
      "扣留",
      "清關",
      "代收",
      "多少錢",
    ],
    contextFact: "藉口海外包裹被扣留，要求代墊清關費用。",
    tactics: ["trust_building", "greed"],
    rebuttalResponses: [
      "親愛的，這箱包裹裡裝著我這幾年在鑽井平台攢下的外幣存單與買給你的禮物！海關說因為涉及跨境資產，必須由在台灣的伴侶代繳清關規費 $65,000。我現在人在外海鑽探平台根本無法操作網銀，除了你我真的不知道還能信任誰了！",
    ],
  },
]

export class FrontendRagEngine {
  private corpus: KnowledgeChunk[]

  constructor(corpus: KnowledgeChunk[] = FRONTEND_KNOWLEDGE_BASE) {
    this.corpus = corpus
  }

  public retrieve(
    category: string,
    role: string,
    playerText: string,
  ): { chunk: KnowledgeChunk | null; score: number } {
    const textLower = playerText.toLowerCase()
    let bestChunk: KnowledgeChunk | null = null
    let bestScore = 0

    const isShopCategory = (cat: string) =>
      cat === "shopping" || cat === "fake-sale"

    for (const chunk of this.corpus) {
      const matchCategory =
        chunk.category === category ||
        (isShopCategory(category) && isShopCategory(chunk.category))
      if (!matchCategory) continue
      if (chunk.role !== role) continue

      let score = 0
      for (const kw of chunk.keywords) {
        const kwLower = kw.toLowerCase()
        if (textLower.includes(kwLower)) {
          score += 3.0 * (1 + 0.1 * kwLower.length)
        }
      }

      if (score > bestScore) {
        bestScore = score
        bestChunk = chunk
      }
    }

    return { chunk: bestChunk, score: bestScore }
  }

  public generateAugmentedReply(
    category: string,
    role: string,
    displayName: string,
    playerText: string,
  ): { reply: string; tactics: string[] } {
    const { chunk, score } = this.retrieve(category, role, playerText)

    if (chunk && score >= 2.0) {
      let reply = chunk.rebuttalResponses[0]
      if (reply.includes("宏盛資本") && displayName) {
        reply = reply.replace("宏盛資本", `宏盛資本（${displayName}團隊）`)
      }
      return { reply, tactics: chunk.tactics }
    }

    // 依分類分別給予精準擬真回覆，絕不胡說八道或亂套用「名額」
    if (category === "fake-sale" || category === "shopping") {
      const lower = playerText.toLowerCase()
      if (
        lower.includes("騙") ||
        lower.includes("詐") ||
        lower.includes("165")
      ) {
        return {
          reply:
            "買家您好，我們是平台正規物流客服，這筆訂單重複扣款若今晚沒在系統撤銷，銀行系統就會自動連續扣款，絕無欺騙！請您務必配合核對資料。",
          tactics: ["authority", "fear"],
        }
      }
      return {
        reply:
          "買家您好！系統顯示該筆訂單因超商入帳異常產生重複扣款，若不及時撤銷將影響您的銀行帳戶，請問您方便配合核對一下收件資料嗎？",
        tactics: ["time_pressure", "trust_building"],
      }
    }

    if (category === "romance") {
      return {
        reply:
          "親愛的，外海油田基地的收訊不太穩定，但我只要看到你的訊息就覺得很安心，你在台灣今天過得還順利嗎？",
        tactics: ["trust_building"],
      }
    }

    if (category === "atm") {
      return {
        reply:
          "這裡是地檢署承辦人員，本案現已進入重大司法偵查程序，請您保持通話配合清查，切勿延誤！",
        tactics: ["authority", "fear"],
      }
    }

    // investment 投資專用
    const lower = playerText.toLowerCase()
    if (
      lower.includes("詐騙") ||
      lower.includes("騙") ||
      lower.includes("165")
    ) {
      return {
        reply:
          "我們是正規私募基金團隊，怎麼可能是詐騙！您不要受網路未經查證的言論影響，錯過建倉黃金期！",
        tactics: ["authority", "fear"],
      }
    }
    if (
      lower.includes("多少") ||
      lower.includes("匯款") ||
      lower.includes("錢")
    ) {
      return {
        reply:
          "本次專案體驗額度是 5 萬元，請先確認您的網銀約定轉帳額度是否充足，我馬上為您登記席位。",
        tactics: ["greed"],
      }
    }

    return {
      reply: `我是 ${displayName}，這期飆股操盤名額只保留到下午收盤前，請您把握機會配合完成入金建倉！`,
      tactics: ["time_pressure"],
    }
  }
}

export const frontendRagEngine = new FrontendRagEngine()
