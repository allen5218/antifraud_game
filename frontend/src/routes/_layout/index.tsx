import { createFileRoute, Link } from "@tanstack/react-router"
import { MascotDisplay } from "@/components/Home/MascotDisplay"
import { ScoreOverview } from "@/components/Home/ScoreOverview"
import useAuth from "@/hooks/useAuth"

export const Route = createFileRoute("/_layout/")({
  component: Dashboard,
  head: () => ({
    meta: [
      {
        title: "首頁 - 反詐騙訓練",
      },
    ],
  }),
})

function Dashboard() {
  const { user: currentUser } = useAuth()

  return (
    <div className="mx-auto max-w-2xl space-y-8">
      <div>
        <h1 className="max-w-sm truncate text-2xl font-bold">
          嗨，{currentUser?.full_name || currentUser?.email} 👋
        </h1>
        <p className="text-muted-foreground">
          歡迎回來，準備好提升你的防詐能力了嗎？
        </p>
      </div>

      <div className="flex justify-center py-4">
        <MascotDisplay />
      </div>

      <ScoreOverview />

      <div className="flex flex-col gap-3 sm:flex-row">
        <Link
          to="/pretest"
          className="flex-1 rounded-xl bg-primary py-4 text-center text-lg font-bold text-primary-foreground transition-transform hover:scale-[1.01] active:scale-[0.99]"
        >
          開始前測
        </Link>
        <Link
          to="/mascot"
          className="flex-1 rounded-xl border-2 border-border py-4 text-center text-lg font-semibold transition-transform hover:scale-[1.01] active:scale-[0.99]"
        >
          查看裝備商店
        </Link>
      </div>
    </div>
  )
}
