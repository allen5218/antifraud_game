import { Link } from "@tanstack/react-router"
import {
  ArrowRight,
  CheckCircle2,
  ChevronDown,
  ChevronUp,
  Circle,
  CircleDot,
  Clock,
  Lock,
  RefreshCw,
  Sparkles,
} from "lucide-react"
import { useState } from "react"
import { useJourney } from "@/hooks/useEconomy"
import { handleAuthFailure, normalizeError } from "@/lib/errorNormalizer"

export function LadderJourney() {
  const { data, isPending, isError, error, refetch } = useJourney()
  const [showAllRungs, setShowAllRungs] = useState(false)

  if (isPending) {
    return (
      <div
        data-testid="journey-loading"
        className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6 text-center text-xs text-slate-400"
      >
        <div className="flex items-center justify-center gap-2">
          <RefreshCw className="size-4 animate-spin text-emerald-400" />
          <span>載入天梯主線中…</span>
        </div>
      </div>
    )
  }

  if (isError || !data) {
    const norm = normalizeError(error)
    return (
      <div
        data-testid="journey-error"
        className="rounded-2xl border border-red-500/30 bg-red-950/20 p-4 text-center text-xs text-slate-300"
      >
        <p className="font-semibold text-red-300">天梯旅程載入失敗</p>
        <p className="mt-1 text-[11px] text-slate-400">
          {norm.message}
        </p>
        {norm.action === "login" ? (
          <button
            type="button"
            data-testid="journey-login-btn"
            onClick={() => handleAuthFailure(error)}
            className="mt-3 inline-flex items-center gap-1.5 rounded-lg border border-emerald-500/40 bg-emerald-600/30 px-3 py-1 text-xs font-bold text-emerald-200 hover:bg-emerald-600/50"
          >
            <span>重新登入</span>
          </button>
        ) : norm.action === "reload" ? (
          <button
            type="button"
            data-testid="journey-reload-btn"
            onClick={() => window.location.reload()}
            className="mt-3 inline-flex items-center gap-1.5 rounded-lg border border-amber-500/40 bg-amber-600/30 px-3 py-1 text-xs font-bold text-amber-200 hover:bg-amber-600/50"
          >
            <RefreshCw className="size-3" />
            <span>重新載入網頁</span>
          </button>
        ) : (
          <button
            type="button"
            data-testid="journey-retry-btn"
            onClick={() => refetch()}
            className="mt-3 inline-flex items-center gap-1.5 rounded-lg border border-white/20 bg-white/10 px-3 py-1 text-xs font-bold text-white hover:bg-white/20"
          >
            <RefreshCw className="size-3" />
            <span>重新載入</span>
          </button>
        )}
      </div>
    )
  }

  const { chapter, next_step, all_chapters, completed_chapters } = data
  const isAllComplete = completed_chapters >= 5

  const quizStep = chapter.steps?.find((s) => s.id === "quiz")
  const scenarioStep = chapter.steps?.find((s) => s.id === "scenario")

  // 下一個可解鎖的人物的預覽資訊（若已全通則無）
  const nextRungPreview = all_chapters.find(
    (r) => r.id === completed_chapters + 2,
  )

  const ctaLabel = (() => {
    switch (next_step.kind) {
      case "resume_scenario":
        return "繼續事件對話"
      case "quiz":
        return "前往短判讀"
      case "start_scenario":
        return "接下生活委託"
      case "chapter_cleared":
        return "進入下一階"
      default:
        return "前往處理"
    }
  })()

  return (
    <div className="space-y-3" data-testid="ladder-journey">
      {/* 1. 接著做：最大且唯一的主 CTA */}
      <div className="relative overflow-hidden rounded-2xl border-[1.5px] border-emerald-500/40 bg-gradient-to-br from-slate-900 via-slate-900/95 to-emerald-950/30 p-4 shadow-xl backdrop-blur-xl">
        <div className="flex items-center justify-between">
          <div className="inline-flex items-center gap-1.5 rounded-full border border-emerald-500/40 bg-emerald-500/15 px-2.5 py-0.5 text-[10px] font-bold text-emerald-300">
            <Sparkles className="size-3" />
            <span>接著做</span>
          </div>
          {next_step.estimated_time && (
            <span className="flex items-center gap-1 text-[11px] font-medium text-slate-400">
              <Clock className="size-3 text-slate-400" />
              <span>{next_step.estimated_time}</span>
            </span>
          )}
        </div>

        <div className="mt-2.5">
          <h2
            data-testid="next-step-title"
            className="text-base font-bold text-white tracking-wide"
          >
            {next_step.title}
          </h2>
          <p
            data-testid="next-step-reason"
            className="mt-1 text-xs text-slate-300 leading-relaxed"
          >
            {next_step.reason}
          </p>
        </div>

        <div className="mt-3.5 pt-2 border-t border-white/10">
          <Link
            to={next_step.href}
            data-testid="journey-main-cta"
            className="flex w-full items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-emerald-500 to-teal-600 py-2.5 text-center text-xs font-bold text-white shadow-lg hover:from-emerald-400 hover:to-teal-500 active:scale-[0.98] transition-all"
          >
            <span>{ctaLabel}</span>
            <ArrowRight className="size-3.5" />
          </Link>
        </div>
      </div>

      {/* 2. 這一章：兩個必要節點的簡潔路徑 */}
      <div className="rounded-2xl border-[1.5px] border-white/20 bg-slate-900/90 p-4 backdrop-blur-xl">
        <div className="flex items-center justify-between border-b border-white/10 pb-2.5">
          <div>
            <div className="flex items-center gap-2">
              <span className="rounded-full border border-sky-500/30 bg-sky-500/10 px-2 py-0.5 text-[10px] font-bold text-sky-300">
                第 {chapter.id} 階 · {chapter.rung_title}
              </span>
              <h3 className="text-xs font-bold text-white">{chapter.title}</h3>
            </div>
            <p className="mt-1 text-[11px] text-slate-400 leading-normal">
              {chapter.description}
            </p>
          </div>
          {chapter.contact_name && (
            <div className="flex shrink-0 flex-col items-center gap-1 pl-3">
              <span className="flex size-9 items-center justify-center rounded-full bg-slate-800 border border-white/15 text-lg">
                {chapter.contact_avatar || "👤"}
              </span>
              <span className="text-[10px] font-semibold text-slate-300">
                {chapter.contact_name}
              </span>
            </div>
          )}
        </div>

        {/* 兩個必要節點：狀態指示，不可同時出現兩個「前往」 */}
        <div
          className="mt-3 grid grid-cols-2 gap-2"
          data-testid="chapter-steps"
        >
          {/* 節點 1：先看一眼 */}
          <div
            data-testid="step-quiz"
            className={`flex items-center justify-between rounded-xl border px-3 py-2 transition-all ${
              quizStep?.status === "completed"
                ? "border-emerald-500/30 bg-emerald-950/20"
                : quizStep?.status === "current"
                  ? "border-sky-500/40 bg-sky-950/20"
                  : "border-white/10 bg-slate-800/40"
            }`}
          >
            <div className="flex items-center gap-2 min-w-0">
              {quizStep?.status === "completed" ? (
                <CheckCircle2 className="size-4 text-emerald-400 shrink-0" />
              ) : quizStep?.status === "current" ? (
                <CircleDot className="size-4 text-sky-400 shrink-0" />
              ) : (
                <Circle className="size-4 text-slate-500 shrink-0" />
              )}
              <span className="text-xs font-semibold text-slate-200 truncate">
                先看一眼
              </span>
            </div>
            <span
              className={`text-[10px] font-bold shrink-0 ${
                quizStep?.status === "completed"
                  ? "text-emerald-400"
                  : quizStep?.status === "current"
                    ? "text-sky-300"
                    : "text-slate-500"
              }`}
            >
              {quizStep?.status === "completed"
                ? "已完成"
                : quizStep?.status === "current"
                  ? "進行中"
                  : "稍後"}
            </span>
          </div>

          {/* 節點 2：接下委託 */}
          <div
            data-testid="step-scenario"
            className={`flex items-center justify-between rounded-xl border px-3 py-2 transition-all ${
              scenarioStep?.status === "completed"
                ? "border-emerald-500/30 bg-emerald-950/20"
                : scenarioStep?.status === "current"
                  ? "border-sky-500/40 bg-sky-950/20"
                  : "border-white/10 bg-slate-800/40"
            }`}
          >
            <div className="flex items-center gap-2 min-w-0">
              {scenarioStep?.status === "completed" ? (
                <CheckCircle2 className="size-4 text-emerald-400 shrink-0" />
              ) : scenarioStep?.status === "current" ? (
                <CircleDot className="size-4 text-sky-400 shrink-0" />
              ) : (
                <Circle className="size-4 text-slate-500 shrink-0" />
              )}
              <span className="text-xs font-semibold text-slate-200 truncate">
                接下委託
              </span>
            </div>
            <span
              className={`text-[10px] font-bold shrink-0 ${
                scenarioStep?.status === "completed"
                  ? "text-emerald-400"
                  : scenarioStep?.status === "current"
                    ? "text-sky-300"
                    : "text-slate-500"
              }`}
            >
              {scenarioStep?.status === "completed"
                ? "已完成"
                : scenarioStep?.status === "current"
                  ? "進行中"
                  : "稍後"}
            </span>
          </div>
        </div>

        {/* 通關解鎖提示 */}
        <div className="mt-2.5 flex items-center justify-between rounded-lg bg-slate-800/50 px-2.5 py-1.5 text-[11px] text-slate-400">
          <span className="flex items-center gap-1.5">
            {isAllComplete ? (
              <>
                <CheckCircle2 className="size-3.5 text-emerald-400" />
                <span className="text-emerald-300 font-semibold">
                  五階天梯全數通關！五位聯絡人皆已解鎖
                </span>
              </>
            ) : nextRungPreview ? (
              <>
                <Lock className="size-3.5 text-amber-400/80" />
                <span>通關解鎖：</span>
                <span className="font-semibold text-amber-300">
                  {nextRungPreview.contact_name}
                </span>
              </>
            ) : (
              <span>當前已是最高階委託</span>
            )}
          </span>
          <span className="font-mono text-[10px] text-slate-400">
            {completed_chapters}/5 階
          </span>
        </div>
      </div>

      {/* 3. 查看完整天梯（低顯著度可展開區） */}
      <div className="rounded-2xl border border-white/10 bg-slate-900/60 p-3">
        <button
          type="button"
          data-testid="toggle-all-rungs"
          onClick={() => setShowAllRungs(!showAllRungs)}
          className="flex w-full items-center justify-between text-left text-xs font-semibold text-slate-300 hover:text-white"
        >
          <span className="flex items-center gap-1.5">
            <span>查看完整天梯 (5 階)</span>
            <span className="rounded bg-white/10 px-1.5 py-0.2 text-[10px] font-mono text-slate-400">
              {completed_chapters} 完成
            </span>
          </span>
          {showAllRungs ? (
            <ChevronUp className="size-4 text-slate-400" />
          ) : (
            <ChevronDown className="size-4 text-slate-400" />
          )}
        </button>

        {showAllRungs && (
          <div
            className="mt-3 space-y-2 border-t border-white/10 pt-2.5"
            data-testid="all-rungs-list"
          >
            {all_chapters.map((r) => {
              const isDone = r.completed
              const isCurrent = r.is_current
              const isLocked = r.is_locked

              return (
                <div
                  key={r.id}
                  data-testid={`rung-item-${r.id}`}
                  className={`flex items-center justify-between rounded-xl border p-2.5 text-xs transition-all ${
                    isDone
                      ? "border-emerald-500/30 bg-emerald-950/15 text-slate-200"
                      : isCurrent
                        ? "border-sky-500/40 bg-sky-950/20 text-white shadow-sm"
                        : "border-white/5 bg-slate-900/40 text-slate-500"
                  }`}
                >
                  <div className="flex items-center gap-2.5 min-w-0">
                    <span className="flex size-7 shrink-0 items-center justify-center rounded-full bg-slate-800 border border-white/10 text-xs">
                      {isLocked ? "🔒" : r.contact_avatar || "👤"}
                    </span>
                    <div className="min-w-0">
                      <div className="flex items-center gap-1.5">
                        <span className="font-bold">
                          第 {r.id} 階 · {r.rung_title}
                        </span>
                        <span className="truncate text-[11px] text-slate-400">
                          {r.title}
                        </span>
                      </div>
                      <p className="truncate text-[10px] text-slate-400">
                        {r.contact_name}
                      </p>
                    </div>
                  </div>

                  <div className="shrink-0 pl-2">
                    {isDone ? (
                      <span className="inline-flex items-center gap-1 rounded-full bg-emerald-500/15 px-2 py-0.5 text-[10px] font-bold text-emerald-400 border border-emerald-500/30">
                        <CheckCircle2 className="size-3" />
                        <span>已通關</span>
                      </span>
                    ) : isCurrent ? (
                      <span className="inline-flex items-center gap-1 rounded-full bg-sky-500/15 px-2 py-0.5 text-[10px] font-bold text-sky-300 border border-sky-500/30">
                        <CircleDot className="size-3" />
                        <span>進行中</span>
                      </span>
                    ) : (
                      <span className="inline-flex items-center gap-1 rounded-full bg-slate-800 px-2 py-0.5 text-[10px] font-semibold text-slate-400 border border-white/10">
                        <Lock className="size-3" />
                        <span>未解鎖</span>
                      </span>
                    )}
                  </div>
                </div>
              )
            })}
          </div>
        )}
      </div>
    </div>
  )
}
