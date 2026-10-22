import { useQueryClient } from "@tanstack/react-query"
import { createFileRoute, Link, useNavigate } from "@tanstack/react-router"
import { useEffect, useState } from "react"
import { ApiError, LoginService } from "@/client"
import { OAUTH_ERRORS, type OAuthProvider, takePending } from "@/lib/oauth"

type Search = { code?: string; state?: string; error?: string }

export const Route = createFileRoute("/oauth/$provider/callback")({
  component: OAuthCallbackPage,
  validateSearch: (search: Record<string, unknown>): Search => ({
    code: typeof search.code === "string" ? search.code : undefined,
    state: typeof search.state === "string" ? search.state : undefined,
    error: typeof search.error === "string" ? search.error : undefined,
  }),
  head: () => ({ meta: [{ title: "登入中 - ScamGym 識詐練習場" }] }),
})

// 同一個授權碼只送一次(StrictMode 會掛載兩次)
const inflight = new Map<string, Promise<string>>()

function exchange(provider: OAuthProvider, search: Search): Promise<string> {
  const code = search.code ?? ""
  const existing = inflight.get(code)
  if (existing) return existing
  const pending = takePending()
  // 不是從這個分頁出發、或 state 對不上:可能是別人塞來的授權碼
  if (
    !search.code ||
    !pending ||
    pending.provider !== provider ||
    pending.state !== search.state
  ) {
    return Promise.reject(new Error("oauth_state_invalid"))
  }
  const request = LoginService.callback({
    provider,
    requestBody: {
      code: search.code,
      state: pending.state,
      code_verifier: pending.verifier,
    },
  }).then((token) => token.access_token)
  inflight.set(code, request)
  return request
}

function errorCode(cause: unknown): string {
  if (cause instanceof ApiError) {
    const detail = (cause.body as { detail?: unknown })?.detail
    if (detail && typeof detail === "object" && "code" in detail) {
      return String((detail as { code: unknown }).code)
    }
    if (detail === "Inactive user") return "inactive"
    return "oauth_failed"
  }
  return cause instanceof Error ? cause.message : "oauth_failed"
}

function OAuthCallbackPage() {
  const { provider } = Route.useParams()
  const search = Route.useSearch()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let active = true
    if (search.error) {
      // 使用者在 Google／LINE 那邊按了取消
      takePending()
      setError("你取消了登入。")
      return
    }
    if (provider !== "google" && provider !== "line") {
      setError(OAUTH_ERRORS.oauth_disabled)
      return
    }
    exchange(provider, search)
      .then(async (accessToken) => {
        if (!active) return
        // 清掉上一個帳號的資料再換人
        await queryClient.cancelQueries()
        queryClient.clear()
        localStorage.setItem("access_token", accessToken)
        await navigate({ to: "/", replace: true })
      })
      .catch((cause: unknown) => {
        if (!active) return
        const code = errorCode(cause)
        setError(
          code === "inactive"
            ? "這個帳號已停用。"
            : (OAUTH_ERRORS[code] ?? OAUTH_ERRORS.oauth_failed),
        )
      })
    return () => {
      active = false
    }
  }, [provider, search, navigate, queryClient])

  return (
    <main className="mx-auto flex min-h-dvh max-w-md items-center px-4">
      <section className="w-full rounded-2xl border border-border bg-card p-6 text-center">
        <h1 className="text-xl font-bold">登入</h1>
        {error ? (
          <>
            <p role="alert" className="my-4 text-scam">
              {error}
            </p>
            <Link to="/login" className="text-sm underline underline-offset-4">
              回到登入頁
            </Link>
          </>
        ) : (
          <output className="mt-4 block text-muted-foreground">登入中…</output>
        )}
      </section>
    </main>
  )
}
