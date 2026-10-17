import { Link } from "@tanstack/react-router"
import type { ExamGate as Gate } from "@/client"
import { fraudTypeLabel } from "@/lib/fraudTypes"
import { gateRemaining } from "./exam"

export function ExamGate({ gate }: { gate: Gate }) {
  return (
    <section className="rounded-2xl border border-warning/40 bg-warning/10 p-4">
      <h2 className="font-bold">
        檢測沒過：先加強{fraudTypeLabel(gate.fraud_type)}
      </h2>
      <p className="mt-2 text-sm">{gateRemaining(gate)}</p>
      {!gate.met && (
        <p className="mt-2 text-xs text-muted-foreground">
          最近十題算滑卡和訊息判讀：目前練了 {gate.recent.total} 題，答對{" "}
          {gate.recent.correct} 題。
        </p>
      )}
      {!gate.met && (
        <div className="mt-3 flex flex-wrap gap-3 text-sm text-primary">
          <Link to="/quick/swipe">練滑卡</Link>
          <Link to="/quick/quiz">練訊息判讀</Link>
          <Link to="/scenarios">練情境對抗</Link>
        </div>
      )}
    </section>
  )
}
