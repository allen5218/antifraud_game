// TODO(Phase 2): wire to a real "today's challenge" route + fetch content from API.
// Plain div for now — the challenge route does not exist yet.
export function TodayChallengeHero() {
  return (
    <div className="mb-3 block rounded-2xl bg-gradient-to-br from-amber-300 to-orange-500 p-4 text-amber-900">
      <span className="mb-2 inline-block rounded bg-white/40 px-2 py-0.5 text-[9px] font-medium">
        今日挑戰
      </span>
      <div className="font-bold">投資詐欺 · 5 題</div>
      <div className="text-[10px] opacity-90">完成可得 +500💰 · 連勝守住</div>
    </div>
  )
}
