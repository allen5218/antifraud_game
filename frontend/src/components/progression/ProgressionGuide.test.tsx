import { expect, mock, test } from "bun:test"
import { fireEvent, render, screen } from "@testing-library/react"
import { GUIDE_STEPS } from "./guideSteps"
import { ProgressionGuide } from "./ProgressionGuide"

test("一步一步看，最後按知道了關掉", () => {
  const onClose = mock(() => {})
  render(<ProgressionGuide open onClose={onClose} mascotSrc="/m.webp" />)
  expect(screen.getByText(GUIDE_STEPS[0].title)).toBeTruthy()
  expect(screen.getByText(`第 1／${GUIDE_STEPS.length} 步`)).toBeTruthy()
  fireEvent.click(screen.getByRole("button", { name: "下一步" }))
  expect(screen.getByText(GUIDE_STEPS[1].title)).toBeTruthy()
  fireEvent.click(screen.getByRole("button", { name: "上一步" }))
  expect(screen.getByText(GUIDE_STEPS[0].title)).toBeTruthy()
  for (let i = 1; i < GUIDE_STEPS.length; i++) {
    fireEvent.click(screen.getByRole("button", { name: "下一步" }))
  }
  expect(screen.getByText(GUIDE_STEPS.at(-1)?.title ?? "")).toBeTruthy()
  expect(screen.queryByRole("button", { name: "下一步" })).toBeNull()
  fireEvent.click(screen.getByRole("button", { name: "知道了" }))
  expect(onClose).toHaveBeenCalledTimes(1)
})

test("中途可以跳過說明", () => {
  const onClose = mock(() => {})
  render(<ProgressionGuide open onClose={onClose} mascotSrc="/m.webp" />)
  fireEvent.click(screen.getByRole("button", { name: "跳過說明" }))
  expect(onClose).toHaveBeenCalledTimes(1)
})

test("重新打開時從第一步開始", () => {
  const onClose = mock(() => {})
  const { rerender } = render(
    <ProgressionGuide open onClose={onClose} mascotSrc="/m.webp" />,
  )
  fireEvent.click(screen.getByRole("button", { name: "下一步" }))
  rerender(
    <ProgressionGuide open={false} onClose={onClose} mascotSrc="/m.webp" />,
  )
  rerender(<ProgressionGuide open onClose={onClose} mascotSrc="/m.webp" />)
  expect(screen.getByText(`第 1／${GUIDE_STEPS.length} 步`)).toBeTruthy()
})
