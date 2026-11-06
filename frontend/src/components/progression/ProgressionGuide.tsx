import { useEffect, useState } from "react"
import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogTitle,
} from "@/components/ui/dialog"
import { GUIDE_STEPS } from "./guideSteps"

/**
 * 養成頁的玩法說明：吉祥物一頁講一件事，可以上一步、下一步或跳過。
 * 房間導覽只帶一句「裝備」，細節都在這裡講清楚。
 */
export function ProgressionGuide({
  open,
  onClose,
  mascotSrc,
}: {
  open: boolean
  onClose: () => void
  mascotSrc: string
}) {
  const [index, setIndex] = useState(0)
  // 每次打開都從第一步開始
  useEffect(() => {
    if (open) setIndex(0)
  }, [open])

  const step = GUIDE_STEPS[index]
  const last = index === GUIDE_STEPS.length - 1

  return (
    <Dialog open={open} onOpenChange={(next) => !next && onClose()}>
      <DialogContent
        data-testid="progression-guide"
        className="max-w-[calc(100%-2rem)] gap-3 p-4 sm:max-w-sm"
      >
        <div className="flex gap-3">
          <img
            src={mascotSrc}
            alt=""
            aria-hidden="true"
            className="size-16 shrink-0 object-contain"
          />
          <div className="min-w-0 pr-5">
            <DialogTitle className="text-base font-bold">
              {step.title}
            </DialogTitle>
            <DialogDescription className="mt-1 text-sm leading-relaxed text-card-foreground">
              {step.text}
            </DialogDescription>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs text-muted-foreground tabular-nums">
            第 {index + 1}／{GUIDE_STEPS.length} 步
          </span>
          {!last && (
            <button
              type="button"
              onClick={onClose}
              className="ml-auto text-xs font-bold text-muted-foreground"
            >
              跳過說明
            </button>
          )}
          {index > 0 && (
            <Button
              size="sm"
              variant="outline"
              className={last ? "ml-auto" : ""}
              onClick={() => setIndex(index - 1)}
            >
              上一步
            </Button>
          )}
          {last ? (
            <Button
              size="sm"
              className={index === 0 ? "ml-auto" : ""}
              onClick={onClose}
            >
              知道了
            </Button>
          ) : (
            <Button size="sm" onClick={() => setIndex(index + 1)}>
              下一步
            </Button>
          )}
        </div>
      </DialogContent>
    </Dialog>
  )
}
