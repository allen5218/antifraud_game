import { createFileRoute } from "@tanstack/react-router"

export const Route = createFileRoute("/_shell/scenarios")({
  component: ScenariosPlaceholder,
})

function ScenariosPlaceholder() {
  return (
    <div className="flex h-full flex-col items-center justify-center gap-3 py-12 text-center">
      <span className="text-5xl">💬</span>
      <h2 className="text-lg font-bold">真實情境模擬</h2>
      <p className="text-xs text-muted-foreground">
        即將開放：聯絡人會傳訊息給你，
        <br />
        你要在對話中辨識詐騙。
      </p>
    </div>
  )
}
