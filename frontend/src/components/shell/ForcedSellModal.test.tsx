import { afterEach, describe, expect, it, mock } from "bun:test"
import { cleanup, fireEvent, render, screen } from "@testing-library/react"

// 破產未發生時
const defaultMeData = {
  cash: 12450,
  streak_days: 5,
  level: 3,
  pending_accrual: 840,
  bankruptcy_pending: false,
  xp: 850,
}

// 破產發生時（-22,550）
const bankruptMeData = {
  cash: -22550,
  streak_days: 5,
  level: 3,
  pending_accrual: 0,
  bankruptcy_pending: true,
  xp: 850,
}

// 模擬擁有的房產
const mockOwned = [
  {
    id: "mock-1",
    tier: {
      id: 1,
      name: "雅房",
      svg_key: "tier-1",
      price: 1000,
      daily_income: 5,
      unlock_level: 1,
    },
    purchased_at: "2026-05-20",
  },
  {
    id: "mock-2",
    tier: {
      id: 2,
      name: "套房",
      svg_key: "tier-2",
      price: 5000,
      daily_income: 35,
      unlock_level: 1,
    },
    purchased_at: "2026-05-25",
  },
]

const mockLiquidate = mock((_ids: string[]) => {})

mock.module("@/hooks/useEconomy", () => ({
  useEconomyMe: () => ({ data: defaultMeData }),
  useProperties: () => ({ data: { tiers: [], owned: mockOwned } }),
  useLiquidate: () => ({ mutate: mockLiquidate }),
  useClaimAccrual: () => ({ mutate: () => {}, isPending: false }),
  useAssets: () => ({ data: null }),
  useBuyProperty: () => ({ mutate: () => {} }),
}))

import { ForcedSellModal } from "./ForcedSellModal"

afterEach(() => {
  cleanup()
  mockLiquidate.mockClear()
})

