import { useQueryClient } from "@tanstack/react-query"
import { createFileRoute, Link, useNavigate } from "@tanstack/react-router"
import { useEffect, useState } from "react"
import { ApiError, InviteService } from "@/client"
import { Button } from "@/components/ui/button"
import { INVITE_SESSION_PREFIX } from "@/lib/inviteSession"

export const Route = createFileRoute("/invite/$token")({
  component: InvitePage,
  head: () => ({ meta: [{ title: "加入試測 - ScamGym 識詐練習場" }] }),
})

// 共用進行中的請求，避免 StrictMode 重掛與重繪建立兩個訪客。
const pending = new Map<string, Promise<Redeemed>>()

// returning：沿用這個瀏覽器先前兌換的帳號（不是新開的）
type Redeemed = { accessToken: string; returning: boolean }

async function redeemOnce(token: string): Promise<Redeemed> {
  const key = `${INVITE_SESSION_PREFIX}${token}`
  const saved = localStorage.getItem(key)
  if (saved) {
    try {
      const session = JSON.parse(saved) as {
        accessToken: string
        expiresAt: number
      }
      if (session.expiresAt > Date.now() && session.accessToken) {
        return { accessToken: session.accessToken, returning: true }
      }
    } catch {
      localStorage.removeItem(key)
    }
  }
  const existing = pending.get(token)
  if (existing) return existing
  const request = InviteService.redeemInvite({ token })
    .then((result) => {
      // 同一瀏覽器重新開邀請網址時沿用帳號，保留先前的作答紀錄。
      localStorage.setItem(
        key,
        JSON.stringify({
          accessToken: result.access_token,
          expiresAt: Date.now() + 30 * 24 * 60 * 60 * 1000,
        }),
      )
      return { accessToken: result.access_token, returning: false }
    })
    .finally(() => pending.delete(token))
  pending.set(token, request)
  return request
}

function InvitePage() {
  const [attempt, setAttempt] = useState(0)
  return (
    <InviteRedeemer
      key={attempt}
      retry={() => setAttempt((value) => value + 1)}
    />
  )
}

function InviteRedeemer({ retry }: { retry: () => void }) {
  const { token } = Route.useParams()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let active = true
    setError(null)
    redeemOnce(token)
      .then(async ({ accessToken, returning }) => {
        if (!active) return
        // 清掉上一個帳號的畫面與前測結果，再切換到訪客。
        await queryClient.cancelQueries()
        if (!active) return
        queryClient.clear()
        sessionStorage.removeItem("pretestResult")
        localStorage.setItem("access_token", accessToken)
        // 新帳號先做前測；隔天再掃同一個 QR code 的人直接回首頁接著玩
        await navigate({ to: returning ? "/" : "/pretest", replace: true })
      })
      .catch((cause: unknown) => {
        if (!active) return
        setError(
          cause instanceof ApiError && cause.status === 404
            ? "這個邀請已停用、過期或不存在，請向邀請你的人索取新的網址。"
            : cause instanceof ApiError && cause.status === 409
              ? "這個邀請的名額已經滿了，請向邀請你的人索取新的網址。"
              : cause instanceof ApiError && cause.status === 429
                ? "目前加入的人較多，請等一分鐘再試。"
                : "目前無法加入試測，請稍後再試。",
        )
      })
    return () => {
      active = false
    }
  }, [token, navigate, queryClient])

  return (
    <main className="mx-auto flex min-h-dvh max-w-md items-center px-4">
      <section className="w-full rounded-2xl border border-border bg-card p-6 text-center">
        <h1 className="text-xl font-bold">加入試測</h1>
        {error ? (
          <>
            <p role="alert" className="my-4 text-scam">
              {error}
            </p>
            <Button onClick={retry}>再試一次</Button>
            <Link
              to="/login"
              className="mt-4 block text-sm text-muted-foreground"
            >
              回到登入頁
            </Link>
          </>
        ) : (
          <output className="mt-4 text-muted-foreground">
            正在為你準備試測帳號…
          </output>
        )}
      </section>
    </main>
  )
}
