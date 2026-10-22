import { Check, MessageSquare, Trash2 } from "lucide-react"
import { type FormEvent, type ReactNode, useMemo, useState } from "react"
import type {
  TeamBank as TeamBankData,
  TeamCase,
  TeamOption,
  TeamPersona,
  TeamPretest,
  TeamQuestion,
  TeamSwipe,
} from "@/client"
import {
  type TeamItemKind,
  useCreateTeamComment,
  useDeleteTeamComment,
  useTeamComments,
} from "@/hooks/useTeam"
import { FRAUD_TYPES, fraudTypeLabel } from "@/lib/fraudTypes"

export type TeamTab = "pretest" | "swipe" | "quiz" | "exam" | "scenario"

export const TABS: { id: TeamTab; label: string }[] = [
  { id: "pretest", label: "前測" },
  { id: "swipe", label: "滑卡" },
  { id: "quiz", label: "訊息判讀" },
  { id: "exam", label: "檢測題" },
  { id: "scenario", label: "情境對抗" },
]

type Truth = "all" | "scam" | "legit"

export type Filters = { type: string; truth: Truth; query: string }

const EXAM_POOL_LABELS: Record<string, string> = {
  exam_message: "檢測・判斷真假",
  exam_tactics: "檢測・話術複選",
  exam_scenario: "檢測・情境對抗案例",
}

function matches(
  item: { fraud_type: string; is_scam?: boolean | null },
  text: string,
  f: Filters,
) {
  if (f.type !== "all" && item.fraud_type !== f.type) return false
  if (f.truth !== "all" && item.is_scam !== (f.truth === "scam")) return false
  const q = f.query.trim()
  return q === "" || text.includes(q)
}

/** 詐騙題依代號排，它的對照正常題緊接在後；沒有對照的排最後 */
export function pairCases(cases: TeamCase[]): TeamCase[] {
  const byMirror = new Map<string, TeamCase>()
  for (const c of cases) {
    if (!c.is_scam && c.mirror_key) byMirror.set(c.mirror_key, c)
  }
  const out: TeamCase[] = []
  const placed = new Set<string>()
  for (const c of [...cases].sort((a, b) => a.key.localeCompare(b.key))) {
    if (!c.is_scam) continue
    out.push(c)
    placed.add(c.key)
    const mirror = byMirror.get(c.key)
    if (mirror) {
      out.push(mirror)
      placed.add(mirror.key)
    }
  }
  return [...out, ...cases.filter((c) => !placed.has(c.key))]
}

function Tag({
  children,
  tone,
}: {
  children: ReactNode
  tone?: "scam" | "legit"
}) {
  const color =
    tone === "scam"
      ? "bg-scam/15 text-scam"
      : tone === "legit"
        ? "bg-legit/15 text-legit"
        : "bg-surface-2 text-muted-foreground"
  return (
    <span className={`rounded-md px-1.5 py-0.5 text-[11px] font-bold ${color}`}>
      {children}
    </span>
  )
}

function Meta({
  fraudType,
  isScam,
  difficulty,
  extra,
  itemKey,
}: {
  fraudType: string
  isScam?: boolean | null
  difficulty?: number
  extra?: string
  itemKey: string
}) {
  return (
    <div className="flex flex-wrap items-center gap-1">
      <Tag>{fraudTypeLabel(fraudType)}</Tag>
      {isScam != null && (
        <Tag tone={isScam ? "scam" : "legit"}>{isScam ? "詐騙" : "正常"}</Tag>
      )}
      {extra && <Tag>{extra}</Tag>}
      {difficulty != null && <Tag>難度 {difficulty}</Tag>}
      <span className="ml-auto text-[11px] text-muted-foreground">
        {itemKey}
      </span>
    </div>
  )
}

function Options({ options }: { options: TeamOption[] }) {
  return (
    <ul className="flex flex-col gap-1 text-sm">
      {options.map((o) => (
        <li
          key={o.key}
          className={`flex gap-1.5 rounded-lg px-2 py-1 ${o.is_correct ? "bg-legit/15 font-bold" : ""}`}
        >
          <span>{o.key}.</span>
          <span className="flex-1">{o.text}</span>
          {o.is_correct && (
            <Check aria-label="正解" className="size-4 shrink-0 text-legit" />
          )}
        </li>
      ))}
    </ul>
  )
}

function Labeled({ label, children }: { label: string; children: ReactNode }) {
  return (
    <p className="text-sm">
      <span className="font-bold">{label}：</span>
      {children}
    </p>
  )
}

