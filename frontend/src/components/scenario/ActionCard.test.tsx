import { describe, expect, it, mock } from "bun:test"
import { fireEvent, render, screen } from "@testing-library/react"
import { ActionCard } from "./ActionCard"

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
})
