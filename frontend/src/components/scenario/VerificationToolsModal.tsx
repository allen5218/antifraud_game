import {
  AlertTriangle,
  CheckCircle2,
  ChevronRight,
  FileSearch,
  MessageSquare,
  ShieldAlert,
  X,
} from "lucide-react"
import { useState } from "react"
import type { ScenarioEvidenceItem, ScenarioToolItem } from "@/client"
import { Button } from "@/components/ui/button"

interface VerificationToolsModalProps {
  open: boolean
  onClose: () => void
  tools: ScenarioToolItem[]
  unlockedEvidence: ScenarioEvidenceItem[]
  onVerify: (toolId: string) => void
  isVerifying: boolean
  onUseEvidenceInChat?: (text: string) => void
}

export function VerificationToolsModal({
  open,
  onClose,
  unlockedEvidence,
  onVerify,
  isVerifying,
  onUseEvidenceInChat,
}: VerificationToolsModalProps) {
  const [selectedRiskWarning, setSelectedRiskWarning] = useState<string | null>(
    null,
  )

  if (!open) return null

  const unlockedToolIds = new Set(
    (unlockedEvidence || [])
      .map((e: any) => (typeof e === "string" ? e : e?.tool_id))
      .filter(Boolean),
  )

  const handleSelectTool = (toolId: string) => {
    setSelectedRiskWarning(null)
    onVerify(toolId)
  }

  const handleDirectComply = () => {
    setSelectedRiskWarning(
      "直接點擊對方提供的未知連結或配合匯款，極易落入釣魚網站盜刷或人頭帳戶洗錢陷阱！建議先透過獨立第三方管道查對身分。",
    )
  }

  const handleConfront = (content: string) => {
    if (onUseEvidenceInChat) {
      // 提取核心問題文字
      let promptText = `我剛才查驗了官方紀錄，${content}，這點請你解釋清楚？`
      if (content.includes("查無")) {
        promptText =
          "我剛才查證主管機關公開名冊，查無你們團隊之特許登記執照與營業字號，這要怎麼解釋？"
      } else if (content.includes("165")) {
        promptText =
          "我剛才致電 165 反詐專線，專線表示這類模式已有大量受害通報，請你說明！"
      } else if (content.includes("釣魚") || content.includes("網址")) {
        promptText =
          "我查了你傳來的連結並非官方伺服器，而是境外註冊的釣魚網頁，為什麼要給我假網址？"
      }
      onUseEvidenceInChat(promptText)
    } else {
      onClose()
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-end justify-center bg-black/70 backdrop-blur-sm p-0 sm:items-center sm:p-4">
      <div className="flex max-h-[85vh] w-full max-w-lg flex-col rounded-t-2xl bg-slate-900 border-[1.5px] border-white/25 p-4 sm:rounded-2xl glow-card overflow-hidden shadow-2xl">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-white/10 pb-3">
          <div>
            <h3 className="flex items-center text-base font-bold text-white">
              <FileSearch className="size-4 text-sky-400 mr-2" />
              <span>查證與應對行動</span>
            </h3>
            <p className="text-xs text-slate-400 mt-0.5">
              面對對方的說法與要求，決定你採取的下一步查核行動
            </p>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="rounded-full p-1 text-slate-400 hover:text-white hover:bg-white/10 transition-colors"
            aria-label="關閉"
          >
            <X className="size-5" />
          </button>
        </div>

        {/* 遊戲模擬查證明確標註 (G4) */}
        <div className="mt-2.5 rounded-xl border border-sky-500/30 bg-sky-950/30 px-3 py-1.5 text-[11px] text-sky-300">
          <span>
            【遊戲模擬查證】本工具為防詐教學模擬查證，非即時串接真實公務機關或金融資料庫。
          </span>
        </div>

        <div className="flex-1 overflow-y-auto py-3 space-y-4">
          {/* Action Decision Prompt */}
          <div className="space-y-2">
            <h4 className="text-xs font-bold text-slate-200">
              你打算怎麼做？（點擊選擇行動方案）
            </h4>

            <div className="grid gap-2">
              {/* Option 1: Official Registry */}
              <button
                type="button"
                disabled={isVerifying}
                onClick={() => handleSelectTool("check_official_registry")}
                className={`w-full flex items-center justify-between p-3 rounded-xl border-[1.5px] text-left transition-all ${
                  unlockedToolIds.has("check_official_registry")
                    ? "border-emerald-500/40 bg-emerald-500/10 text-white"
                    : "border-white/20 bg-slate-800/80 hover:border-white/40 text-slate-200 hover:bg-slate-800"
                }`}
              >
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-1.5 font-bold text-xs">
                    <span>前往金管會、數位部或商業司名冊查證資格</span>
                    {unlockedToolIds.has("check_official_registry") && (
                      <span className="text-[10px] text-emerald-300 font-normal px-1.5 py-0.2 bg-emerald-500/20 rounded">
                        已取得事實
                      </span>
                    )}
                  </div>
                  <p className="text-[11px] text-slate-400 mt-0.5">
                    透過法定主管機關公開查詢系統核實有無特許營業登記與核准字號
                  </p>
                </div>
                <ChevronRight className="size-4 text-slate-400 shrink-0 ml-2" />
              </button>

              {/* Option 2: 165 or official hotline */}
              <button
                type="button"
                disabled={isVerifying}
                onClick={() => handleSelectTool("check_independent_service")}
                className={`w-full flex items-center justify-between p-3 rounded-xl border-[1.5px] text-left transition-all ${
                  unlockedToolIds.has("check_independent_service")
                    ? "border-emerald-500/40 bg-emerald-500/10 text-white"
                    : "border-white/20 bg-slate-800/80 hover:border-white/40 text-slate-200 hover:bg-slate-800"
                }`}
              >
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-1.5 font-bold text-xs">
                    <span>撥打 165 防詐專線或卡片背面官方客服求證</span>
                    {unlockedToolIds.has("check_independent_service") && (
                      <span className="text-[10px] text-emerald-300 font-normal px-1.5 py-0.2 bg-emerald-500/20 rounded">
                        已取得事實
                      </span>
                    )}
                  </div>
                  <p className="text-[11px] text-slate-400 mt-0.5">
                    自行主動撥打官方既有專線諮詢，不使用對方傳來的電話或代碼
                  </p>
                </div>
                <ChevronRight className="size-4 text-slate-400 shrink-0 ml-2" />
              </button>

              {/* Option 3: Personal app records */}
              <button
                type="button"
                disabled={isVerifying}
                onClick={() => handleSelectTool("check_personal_records")}
                className={`w-full flex items-center justify-between p-3 rounded-xl border-[1.5px] text-left transition-all ${
                  unlockedToolIds.has("check_personal_records")
                    ? "border-emerald-500/40 bg-emerald-500/10 text-white"
                    : "border-white/20 bg-slate-800/80 hover:border-white/40 text-slate-200 hover:bg-slate-800"
                }`}
              >
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-1.5 font-bold text-xs">
                    <span>登入自己的網銀帳戶或原官方 App 查看原始紀錄</span>
                    {unlockedToolIds.has("check_personal_records") && (
                      <span className="text-[10px] text-emerald-300 font-normal px-1.5 py-0.2 bg-emerald-500/20 rounded">
                        已取得事實
                      </span>
                    )}
                  </div>
                  <p className="text-[11px] text-slate-400 mt-0.5">
                    核對真實扣款清單、授權紀錄與受款人戶名是否異常
                  </p>
                </div>
                <ChevronRight className="size-4 text-slate-400 shrink-0 ml-2" />
              </button>

              {/* Option 4: Passive Gullible Choice */}
              <button
                type="button"
                onClick={handleDirectComply}
                className="w-full flex items-center justify-between p-3 rounded-xl border-[1.5px] border-rose-500/30 bg-rose-950/20 hover:border-rose-500/50 hover:bg-rose-950/30 text-left transition-all text-slate-200"
              >
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-1.5 font-bold text-xs text-rose-300">
                    <AlertTriangle className="size-3.5 text-rose-400" />
                    <span>相信對方說法，直接點選連結或依照指示匯款</span>
                  </div>
                  <p className="text-[11px] text-slate-400 mt-0.5">
                    未經查驗直接聽信話術，接受對方提供的快速通道或個人戶頭
                  </p>
                </div>
                <ChevronRight className="size-4 text-rose-400 shrink-0 ml-2" />
              </button>
            </div>
          </div>

          {/* High risk warning alert if gullible choice picked */}
          {selectedRiskWarning && (
            <div className="rounded-xl border-[1.5px] border-rose-500/40 bg-rose-950/40 p-3 text-xs leading-relaxed text-rose-200 flex items-start gap-2.5">
              <ShieldAlert className="size-4 text-rose-400 shrink-0 mt-0.5" />
              <div>
                <p className="font-bold text-rose-300">高風險警訊提醒</p>
                <p className="mt-0.5 text-[11px]">{selectedRiskWarning}</p>
              </div>
            </div>
          )}

          {/* Unlocked Facts & Actionable Counter-Attack */}
          {unlockedEvidence && unlockedEvidence.length > 0 && (
            <div className="space-y-2 border-t border-white/10 pt-3">
              <div className="flex items-center justify-between">
                <h4 className="text-xs font-bold text-slate-200 flex items-center gap-1.5">
                  <CheckCircle2 className="size-3.5 text-emerald-400" />
                  <span>已查驗出之客觀事實</span>
                </h4>
              </div>

              <div className="grid gap-2">
                {unlockedEvidence.map((ev: any, idx: number) => {
                  const title = ev?.title || "查驗報告"
                  const content =
                    ev?.content || (typeof ev === "string" ? ev : "")
                  return (
                    <div
                      key={idx}
                      className="rounded-xl border-[1.5px] border-sky-400/30 bg-sky-950/30 p-3 text-xs leading-relaxed space-y-2"
                    >
                      <div className="font-bold text-sky-200">{title}</div>
                      <p className="text-slate-200 text-[11px] bg-slate-900/60 p-2.5 rounded-lg border border-white/10">
                        {content}
                      </p>
                      {onUseEvidenceInChat && (
                        <button
                          type="button"
                          onClick={() => handleConfront(content)}
                          className="w-full flex items-center justify-center gap-1.5 rounded-lg bg-sky-500/20 border border-sky-400/40 py-1.5 text-xs font-bold text-sky-200 hover:bg-sky-500/30 transition-all shadow-sm"
                        >
                          <MessageSquare className="size-3.5" />
                          <span>將此疑點帶回對話反問對方</span>
                        </button>
                      )}
                    </div>
                  )
                })}
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="border-t border-white/10 pt-3">
          <Button
            onClick={onClose}
            className="w-full bg-slate-800 hover:bg-slate-700 text-white font-bold text-xs border border-white/20"
          >
            返回對話
          </Button>
        </div>
      </div>
    </div>
  )
}
