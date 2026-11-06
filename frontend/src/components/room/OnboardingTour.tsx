import { Link } from "@tanstack/react-router"
import { useLayoutEffect, useState } from "react"
import { Button } from "@/components/ui/button"
import { TOUR_TEST_IDS, type TourStep } from "./tour"

type Spot = { left: number; top: number; width: number; height: number }

const PAD = 6 // 亮框比物件大一點，邊緣不會切到
// 亮框外面的遮罩用超大的 box-shadow 畫，顏色和沒有亮框時的 bg-black/55 一樣
const DIM = "rgb(0 0 0 / 0.55)"

/** 找出這一步要亮的東西在畫面上的位置；找不到（或這一步不亮東西）就整片變暗 */
function measure(step: TourStep): Spot | null {
  if (!step.target) return null
  const el = document.querySelector(
    `[data-testid="${TOUR_TEST_IDS[step.target]}"]`,
  )
  if (!el) return null
  const r = el.getBoundingClientRect()
  if (r.width === 0 && r.height === 0) return null
  return {
    left: r.left - PAD,
    top: r.top - PAD,
    width: r.width + PAD * 2,
    height: r.height + PAD * 2,
  }
}

/**
 * 新手導覽：畫面變暗，一次亮一件東西，吉祥物在對話框說明。
 * 亮的東西在畫面上半部時對話框放下面，反過來放上面，不會擋住正在介紹的東西。
 */
export function OnboardingTour({
  steps,
  mascotSrc,
  onFinish,
}: {
  steps: TourStep[]
  mascotSrc: string
  onFinish: () => void
}) {
  const [index, setIndex] = useState(0)
  const step = steps[index]
  const last = index === steps.length - 1
  const [spot, setSpot] = useState<Spot | null>(null)

  useLayoutEffect(() => {
    const update = () => setSpot(measure(step))
    update()
    window.addEventListener("resize", update)
    return () => window.removeEventListener("resize", update)
  }, [step])

  const spotCenter = spot ? spot.top + spot.height / 2 : 0
  const dialogBelow = spot !== null && spotCenter < window.innerHeight / 2

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-label="新手導覽"
      data-testid="onboarding-tour"
      className="fixed inset-0 z-[60]"
    >
      {spot ? (
        <div
          aria-hidden="true"
          className="pointer-events-none fixed rounded-2xl ring-2 ring-warning transition-all duration-300"
          style={{ ...spot, boxShadow: `0 0 0 9999px ${DIM}` }}
        />
      ) : (
        <div aria-hidden="true" className="fixed inset-0 bg-black/55" />
      )}
      <div
        className={`fixed inset-x-3 mx-auto max-w-sm rounded-2xl border bg-card p-4 text-card-foreground shadow-xl ${
          dialogBelow
            ? "bottom-[calc(env(safe-area-inset-bottom)+1.5rem)]"
            : "top-[calc(env(safe-area-inset-top)+4.5rem)]"
        }`}
      >
        <div className="flex gap-3">
          <img
            src={mascotSrc}
            alt=""
            aria-hidden="true"
            className="size-16 shrink-0 object-contain"
          />
          <div className="min-w-0">
            <p className="font-bold">{step.title}</p>
            <p className="mt-1 text-sm leading-relaxed">{step.text}</p>
          </div>
        </div>
        <div className="mt-3 flex items-center gap-2">
          <span className="text-xs text-muted-foreground tabular-nums">
            第 {index + 1}／{steps.length} 步
          </span>
          {!last && (
            <button
              type="button"
              onClick={onFinish}
              className="ml-auto text-xs font-bold text-muted-foreground"
            >
              跳過導覽
            </button>
          )}
          {!last && (
            <Button size="sm" onClick={() => setIndex(index + 1)}>
              下一步
            </Button>
          )}
          {last && step.action && (
            <Button size="sm" asChild className="ml-auto">
              <Link to={step.action.to} onClick={onFinish}>
                {step.action.label}
              </Link>
            </Button>
          )}
          {last && !step.action && (
            <Button size="sm" className="ml-auto" onClick={onFinish}>
              知道了
            </Button>
          )}
        </div>
      </div>
    </div>
  )
}
