import { ChevronLeft, Phone, PhoneOff } from "lucide-react"
import { useState } from "react"

interface LineChatWrapperProps {
  title: string
  subtitle?: string
  avatarUrl?: string
  children: React.ReactNode
  onBack?: () => void
  headerActions?: React.ReactNode
}

export function LineChatWrapper({
  title,
  subtitle,
  avatarUrl = "https://api.dicebear.com/7.x/bottts/svg?seed=scam_npc",
  children,
  onBack,
  headerActions,
}: LineChatWrapperProps) {
  const [showCallModal, setShowCallModal] = useState(false)

  return (
    <div className="flex flex-col h-full bg-[#121b2b] rounded-2xl overflow-hidden border-[1.5px] border-white/25 glow-card">
      {/* Unified Chat Header */}
      <div className="bg-slate-900 border-b-[1.5px] border-white/15 text-white px-3.5 py-2.5 flex items-center justify-between shadow-md shrink-0 z-20">
        <div className="flex items-center gap-2.5 min-w-0">
          {onBack && (
            <button
              onClick={onBack}
              type="button"
              className="p-1 -ml-1 text-slate-400 hover:text-white rounded-lg transition-colors"
              aria-label="返回上一頁"
            >
              <ChevronLeft className="size-5" />
            </button>
          )}
          <div className="relative shrink-0">
            <img
              src={avatarUrl}
              alt={title}
              className="w-9 h-9 rounded-full bg-slate-800 p-0.5 border border-slate-700 object-cover shadow-sm"
            />
            <span className="absolute bottom-0 right-0 size-2.5 bg-emerald-500 border-2 border-slate-900 rounded-full" />
          </div>
          <div className="min-w-0">
            <h3 className="font-bold text-sm tracking-wide text-white truncate">
              {title}
            </h3>
            {subtitle && (
              <p className="text-[11px] text-slate-400 truncate">{subtitle}</p>
            )}
          </div>
        </div>

        {/* Right Action Buttons */}
        <div className="flex items-center gap-2 shrink-0">
          {headerActions}
          <button
            onClick={() => setShowCallModal(true)}
            className="p-1.5 rounded-full hover:bg-white/20 transition-colors text-white text-xs bg-white/10 shrink-0"
            title="打電話"
          >
            <Phone className="size-3.5" />
          </button>
        </div>
      </div>

      {/* Main chat body with single scrollbar handled by children */}
      <div className="flex-1 flex flex-col min-h-0 bg-[#0d1424] relative">
        <div className="text-center py-1.5 bg-[#0a0f1d]/60 border-b border-white/5 shrink-0">
          <span className="text-[10px] text-slate-400">今天</span>
        </div>
        <div className="flex-1 min-h-0 flex flex-col">{children}</div>
      </div>

      {/* Simulated Line Audio Call Modal */}
      {showCallModal && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-md flex flex-col items-center justify-between p-8 text-white">
          <div className="text-center mt-12 space-y-3">
            <img
              src={avatarUrl}
              alt={title}
              className="w-24 h-24 rounded-full mx-auto border-4 border-[#06C755] animate-pulse"
            />
            <h2 className="text-2xl font-bold">{title}</h2>
            <p className="text-sm text-green-400">撥號中…</p>
          </div>

          <div className="flex items-center gap-8 mb-12">
            <button
              onClick={() => setShowCallModal(false)}
              className="w-16 h-16 bg-red-600 hover:bg-red-500 rounded-full flex items-center justify-center shadow-xl transition-all"
            >
              <PhoneOff className="size-7" />
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
