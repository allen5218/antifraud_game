import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"

/** 檢測頁與首頁共用。繼續作答是主要按鈕，確定放棄是次要，避免誤按。 */
export function ExamAbandonDialog({
  open,
  pending = false,
  onOpenChange,
  onConfirm,
}: {
  open: boolean
  pending?: boolean
  onOpenChange: (open: boolean) => void
  onConfirm: () => void
}) {
  return (
    <Dialog
      open={open}
      onOpenChange={(next) => {
        if (!pending) onOpenChange(next)
      }}
    >
      <DialogContent>
        <DialogHeader>
          <DialogTitle>要放棄這次檢測嗎？</DialogTitle>
          <DialogDescription>
            放棄算一次沒過。已交的關卡照算，還沒交的關卡以零分計算。
          </DialogDescription>
        </DialogHeader>
        <DialogFooter>
          <Button disabled={pending} onClick={() => onOpenChange(false)}>
            繼續作答
          </Button>
          <Button variant="outline" disabled={pending} onClick={onConfirm}>
            確定放棄
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
