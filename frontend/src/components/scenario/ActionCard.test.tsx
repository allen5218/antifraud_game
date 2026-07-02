import { afterEach, describe, expect, it, mock } from "bun:test"
import { cleanup, fireEvent, render, screen } from "@testing-library/react"
import { ActionCard } from "./ActionCard"

afterEach(cleanup)

describe("<ActionCard />", () => {
  it("shows demand text and fires callbacks", () => {
    const onComply = mock(() => {})
    const onRefuse = mock(() => {})
    render(
      <ActionCard
        text="先轉 5000 到合作券商鎖額度"
        onComply={onComply}
        onRefuse={onRefuse}
        disabled={false}
      />,
    )
    expect(screen.getByText(/先轉 5000/)).toBeTruthy()
    fireEvent.click(screen.getByText("照做"))
    expect(onComply).toHaveBeenCalledTimes(1)
    fireEvent.click(screen.getByText("拒絕"))
    expect(onRefuse).toHaveBeenCalledTimes(1)
  })

  it("回合用盡(refuseDisabled)時拒絕鈕鎖住、照做鈕仍可點", () => {
    const onComply = mock(() => {})
    const onRefuse = mock(() => {})
    render(
      <ActionCard
        text="先轉 5000 到合作券商鎖額度"
        onComply={onComply}
        onRefuse={onRefuse}
        disabled={false}
        refuseDisabled={true}
      />,
    )
    const refuseBtn = screen.getByText("拒絕") as HTMLButtonElement
    expect(refuseBtn.disabled).toBe(true)
    fireEvent.click(refuseBtn)
    expect(onRefuse).not.toHaveBeenCalled()

    const complyBtn = screen.getByText("照做") as HTMLButtonElement
    expect(complyBtn.disabled).toBe(false)
    fireEvent.click(complyBtn)
    expect(onComply).toHaveBeenCalledTimes(1)
  })
})
