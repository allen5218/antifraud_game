import { useMutation, useQueryClient } from "@tanstack/react-query"
import { Link } from "@tanstack/react-router"
import { ChevronDown, ChevronUp, Circle, CircleCheck } from "lucide-react"
import { useState } from "react"
import type { StarterTasks } from "@/client"
import { Button } from "@/components/ui/button"
import useCustomToast from "@/hooks/useCustomToast"
import { extractErrorCode } from "@/hooks/useEconomy"
import { HOME_SUMMARY_KEY } from "@/hooks/useHomeSummary"
import { onboardingApi } from "./onboardingApi"

const COLLAPSED_KEY = "starter-tasks-collapsed"

const TASKS = [
  { key: "swipe", label: "滑一輪卡", to: "/quick/swipe" },
  { key: "quiz", label: "判讀一輪訊息", to: "/quick/quiz" },
  { key: "scenario", label: "和 AI 角色聊一場", to: "/scenarios" },
  { key: "shop", label: "去購物看看", to: "/shop" },
] as const

const CLAIM_ERRORS: Record<string, string> = {
  reward_claimed: "獎勵已經領過了。",
  tasks_incomplete: "四項任務都完成才能領。",
}

function readCollapsed(): boolean {
  try {
    return localStorage.getItem(COLLAPSED_KEY) === "1"
  } catch {
    return false
  }
}

function writeCollapsed(value: boolean): void {
  try {
    localStorage.setItem(COLLAPSED_KEY, value ? "1" : "0")
  } catch {
    // 無痕視窗等情況存不了，收起狀態只在這次有效
  }
}

/** 新手任務：每種練習各玩一次、看看商店，四項都做完可以領一次獎勵 */
export function StarterTasksCard({ tasks }: { tasks: StarterTasks }) {
  const [collapsed, setCollapsed] = useState(readCollapsed)
  const queryClient = useQueryClient()
  const { showSuccessToast, showErrorToast } = useCustomToast()
  const done = TASKS.filter((task) => tasks[task.key]).length
  const claim = useMutation({
    mutationFn: () => onboardingApi.claim(),
    onSuccess: (reward) => {
      showSuccessToast(`拿到 ${reward.cash} 元和 ${reward.xp} 經驗值`)
      queryClient.invalidateQueries({ queryKey: HOME_SUMMARY_KEY })
      queryClient.invalidateQueries({ queryKey: ["economy"] })
    },
    onError: (err) => {
      const code = extractErrorCode(err)
      showErrorToast(
        (code && CLAIM_ERRORS[code]) ?? "領獎沒有成功，請再試一次。",
      )
      queryClient.invalidateQueries({ queryKey: HOME_SUMMARY_KEY })
    },
  })
  const toggle = () => {
    writeCollapsed(!collapsed)
    setCollapsed(!collapsed)
  }

  return (
    <section
      data-testid="starter-tasks"
      className="w-full rounded-2xl border bg-card/95 p-2.5 text-card-foreground shadow-lg"
    >
      <div className="flex items-center gap-1">
        <p className="flex-1 text-sm font-bold tabular-nums">
          新手任務 {done}／{TASKS.length}
        </p>
        <button
          type="button"
          onClick={toggle}
          aria-label={collapsed ? "展開新手任務" : "收起新手任務"}
          className="rounded-full p-1 text-muted-foreground"
        >
          {collapsed ? (
            <ChevronDown aria-hidden className="size-4" />
          ) : (
            <ChevronUp aria-hidden className="size-4" />
          )}
        </button>
      </div>
      {!collapsed && (
        <p className="text-[11px] text-muted-foreground">
          獎勵：{tasks.reward_cash} 元、{tasks.reward_xp} 經驗值
        </p>
      )}
      {!collapsed && (
        <ul className="mt-1 flex flex-col">
          {TASKS.map((task) => {
            const finished = tasks[task.key]
            return (
              <li key={task.key}>
                <Link
                  to={task.to}
                  data-done={finished}
                  className={`flex items-center gap-2 rounded-lg px-1 py-1 text-sm ${
                    finished ? "text-muted-foreground line-through" : ""
                  }`}
                >
                  {finished ? (
                    <CircleCheck aria-hidden className="size-4 text-legit" />
                  ) : (
                    <Circle aria-hidden className="size-4" />
                  )}
                  {task.label}
                </Link>
              </li>
            )
          })}
        </ul>
      )}
      {/* 收起時也看得到領獎，免得做完了卻找不到 */}
      {done === TASKS.length && (
        <Button
          size="sm"
          className="mt-2 w-full"
          disabled={claim.isPending}
          onClick={() => claim.mutate()}
        >
          領獎勵
        </Button>
      )}
    </section>
  )
}
