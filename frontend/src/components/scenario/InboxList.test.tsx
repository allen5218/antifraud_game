import { afterEach, describe, expect, it } from "bun:test"
import { cleanup, fireEvent, render, screen } from "@testing-library/react"
import { InboxList, listTime } from "./InboxList"

afterEach(cleanup)

const items = [
  {
    id: "1",
    fraud_type: "investment",
    display_name: "Kevin",
    avatar: "investment-1",
    preview: "先跟兩天看看績效再說!",
    status: "active",
    outcome: null,
    unread: true,
    unread_count: 3,
    last_at: new Date().toISOString(),
  },
  {
    id: "2",
    fraud_type: "romance",
    display_name: "Sunny",
    avatar: "🧗", // 改版前存的 emoji,要顯示通用圖示而不是原字串
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
    expect(screen.getByText("投資詐騙")).toBeTruthy()
    expect(screen.getByText(/先跟兩天看看績效/)).toBeTruthy()
    expect(screen.getByTestId("unread-1").textContent).toBe("3")
    expect(screen.queryByTestId("unread-2")).toBeNull()
  })

  it("頭貼用插圖;改版前存的 emoji 不直接印出來", () => {
    const { container } = render(<InboxList items={items} onOpen={() => {}} />)
    const img = container.querySelector("img")
    expect(img?.getAttribute("src")).toBe("/assets/avatar/investment-1.webp")
    expect(screen.queryByText("🧗")).toBeNull()
  })

  // 2026-10-18 正式環境：螢幕閱讀器只念「按鈕」，聽不出是哪一位聯絡人
  it("每一列的按鈕念得出聯絡人、類型、狀態與最新訊息", () => {
    render(<InboxList items={items} onOpen={() => {}} />)
    expect(
      screen.getByRole("button", {
        name: "Kevin，投資詐騙，未讀 3 則，先跟兩天看看績效再說!",
      }),
    ).toBeTruthy()
    expect(
      screen.getByRole("button", {
        name: "Sunny，假交友，識破成功，你週末有空嗎?",
      }),
    ).toBeTruthy()
  })

  it("shows outcome badge for completed scenario", () => {
    render(<InboxList items={items} onOpen={() => {}} />)
    expect(screen.getByText("識破成功")).toBeTruthy()
  })

  it("搜尋名字、訊息或類型", () => {
    render(<InboxList items={items} onOpen={() => {}} />)
    const search = screen.getByRole("searchbox", { name: "搜尋聊天" })
    fireEvent.change(search, { target: { value: "週末" } })
    expect(screen.queryByText("Kevin")).toBeNull()
    expect(screen.getByText("Sunny")).toBeTruthy()
    fireEvent.change(search, { target: { value: "投資" } })
    expect(screen.getByText("Kevin")).toBeTruthy()
    fireEvent.change(search, { target: { value: "沒有這個人" } })
    expect(screen.getByText("找不到符合的聊天")).toBeTruthy()
  })

  it("時間：今天寫幾點、昨天寫昨天、更早寫日期", () => {
    const now = new Date(2026, 9, 23, 15, 0)
    expect(listTime(new Date(2026, 9, 23, 9, 5).toISOString(), now)).toMatch(
      /9:05/,
    )
    expect(listTime(new Date(2026, 9, 22, 9, 5).toISOString(), now)).toBe(
      "昨天",
    )
    expect(listTime(new Date(2026, 9, 2, 9, 5).toISOString(), now)).toBe("10/2")
    expect(listTime(null, now)).toBe("")
  })
})
