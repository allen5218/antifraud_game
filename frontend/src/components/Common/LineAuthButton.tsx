import { Shield, Sparkles, X } from "lucide-react"
import { useState } from "react"

interface LineAuthButtonProps {
  mode?: "login" | "signup"
  onSuccess?: () => void
}

export function LineAuthButton({
  mode = "login",
  onSuccess,
}: LineAuthButtonProps) {
  const [isOpen, setIsOpen] = useState(false)
  const [lineUserId, setLineUserId] = useState("")
  const [displayName, setDisplayName] = useState("")
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState("")

  const handleQuickLogin = async (customId?: string, customName?: string) => {
    setLoading(true)
    setError("")
    const uid =
      customId ||
      lineUserId.trim() ||
      `line_user_${Math.floor(100000 + Math.random() * 900000)}`
    const name = customName || displayName.trim() || "LINE 防詐探員"

    try {
      const res = await fetch("/api/v1/auth/line/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          line_user_id: uid,
          display_name: name,
        }),
      })

      if (!res.ok) {
        const err = await res.json().catch(() => ({}))
        throw new Error(err.detail || "LINE 登入授權失敗")
      }

      const data = await res.json()
      localStorage.setItem("access_token", data.access_token)
      if (onSuccess) {
        onSuccess()
      } else {
        window.location.href = "/"
      }
    } catch (e: unknown) {
      const errMsg = e instanceof Error ? e.message : "連線發生錯誤"
      setError(errMsg)
    } finally {
      setLoading(false)
    }
  }

  return (
    <>
      <button
        type="button"
        onClick={() => setIsOpen(true)}
        className="w-full py-2.5 px-4 bg-[#06C755] hover:bg-[#05B34C] active:scale-[0.99] text-white font-bold rounded-xl shadow-lg shadow-[#06C755]/20 transition-all flex items-center justify-center gap-2.5 text-xs cursor-pointer"
      >
        <svg className="w-4 h-4 fill-current" viewBox="0 0 24 24">
          <path d="M12 2C6.48 2 2 5.92 2 10.75c0 3.12 1.89 5.89 4.75 7.37-.21.75-.85 2.72-.98 3.14-.15.52.19.51.4.38.16-.1 2.22-1.51 3.13-2.13.88.16 1.78.25 2.7.25 5.52 0 10-3.92 10-8.75S17.52 2 12 2z" />
        </svg>
        {mode === "signup" ? "使用 LINE 帳號一鍵註冊" : "以 LINE 帳號快速登入"}
      </button>

      {isOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4 animate-in fade-in duration-200">
          <div className="bg-slate-900 border border-slate-800 w-full max-w-sm rounded-2xl p-6 shadow-2xl relative text-white">
            <button
              type="button"
              onClick={() => setIsOpen(false)}
              className="absolute top-4 right-4 text-slate-400 hover:text-white p-1 rounded-lg hover:bg-slate-800 transition"
            >
              <X className="w-4 h-4" />
            </button>

            <div className="flex items-center gap-3 mb-4">
              <div className="w-10 h-10 rounded-xl bg-[#06C755] flex items-center justify-center shadow-md shadow-[#06C755]/30">
                <svg className="w-5 h-5 fill-white" viewBox="0 0 24 24">
                  <path d="M12 2C6.48 2 2 5.92 2 10.75c0 3.12 1.89 5.89 4.75 7.37-.21.75-.85 2.72-.98 3.14-.15.52.19.51.4.38.16-.1 2.22-1.51 3.13-2.13.88.16 1.78.25 2.7.25 5.52 0 10-3.92 10-8.75S17.52 2 12 2z" />
                </svg>
              </div>
              <div>
                <h3 className="text-base font-bold">LINE 探員身分核驗</h3>
                <p className="text-[11px] text-slate-400">
                  雙向連動官方帳號與 Web 防詐總部
                </p>
              </div>
            </div>

            {error && (
              <div className="mb-4 p-2.5 bg-rose-500/10 border border-rose-500/30 rounded-xl text-xs text-rose-300">
                {error}
              </div>
            )}

            <div className="space-y-3">
              <div>
                <label className="text-xs font-medium text-slate-300 block mb-1">
                  探員暱稱（選填）
                </label>
                <input
                  type="text"
                  value={displayName}
                  onChange={(e) => setDisplayName(e.target.value)}
                  placeholder="例：台北防詐先鋒"
                  className="w-full px-3 py-2 bg-slate-950/80 border border-slate-700/80 rounded-xl text-xs text-white placeholder:text-slate-500 focus:outline-none focus:border-[#06C755]"
                />
              </div>

              <div>
                <label className="text-xs font-medium text-slate-300 block mb-1">
                  LINE 帳號標識 / 手機代號（選填）
                </label>
                <input
                  type="text"
                  value={lineUserId}
                  onChange={(e) => setLineUserId(e.target.value)}
                  placeholder="留空則自動配發專屬探員碼"
                  className="w-full px-3 py-2 bg-slate-950/80 border border-slate-700/80 rounded-xl text-xs text-white placeholder:text-slate-500 focus:outline-none focus:border-[#06C755]"
                />
              </div>

              <button
                type="button"
                disabled={loading}
                onClick={() => handleQuickLogin()}
                className="w-full mt-2 py-2.5 bg-[#06C755] hover:bg-[#05B34C] text-white font-bold rounded-xl text-xs flex items-center justify-center gap-2 cursor-pointer shadow-md shadow-[#06C755]/20 disabled:opacity-50"
              >
                <Sparkles className="w-3.5 h-3.5" />
                {loading ? "核驗中..." : "一鍵以 LINE 身分快速開戶 / 登入"}
              </button>
            </div>

            <div className="mt-4 pt-4 border-t border-slate-800 text-[11px] text-slate-400 space-y-2">
              <div className="flex items-center gap-2 text-slate-300 font-semibold">
                <Shield className="w-3.5 h-3.5 text-emerald-400" />
                <span>手機已加 LINE 官方好友？</span>
              </div>
              <p className="text-slate-400 leading-relaxed">
                在 LINE 聊天室輸入「
                <span className="text-white font-bold">註冊</span>」或「
                <span className="text-white font-bold">探員卡</span>
                」，機器人將直接派發數位證件，點擊即可免密碼直通總部！
              </p>
            </div>
          </div>
        </div>
      )}
    </>
  )
}
