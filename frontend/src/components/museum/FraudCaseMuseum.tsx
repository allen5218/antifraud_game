import { useState } from "react"

export interface RealCase {
  id: string
  title: string
  type: string
  source: string
  date: string
  summary: string
  evidenceKey: string
  unlocked: boolean
  pdfUrl?: string
}

const REAL_CASES: RealCase[] = [
  {
    id: "case_01",
    title: "01｜中古車貸款，簽了契約卻沒有交車",
    type: "買車/貸款詐欺",
    source: "臺中地院 110 年度訴字第 2430 號判決",
    date: "2022-08-31",
    summary: "廣告宣稱低利率貸款買車，簽約與過戶後款項被撥走，但始終未交車。法院認定行使偽造私文書罪。",
    evidenceKey: "查核重點：核對實際車輛過戶授權與撥款受款對象。",
    unlocked: true,
  },
  {
    id: "case_02",
    title: "02｜同一中古車投資案，有罪與無罪並存",
    type: "投資/合夥詐欺",
    source: "臺灣高等法院 114 年度上易字第 1123 號判決",
    date: "2025-10-02",
    summary: "同一中古車投資案中，部分獲判有罪；另一投資人因曾有交易分潤報告，法院認事後未還本金不代表預謀詐欺。",
    evidenceKey: "查核重點：曾收到利息/出金不能作為投資安全的充分證明。",
    unlocked: true,
  },
  {
    id: "case_03",
    title: "03｜假檢警/投資，進一步誘導房屋抵押",
    type: "房產抵押/假檢警",
    source: "桃園地檢署 114 年地面師起訴案",
    date: "2025-05-21",
    summary: "被害人先受投資話術引誘，再被介紹以不動產高利抵押借款，涉案專業人士甚至安排免責聲明作掩護。",
    evidenceKey: "查核重點：專業人士與免責聲明不等於合法授權。",
    unlocked: true,
  },
  {
    id: "case_04",
    title: "04｜有公司有契約，建案卻未動工吸金案",
    type: "建案/非法吸金",
    source: "桃園地檢署 115 年建案吸金案起訴新聞",
    date: "2026-07-22",
    summary: "宣稱投資 9 個建案工程，約定年化 10-35% 報酬，實勘發現建案根本未動工或停工。",
    evidenceKey: "查核重點：必須獨立查核實體工程許可與實際進度。",
    unlocked: false,
  },
  {
    id: "case_05",
    title: "05｜真的見面約會，之後要求周轉或援助",
    type: "假交友/真人面交",
    source: "警察廣播電臺 114 年案件報導",
    date: "2025-01-07",
    summary: "集團建立線上感情後，派真人男公關面交約會建立極高信任，再以公司周轉、生病為由借款。",
    evidenceKey: "查核重點：打破『見過面就不是詐騙』的直覺迷思。",
    unlocked: true,
  },
  {
    id: "case_07",
    title: "07｜買芒果，連續轉介假物流及假銀行專員",
    type: "假網拍/轉介客服",
    source: "內政部警政署 165 宣導報導",
    date: "2026-07-06",
    summary: "網購接洽後收到假物流連結要求實名認證，隨後轉介假銀行人員引導操作網銀與無卡提款。",
    evidenceKey: "查核重點：物流實名認證絕不需要進行金融匯款操作。",
    unlocked: true,
  },
]

interface FraudCaseMuseumProps {
  isOpen: boolean
  onClose: () => void
}

export function FraudCaseMuseum({ isOpen, onClose }: FraudCaseMuseumProps) {
  const [selectedCase, setSelectedCase] = useState<RealCase | null>(null)

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-md flex items-center justify-center p-4 animate-in fade-in duration-200">
      <div className="bg-slate-900 text-white rounded-2xl border border-blue-500/30 w-full max-w-xl overflow-hidden shadow-2xl flex flex-col max-h-[90vh]">
        {/* Header */}
        <div className="p-4 bg-gradient-to-r from-blue-900/60 to-slate-900 border-b border-blue-500/20 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="text-2xl">🏛️</span>
            <div>
              <h2 className="text-lg font-bold text-blue-400">真實防詐案件展覽館 (Case Museum)</h2>
              <p className="text-xs text-slate-400">司法院裁判書與 165 官方起訴案情實錄</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="w-8 h-8 rounded-full bg-slate-800 hover:bg-slate-700 flex items-center justify-center text-slate-300 text-sm"
          >
            ✕
          </button>
        </div>

        {/* Case List Grid */}
        <div className="p-4 overflow-y-auto space-y-3 flex-1">
          {REAL_CASES.map((c) => (
            <div
              key={c.id}
              onClick={() => setSelectedCase(c)}
              className={`p-3.5 rounded-xl border transition-all cursor-pointer flex items-center justify-between ${
                c.unlocked
                  ? "bg-slate-800/70 border-blue-500/30 hover:border-blue-400 hover:bg-slate-800"
                  : "bg-slate-900/40 border-slate-800 opacity-60"
              }`}
            >
              <div className="space-y-1 pr-2">
                <div className="flex items-center gap-2">
                  <span className="text-xs bg-blue-500/20 text-blue-300 px-2 py-0.5 rounded font-medium">
                    {c.type}
                  </span>
                  <span className="text-[11px] text-slate-400">{c.date}</span>
                </div>
                <h3 className="font-bold text-sm text-slate-100">{c.title}</h3>
                <p className="text-xs text-slate-400 line-clamp-1">{c.summary}</p>
              </div>
              <div className="text-right whitespace-nowrap">
                {c.unlocked ? (
                  <span className="text-xs bg-emerald-500/20 text-emerald-400 px-2.5 py-1 rounded-lg font-bold">
                    🔍 檢視證據
                  </span>
                ) : (
                  <span className="text-xs bg-slate-800 text-slate-500 px-2.5 py-1 rounded-lg">
                    🔒 未解鎖
                  </span>
                )}
              </div>
            </div>
          ))}
        </div>

        {/* Detail Modal Layer */}
        {selectedCase && (
          <div className="p-4 bg-slate-950 border-t border-slate-800 space-y-3 animate-in slide-in-from-bottom duration-200">
            <div className="flex items-center justify-between">
              <span className="text-xs text-blue-400 font-bold">{selectedCase.source}</span>
              <button
                onClick={() => setSelectedCase(null)}
                className="text-xs text-slate-400 hover:text-white"
              >
                收起 ▲
              </button>
            </div>
            <p className="text-xs text-slate-200 leading-relaxed">{selectedCase.summary}</p>
            <div className="bg-amber-950/40 border border-amber-500/30 p-2.5 rounded-lg text-xs text-amber-300 font-medium">
              💡 {selectedCase.evidenceKey}
            </div>
          </div>
        )}

        <div className="p-3 bg-slate-950 text-center text-[11px] text-slate-500 border-t border-slate-800">
          🏆 每解鎖一份真實裁判案例，解鎖 +2% 全局房產收益加成！
        </div>
      </div>
    </div>
  )
}
