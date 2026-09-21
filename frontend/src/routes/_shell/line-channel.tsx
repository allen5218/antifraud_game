import { createFileRoute } from "@tanstack/react-router"
import {
  CheckCircle2,
  Copy,
  Lock,
  QrCode,
  RotateCcw,
  Send,
  ShieldAlert,
  ShieldCheck,
  Smartphone,
} from "lucide-react"
import { useEffect, useRef, useState } from "react"

export const Route = createFileRoute("/_shell/line-channel")({
  component: LineChannelPage,
})

interface SimMessage {
  id: string
  sender: "user" | "bot"
  type: "text" | "flex"
  text?: string
  flex?: any
  quickReplies?: Array<{ label: string; text: string }>
}

function LineChannelPage() {
  const [activeTab, setActiveTab] = useState<"simulator" | "integration">(
    "simulator",
  )
  const [messages, setMessages] = useState<SimMessage[]>([])
  const [inputText, setInputText] = useState("")
  const [isSending, setIsSending] = useState(false)
  const [quickReplies, setQuickReplies] = useState<
    Array<{ label: string; text: string }>
  >([
    { label: "挑戰投資顧問案", text: "開始情境 invest" },
    { label: "挑戰假檢警案", text: "開始情境 authority" },
    { label: "挑戰假網拍案", text: "開始情境 shopping" },
  ])
  const [copied, setCopied] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }

  useEffect(() => {
    scrollToBottom()
  }, [scrollToBottom])

  const sendMessage = async (textToSend: string, isSilent = false) => {
    const text = textToSend.trim()
    if (!text) return

    if (!isSilent) {
      const userMsg: SimMessage = {
        id: `user-${Date.now()}`,
        sender: "user",
        type: "text",
        text,
      }
      setMessages((prev) => [...prev, userMsg])
      setInputText("")
    }

    setIsSending(true)
    try {
      const res = await fetch("/api/v1/line/simulate-message", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          user_id: "line_web_demo_user",
          text,
        }),
      })

      let rawMessages: any[] = []
      if (res?.ok) {
        const data = await res.json()
        rawMessages = data.messages || []
      } else {
        // Resilient fallback for pure client-side demonstration
        if (
          text.includes("選案") ||
          (text.includes("開始") && !text.includes("情境"))
        ) {
          rawMessages = [
            {
              type: "text",
              text: "【反詐大師 · 官方實境對話】\n歡迎進入真實通訊防詐攻防。請點選下方快捷鍵選擇欲挑戰的詐騙情境：",
              quickReply: {
                items: [
                  {
                    action: {
                      label: "挑戰投資顧問案",
                      text: "開始情境 invest",
                    },
                  },
                  {
                    action: {
                      label: "挑戰假檢警案",
                      text: "開始情境 authority",
                    },
                  },
                  {
                    action: {
                      label: "挑戰假網拍案",
                      text: "開始情境 shopping",
                    },
                  },
                ],
              },
            },
          ]
        } else if (text.includes("情境") || text.includes("invest")) {
          rawMessages = [
            {
              type: "text",
              text: "【防詐情境開啟 · 金牌投資顧問 - 陳經理】\n情境類型：INVEST · 倒數 10 回合\n---------------------------\n金牌投資顧問 - 陳經理：您好！看到您對理財有興趣，我們團隊有獨家的飆股分析軟體，每日提供保證獲利名單。",
              quickReply: {
                items: [
                  { action: { label: "檢舉詐騙", text: "檢舉" } },
                  { action: { label: "165 查證", text: "查證" } },
                  { action: { label: "安全退出", text: "退出" } },
                ],
              },
            },
          ]
        } else if (text.includes("查證")) {
          rawMessages = [
            {
              type: "text",
              text: "【165 防詐資料庫反查報告】\n查詢項目：金管會合法投顧名冊\n查核事實：查無該機構之特許登記執照與核准營業字號。\n指標意義：凡宣稱保證高獲利或獨家內線者，100% 為非法吸金與詐欺手法。",
              quickReply: {
                items: [
                  { action: { label: "確認檢舉", text: "檢舉" } },
                  {
                    action: {
                      label: "繼續對話",
                      text: "請問能出示官方合法證明嗎？",
                    },
                  },
                  { action: { label: "安全退出", text: "退出" } },
                ],
              },
            },
          ]
        } else if (
          text.includes("檢舉") ||
          text.includes("詐騙") ||
          text.includes("退出")
        ) {
          rawMessages = [
            {
              type: "flex",
              altText: "【防詐診斷書】識破成功！防詐免疫力提升",
              contents: {
                header: {
                  backgroundColor: "#059669",
                  contents: [{ text: "識破成功！防詐免疫力提升" }],
                },
                body: {
                  contents: [
                    {
                      type: "text",
                      text: "對象真實身份：詐騙集團成員 (金牌投資顧問 - 陳經理)",
                      color: "#111827",
                      weight: "bold",
                    },
                    {
                      type: "text",
                      text: "資產獎勵：+$500 · +120 XP",
                      color: "#059669",
                      weight: "bold",
                    },
                    {
                      type: "text",
                      text: "【對話偵查線索與紅旗】",
                      color: "#1F2937",
                      weight: "bold",
                    },
                    {
                      type: "text",
                      text: "[權威服從] 宣稱海外私募專家與內部軟體",
                      color: "#B45309",
                    },
                    {
                      type: "text",
                      text: "[時間壓力] 宣稱名額只剩 2 位，要求立即匯款",
                      color: "#B45309",
                    },
                    {
                      type: "text",
                      text: "【心理說服槓桿與認知煞車解密】",
                      color: "#B45309",
                      weight: "bold",
                    },
                    {
                      type: "text",
                      text: "本案透過海外背景建立虛假權威，並以即將截止的時間壓力劫持思考。關鍵防禦思維：在通訊軟體遇到要求匯款至非公司戶頭，一律親撥 165 反詐查證。",
                      color: "#4B5563",
                    },
                  ],
                },
              },
              quickReply: {
                items: [{ action: { label: "挑戰下一案", text: "選案" } }],
              },
            },
          ]
        } else {
          rawMessages = [
            {
              type: "text",
              text: "金牌投資顧問 - 陳經理 (剩 8 回合)：\n我們是海外私募團隊，不需要台灣執照！名額只剩最後 2 位，請盡快匯款至指定特別戶頭。\n\n【對方要求】要立即匯款 NT$50,000 加入投資專案嗎？",
              quickReply: {
                items: [
                  { action: { label: "檢舉詐騙", text: "檢舉" } },
                  { action: { label: "165 查證", text: "查證" } },
                  { action: { label: "安全退出", text: "退出" } },
                ],
              },
            },
          ]
        }
      }

      const botMessages: SimMessage[] = rawMessages.map(
        (m: any, idx: number) => {
          const qrList: Array<{ label: string; text: string }> = []
          if (m.quickReply?.items) {
            for (const item of m.quickReply.items) {
              if (item.action) {
                qrList.push({
                  label: item.action.label || item.action.text,
                  text: item.action.text,
                })
              }
            }
          }

          if (qrList.length > 0) {
            setQuickReplies(qrList)
          }

          if (m.type === "flex") {
            return {
              id: `bot-${Date.now()}-${idx}`,
              sender: "bot" as const,
              type: "flex" as const,
              flex: m.contents,
              quickReplies: qrList,
            }
          }

          return {
            id: `bot-${Date.now()}-${idx}`,
            sender: "bot" as const,
            type: "text" as const,
            text: m.text,
            quickReplies: qrList,
          }
        },
      )

      setMessages((prev) => [...prev, ...botMessages])
    } catch (e) {
      console.error("LINE simulation error:", e)
    } finally {
      setIsSending(false)
    }
  }

  // Initial welcome message from LINE Bot
  useEffect(() => {
    if (messages.length === 0) {
      sendMessage("選案", true)
    }
  }, [messages.length, sendMessage])

  const handleCopyWebhook = () => {
    const fullUrl = `${window.location.origin}/api/v1/line/webhook`
    navigator.clipboard.writeText(fullUrl)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  const restartSimulation = () => {
    setMessages([])
    setQuickReplies([
      { label: "挑戰投資顧問案", text: "開始情境 invest" },
      { label: "挑戰假檢警案", text: "開始情境 authority" },
      { label: "挑戰假網拍案", text: "開始情境 shopping" },
    ])
    sendMessage("選案", true)
  }

  return (
    <div className="flex flex-col h-full space-y-3">
      {/* Top Banner & Mode Toggle */}
      <div className="flex items-center justify-between bg-slate-900/90 border border-white/10 rounded-2xl p-3 shadow-md">
        <div className="flex items-center gap-2.5">
          <div className="size-9 rounded-xl bg-[#06C755] flex items-center justify-center text-white shadow-sm">
            <Smartphone className="size-5" />
          </div>
          <div>
            <h2 className="text-sm font-bold tracking-tight text-white flex items-center gap-1.5">
              <span>LINE 官方頻道實境防詐對話</span>
              <span className="text-[10px] bg-[#06C755]/20 text-emerald-400 px-2 py-0.5 rounded-full font-medium border border-emerald-500/30">
                競賽標準對接
              </span>
            </h2>
            <p className="text-[11px] text-slate-400">
              直覺留給用戶，分析留給系統
            </p>
          </div>
        </div>

        <div className="flex items-center gap-1 bg-slate-950/80 p-1 rounded-xl border border-white/5">
          <button
            type="button"
            onClick={() => setActiveTab("simulator")}
            className={`px-3 py-1 text-xs font-semibold rounded-lg transition-all ${
              activeTab === "simulator"
                ? "bg-[#06C755] text-white shadow"
                : "text-slate-400 hover:text-white"
            }`}
          >
            實機模擬器
          </button>
          <button
            type="button"
            onClick={() => setActiveTab("integration")}
            className={`px-3 py-1 text-xs font-semibold rounded-lg transition-all ${
              activeTab === "integration"
                ? "bg-[#06C755] text-white shadow"
                : "text-slate-400 hover:text-white"
            }`}
          >
            頻道對接指南
          </button>
        </div>
      </div>

      {/* Main Content Area */}
      {activeTab === "simulator" ? (
        <div className="flex-1 flex flex-col min-h-0 bg-[#0c121e] rounded-2xl border border-white/10 overflow-hidden shadow-2xl">
          {/* Simulated LINE Header */}
          <div className="bg-[#06C755] text-white px-4 py-2.5 flex items-center justify-between shrink-0 shadow-sm">
            <div className="flex items-center gap-2.5">
              <div className="size-8 rounded-full bg-white/20 p-1 border border-white/40 flex items-center justify-center">
                <ShieldCheck className="size-5 text-white" />
              </div>
              <div>
                <div className="text-xs font-bold flex items-center gap-1">
                  <span>反詐大師 · 官方實境防詐頻道</span>
                  <span className="text-[9px] bg-white/25 px-1.5 py-0.2 rounded">
                    官方認證
                  </span>
                </div>
                <div className="text-[10px] text-white/80">
                  雙歷程認知免疫模擬對話中
                </div>
              </div>
            </div>

            <button
              type="button"
              onClick={restartSimulation}
              className="p-1.5 rounded-lg bg-white/10 hover:bg-white/20 text-white text-xs flex items-center gap-1 transition-colors"
              title="重新開案"
            >
              <RotateCcw className="size-3.5" />
              <span className="text-[11px]">重啟</span>
            </button>
          </div>

          {/* Chat Bubble Scroll Area */}
          <div className="flex-1 overflow-y-auto p-3.5 space-y-3 bg-gradient-to-b from-[#8CABD9]/10 via-[#0d1424] to-[#0d1424]">
            <div className="text-center py-1">
              <span className="inline-flex items-center gap-1 text-[10px] bg-slate-900/80 text-slate-400 px-3 py-0.5 rounded-full border border-white/5">
                <Lock className="size-3 text-emerald-400" />
                <span>訊息端對端加密（防詐攻防對話已連線）</span>
              </span>
            </div>

            {messages.map((m) => {
              if (m.sender === "user") {
                return (
                  <div key={m.id} className="flex justify-end">
                    <div className="max-w-[80%] rounded-2xl rounded-tr-xs bg-[#06C755] text-white px-3.5 py-2 text-sm font-medium shadow-sm leading-relaxed break-words">
                      {m.text}
                    </div>
                  </div>
                )
              }

              // Bot Message
              if (m.type === "flex" && m.flex) {
                const bubble = m.flex
                const headerColor = bubble.header?.backgroundColor || "#06C755"
                const headerText =
                  bubble.header?.contents?.[0]?.text || "反詐通知"
                return (
                  <div key={m.id} className="flex justify-start">
                    <div className="max-w-[90%] rounded-2xl overflow-hidden border border-slate-200 bg-white text-slate-900 shadow-2xl">
                      <div
                        className="px-4 py-3 text-white font-bold text-sm"
                        style={{ backgroundColor: headerColor }}
                      >
                        {headerText}
                      </div>
                      <div className="p-4 space-y-2 text-xs text-slate-800">
                        {bubble.body?.contents?.map((item: any, i: number) => {
                          if (item.type === "text") {
                            return (
                              <p
                                key={i}
                                className="leading-relaxed font-medium"
                                style={{ color: item.color || "#1f2937" }}
                              >
                                {item.text}
                              </p>
                            )
                          }
                          if (item.type === "box" && item.contents) {
                            return (
                              <div
                                key={i}
                                className="flex justify-between items-center py-1.5 border-b border-slate-100"
                              >
                                {item.contents.map((sub: any, j: number) => (
                                  <span
                                    key={j}
                                    style={{ color: sub.color || "#4b5563" }}
                                    className={
                                      sub.weight === "bold"
                                        ? "font-bold text-slate-900"
                                        : ""
                                    }
                                  >
                                    {sub.text}
                                  </span>
                                ))}
                              </div>
                            )
                          }
                          return null
                        })}
                      </div>
                    </div>
                  </div>
                )
              }

              return (
                <div
                  key={m.id}
                  className="flex justify-start items-start gap-2"
                >
                  <div className="size-7 rounded-full bg-slate-800 border border-white/20 flex items-center justify-center text-[10px] font-bold text-emerald-400 shrink-0 mt-1">
                    LINE
                  </div>
                  <div className="max-w-[85%] rounded-2xl rounded-tl-xs bg-slate-900 text-slate-100 border border-white/10 px-3.5 py-2.5 text-sm shadow-sm leading-relaxed whitespace-pre-line break-words">
                    {m.text}
                  </div>
                </div>
              )
            })}
            <div ref={messagesEndRef} />
          </div>

          {/* Quick Reply Actions (LINE Quick Reply Chips) */}
          {quickReplies.length > 0 && (
            <div className="px-3 py-2 bg-slate-950/90 border-t border-white/5 flex items-center gap-1.5 overflow-x-auto shrink-0 scrollbar-none">
              <span className="text-[10px] text-slate-400 shrink-0">
                快捷行動：
              </span>
              {quickReplies.map((qr, idx) => (
                <button
                  key={idx}
                  type="button"
                  disabled={isSending}
                  onClick={() => sendMessage(qr.text)}
                  className="rounded-full border border-emerald-500/40 bg-emerald-500/10 px-3 py-1 text-xs font-semibold text-emerald-300 hover:bg-emerald-500/20 whitespace-nowrap transition-colors disabled:opacity-50 shrink-0"
                >
                  {qr.label}
                </button>
              ))}
            </div>
          )}

          {/* Input Bar */}
          <div className="p-2.5 bg-slate-950 border-t border-white/10 shrink-0">
            <form
              className="flex items-center gap-2"
              onSubmit={(e) => {
                e.preventDefault()
                sendMessage(inputText)
              }}
            >
              <input
                type="text"
                value={inputText}
                onChange={(e) => setInputText(e.target.value)}
                placeholder="輸入訊息（依直覺回覆，或使用上方快捷鍵）..."
                disabled={isSending}
                className="flex-1 rounded-full bg-slate-900 border border-white/10 px-4 py-2 text-xs text-white placeholder-slate-500 outline-none focus:border-emerald-500/60 disabled:opacity-50"
              />
              <button
                type="submit"
                disabled={isSending || !inputText.trim()}
                className="size-8 rounded-full bg-[#06C755] hover:bg-green-500 text-white flex items-center justify-center transition-colors disabled:opacity-40"
                aria-label="送出"
              >
                <Send className="size-3.5" />
              </button>
            </form>
          </div>
        </div>
      ) : (
        /* Integration Guide Tab */
        <div className="flex-1 overflow-y-auto space-y-4 pr-1">
          {/* Card 1: Official Account QR & Webhook */}
          <div className="bg-slate-900/90 border border-white/10 rounded-2xl p-4 space-y-3 shadow-md">
            <div className="flex items-center gap-2 text-emerald-400 font-bold text-sm">
              <QrCode className="size-4" />
              <span>官方頻道對接配置</span>
            </div>
            <p className="text-xs text-slate-300 leading-relaxed">
              本防詐攻防系統已具備完整的 LINE Messaging API Webhook 支援。只要在
              LINE Developers 後台配置 Webhook
              URL，即可直接讓評審與大專學生以真實 LINE App
              掃描加入好友展開實境對話。
            </p>

            <div className="p-3 bg-slate-950 rounded-xl border border-white/10 space-y-2">
              <div className="text-[11px] text-slate-400 font-semibold">
                Webhook URL (Messaging API)：
              </div>
              <div className="flex items-center gap-2">
                <code className="flex-1 bg-slate-900 px-3 py-1.5 rounded-lg text-xs font-mono text-emerald-300 truncate border border-white/5">
                  {typeof window !== "undefined"
                    ? `${window.location.origin}/api/v1/line/webhook`
                    : "/api/v1/line/webhook"}
                </code>
                <button
                  type="button"
                  onClick={handleCopyWebhook}
                  className="px-3 py-1.5 text-xs font-bold rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white flex items-center gap-1 transition-colors"
                >
                  <Copy className="size-3" />
                  <span>{copied ? "已複製" : "複製"}</span>
                </button>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-2 text-xs">
              <div className="p-2.5 bg-slate-950/60 rounded-xl border border-white/5">
                <span className="text-slate-400 block text-[10px]">
                  驗證機制
                </span>
                <span className="font-semibold text-slate-200">
                  HMAC-SHA256 數位簽名
                </span>
              </div>
              <div className="p-2.5 bg-slate-950/60 rounded-xl border border-white/5">
                <span className="text-slate-400 block text-[10px]">
                  訊息格式
                </span>
                <span className="font-semibold text-slate-200">
                  Flex Message + Quick Reply
                </span>
              </div>
            </div>
          </div>

          {/* Card 2: Pedagogical & Cognitive Architecture */}
          <div className="bg-slate-900/90 border border-white/10 rounded-2xl p-4 space-y-2.5 shadow-md">
            <div className="flex items-center gap-2 text-amber-400 font-bold text-sm">
              <ShieldAlert className="size-4" />
              <span>「直覺留給用戶，分析留給系統」設計規範</span>
            </div>
            <ul className="space-y-2 text-xs text-slate-300">
              <li className="flex items-start gap-2">
                <CheckCircle2 className="size-4 text-emerald-400 shrink-0 mt-0.5" />
                <span>
                  <b>沉浸式直覺對話：</b>
                  對話過程中不呈現提示卡或心理學劇透，忠實還原學生在日常通訊軟體中的直覺應答（Gut
                  Reaction）。
                </span>
              </li>
              <li className="flex items-start gap-2">
                <CheckCircle2 className="size-4 text-emerald-400 shrink-0 mt-0.5" />
                <span>
                  <b>後台深度診斷覆盤：</b>
                  玩家點擊「檢舉」或「退出」結束攻防後，由 LINE Bot 推送專屬
                  Flex Message 診斷書，一次性解密席爾迪尼 7
                  大心理說服槓桿與關鍵紅旗。
                </span>
              </li>
              <li className="flex items-start gap-2">
                <CheckCircle2 className="size-4 text-emerald-400 shrink-0 mt-0.5" />
                <span>
                  <b>全國大專聯賽聯動：</b>在 LINE
                  官方頻道的防詐戰績與辨識敏銳度，將即時同步累計至全校防禦指數（Collegiate
                  Defense League）。
                </span>
              </li>
            </ul>
          </div>
        </div>
      )}
    </div>
  )
}
