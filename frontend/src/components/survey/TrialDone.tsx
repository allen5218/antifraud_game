import { Link } from "@tanstack/react-router"
import { CircleCheck, CircleX } from "lucide-react"
import type { TrialSurveyPublic } from "@/client"
import { Button } from "@/components/ui/button"

/** 問卷交完：受試編號與能不能領錢，給工作人員在管理頁核對（同一套判定） */
export function TrialDone({ data }: { data: TrialSurveyPublic }) {
  const eligible = data.payout_eligible === true
  const reasons = data.payout_reasons ?? []
  return (
    <div className="flex flex-col items-center gap-5 py-8 text-center">
      <p className="font-bold">問卷收到了，謝謝你！</p>
      <section className="w-full max-w-sm rounded-2xl border-2 border-primary bg-card p-6">
        <p className="text-sm text-muted-foreground">你的受試編號</p>
        <p
          className="my-2 text-5xl font-extrabold tracking-wider"
          data-testid="participant-code"
        >
          {data.participant_code ?? "沒有編號"}
        </p>
        <p
          className={`mt-4 flex items-center justify-center gap-2 rounded-xl p-3 text-lg font-bold ${
            eligible ? "bg-legit/10 text-legit" : "bg-scam/10 text-scam"
          }`}
          data-testid="payout-status"
        >
          {eligible ? (
            <CircleCheck aria-hidden className="size-6" />
          ) : (
            <CircleX aria-hidden className="size-6" />
          )}
          {eligible ? "可以領取禮券" : "不能領取禮券"}
        </p>
        {!eligible && reasons.length > 0 && (
          <p className="mt-2 text-sm text-muted-foreground">
            原因：{reasons.join("、")}
          </p>
        )}
      </section>
      <p className="max-w-sm text-sm">
        請截圖這個畫面，或直接拿給工作人員看。之後從房間選單的「試測完成」也能再打開。
      </p>
      <Button asChild>
        <Link to="/">回房間</Link>
      </Button>
    </div>
  )
}
