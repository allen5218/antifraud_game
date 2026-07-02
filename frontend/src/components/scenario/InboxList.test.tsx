import { afterEach, describe, expect, it } from "bun:test"
import { cleanup, render, screen } from "@testing-library/react"
import { InboxList } from "./InboxList"

afterEach(cleanup)

const items = [
  {
    id: "1",
    fraud_type: "investment",
    display_name: "Kevin",
    avatar: "📈",
    preview: "先跟兩天看看績效再說!",
    status: "active",
    outcome: null,
    unread: true,
  },
  {
    id: "2",
    fraud_type: "romance",
    display_name: "Sunny",
    avatar: "🧗",
    preview: "你週末有空嗎?",
    status: "completed",
    outcome: "win_report",
    unread: false,
  },
]

describe("<InboxList />", () => {
  it("renders contact rows with type label, preview and unread dot", () => {
    render(<InboxList items={items} onOpen={() => {}} />)
    expect(screen.getByText("Kevin")).toBeTruthy()
    expect(screen.getByText("投資")).toBeTruthy()
    expect(screen.getByText(/先跟兩天看看績效/)).toBeTruthy()
    expect(screen.getByTestId("unread-1")).toBeTruthy()
  })

  it("shows outcome badge for completed scenario", () => {
    render(<InboxList items={items} onOpen={() => {}} />)
    expect(screen.getByText("✓ 識破成功")).toBeTruthy()
  })
})
