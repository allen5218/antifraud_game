import { afterEach, expect, mock, spyOn, test } from "bun:test"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import {
  createMemoryHistory,
  createRootRoute,
  createRouter,
  RouterProvider,
} from "@tanstack/react-router"
import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react"
import type { UserPublic } from "@/client"
import { CancelablePromise } from "@/client/core/CancelablePromise"
import { UsersService } from "@/client/sdk.gen"
import { TeacherStatusCard } from "./TeacherStatusCard"

afterEach(() => {
  cleanup()
  mock.restore()
})

function renderCard(status: string, isGuest = false) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  const user = {
    id: "u1",
    email: "a@example.com",
    teacher_status: status,
    is_guest: isGuest,
  } as UserPublic
  const router = createRouter({
    routeTree: createRootRoute({
      component: () => (
        <QueryClientProvider client={qc}>
          <TeacherStatusCard user={user} />
        </QueryClientProvider>
      ),
    }),
    history: createMemoryHistory({ initialEntries: ["/me"] }),
  })
  render(<RouterProvider router={router} />)
}

test("還不是老師：可以申請，送出學校與科目", async () => {
  const apply = spyOn(UsersService, "applyTeacherMe").mockImplementation(
    () =>
      new CancelablePromise((resolve) =>
        resolve({ teacher_status: "pending" } as UserPublic),
      ),
  )
  renderCard("none")
  fireEvent.click(await screen.findByRole("button", { name: "申請成為老師" }))
  fireEvent.change(screen.getByLabelText("學校"), {
    target: { value: "範例國中" },
  })
  fireEvent.change(screen.getByLabelText("任教科目"), {
    target: { value: "公民" },
  })
  fireEvent.click(screen.getByRole("button", { name: "送出申請" }))
  await waitFor(() => expect(apply).toHaveBeenCalledTimes(1))
  expect(apply.mock.calls[0][0]).toEqual({
    requestBody: { school: "範例國中", subject: "公民" },
  })
})

test("審核中、沒通過、已核准、停權各自的文字", async () => {
  renderCard("pending")
  expect(await screen.findByText("老師身分審核中")).toBeTruthy()
  cleanup()
  renderCard("rejected")
  expect(await screen.findByText(/沒有通過/)).toBeTruthy()
  expect(screen.getByRole("button", { name: "再申請一次" })).toBeTruthy()
  cleanup()
  renderCard("approved")
  const link = await screen.findByRole("link", { name: /班級管理/ })
  expect(link.getAttribute("href")).toBe("/classes")
  cleanup()
  renderCard("suspended")
  expect(await screen.findByText(/老師身分已暫停/)).toBeTruthy()
})

test("免註冊帳號不顯示申請", async () => {
  renderCard("none", true)
  await new Promise((r) => setTimeout(r, 20))
  expect(screen.queryByRole("button", { name: "申請成為老師" })).toBeNull()
})
