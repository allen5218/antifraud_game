import { afterEach, expect, mock, spyOn, test } from "bun:test"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { cleanup, render, waitFor } from "@testing-library/react"
import { CancelablePromise } from "@/client/core/CancelablePromise"
import type { HomeSummary } from "@/hooks/useHomeSummary"
import { homeApi } from "@/hooks/useHomeSummary"
import { MascotAvatar } from "./MascotAvatar"

const summary: HomeSummary = {
  room_stage: 0,
  mascot_image_url: "/assets/mascot/cat/base.webp",
  pretest_done: true,
  inbox_pending: 0,
  daily_unlocked: false,
  daily_done: false,
  exam_active_attempt_id: null,
  exam_can_start: false,
  retake: null,
  focus_type: null,
  focus_label: null,
  badges: [],
}

afterEach(() => {
  cleanup()
  mock.restore()
})

test("顯示玩家正在展示的吉祥物，不是寫死的柴犬", async () => {
  spyOn(homeApi, "summary").mockImplementation(
    () => new CancelablePromise((resolve) => resolve(summary)),
  )
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  const { container } = render(
    <QueryClientProvider client={qc}>
      <MascotAvatar className="size-16" />
    </QueryClientProvider>,
  )
  await waitFor(() =>
    expect(container.querySelector("img")?.getAttribute("src")).toBe(
      "/assets/mascot/cat/base.webp",
    ),
  )
})
