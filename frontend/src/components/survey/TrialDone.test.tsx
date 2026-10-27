import { afterEach, expect, test } from "bun:test"
import {
  createMemoryHistory,
  createRootRoute,
  createRouter,
  RouterProvider,
} from "@tanstack/react-router"
import { cleanup, render, screen } from "@testing-library/react"
import type { TrialSurveyPublic } from "@/client"
import { TrialDone } from "./TrialDone"

afterEach(cleanup)

function mount(data: Partial<TrialSurveyPublic>) {
  const full: TrialSurveyPublic = {
    questions: [],
    started: true,
    submitted: true,
    exam_done: true,
    ...data,
  }
  const router = createRouter({
    routeTree: createRootRoute({ component: () => <TrialDone data={full} /> }),
    history: createMemoryHistory({ initialEntries: ["/survey"] }),
  })
  render(<RouterProvider router={router} />)
}

test("可以領：顯示編號與可以領取", async () => {
  mount({ participant_code: "T-0042", payout_eligible: true })
  expect((await screen.findByTestId("participant-code")).textContent).toBe(
    "T-0042",
  )
  expect(screen.getByTestId("payout-status").textContent).toBe("可以領取禮券")
  expect(screen.getByText(/請截圖這個畫面/)).toBeTruthy()
  expect(screen.queryByText(/原因：/)).toBeNull()
})

test("不能領：顯示原因給工作人員看", async () => {
  mount({
    participant_code: "T-0043",
    payout_eligible: false,
    payout_reasons: ["檢測太快", "問卷注意力題答錯"],
  })
  expect((await screen.findByTestId("payout-status")).textContent).toBe(
    "不能領取禮券",
  )
  expect(screen.getByText("原因：檢測太快、問卷注意力題答錯")).toBeTruthy()
})
