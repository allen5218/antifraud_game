import { createFileRoute, Link } from "@tanstack/react-router"
import type { ReactNode } from "react"

export const Route = createFileRoute("/privacy")({
  component: PrivacyPage,
  head: () => ({ meta: [{ title: "隱私權政策 - ScamGym 識詐練習場" }] }),
})

function Section({ title, children }: { title: string; children: ReactNode }) {
  return (
    <section className="flex flex-col gap-1.5">
      <h2 className="font-bold">{title}</h2>
      {children}
    </section>
  )
}

function PrivacyPage() {
  return (
    <main className="mx-auto flex min-h-dvh max-w-2xl flex-col gap-5 px-4 py-8 text-sm leading-relaxed">
      <h1 className="text-xl font-bold">隱私權政策</h1>
      <p>
        ScamGym
        識詐練習場是練習辨認詐騙的遊戲。這一頁說明我們收集哪些資料、拿來做什麼。
      </p>
      <Section title="我們收集的資料">
        <ul className="list-disc pl-5">
          <li>
            帳號：用 Email 註冊時，是你的 Email 和加密後的密碼；用 Google
            登入時，是 Google 提供的帳號代號、Email 和名字；用 LINE 登入時，是
            LINE 提供的帳號代號和顯示名稱，不取得 Email。
          </li>
          <li>你自己設定的暱稱（顯示在排行榜上）。</li>
          <li>
            遊戲紀錄：每一題的作答與對錯、情境對抗的對話內容、檢測成績、遊戲裡的金錢、經驗與購買紀錄。
          </li>
          <li>
            用試測邀請網址加入的訪客帳號不收任何聯絡資料，只有系統產生的受試編號。
          </li>
        </ul>
      </Section>
      <Section title="資料的用途">
        <ul className="list-disc pl-5">
          <li>讓你登入，並保存你的練習進度。</li>
          <li>依你答錯較多的詐騙類型，調整之後出題的比例。</li>
          <li>
            統計試測成效，用來改進題目；對外只呈現不能辨識個人的統計結果。
          </li>
        </ul>
      </Section>
      <Section title="AI 服務">
        <p>
          情境對抗裡的對方由 Google 的 Gemini 扮演，你在對話中輸入的文字會送到
          Gemini 產生回覆。調整出題比例時，送給 Gemini
          的只有各類型的答題統計，不含你的帳號資料。請不要在對話中輸入真實的個人資料。
        </p>
      </Section>
      <Section title="資料的分享">
        <p>
          我們不販售、不出租你的資料。除了上面提到的 AI
          服務與登入服務（Google、LINE），不會提供給其他人，法律要求時除外。
        </p>
      </Section>
      <Section title="刪除資料">
        <p>
          你可以在「我」→「帳號設定」刪除帳號，帳號與所有遊戲紀錄會一起刪除。
        </p>
      </Section>
      <Link
        to="/login"
        className="text-muted-foreground underline underline-offset-4"
      >
        回到登入頁
      </Link>
    </main>
  )
}
