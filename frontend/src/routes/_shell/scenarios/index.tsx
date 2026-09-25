import { createFileRoute, useNavigate } from "@tanstack/react-router"
import { PracticeFocusBadge } from "@/components/practice/PracticeFocus"
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
        載入失敗，請稍後再試
      </p>
    )
  }
  return (
    <div className="flex flex-col">
      <p className="px-4 pt-3 text-xs text-muted-foreground">
        這些人傳訊息給你，有的是詐騙、有的是正常聯絡。聊聊看，再判斷要不要相信。
      </p>
      <PracticeFocusBadge className="mx-4 mt-2" />
      <div className="h-2" />
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
