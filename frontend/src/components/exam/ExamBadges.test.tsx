import { afterEach, beforeEach, expect, mock, spyOn, test } from "bun:test"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react"
import type { ExamBadgePublic } from "@/client"
import { CancelablePromise } from "@/client/core/CancelablePromise"
import { BadgesService } from "@/client/sdk.gen"
import { ExamBadges } from "./ExamBadges"
import { PublicBadge } from "./PublicBadge"

const response = <T,>(value: T) =>
  new CancelablePromise<T>((resolve) => resolve(value))
const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
const badge: ExamBadgePublic = {
  id: "b",
  kind: "comprehensive",
  fraud_type: null,
  tested_type: "romance",
  name: "綜合檢測徽章",
  first_passed_at: "2026-10-09T00:00:00Z",
  last_passed_at: "2026-10-09T00:00:00Z",
  last_score: 90,
  suggested_retest_at: "2027-01-07",
  is_public: false,
  public_slug: null,
}
let currentBadges = [badge]
beforeEach(() => {
  currentBadges = [badge]
  spyOn(BadgesService, "ownBadges").mockImplementation(() =>
    response(currentBadges),
  )
})
afterEach(() => {
  cleanup()
  qc.clear()
  mock.restore()
})
const mount = (ui: React.ReactNode) =>
  render(<QueryClientProvider client={qc}>{ui}</QueryClientProvider>)
test("開啟公開才顯示查驗連結及 QR，關閉收起連結", async () => {
  const toggle = spyOn(BadgesService, "updateBadge").mockImplementation(
    ({ requestBody }) => {
      const updated = {
        ...badge,
        is_public: requestBody.is_public,
        public_slug: "slug",
      }
      currentBadges = [updated]
      return response(updated)
    },
  )
  mount(<ExamBadges badges={[badge]} />)
  expect(screen.queryByRole("link")).toBeNull()
  fireEvent.click(await screen.findByRole("checkbox", { name: "公開這枚徽章" }))
  const link = await screen.findByRole("link")
  expect(link.getAttribute("href")).toBe(`${window.location.origin}/badge/slug`)
  expect(screen.getByTitle("綜合檢測徽章查驗連結")).toBeTruthy()
  expect(toggle.mock.calls[0][0]).toEqual({
    badgeId: "b",
    requestBody: { is_public: true },
  })
  fireEvent.click(screen.getByRole("checkbox", { name: "公開這枚徽章" }))
  await waitFor(() => expect(screen.queryByRole("link")).toBeNull())
})
test("公開查驗只顯示允許欄位與複測提示，不顯示分數或私有類型", async () => {
  const read = spyOn(BadgesService, "publicBadge").mockImplementation(() =>
    response({
      nickname: "玩家 #1234",
      badge_name: "綜合檢測徽章",
      criteria: "完成檢測，總分達七十分。",
      last_passed_day: "2026-10-09",
      suggested_retest_day: "2027-01-07",
      status: "retest_recommended",
    }),
  )
  mount(<PublicBadge slug="slug" />)
  await screen.findByText("玩家 #1234")
  expect(read.mock.calls[0][0]).toEqual({ slug: "slug" })
  expect(screen.getByText("建議再次檢測，徽章仍有效")).toBeTruthy()
  expect(screen.queryByText("假交友")).toBeNull()
  expect(screen.queryByText(/90 分/)).toBeNull()
})
test("公開頁 404 顯示徽章未公開或連結無效", async () => {
  spyOn(BadgesService, "publicBadge").mockImplementation(
    () => new CancelablePromise((_resolve, reject) => reject({ status: 404 })),
  )
  mount(<PublicBadge slug="closed" />)
  expect((await screen.findByRole("alert")).textContent).toContain("沒有公開")
})

test("歷史結果的徽章快照仍使用目前公開設定，可直接關閉", async () => {
  let live = { ...badge, is_public: true, public_slug: "live-slug" }
  spyOn(BadgesService, "ownBadges").mockImplementation(() => response([live]))
  const toggle = spyOn(BadgesService, "updateBadge").mockImplementation(
    ({ requestBody }) => {
      live = { ...live, is_public: requestBody.is_public }
      return response(live)
    },
  )
  mount(<ExamBadges badges={[badge]} />)
  await waitFor(() =>
    expect(
      (
        screen.getByRole("checkbox", {
          name: "公開這枚徽章",
        }) as HTMLInputElement
      ).checked,
    ).toBe(true),
  )
  fireEvent.click(screen.getByRole("checkbox", { name: "公開這枚徽章" }))
  await waitFor(() => expect(toggle).toHaveBeenCalledTimes(1))
  expect(toggle.mock.calls[0][0]).toEqual({
    badgeId: "b",
    requestBody: { is_public: false },
  })
  await waitFor(() => expect(screen.queryByRole("link")).toBeNull())
})
