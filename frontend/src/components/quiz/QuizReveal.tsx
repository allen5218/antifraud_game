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
    <details className="mt-3 rounded-xl border border-border bg-muted/40 p-3">
      <summary className="cursor-pointer text-xs font-bold">想知道更多</summary>
      <ul className="mt-2 grid gap-2">
        {details.map((detail) => (
          <li key={detail.tag} className="text-xs">
            <span className="font-bold">{detail.label}：</span>
            <span className="text-muted-foreground">{detail.suggestion}</span>
          </li>
        ))}
      </ul>
    </details>
  )
}

function VerdictReveal({ result }: { result: QuickQuizAnswerResponse }) {
  if (result.type !== "verdict") return null
  const labelFor = (tag: string) =>
    result.tag_details.find((detail) => detail.tag === tag)?.label ?? "其他話術"
  return (
    <>
      <p className="mt-1 text-center text-sm font-bold">
        這則{result.is_scam ? "有詐騙風險" : "目前看起來正常"}
      </p>
      {result.red_flags[0] && (
        <p className="mt-3 rounded-xl bg-muted p-3 text-xs leading-relaxed">
          {result.red_flags[0].text}
        </p>
      )}
      {(result.red_flags.length > 1 || result.provenance) && (
        <details className="mt-2 text-xs text-muted-foreground">
          <summary className="cursor-pointer font-bold text-foreground">
            看完整原因
          </summary>
          <ul className="mt-2 grid gap-1.5">
            {result.red_flags.slice(1).map((flag) => (
              <li key={flag.text}>
                {flag.text}
                {flag.tag ? `（${labelFor(flag.tag)}）` : ""}
              </li>
            ))}
          </ul>
          <p className="mt-2">資料來源：{result.provenance}</p>
        </details>
      )}
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
          <span className="font-bold text-green-600">這裡用了：</span>
          {result.correct_tags.map(labelFor).join("、") || "無"}
        </p>
        {(result.missed_tags.length > 0 || result.extra_tags.length > 0) && (
          <details className="rounded-lg bg-muted p-2">
            <summary className="cursor-pointer font-bold">看看差在哪裡</summary>
            <p className="mt-1">
              少選：{result.missed_tags.map(labelFor).join("、") || "無"}
            </p>
            <p>多選：{result.extra_tags.map(labelFor).join("、") || "無"}</p>
          </details>
        )}
      </div>
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
          </li>
        ))}
      </ul>
      <WeaknessDetails details={result.tag_details} />
    </>
  )
}

function VerificationReveal({ result }: { result: QuickQuizAnswerResponse }) {
  if (result.type !== "verification") return null
  return (
    <>
      <div className="mt-3 rounded-xl bg-muted p-3 text-xs leading-relaxed">
        <span className="font-bold text-foreground">記住這一句：</span>
        <p className="mt-1 text-muted-foreground">{result.explanation}</p>
      </div>
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
          {result.correct ? "答對了！" : "再想一下"}
        </h3>
        <VerdictReveal result={result} />
        <VerificationReveal result={result} />
        <TacticsReveal result={result} />
        <MatchReveal item={item} result={result} />
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
