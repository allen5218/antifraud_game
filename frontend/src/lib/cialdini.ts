export interface InfluenceCue {
  lever: string
  leverName: string
  matchedText: string
  trap: string
  counter: string
}

export const INFLUENCE_PATTERNS = [
  {
    lever: "authority",
    leverName: "權威服從 (Authority)",
    regex:
      /(地檢署|檢察官|刑事局|警調|特偵組|分局|監管帳戶|涉嫌洗錢|公文傳真|拘提|保密原則|開庭|金管會|合法執照|私募團隊|投資顧問)/g,
    trap: "利用國家公務司法或金融專業頭銜製造階級壓迫與虛假背書，阻斷批判思維",
    counter:
      "公務機關絕不透過電話製作筆錄或要求監管帳戶，合法投顧必受金管會嚴格列管，切勿輕信口頭宣稱",
    badgeColor: "bg-blue-500/20 text-blue-300 border-blue-500/30",
  },
  {
    lever: "scarcity",
    leverName: "稀缺急迫 (Scarcity)",
    regex:
      /(限時|立刻|最後.*名額|名額.*剩|名額.*最後|剩.*位|最後.*位|即刻凍結|逾期無效|倒數|搶先|手慢無|僅剩|緊急手續|盡快|馬上)/g,
    trap: "人為製造急迫感觸發錯失恐懼 (FOMO)，逼迫受害者跳過查核直接衝動決策",
    counter: "合規交易皆有正規處理期，催促立即操作者必有詐，強制冷靜 15 分鐘",
    badgeColor: "bg-amber-500/20 text-amber-300 border-amber-500/30",
  },
  {
    lever: "reciprocity",
    leverName: "互惠誘餌 (Reciprocity)",
    regex:
      /(免費領取|送你.*飆股|飆股|保證獲利|獨家.*軟體|穩賺不賠|老師代墊|贈金|好禮相贈|不用錢先試聽|無償提供)/g,
    trap: "以免費明牌、獨家軟體或保證高回報為誘餌，誘導受害者產生貪念與心理依賴",
    counter: "投資必有風險，凡宣稱保證獲利或獨家內線者 100% 為非法吸金與詐欺",
    badgeColor: "bg-purple-500/20 text-purple-300 border-purple-500/30",
  },
  {
    lever: "social_proof",
    leverName: "社會認同 (Social Proof)",
    regex:
      /(大家都|學員已提領|萬人見證|群組.*曬單|大家都賺到|老學員獲利|全員一致好評)/g,
    trap: "以封閉群組內的大量暗樁曬單營造虛假從眾效應，削弱個人戒心",
    counter: "群組內 99% 皆為暗樁或機器人，獨立透過金管會登記名冊查驗",
    badgeColor: "bg-emerald-500/20 text-emerald-300 border-emerald-500/30",
  },
  {
    lever: "consistency",
    leverName: "承諾一致 (Consistency)",
    regex:
      /(先投入.*試水|第一次.*成功出金|既然都已經.*不如再補|就差最後一步手續費)/g,
    trap: "利用登門檻效應逐步綁架沉沒成本，使受害者因不甘心損失而越陷越深",
    counter: "勇於及時停損，一旦發現疑點立刻中止操作並尋求警方協助",
    badgeColor: "bg-rose-500/20 text-rose-300 border-rose-500/30",
  },
  {
    lever: "liking",
    leverName: "喜好人設 (Liking)",
    regex:
      /(小哥哥|小姐姐|早安.*心疼你|我只跟你說|看到你就覺得投緣|想跟你一起生活)/g,
    trap: "打造溫柔體貼或崇高人設，以情感寄託削弱財務防線",
    counter: "網路身分極易偽造，在未經現實多方驗證前，始終將金錢與情感劃清界限",
    badgeColor: "bg-pink-500/20 text-pink-300 border-pink-500/30",
  },
  {
    lever: "unity",
    leverName: "群體歸屬 (Unity)",
    regex:
      /(我們都是.*同鄉|校友專屬|信徒大家庭|都是自己人|只有我們這個圈子才懂)/g,
    trap: "藉由同鄉、校友或特定信仰的圈內人認同感，降低受害者防範",
    counter: "涉資交易不分親疏，重大款項轉移一律依法簽訂合約與信託履約",
    badgeColor: "bg-cyan-500/20 text-cyan-300 border-cyan-500/30",
  },
]

export function detectInfluenceCues(text: string): InfluenceCue[] {
  const results: InfluenceCue[] = []
  const seenLevers = new Set<string>()

  for (const item of INFLUENCE_PATTERNS) {
    if (seenLevers.has(item.lever)) continue
    const regex = new RegExp(item.regex.source, "g")
    const match = regex.exec(text)
    if (match) {
      seenLevers.add(item.lever)
      results.push({
        lever: item.lever,
        leverName: item.leverName,
        matchedText: match[0],
        trap: item.trap,
        counter: item.counter,
      })
    }
  }

  return results
}
