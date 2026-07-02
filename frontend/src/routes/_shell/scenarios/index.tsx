import { createFileRoute, useNavigate } from "@tanstack/react-router"
import { InboxList } from "@/components/scenario/InboxList"
import { useScenarioInbox } from "@/hooks/useScenario"

export const Route = createFileRoute("/_shell/scenarios/")({
  component: ScenariosInboxPage,
})

function ScenariosInboxPage() {
  const navigate = useNavigate()
  const { data, isPending, isError } = useScenarioInbox()

  if (isPending) {
    return (
      <p className="py-12 text-center text-xs text-muted-foreground">載入中…</p>
    )
  }
  if (isError || !data) {
    return (
      <p className="py-12 text-center text-xs text-muted-foreground">
        載入失敗,請稍後再試
      </p>
    )
  }
  return (
    <div className="flex flex-col">
      <p className="px-4 py-3 text-xs text-muted-foreground">
        陌生人傳訊息給你——在對話中辨識真偽,小心你的錢包 💸
      </p>
      <InboxList
        items={data}
        onOpen={(item) =>
          navigate({
            to: "/scenarios/$scenarioId",
            params: { scenarioId: item.id },
          })
        }
      />
    </div>
  )
}