describe("<ForcedSellModal />", () => {
  it("renders null when bankruptcy_pending is false", () => {
    const { container } = render(<ForcedSellModal />)
    expect(container.firstChild).toBeNull()
  })

  it("renders modal with deficit when bankruptcy_pending is true", () => {
    mock.module("@/hooks/useEconomy", () => ({
      useEconomyMe: () => ({ data: bankruptMeData }),
      useProperties: () => ({ data: { tiers: [], owned: mockOwned } }),
      useLiquidate: () => ({ mutate: mockLiquidate }),
      useClaimAccrual: () => ({ mutate: () => {}, isPending: false }),
      useAssets: () => ({ data: null }),
      useBuyProperty: () => ({ mutate: () => {} }),
    }))
    render(<ForcedSellModal />)
    expect(screen.getByText(/被詐騙/)).toBeTruthy()
    expect(screen.getByText(/現金不足/)).toBeTruthy()
  })

  it("confirm disabled with no selection, enabled after enough selected", () => {
    // cash -1550 → deficit 1550; 套房(mock-2) recovers floor(5000*0.6)=3000 >= 1550
    mock.module("@/hooks/useEconomy", () => ({
      useEconomyMe: () => ({
        data: {
          cash: -1550,
          streak_days: 5,
          level: 3,
          pending_accrual: 0,
          bankruptcy_pending: true,
          xp: 850,
        },
      }),
      useProperties: () => ({ data: { tiers: [], owned: mockOwned } }),
      useLiquidate: () => ({ mutate: mockLiquidate }),
      useClaimAccrual: () => ({ mutate: () => {}, isPending: false }),
      useAssets: () => ({ data: null }),
      useBuyProperty: () => ({ mutate: () => {} }),
    }))
    render(<ForcedSellModal />)
    const btn = screen.getByRole("button", { name: /確認變賣/ })
    expect(btn.hasAttribute("disabled")).toBe(true)
    fireEvent.click(screen.getByTestId("sell-row-mock-2"))
    expect(btn.hasAttribute("disabled")).toBe(false)
  })

  it("renders null when bankruptcy_pending is true but cash >= 0 (stale flag)", () => {
    // 模擬管理員手動補現金卻沒清 flag：不該出現 $0 缺口的空視窗
    mock.module("@/hooks/useEconomy", () => ({
      useEconomyMe: () => ({
        data: { ...bankruptMeData, cash: 500 },
      }),
      useProperties: () => ({ data: { tiers: [], owned: mockOwned } }),
      useLiquidate: () => ({ mutate: mockLiquidate }),
      useClaimAccrual: () => ({ mutate: () => {}, isPending: false }),
      useAssets: () => ({ data: null }),
      useBuyProperty: () => ({ mutate: () => {} }),
    }))
    const { container } = render(<ForcedSellModal />)
    expect(container.firstChild).toBeNull()
  })

  it("no assets: shows recovery notice and dismiss button, never a confirm button", () => {
    mock.module("@/hooks/useEconomy", () => ({
      useEconomyMe: () => ({ data: bankruptMeData }),
      useProperties: () => ({ data: { tiers: [], owned: [] } }),
      useLiquidate: () => ({ mutate: mockLiquidate }),
      useClaimAccrual: () => ({ mutate: () => {}, isPending: false }),
      useAssets: () => ({ data: null }),
      useBuyProperty: () => ({ mutate: () => {} }),
    }))
    const { container } = render(<ForcedSellModal />)
    expect(screen.getByTestId("no-assets-notice")).toBeTruthy()
    // 沒有「確認變賣」按鈕 → 不可能送出空 property_ids
    expect(screen.queryByRole("button", { name: /確認變賣/ })).toBeNull()
    // 點「先去答題還債」關閉視窗，玩家可以繼續遊戲還債
    fireEvent.click(screen.getByTestId("go-earn-btn"))
    expect(container.firstChild).toBeNull()
    expect(mockLiquidate).not.toHaveBeenCalled()
  })

  it("insufficient assets: allows partial liquidation but not empty submit", () => {
    // deficit 22550 > 全部回收 600+3000=3600 → insufficientAssets
    mock.module("@/hooks/useEconomy", () => ({
      useEconomyMe: () => ({ data: bankruptMeData }),
      useProperties: () => ({ data: { tiers: [], owned: mockOwned } }),
      useLiquidate: () => ({ mutate: mockLiquidate }),
      useClaimAccrual: () => ({ mutate: () => {}, isPending: false }),
      useAssets: () => ({ data: null }),
      useBuyProperty: () => ({ mutate: () => {} }),
    }))
    render(<ForcedSellModal />)
    const btn = screen.getByRole("button", { name: /確認變賣/ })
    // 未勾選 → 永遠 disabled
    expect(btn.hasAttribute("disabled")).toBe(true)
    // 勾選其一 → 允許部分清償
    fireEvent.click(screen.getByTestId("sell-row-mock-1"))
    expect(btn.hasAttribute("disabled")).toBe(false)
    // 同時提供答題還債逃生路徑
    expect(screen.getByTestId("go-earn-btn")).toBeTruthy()
  })

  it("confirm calls liquidate with correct ids", () => {
    const calls: string[][] = []
    const mutateSpy = (ids: string[], _opts?: unknown) => {
      calls.push(ids)
    }
    mock.module("@/hooks/useEconomy", () => ({
      useEconomyMe: () => ({
        data: {
          cash: -1550,
          streak_days: 5,
          level: 3,
          pending_accrual: 0,
          bankruptcy_pending: true,
          xp: 850,
        },
      }),
      useProperties: () => ({ data: { tiers: [], owned: mockOwned } }),
      useLiquidate: () => ({ mutate: mutateSpy }),
      useClaimAccrual: () => ({ mutate: () => {}, isPending: false }),
      useAssets: () => ({ data: null }),
      useBuyProperty: () => ({ mutate: () => {} }),
    }))
    render(<ForcedSellModal />)
    // 勾選 mock-2
    fireEvent.click(screen.getByTestId("sell-row-mock-2"))
    // 點擊確認變賣
    const btn = screen.getByRole("button", { name: /確認變賣/ })
    fireEvent.click(btn)
    // 確認 liquidate 被呼叫且包含 "mock-2"
    expect(calls.length).toBeGreaterThan(0)
    expect(calls[0]).toContain("mock-2")
  })
})
