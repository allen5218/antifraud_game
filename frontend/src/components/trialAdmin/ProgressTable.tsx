import type { CohortProgress, CohortProgressMember } from "@/client"
import { examText, pretestText, surveyText, taipeiTime } from "./format"

function CodeButton({
  member,
  onOpen,
}: {
  member: CohortProgressMember
  onOpen: (member: CohortProgressMember) => void
}) {
  return (
    <button
      type="button"
      onClick={() => onOpen(member)}
      className="font-bold text-primary underline underline-offset-2"
    >
      {member.participant_code ?? "沒有編號"}
    </button>
  )
}

/** 每個人的前測、檢測、問卷與能不能領錢（和「下載作答資料」同一套判定）；點編號看詳情 */
export function ProgressTable({
  progress,
  onOpen,
}: {
  progress: CohortProgress
  onOpen: (member: CohortProgressMember) => void
}) {
  const stats = [
    ["已加入", progress.member_count],
    ["前測做完", progress.pretest_done],
    ["檢測交卷", progress.exam_completed],
    ["問卷交了", progress.survey_done],
    ["可以領錢", progress.payout_eligible],
  ] as const
  return (
    <div className="flex flex-col gap-3">
      <dl className="grid grid-cols-5 gap-2">
        {stats.map(([label, value]) => (
          <div
            key={label}
            className="rounded-lg border border-border bg-card p-2 text-center"
          >
            <dt className="whitespace-nowrap text-[11px] text-muted-foreground">
              {label}
            </dt>
            <dd className="text-xl font-bold">{value}</dd>
          </div>
        ))}
      </dl>
      {progress.members.length === 0 ? (
        <p className="text-muted-foreground">還沒有人加入。</p>
      ) : (
        <>
          <p className="text-xs text-muted-foreground">
            點受試編號看這個人的前測每題、每次檢測、練習量與問卷答案。
          </p>
          {/* 手機：一人一張卡片 */}
          <ul className="flex flex-col gap-2 md:hidden">
            {progress.members.map((m) => (
              <li
                key={m.user_id}
                className="rounded-lg border border-border bg-card p-3 text-sm"
              >
                <div className="flex items-center justify-between">
                  <CodeButton member={m} onOpen={onOpen} />
                  <span
                    className={`font-bold ${m.payout_eligible ? "text-legit" : "text-muted-foreground"}`}
                  >
                    {m.payout_eligible ? "可以領錢" : "還不能領"}
                  </span>
                </div>
                <p>前測：{pretestText(m)}</p>
                <p>檢測：{examText(m)}</p>
                <p>問卷：{surveyText(m)}</p>
                {m.payout_reasons.length > 0 && (
                  <p className="text-muted-foreground">
                    原因：{m.payout_reasons.join("、")}
                  </p>
                )}
              </li>
            ))}
          </ul>
          <div className="hidden overflow-x-auto md:block">
            <table className="w-full text-left text-sm">
              <thead>
                <tr className="border-b border-border">
                  <th className="whitespace-nowrap p-2">受試編號</th>
                  <th className="whitespace-nowrap p-2">加入時間</th>
                  <th className="whitespace-nowrap p-2">前測</th>
                  <th className="whitespace-nowrap p-2">檢測</th>
                  <th className="whitespace-nowrap p-2">問卷</th>
                  <th className="whitespace-nowrap p-2">可以領錢</th>
                  <th className="whitespace-nowrap p-2">不能領的原因</th>
                </tr>
              </thead>
              <tbody>
                {progress.members.map((m) => (
                  <tr
                    key={m.user_id}
                    className="border-b border-border align-top"
                  >
                    <td className="whitespace-nowrap p-2">
                      <CodeButton member={m} onOpen={onOpen} />
                    </td>
                    <td className="p-2 whitespace-nowrap">
                      {taipeiTime(m.created_at)}
                    </td>
                    <td className="p-2">{pretestText(m)}</td>
                    <td className="p-2">{examText(m)}</td>
                    <td className="p-2">{surveyText(m)}</td>
                    <td
                      className={`whitespace-nowrap p-2 font-bold ${m.payout_eligible ? "text-legit" : "text-muted-foreground"}`}
                    >
                      {m.payout_eligible ? "可以" : "還不行"}
                    </td>
                    <td className="p-2 text-muted-foreground">
                      {m.payout_reasons.join("、")}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
    </div>
  )
}
