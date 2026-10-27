import { useMutation, useQueryClient } from "@tanstack/react-query"
import { createFileRoute, Link, useNavigate } from "@tanstack/react-router"
import { useEffect, useState } from "react"
import { redeemClassOnce } from "@/components/classroom/classRedeem"
import { classApi } from "@/components/classroom/classroomApi"
import { Button } from "@/components/ui/button"
import { isLoggedIn } from "@/hooks/useAuth"

export const Route = createFileRoute("/class/$token")({
  component: ClassJoinPage,
  head: () => ({ meta: [{ title: "加入班級 - ScamGym 識詐練習場" }] }),
})

const FAILED = "找不到這個班級，或老師已經停止加入。請向老師確認。"

function Card({ children }: { children: React.ReactNode }) {
  return (
    <main className="mx-auto flex min-h-dvh max-w-md items-center px-4">
      <section className="flex w-full flex-col gap-4 rounded-2xl border border-border bg-card p-6 text-center">
        <h1 className="text-xl font-bold">加入班級</h1>
        {children}
      </section>
    </main>
  )
}

/** 掃老師給的 QR：已登入就問要不要用目前的帳號加入；沒登入就開免註冊帳號 */
function ClassJoinPage() {
  const { token } = Route.useParams()
  const [attempt, setAttempt] = useState(0)
  return isLoggedIn() ? (
    <JoinWithAccount token={token} />
  ) : (
    <JoinAsGuest
      key={attempt}
      token={token}
      retry={() => setAttempt((value) => value + 1)}
    />
  )
}

function JoinWithAccount({ token }: { token: string }) {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const join = useMutation({
    mutationFn: () => classApi.join({ token }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["classes"] })
      queryClient.invalidateQueries({ queryKey: ["home-summary"] })
      navigate({ to: "/classwork", replace: true })
    },
  })
  return (
    <Card>
      <p>
        要用目前的帳號加入這個班級嗎？加入後填學號和名字，就看得到老師出的作業。
      </p>
      {join.isError && (
        <p role="alert" className="text-scam">
          {FAILED}
        </p>
      )}
      <Button disabled={join.isPending} onClick={() => join.mutate()}>
        加入
      </Button>
      <Link to="/" className="text-sm text-muted-foreground">
        先不要，回房間
      </Link>
    </Card>
  )
}

function JoinAsGuest({ token, retry }: { token: string; retry: () => void }) {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [error, setError] = useState<string | null>(null)
  useEffect(() => {
    let active = true
    setError(null)
    redeemClassOnce(token)
      .then(async (accessToken) => {
        if (!active) return
        await queryClient.cancelQueries()
        if (!active) return
        queryClient.clear()
        localStorage.setItem("access_token", accessToken)
        await navigate({ to: "/classwork", replace: true })
      })
      .catch((cause: unknown) => {
        if (!active) return
        const status = (cause as { status?: number })?.status
        setError(
          status === 429
            ? "目前加入的人較多，請等一分鐘再試。"
            : status === 404
              ? FAILED
              : "目前無法加入，請稍後再試。",
        )
      })
    return () => {
      active = false
    }
  }, [token, navigate, queryClient])
  return (
    <Card>
      {error ? (
        <>
          <p role="alert" className="text-scam">
            {error}
          </p>
          <Button onClick={retry}>再試一次</Button>
        </>
      ) : (
        <output className="text-muted-foreground">正在幫你加入班級…</output>
      )}
      <Link to="/login" className="text-sm text-muted-foreground">
        已經有帳號？先登入再掃一次
      </Link>
    </Card>
  )
}
