import { Link } from "@tanstack/react-router"
import { Button } from "@/components/ui/button"

interface ErrorComponentProps {
  error?: Error | unknown
}

const ErrorComponent = ({ error }: ErrorComponentProps) => {
  const errorMessage = error instanceof Error ? error.message : String(error ?? "未知錯誤")
  const errorStack = error instanceof Error ? error.stack : undefined

  return (
    <div
      className="flex min-h-screen items-center justify-center flex-col p-6 bg-slate-950 text-white font-mono"
      data-testid="error-component"
    >
      <div className="flex flex-col items-center justify-center p-4 text-center max-w-2xl w-full">
        <span className="text-5xl font-extrabold text-red-500 mb-2">
          ⚠️ 系統捕獲倒錯 (Runtime Error)
        </span>
        <p className="text-sm text-slate-400 mb-4">
          已成功攔截前端運行錯誤，以下為詳細堆疊追蹤資訊：
        </p>

        {/* 核心錯誤訊息 */}
        <div className="w-full bg-red-950/60 border border-red-500/50 p-4 rounded-xl text-left mb-4 shadow-xl">
          <p className="text-xs font-bold text-red-400 mb-1">📌 Error Message:</p>
          <pre className="text-sm text-red-200 font-bold whitespace-pre-wrap break-all">
            {errorMessage}
          </pre>
        </div>

        {/* 堆疊追蹤 Stack Trace */}
        {errorStack && (
          <div className="w-full bg-slate-900 border border-slate-800 p-3 rounded-xl text-left mb-6 max-h-60 overflow-y-auto">
            <p className="text-[11px] font-bold text-slate-400 mb-1">📜 Stack Trace:</p>
            <pre className="text-[11px] text-slate-300 font-mono whitespace-pre-wrap leading-relaxed">
              {errorStack}
            </pre>
          </div>
        )}

        <div className="flex items-center gap-3">
          <Link to="/">
            <Button variant="default">Go Home</Button>
          </Link>
          <button
            onClick={() => {
              localStorage.clear()
              window.location.href = "/login"
            }}
            className="px-4 py-2 bg-red-600 hover:bg-red-500 text-white font-bold text-xs rounded-lg shadow"
          >
            🧹 清除所有登入快取並返回登入頁
          </button>
        </div>
      </div>
    </div>
  )
}

export default ErrorComponent
