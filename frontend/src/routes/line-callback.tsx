import { createFileRoute, useNavigate } from "@tanstack/react-router"
import { AlertCircle, Loader2, ShieldCheck } from "lucide-react"
import { useEffect, useState } from "react"

export const Route = createFileRoute("/line-callback")({
  component: LineCallback,
})

function LineCallback() {
  const navigate = useNavigate()
  const [status, setStatus] = useState<"loading" | "success" | "error">(
    "loading",
  )
  const [message, setMessage] = useState("正在透過 LINE 官方授權連線中...")
  const [userData, setUserData] = useState<{
    display_name: string
    cash: number
  } | null>(null)

  useEffect(() => {
    const params = new URLSearchParams(window.location.search)
    const token = params.get("token")

    if (!token) {
      setStatus("error")
      setMessage("缺少 LINE 單次安全驗證碼，請由 LINE 官方帳號對話中重新點擊。")
      return
    }

    const exchangeToken = async () => {
      try {
        const res = await fetch("/api/v1/auth/line/exchange-magic-token", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ token }),
        })

        if (!res.ok) {
          const err = await res.json().catch(() => ({}))
          throw new Error(err.detail || "驗證碼無效或已過期")
        }

        const data = await res.json()
        localStorage.setItem("access_token", data.access_token)
        setUserData(data)
        setStatus("success")
        setMessage(`歡迎回來，${data.display_name}！已完成 LINE 探員身分核銷。`)

        setTimeout(() => {
          window.location.href = "/"
        }, 1200)
      } catch (e: unknown) {
        const errMessage =
          e instanceof Error ? e.message : "登入驗證失敗，請稍後重試"
        setStatus("error")
        setMessage(errMessage)
      }
    }

    exchangeToken()
  }, [])

  return (
    <div className="min-h-screen bg-slate-950 flex items-center justify-center p-4 text-white">
      <div className="max-w-md w-full bg-slate-900/90 border border-slate-800 rounded-2xl p-6 shadow-2xl text-center">
        {status === "loading" && (
          <div className="flex flex-col items-center gap-4 py-8">
            <Loader2 className="w-12 h-12 text-[#06C755] animate-spin" />
            <h2 className="text-lg font-bold">驗證 LINE 探員身分中</h2>
            <p className="text-xs text-slate-400">{message}</p>
          </div>
        )}

        {status === "success" && (
          <div className="flex flex-col items-center gap-4 py-8">
            <div className="w-16 h-16 rounded-full bg-[#06C755]/20 flex items-center justify-center border border-[#06C755]/50">
              <ShieldCheck className="w-10 h-10 text-[#06C755]" />
            </div>
            <h2 className="text-xl font-bold text-white">探員身分核驗成功</h2>
            <p className="text-sm text-slate-300">{message}</p>
            {userData && (
              <div className="w-full bg-slate-950/80 rounded-xl p-3 border border-slate-800 text-left text-xs space-y-1.5 mt-2">
                <div className="flex justify-between">
                  <span className="text-slate-400">探員姓名</span>
                  <span className="font-semibold text-white">
                    {userData.display_name}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">帳戶資金</span>
                  <span className="font-semibold text-emerald-400">
                    NT$ {userData.cash?.toLocaleString()}
                  </span>
                </div>
              </div>
            )}
            <p className="text-xs text-slate-500 mt-2">
              正在為您開啟總部指揮中心...
            </p>
          </div>
        )}

        {status === "error" && (
          <div className="flex flex-col items-center gap-4 py-8">
            <div className="w-16 h-16 rounded-full bg-rose-500/20 flex items-center justify-center border border-rose-500/50">
              <AlertCircle className="w-10 h-10 text-rose-500" />
            </div>
            <h2 className="text-lg font-bold text-white">身分驗證中斷</h2>
            <p className="text-xs text-rose-300">{message}</p>
            <button
              type="button"
              onClick={() => navigate({ to: "/login" })}
              className="mt-4 px-6 py-2 bg-slate-800 hover:bg-slate-700 text-white rounded-xl text-xs font-semibold transition cursor-pointer"
            >
              返回登入頁
            </button>
          </div>
        )}
      </div>
    </div>
  )
}
