import { afterEach, describe, expect, it, mock } from "bun:test"
import { cleanup, fireEvent, render, screen } from "@testing-library/react"
import type { ScenarioBranchAction } from "@/client"
import { BranchActionsModal } from "./BranchActionsModal"

afterEach(cleanup)

const MOCK_ACTIONS: ScenarioBranchAction[] = [
  {
    action_id: "check_personal_records",
    label: "調閱親友自查紀錄",
    category: "network",
    description: "調閱親友留存收據與通訊紀錄",
    available: true,
  },
  {
    action_id: "high_cash_collateral",
    label: "提存大額保證金",
    category: "cash",
    description: "自備五千元現金前往約定處所抵押",
    available: false,
    unavailable_reason: "現金不足 $5,000",
  },
  {
    action_id: "item_dashcam_verify",
    label: "行車記錄器查證",
    category: "xp_item",
    description: "調閱行車記錄器時間軸比對行程",
    available: false,
    completed: true,
    unavailable_reason: "本事件已完成這項行動",
  },
]

describe("<BranchActionsModal />", () => {
  it("renders actions with correct status, category and labels", () => {
    const onExecute = mock(() => {})
    const onClose = mock(() => {})
    const onGoShop = mock(() => {})

    render(
      <BranchActionsModal
        open={true}
        onClose={onClose}
        actions={MOCK_ACTIONS}
        onExecute={onExecute}
        isExecuting={false}
        onGoShop={onGoShop}
      />,
    )

    // Header and count
    expect(screen.getByText(/可以怎麼幫忙 \(1\/3\)/)).toBeTruthy()
    expect(screen.getByText(/每個方法只提供一部分線索/)).toBeTruthy()

    // Available action
    expect(screen.getByText("調閱親友自查紀錄")).toBeTruthy()
    const execBtn = screen.getByTestId("execute-action-check_personal_records")
    expect(execBtn).toBeTruthy()
    fireEvent.click(execBtn)
    expect(onExecute).toHaveBeenCalledWith("check_personal_records")

    // Unavailable action reasons
    expect(screen.getByText("現金不足 $5,000")).toBeTruthy()
    expect(screen.getByText("本次已完成")).toBeTruthy()
    expect(screen.getByText("結果已寫入聊天紀錄")).toBeTruthy()

    // Shop navigation
    const shopBtn = screen.getByText(/前往防詐道具商店購置裝備/)
    fireEvent.click(shopBtn)
    expect(onGoShop).toHaveBeenCalledTimes(1)

    // Close button
    fireEvent.click(screen.getByRole("button", { name: "關閉" }))
    expect(onClose).toHaveBeenCalledTimes(1)
  })

  it("does not render when open is false", () => {
    const { container } = render(
      <BranchActionsModal
        open={false}
        onClose={() => {}}
        actions={MOCK_ACTIONS}
        onExecute={() => {}}
        isExecuting={false}
      />,
    )
    expect(container.firstChild).toBeNull()
  })
})
