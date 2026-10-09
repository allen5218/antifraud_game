import { useQuery } from "@tanstack/react-query"
import { Link } from "@tanstack/react-router"
import { ExamService } from "@/client/sdk.gen"
import { errorCode } from "./exam"

const LINK =
  "inline-block rounded-xl bg-primary px-4 py-3 text-sm font-bold text-primary-foreground"

export function ExamInProgress({ error }: { error: unknown }) {
  const locked = errorCode(error) === "exam_in_progress"
  const status = useQuery({
    queryKey: ["exam", "status"],
    queryFn: () => ExamService.readStatus(),
    enabled: locked,
    retry: false,
    staleTime: 0,
  })
  if (!locked) return null
  const attemptId = status.data?.active_attempt_id
  return (
    <section
      role="alert"
      className="rounded-2xl border border-warning/40 bg-warning/10 p-5 text-center"
    >
      <p className="mb-4 text-sm">
        你還有一場檢測沒完成，先完成檢測再回來練習。
      </p>
      {attemptId ? (
        <Link to="/exam/$attemptId" params={{ attemptId }} className={LINK}>
          繼續檢測
        </Link>
      ) : (
        <Link to="/exam" className={LINK}>
          繼續檢測
        </Link>
      )}
    </section>
  )
}
