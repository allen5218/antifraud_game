import { Check, ChevronRight, CircleCheck, CircleX, X } from "lucide-react"
import type {
  QuickQuizAnswerResponse,
  QuizDeckResponse,
  QuizWeaknessDetail,
} from "@/client"
import { useDialogFocus } from "@/hooks/useDialogFocus"
import { Provenance, SignalItem } from "./Signals"

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
        className="text-[11px] font-bold text-muted-foreground"
      >
        下次遇到可以這樣做
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
        正解：{result.is_scam ? "這是詐騙" : "這不是詐騙"}
      </p>
      <p className="mt-3 text-[11px] font-bold text-muted-foreground">
        {result.is_scam ? "可疑的地方" : "看得出是正常的地方"}
      </p>
      <ul className="mt-1.5 flex flex-col gap-1.5">
        {result.red_flags.map((flag) => (
          <SignalItem
            key={flag.text}
            suspicious={Boolean(flag.tag)}
            text={flag.text}
            label={flag.tag ? labelFor(flag.tag) : undefined}
          />
        ))}
      </ul>
      <Provenance text={result.provenance} className="mt-3" />
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
          <span className="font-bold text-legit">對方用了：</span>
          {result.correct_tags.map(labelFor).join("、") || "無"}
        </p>
        <p>
          <span className="font-bold text-warning">你漏掉：</span>
          {result.missed_tags.map(labelFor).join("、") || "無"}
        </p>
        <p>
          <span className="font-bold text-scam">你多選了：</span>
          {result.extra_tags.map(labelFor).join("、") || "無"}
        </p>
      </div>
      <Provenance text={result.provenance} className="mt-3" />
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
        {result.results.map((pair) => {
          const Mark = pair.correct ? Check : X
          return (
            <li key={pair.pair_id} className="rounded-xl border p-3 text-xs">
              <p className="flex gap-1.5 leading-relaxed">
                <Mark
                  aria-label={pair.correct ? "配對正確" : "配對錯誤"}
                  className={`mt-0.5 size-3.5 shrink-0 ${pair.correct ? "text-legit" : "text-scam"}`}
                />
                <span>{prompts.get(pair.pair_id) ?? pair.pair_id}</span>
              </p>
              <p
                className={`mt-1 font-bold ${pair.correct ? "text-legit" : "text-scam"}`}
              >
                正解：{targets.get(pair.correct_tag) ?? "其他話術"}
              </p>
              <Provenance text={pair.provenance} className="mt-2 px-2 py-1.5" />
            </li>
          )
        })}
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
        <p className="font-bold text-legit">
          <span aria-hidden="true">正解 {result.correct_key}：</span>
          <span className="sr-only">正解：</span>
          {correctOption?.text ?? ""}
        </p>
        <p className="mt-2 leading-relaxed">{result.explanation}</p>
      </div>
      <Provenance text={result.provenance} className="mt-3" />
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
  const Verdict = result.correct ? CircleCheck : CircleX
  const dialogRef = useDialogFocus<HTMLDivElement>(true)
  return (
    <div className="fixed inset-0 z-50 flex items-end justify-center bg-black/50">
      <div
        ref={dialogRef}
        tabIndex={-1}
        role="dialog"
        aria-modal="true"
        aria-labelledby="quiz-reveal-title"
        className="max-h-[85vh] w-full max-w-md overflow-y-auto rounded-t-2xl border-t border-border bg-card p-4 pb-6 outline-none"
      >
        <h3
          id="quiz-reveal-title"
          className={`flex items-center justify-center gap-1.5 text-lg font-extrabold ${result.correct ? "text-legit" : "text-scam"}`}
        >
          <Verdict aria-hidden className="size-5" />
          {result.correct ? "答對了！" : "答錯了"}
        </h3>
        <VerdictReveal result={result} />
        <TacticsReveal result={result} />
        <MatchReveal item={item} result={result} />
        <VerificationReveal item={item} result={result} />
        <button
          type="button"
          disabled={disabled}
          onClick={onNext}
          className="mt-4 flex w-full items-center justify-center gap-1 rounded-xl bg-primary py-2.5 text-sm font-bold text-primary-foreground disabled:opacity-50"
        >
          {isLast ? "看結算" : "下一題"}
          <ChevronRight aria-hidden className="size-4" />
        </button>
      </div>
    </div>
  )
}
