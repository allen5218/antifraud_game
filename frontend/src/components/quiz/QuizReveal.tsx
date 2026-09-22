import type {
  QuickQuizAnswerResponse,
  QuizDeckResponse,
  QuizWeaknessDetail,
} from "@/client"

type QuizItem = QuizDeckResponse["items"][number]

interface QuizRevealProps {
  item: QuizItem
  result: QuickQuizAnswerResponse
  onNext: () => void
  isLast: boolean
  disabled?: boolean
}

function WeaknessDetails({ details }: { details: QuizWeaknessDetail[] }) {
  if (details.length === 0) return null
  return (
    <section className="mt-4" aria-labelledby="weakness-teaching-title">
      <h4
        id="weakness-teaching-title"
        className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground"
      >
        弱點提醒與建議
      </h4>
      <ul className="mt-2 grid gap-2">
        {details.map((detail) => (
          <li key={detail.tag} className="rounded-xl bg-muted p-3">
            <span className="text-xs font-bold">{detail.label}</span>
            <p className="mt-1 text-xs leading-relaxed text-muted-foreground">
              {detail.suggestion}
            </p>
          </li>
        ))}
      </ul>
    </section>
  )
}

function VerdictReveal({ result }: { result: QuickQuizAnswerResponse }) {
  if (result.type !== "verdict") return null
  const labelFor = (tag: string) =>
    result.tag_details.find((detail) => detail.tag === tag)?.label ?? "其他話術"
  return (
    <>
      <p className="mt-1 text-center text-xs text-muted-foreground">
        正解：這則{result.is_scam ? "是詐騙" : "是正當內容"}
      </p>
      <p className="mt-3 text-[10px] font-bold uppercase tracking-wider text-muted-foreground">
        {result.is_scam ? "紅旗解析" : "正當訊號"}
      </p>
      <ul className="mt-1.5 flex flex-col gap-1.5">
        {result.red_flags.map((flag) => (
          <li key={flag.text} className="text-xs leading-snug">
            {flag.tag ? "🚩" : "✅"} {flag.text}
            {flag.tag && (
              <span className="ml-1 rounded bg-red-50 px-1 py-0.5 text-[9px] font-bold text-red-600 dark:bg-red-950">
                {labelFor(flag.tag)}
              </span>
            )}
          </li>
        ))}
      </ul>
      <p className="mt-3 rounded-lg bg-muted px-3 py-2 text-[11px] text-muted-foreground">
        📎 {result.provenance}
      </p>
      <WeaknessDetails details={result.tag_details} />
    </>
  )
}

function TacticsReveal({ result }: { result: QuickQuizAnswerResponse }) {
  if (result.type !== "tactics") return null
  const labelFor = (tag: string) =>
    result.tag_details.find((detail) => detail.tag === tag)?.label ?? "其他話術"
  return (
    <>
      <div className="mt-3 grid gap-2 text-xs">
        <p>
          <span className="font-bold text-green-600">正確話術：</span>
          {result.correct_tags.map(labelFor).join("、") || "無"}
        </p>
        <p>
          <span className="font-bold text-amber-600">漏選：</span>
          {result.missed_tags.map(labelFor).join("、") || "無"}
        </p>
        <p>
          <span className="font-bold text-red-600">多選：</span>
          {result.extra_tags.map(labelFor).join("、") || "無"}
        </p>
      </div>
      <p className="mt-3 rounded-lg bg-muted px-3 py-2 text-[11px] text-muted-foreground">
        📎 {result.provenance}
      </p>
      <WeaknessDetails details={result.tag_details} />
    </>
  )
}

function MatchReveal({
  item,
  result,
}: {
  item: QuizItem
  result: QuickQuizAnswerResponse
}) {
  if (item.type !== "match" || result.type !== "match") return null
  const prompts = new Map(
    item.match_prompts.map((prompt) => [prompt.pair_id, prompt.text]),
  )
  const targets = new Map(
    item.match_targets.map((target) => [target.tag, target.label]),
  )
  return (
    <>
      <ul className="mt-3 grid gap-2">
        {result.results.map((pair) => (
          <li key={pair.pair_id} className="rounded-xl border p-3 text-xs">
            <p className="leading-relaxed">
              {pair.correct ? "✓" : "✗"}{" "}
              {prompts.get(pair.pair_id) ?? pair.pair_id}
            </p>
            <p
              className={`mt-1 font-bold ${pair.correct ? "text-green-600" : "text-red-600"}`}
            >
              正解：{targets.get(pair.correct_tag) ?? "其他話術"}
            </p>
            <p className="mt-1 text-[10px] text-muted-foreground">
              📎 {pair.provenance}
            </p>
          </li>
        ))}
      </ul>
      <WeaknessDetails details={result.tag_details} />
    </>
  )
}

function VerificationReveal({
  item,
  result,
}: {
  item: QuizItem
  result: QuickQuizAnswerResponse
}) {
  if (item.type !== "verification" || result.type !== "verification")
    return null
  const correctOption = item.options.find(
    (option) => option.key === result.correct_key,
  )
  return (
    <>
      <div className="mt-3 rounded-xl border p-3 text-xs">
        {/* 選項卡上的 A/B/C 是 aria-hidden 的視覺標記,螢幕閱讀器聽不到,
            所以這裡不能只報代號——只講選項文字才對得回去。 */}
        <p className="font-bold text-green-600">
          <span aria-hidden="true">正解 {result.correct_key}：</span>
          <span className="sr-only">正解：</span>
          {correctOption?.text ?? ""}
        </p>
        <p className="mt-2 leading-relaxed">{result.explanation}</p>
      </div>
      <p className="mt-3 rounded-lg bg-muted px-3 py-2 text-[11px] text-muted-foreground">
        📎 {result.provenance}
      </p>
      <WeaknessDetails details={result.tag_details} />
    </>
  )
}

/** 單題揭曉：依題型顯示答案差異，並共用後端提供的弱點建議。 */
export function QuizReveal({
  item,
  result,
  onNext,
  isLast,
  disabled = false,
}: QuizRevealProps) {
  return (
    <div className="fixed inset-0 z-50 flex items-end justify-center bg-black/40">
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="quiz-reveal-title"
        className="max-h-[85vh] w-full max-w-md overflow-y-auto rounded-t-2xl bg-background p-4 pb-6"
      >
        <h3
          id="quiz-reveal-title"
          className={`text-center text-lg font-extrabold ${result.correct ? "text-green-600" : "text-red-600"}`}
        >
          {result.correct ? "✓ 答對了！" : "✗ 答錯了…"}
        </h3>
        <VerdictReveal result={result} />
        <TacticsReveal result={result} />
        <MatchReveal item={item} result={result} />
        <VerificationReveal item={item} result={result} />
        <button
          type="button"
          disabled={disabled}
          onClick={onNext}
          className="mt-4 w-full rounded-xl bg-foreground py-2.5 text-sm font-bold text-background disabled:opacity-50"
        >
          {isLast ? "看結算 ›" : "下一題 ›"}
        </button>
      </div>
    </div>
  )
}