function Discussion({
  kind,
  itemKey,
  count,
}: {
  kind: TeamItemKind
  itemKey: string
  count: number
}) {
  const [open, setOpen] = useState(false)
  const [draft, setDraft] = useState("")
  const comments = useTeamComments(kind, itemKey, open)
  const create = useCreateTeamComment(kind, itemKey)
  const remove = useDeleteTeamComment(kind, itemKey)

  const submit = (e: FormEvent) => {
    e.preventDefault()
    const body = draft.trim()
    if (!body) return
    create.mutate(body, { onSuccess: () => setDraft("") })
  }

  return (
    <div className="border-t border-border/60 pt-2">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        aria-expanded={open}
        className="flex items-center gap-1 text-xs text-muted-foreground"
      >
        <MessageSquare aria-hidden className="size-3.5" />
        {count > 0 ? `討論（${count}）` : "討論"}
      </button>
      {open && (
        <div className="mt-2 flex flex-col gap-2">
          {comments.isPending ? (
            <p className="text-xs text-muted-foreground">載入中…</p>
          ) : comments.error ? (
            <p className="text-xs text-muted-foreground">討論載入失敗</p>
          ) : comments.data && comments.data.length > 0 ? (
            <ul className="flex flex-col gap-1.5">
              {comments.data.map((c) => (
                <li
                  key={c.id}
                  className="rounded-lg bg-surface-2 px-2 py-1.5 text-sm"
                >
                  <div className="flex items-center gap-2 text-[11px] text-muted-foreground">
                    <span className="font-bold">{c.author}</span>
                    <span>
                      {new Date(c.created_at).toLocaleString("zh-TW")}
                    </span>
                    {c.mine && (
                      <button
                        type="button"
                        aria-label="刪除這則留言"
                        onClick={() => remove.mutate(c.id)}
                        disabled={remove.isPending}
                        className="ml-auto"
                      >
                        <Trash2 aria-hidden className="size-3.5" />
                      </button>
                    )}
                  </div>
                  <p className="whitespace-pre-wrap">{c.body}</p>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-xs text-muted-foreground">還沒有人留言。</p>
          )}
          <form onSubmit={submit} className="flex flex-col gap-1.5">
            <textarea
              value={draft}
              onChange={(e) => setDraft(e.target.value)}
              maxLength={1000}
              rows={2}
              aria-label="留言"
              placeholder="這題要不要改、怎麼改"
              className="rounded-lg border border-border bg-background px-2 py-1.5 text-sm"
            />
            <button
              type="submit"
              disabled={create.isPending || draft.trim() === ""}
              className="self-end rounded-lg bg-primary px-3 py-1 text-xs font-bold text-primary-foreground disabled:opacity-50"
            >
              留言
            </button>
            {create.error && (
              <p className="text-xs text-scam">留言沒有送出，請再試一次。</p>
            )}
          </form>
        </div>
      )}
    </div>
  )
}

function Card({ children }: { children: ReactNode }) {
  return (
    <li className="flex flex-col gap-2 rounded-xl border border-border bg-surface-3 p-3">
      {children}
    </li>
  )
}

function PretestItem({ q, count }: { q: TeamPretest; count: number }) {
  return (
    <Card>
      <Meta
        fraudType={q.fraud_type}
        isScam={q.is_scam}
        difficulty={q.difficulty}
        itemKey={q.key}
      />
      <p className="text-sm">{q.question}</p>
      <Options options={q.options} />
      <Labeled label="詳解">{q.explanation}</Labeled>
      <Discussion kind="pretest" itemKey={q.key} count={count} />
    </Card>
  )
}

function SwipeItem({
  c,
  labels,
  count,
}: {
  c: TeamSwipe
  labels: Record<string, string>
  count: number
}) {
  return (
    <Card>
      <Meta
        fraudType={c.fraud_type}
        isScam={c.is_scam}
        difficulty={c.difficulty}
        extra={c.pool === "exam" ? "檢測用" : "練習用"}
        itemKey={c.key}
      />
      <p className="text-xs text-muted-foreground">{c.source_label}</p>
      <p className="whitespace-pre-wrap text-sm">{c.scenario}</p>
      <Labeled label="答案">
        {c.is_scam ? "詐騙，往左滑" : "正常，往右滑"}
      </Labeled>
      {c.weakness_tags.length > 0 && (
        <Labeled label="話術">
          {c.weakness_tags.map((t) => labels[t] ?? t).join("、")}
        </Labeled>
      )}
      <Labeled label="詳解">{c.explanation}</Labeled>
      <Discussion kind="swipe" itemKey={c.key} count={count} />
    </Card>
  )
}

function QuestionBlock({
  q,
  labels,
  count,
}: {
  q: TeamQuestion
  labels: Record<string, string>
  count: number
}) {
  return (
    <div className="flex flex-col gap-1.5 rounded-lg border border-border/60 p-2">
      <p className="text-xs font-bold">
        查證題（
        {q.question_kind === "next_action"
          ? "查證管道"
          : "手上的資料能證明什麼"}
        ・難度 {q.difficulty}）
        <span className="ml-1 font-normal text-muted-foreground">{q.key}</span>
      </p>
      <p className="text-sm">{q.question}</p>
      <Options options={q.options} />
      <Labeled label="詳解">{q.explanation}</Labeled>
      {q.weakness_tag && (
        <Labeled label="對應話術">
          {labels[q.weakness_tag] ?? q.weakness_tag}
        </Labeled>
      )}
      <Discussion kind="question" itemKey={q.key} count={count} />
    </div>
  )
}

function CaseItem({
  c,
  questions,
  labels,
  counts,
}: {
  c: TeamCase
  questions: TeamQuestion[]
  labels: Record<string, string>
  counts: Record<string, number>
}) {
  const tags = [
    ...new Set(c.red_flags.map((f) => f.tag).filter(Boolean)),
  ] as string[]
  return (
    <Card>
      <Meta
        fraudType={c.fraud_type}
        isScam={c.is_scam}
        difficulty={c.difficulty}
        extra={EXAM_POOL_LABELS[c.pool]}
        itemKey={c.key}
      />
      <p className="font-bold">{c.title}</p>
      <p className="whitespace-pre-wrap text-sm">{c.narrative}</p>
      <p className="text-sm font-bold">
        {c.is_scam ? "可疑的地方" : "看得出是正常的地方"}
      </p>
      <ul className="flex flex-col gap-1 text-sm">
        {c.red_flags.map((f) => (
          <li key={f.text} className="flex gap-1.5">
            {f.tag && (
              <span className="shrink-0 font-bold">
                【{labels[f.tag] ?? f.tag}】
              </span>
            )}
            <span>{f.text}</span>
          </li>
        ))}
      </ul>
      {c.pool === "exam_tactics" && (
        <Labeled label="這題要勾的話術">
          {tags.map((t) => labels[t] ?? t).join("、")}
        </Labeled>
      )}
      {c.mirror_key && (
        <p className="text-xs text-muted-foreground">對照題：{c.mirror_key}</p>
      )}
      <p className="text-xs text-muted-foreground">{c.provenance}</p>
      <Discussion
        kind="case"
        itemKey={c.key}
        count={counts[`case:${c.key}`] ?? 0}
      />
      {questions.map((q) => (
        <QuestionBlock
          key={q.key}
          q={q}
          labels={labels}
          count={counts[`question:${q.key}`] ?? 0}
        />
      ))}
    </Card>
  )
}

function PersonaItem({
  p,
  labels,
  count,
}: {
  p: TeamPersona
  labels: Record<string, string>
  count: number
}) {
  return (
    <Card>
      <Meta
        fraudType={p.fraud_type}
        isScam={p.role === "scam"}
        extra={p.pool === "exam" ? "檢測用" : "練習用"}
        itemKey={p.key}
      />
      <p className="font-bold">
        {p.role === "scam" ? "詐騙者" : "正常人"}：{p.name}
      </p>
      <Labeled label="開場白">{p.teaser}</Labeled>
      {p.primary_tactics.length > 0 && (
        <Labeled label="主要話術">
          {p.primary_tactics.map((t) => labels[t] ?? t).join("、")}
        </Labeled>
      )}
      <details>
        <summary className="cursor-pointer text-sm font-bold">
          人格設定全文
        </summary>
        <p className="mt-1 whitespace-pre-wrap text-sm">{p.body}</p>
      </details>
      <Discussion kind="persona" itemKey={p.key} count={count} />
    </Card>
  )
}

/** 依分頁與篩選列出題目；回傳筆數給頁面顯示 */
export function TeamBankList({
  bank,
  tab,
  filters,
}: {
  bank: TeamBankData
  tab: TeamTab
  filters: Filters
}) {
  const labels = bank.tactic_labels
  const counts = bank.comment_counts
  const questionsByCase = useMemo(() => {
    const map = new Map<string, TeamQuestion[]>()
    for (const q of bank.questions) {
      map.set(q.case_key, [...(map.get(q.case_key) ?? []), q])
    }
    return map
  }, [bank.questions])

  const caseText = (c: TeamCase) =>
    [c.key, c.title, c.narrative, ...c.red_flags.map((f) => f.text)].join(
      "\n",
    ) +
    (questionsByCase.get(c.key) ?? [])
      .map((q) => `${q.key}\n${q.question}`)
      .join("\n")

  let items: ReactNode[] = []
  if (tab === "pretest") {
    items = bank.pretest
      .filter((q) =>
        matches(q, `${q.key}\n${q.question}\n${q.explanation}`, filters),
      )
      .map((q) => (
        <PretestItem
          key={q.key}
          q={q}
          count={counts[`pretest:${q.key}`] ?? 0}
        />
      ))
  } else if (tab === "swipe") {
    items = bank.swipe
      .filter((c) =>
        matches(c, `${c.key}\n${c.scenario}\n${c.explanation}`, filters),
      )
      .map((c) => (
        <SwipeItem
          key={c.key}
          c={c}
          labels={labels}
          count={counts[`swipe:${c.key}`] ?? 0}
        />
      ))
  } else if (tab === "quiz" || tab === "exam") {
    const pool = (c: TeamCase) =>
      tab === "quiz" ? c.pool === "practice" : c.pool !== "practice"
    items = pairCases(bank.cases.filter(pool))
      .filter((c) => matches(c, caseText(c), filters))
      .map((c) => (
        <CaseItem
          key={c.key}
          c={c}
          questions={questionsByCase.get(c.key) ?? []}
          labels={labels}
          counts={counts}
        />
      ))
  } else {
    const skills = bank.skills.filter(
      (s) => filters.type === "all" || s.fraud_type === filters.type,
    )
    items = [
      ...skills.map((s) => (
        <Card key={`skill:${s.fraud_type}`}>
          <Meta fraudType={s.fraud_type} itemKey={`fraud-${s.fraud_type}`} />
          <details>
            <summary className="cursor-pointer text-sm font-bold">
              {fraudTypeLabel(s.fraud_type)}：手法資料全文
            </summary>
            <p className="mt-1 whitespace-pre-wrap text-sm">{s.body}</p>
          </details>
        </Card>
      )),
      ...bank.personas
        .filter((p) =>
          matches(
            { fraud_type: p.fraud_type, is_scam: p.role === "scam" },
            `${p.key}\n${p.name}\n${p.teaser}\n${p.body}`,
            filters,
          ),
        )
        .map((p) => (
          <PersonaItem
            key={p.key}
            p={p}
            labels={labels}
            count={counts[`persona:${p.key}`] ?? 0}
          />
        )),
    ]
  }

  return (
    <>
      <p className="text-xs text-muted-foreground">共 {items.length} 筆</p>
      {items.length === 0 ? (
        <p className="py-8 text-center text-xs text-muted-foreground">
          沒有符合的題目
        </p>
      ) : (
        <ul className="flex flex-col gap-2">{items}</ul>
      )}
    </>
  )
}

export function TeamFilters({
  filters,
  onChange,
}: {
  filters: Filters
  onChange: (f: Filters) => void
}) {
  return (
    <div className="flex flex-col gap-2">
      <div className="flex flex-wrap gap-1">
        {["all", ...FRAUD_TYPES].map((t) => (
          <button
            key={t}
            type="button"
            aria-pressed={filters.type === t}
            onClick={() => onChange({ ...filters, type: t })}
            className={`rounded-full px-2.5 py-1 text-xs ${
              filters.type === t
                ? "bg-primary font-bold text-primary-foreground"
                : "bg-surface-2 text-muted-foreground"
            }`}
          >
            {t === "all" ? "全部類型" : fraudTypeLabel(t)}
          </button>
        ))}
      </div>
      <div className="flex gap-2">
        <select
          aria-label="詐騙或正常"
          value={filters.truth}
          onChange={(e) =>
            onChange({ ...filters, truth: e.target.value as Truth })
          }
          className="rounded-lg border border-border bg-background px-2 py-1 text-sm"
        >
          <option value="all">詐騙與正常</option>
          <option value="scam">只看詐騙</option>
          <option value="legit">只看正常</option>
        </select>
        <input
          type="search"
          aria-label="搜尋題目"
          placeholder="搜尋內容或代號"
          value={filters.query}
          onChange={(e) => onChange({ ...filters, query: e.target.value })}
          className="min-w-0 flex-1 rounded-lg border border-border bg-background px-2 py-1 text-sm"
        />
      </div>
    </div>
  )
}
