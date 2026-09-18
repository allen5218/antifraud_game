import React, { useState } from "react"

interface LineChatWrapperProps {
  title: string
  subtitle?: string
  avatarUrl?: string
  children: React.ReactNode
  onReportToLineBot?: () => void
}

export function LineChatWrapper({
  title,
  subtitle = "LINE 官方認證對話模組",
  avatarUrl = "https://api.dicebear.com/7.x/bottts/svg?seed=scam_npc",
  children,
  onReportToLineBot,
}: LineChatWrapperProps) {
  const [showCallModal, setShowCallModal] = useState(false)
  const [showStickerPicker, setShowStickerPicker] = useState(false)

  return (
    <div className="flex flex-col h-full bg-[#8CABD9]/20 rounded-2xl overflow-hidden border border-[#06C755]/30 shadow-lg">
      {/* LINE Header */}
      <div className="bg-[#06C755] text-white px-4 py-3 flex items-center justify-between shadow-md">
        <div className="flex items-center gap-3">
          <div className="relative">
            <img
              src={avatarUrl}
              alt={title}
              className="w-10 h-10 rounded-full bg-white/20 p-1 border border-white/40"
            />
            <span className="absolute bottom-0 right-0 w-3 h-3 bg-green-400 border-2 border-white rounded-full"></span>
          </div>
          <div>
            <h3 className="font-bold text-sm tracking-wide flex items-center gap-1">
              {title}
              <span className="text-[10px] bg-white/20 text-white px-1.5 py-0.5 rounded font-mono">
                LINE 擬真
              </span>
            </h3>
            <p className="text-[11px] text-white/80">{subtitle}</p>
          </div>
        </div>

        {/* LINE Action Buttons */}
        <div className="flex items-center gap-2">
          <button
            onClick={() => setShowCallModal(true)}
            className="p-2 rounded-full hover:bg-white/20 transition-colors text-white text-xs flex items-center gap-1 bg-white/10"
            title="模擬 LINE 語音通話"
          >
            📞 <span className="hidden sm:inline">語音</span>
          </button>
          {onReportToLineBot && (
            <button
              onClick={onReportToLineBot}
              className="px-2.5 py-1 text-xs bg-amber-400 text-slate-900 font-bold rounded-lg shadow hover:bg-amber-300 transition-all flex items-center gap-1"
            >
              🛡️ 轉傳 LINE 查證
            </button>
          )}
        </div>
      </div>

      {/* LINE Chat Content Body */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-gradient-to-b from-[#8CABD9]/10 to-[#8CABD9]/30">
        <div className="text-center my-2">
          <span className="text-[10px] bg-slate-800/60 text-slate-200 px-3 py-1 rounded-full backdrop-blur-sm">
            🔒 訊息端對端加密（LINE 詐騙防禦測試中）
          </span>
        </div>
        {children}
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
            <p className="text-sm text-green-400 font-mono">LINE 語音通話擬真中...</p>
            <p className="text-xs text-slate-400 max-w-xs mx-auto">
              ⚠️ 防詐提示：真人電話絕不會要求您操作 ATM 或提領現金交付給第三人。
            </p>
          </div>

          <div className="flex items-center gap-8 mb-12">
            <button
              onClick={() => setShowCallModal(false)}
              className="w-16 h-16 bg-red-600 hover:bg-red-500 rounded-full flex items-center justify-center text-2xl shadow-xl transition-all"
            >
              📵
            </button>
            <button
              onClick={() => {
                alert("已開啟通話防務錄音，系統將自動比對關鍵字！")
                setShowCallModal(false)
              }}
              className="w-16 h-16 bg-[#06C755] hover:bg-green-400 rounded-full flex items-center justify-center text-2xl shadow-xl transition-all"
            >
              📞
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
