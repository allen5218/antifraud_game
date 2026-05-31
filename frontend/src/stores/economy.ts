import { create } from "zustand"

export interface PropertyTier {
  id: number
  name: string
  svgKey: string
  price: number
  dailyIncome: number
  unlockLevel: number
}

export interface OwnedProperty {
  id: string
  tier: PropertyTier
  purchasedAt: string
}

export const MOCK_TIERS: PropertyTier[] = [
  {
    id: 1,
    name: "雅房",
    svgKey: "tier-1",
    price: 1000,
    dailyIncome: 5,
    unlockLevel: 1,
  },
  {
    id: 2,
    name: "套房",
    svgKey: "tier-2",
    price: 5000,
    dailyIncome: 35,
    unlockLevel: 1,
  },
  {
    id: 3,
    name: "兩房公寓",
    svgKey: "tier-3",
    price: 25000,
    dailyIncome: 250,
    unlockLevel: 2,
  },
  {
    id: 4,
    name: "三房公寓",
    svgKey: "tier-4",
    price: 100000,
    dailyIncome: 1200,
    unlockLevel: 3,
  },
  {
    id: 5,
    name: "別墅",
    svgKey: "tier-5",
    price: 300000,
    dailyIncome: 4200,
    unlockLevel: 5,
  },
  {
    id: 6,
    name: "豪宅",
    svgKey: "tier-6",
    price: 1000000,
    dailyIncome: 15000,
    unlockLevel: 10,
  },
]

export const LIQUIDATION_RATIO = 0.6

interface EconomyState {
  cash: number
  streak: number
  level: number
  xp: number
  pendingAccrual: number
  bankruptcyPending: boolean
  ownedProperties: OwnedProperty[]
  claimAccrual: () => void
  triggerBankruptcy: (amount: number) => void
  liquidateProperties: (ids: string[]) => void
  reset: () => void
}

const DEFAULT_OWNED: OwnedProperty[] = [
  { id: "mock-1", tier: MOCK_TIERS[0], purchasedAt: "2026-05-20" },
  { id: "mock-2", tier: MOCK_TIERS[1], purchasedAt: "2026-05-25" },
]

const defaultState = {
  cash: 12450,
  streak: 5,
  level: 3,
  xp: 850,
  pendingAccrual: 840,
  bankruptcyPending: false,
  ownedProperties: DEFAULT_OWNED,
}

export const useEconomyStore = create<EconomyState>((set, get) => ({
  ...defaultState,
  claimAccrual: () =>
    set((s) => ({ cash: s.cash + s.pendingAccrual, pendingAccrual: 0 })),
  triggerBankruptcy: (amount) =>
    set((s) => {
      const newCash = s.cash - amount
      return { cash: newCash, bankruptcyPending: newCash < 0 }
    }),
  liquidateProperties: (ids) => {
    const s = get()
    const sold = s.ownedProperties.filter((p) => ids.includes(p.id))
    const recovered = sold.reduce(
      (sum, p) => sum + Math.floor(p.tier.price * LIQUIDATION_RATIO),
      0,
    )
    const remaining = s.ownedProperties.filter((p) => !ids.includes(p.id))
    const newCash = s.cash + recovered
    set({
      ownedProperties: remaining,
      cash: newCash,
      bankruptcyPending: newCash < 0,
    })
  },
  reset: () =>
    set({
      ...defaultState,
      ownedProperties: DEFAULT_OWNED.map((p) => ({ ...p })),
    }),
}))
