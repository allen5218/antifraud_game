import { afterEach, describe, expect, it } from "bun:test"
import { cleanup, render, screen } from "@testing-library/react"
import { QuizReveal } from "./QuizReveal"

afterEach(cleanup)

const result = {
  type: "verdict" as const,
  correct: true,
  is_scam: true,
  red_flags: [
    { tag: "greed", text: "保證獲利穩賺不賠" },
    { tag: "time_pressure", text: "名額只到今晚" },
  ],
  provenance: "改編自:司法院裁判書詐欺案件",
  tag_details: [
    {
      tag: "greed",
      label: "貪念誘惑",
      suggestion: "保證獲利時，先停下來查證風險",
    },
    {
      tag: "time_pressure",
      label: "時間壓力",
      suggestion: "遇到限時話術先冷靜",
    },
  ],
}

const verdictItem = {
  item_id: "verdict-1",
  type: "verdict" as const,
  fraud_type: "investment",
  title: "穩賺投資",
  narrative: "加入群組立即獲利",
  difficulty: 2,
}

describe("<QuizReveal />", () => {
  it("shows verdict and localized flags without raw tags", () => {
    render(
      <QuizReveal
        item={verdictItem}
        result={result}
        onNext={() => {}}
        isLast={false}
      />,
    )
    expect(screen.getByText(/答對了/)).toBeTruthy()
    expect(screen.getByText(/保證獲利穩賺不賠/)).toBeTruthy()
    expect(screen.getAllByText("貪念誘惑")).toHaveLength(2)
    expect(screen.getByText(/先停下來查證風險/)).toBeTruthy()
    expect(screen.getByText(/改編自:司法院裁判書詐欺案件/)).toBeTruthy()
    expect(screen.queryByText("greed")).toBeNull()
  })

  it("shows wrong verdict for incorrect", () => {
    render(
      <QuizReveal
        result={{ ...result, correct: false }}
        item={verdictItem}
        onNext={() => {}}
        isLast
      />,
    )
    expect(screen.getByText(/答錯了/)).toBeTruthy()
    expect(screen.getByText(/看結算/)).toBeTruthy()
  })

  it("shows tactics missed and extra choices with teaching suggestions", () => {
    render(
      <QuizReveal
        item={{
          item_id: "tactics-1",
          type: "tactics",
          fraud_type: "investment",
          title: "限時投資",
          narrative: "今晚截止",
          difficulty: 2,
          question: "用了哪些話術？",
          options: [
            { tag: "time_pressure", label: "時間壓力" },
            { tag: "authority", label: "權威服從" },
          ],
        }}
        result={{
          type: "tactics",
          correct: false,
          correct_tags: ["time_pressure"],
          missed_tags: ["time_pressure"],
          extra_tags: ["authority"],
          provenance: "改編自:Cofacts 原始訊息",
          tag_details: [
            {
              tag: "time_pressure",
              label: "時間壓力",
              suggestion: "先給自己冷靜期",
            },
            {
              tag: "authority",
              label: "權威服從",
              suggestion: "主動查證身份",
            },
          ],
        }}
        onNext={() => {}}
        isLast={false}
      />,
    )

    expect(screen.getByText(/漏選/)).toBeTruthy()
    expect(screen.getByText(/多選/)).toBeTruthy()
    expect(screen.getByText(/先給自己冷靜期/)).toBeTruthy()
    expect(screen.getByText(/主動查證身份/)).toBeTruthy()
    expect(screen.getByText(/改編自:Cofacts 原始訊息/)).toBeTruthy()
  })

  it("shows each match result and suggestions for incorrect pairs", () => {
    render(
      <QuizReveal
        item={{
          item_id: "match-1",
          type: "match",
          question: "配對",
          match_prompts: [
            { pair_id: "pair-1", text: "今晚前匯款" },
            { pair_id: "pair-2", text: "我是警察" },
          ],
          match_targets: [
            { tag: "time_pressure", label: "時間壓力" },
            { tag: "authority", label: "權威服從" },
          ],
        }}
        result={{
          type: "match",
          correct: false,
          results: [
            {
              pair_id: "pair-1",
              correct_tag: "time_pressure",
              correct: false,
              provenance: "改編自:金管會新聞稿",
            },
            {
              pair_id: "pair-2",
              correct_tag: "authority",
              correct: true,
              provenance: "改編自:司法院判決",
            },
          ],
          tag_details: [
            {
              tag: "time_pressure",
              label: "時間壓力",
              suggestion: "先給自己冷靜期",
            },
          ],
        }}
        onNext={() => {}}
        isLast
      />,
    )

    expect(screen.getByText(/今晚前匯款/)).toBeTruthy()
    expect(screen.getByText(/正解：.*時間壓力/)).toBeTruthy()
    expect(screen.getByText(/先給自己冷靜期/)).toBeTruthy()
    expect(screen.getByText(/改編自:金管會新聞稿/)).toBeTruthy()
    expect(screen.getByText(/改編自:司法院判決/)).toBeTruthy()
  })
})

const verificationItem = {
  item_id: "verif-1",
  type: "verification" as const,
  fraud_type: "atm",
  title: "客服說今晚會扣款",
  narrative: "有人自稱購物平台客服，說你被誤設成會員。",
  difficulty: 1,
  question: "接下來怎麼做比較好？",
  // 與正式題庫同一種寫法:三個都是正當管道,只差在這個情境該走哪一條。
  // 不要寫成「照對方連結操作」——策展文件明文禁止，之後有人照測試抄題會抄到廢棄寫法。
  options: [
    { key: "A", text: "從原平台官方入口查帳戶狀態" },
    { key: "B", text: "掛斷後自行改撥卡片背面客服" },
    { key: "C", text: "從主管機關官方名單查資格" },
  ],
}

const verificationResult = {
  type: "verification" as const,
  correct: false,
  correct_key: "A",
  explanation:
    "帳戶狀態只有原平台查得到；卡背客服處理卡片爭議，主管機關名單查的是機構資格。",
  provenance: "改編自:內政部警政署假客服案例",
  tag_details: [
    {
      tag: "authority",
      label: "權威服從",
      suggestion: "對方自稱官方時，掛掉電話自己打官方號碼",
    },
  ],
}

describe("<QuizReveal /> 查證題", () => {
  it("顯示正解選項、解說與素材來源", () => {
    render(
      <QuizReveal
        item={verificationItem}
        result={verificationResult}
        onNext={() => {}}
        isLast={false}
      />,
    )

    expect(screen.getByText(/正解 A/)).toBeDefined()
    expect(screen.getByText(/從原平台官方入口查帳戶狀態/)).toBeDefined()
    expect(
      screen.getByText(
        "帳戶狀態只有原平台查得到；卡背客服處理卡片爭議，主管機關名單查的是機構資格。",
      ),
    ).toBeDefined()
    // 四種題型的揭曉卡都要標素材來源。
    expect(screen.getByText("📎 改編自:內政部警政署假客服案例")).toBeDefined()
  })

  it("不把其他選項當成正解顯示", () => {
    render(
      <QuizReveal
        item={verificationItem}
        result={verificationResult}
        onNext={() => {}}
        isLast={false}
      />,
    )

    expect(screen.queryByText(/正解 B/)).toBeNull()
    expect(screen.queryByText(/正解 C/)).toBeNull()
  })
})
