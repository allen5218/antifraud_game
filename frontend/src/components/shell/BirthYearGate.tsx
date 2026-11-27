import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { Cake } from "lucide-react"
import { type FormEvent, useState } from "react"
import { UsersService } from "@/client"
import { Input } from "@/components/ui/input"
import { LoadingButton } from "@/components/ui/loading-button"
import { currentUserQuery, isLoggedIn } from "@/hooks/useAuth"
import { HOME_SUMMARY_KEY } from "@/hooks/useHomeSummary"
import { BIRTH_YEAR_HINT, parseBirthYear } from "@/lib/birthYear"

/**
 * 還沒有出生年的帳號（掃 QR code 的訪客、LINE／Google 登入、改版前的舊帳號）
 * 進來時先問一次，蓋住整個畫面，填完才看得到房間。50 歲以上用年長者介面。
 */
export function BirthYearGate() {
  const queryClient = useQueryClient()
  const { data: user } = useQuery({
    ...currentUserQuery,
    enabled: isLoggedIn(),
  })
  const [text, setText] = useState("")
  const [error, setError] = useState<string | null>(null)

  const save = useMutation({
    mutationFn: (birthYear: number) =>
      UsersService.setBirthYearMe({ requestBody: { birth_year: birthYear } }),
    onSuccess: (updated) => {
      queryClient.setQueryData(currentUserQuery.queryKey, updated)
      queryClient.invalidateQueries({ queryKey: HOME_SUMMARY_KEY })
    },
    onError: () => setError("沒有存成功，請再按一次"),
  })

  if (!user || user.birth_year != null) return null

  const submit = (event: FormEvent) => {
    event.preventDefault()
    const year = parseBirthYear(text)
    if (year === null) {
      setError("看不懂這個年份，請再輸入一次")
      return
    }
    setError(null)
    save.mutate(year)
  }

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="birth-year-title"
      className="fixed inset-0 z-[60] flex items-center justify-center bg-black/50 p-4"
    >
      <form
        onSubmit={submit}
        className="w-full max-w-sm rounded-2xl border border-border bg-card p-6 shadow-lg"
      >
        <div className="mb-4 flex flex-col items-center gap-2 text-center">
          <Cake aria-hidden className="size-10 text-primary" />
          <h2 id="birth-year-title" className="text-2xl font-bold">
            你是哪一年出生的？
          </h2>
          <p className="text-base text-muted-foreground">{BIRTH_YEAR_HINT}</p>
        </div>
        <Input
          data-testid="birth-year-gate-input"
          aria-label="出生年"
          inputMode="numeric"
          autoComplete="bday-year"
          autoFocus
          value={text}
          onChange={(event) => setText(event.target.value)}
          className="h-14 text-center text-2xl"
        />
        {error && (
          <p role="alert" className="mt-2 text-center text-sm text-scam">
            {error}
          </p>
        )}
        <p className="mt-3 text-center text-sm text-muted-foreground">
          送出後不能修改。
        </p>
        <LoadingButton
          type="submit"
          className="mt-4 h-12 w-full text-lg"
          loading={save.isPending}
        >
          確定
        </LoadingButton>
      </form>
    </div>
  )
}
