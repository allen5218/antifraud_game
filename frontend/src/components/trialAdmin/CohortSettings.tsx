import { useMutation, useQueryClient } from "@tanstack/react-query"
import { useState } from "react"
import { AdminCohortsService, type CohortPublic } from "@/client"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { dateInputValue, expiryOf } from "./format"

/** 名稱、名額與期限：名額期限留空是不限。改了馬上生效，已經加入的人不受影響 */
export function CohortSettings({ cohort }: { cohort: CohortPublic }) {
  const queryClient = useQueryClient()
  const [name, setName] = useState(cohort.name)
  const [quota, setQuota] = useState(
    cohort.max_members == null ? "" : String(cohort.max_members),
  )
  const [date, setDate] = useState(dateInputValue(cohort.expires_at))
  const [message, setMessage] = useState<string | null>(null)
  const save = useMutation({
    mutationFn: () =>
      AdminCohortsService.updateCohort({
        cohortId: cohort.id,
        requestBody: {
          name: name.trim(),
          max_members: quota.trim() ? Number(quota) : null,
          expires_at: date ? expiryOf(date) : null,
        },
      }),
    onSuccess: () => {
      setMessage("已儲存。")
      queryClient.invalidateQueries({ queryKey: ["admin", "cohorts"] })
    },
    onError: () =>
      setMessage("儲存失敗：名稱不能空白，名額要是 1 到 5000 的整數。"),
  })
  return (
    <form
      className="mt-6 flex flex-wrap items-end gap-3"
      onSubmit={(event) => {
        event.preventDefault()
        save.mutate()
      }}
    >
      <div className="basis-full sm:flex-1 sm:basis-auto">
        <label
          htmlFor="cohort-rename"
          className="mb-1 block text-sm font-medium"
        >
          梯次名稱
        </label>
        <Input
          id="cohort-rename"
          value={name}
          maxLength={100}
          required
          onChange={(event) => setName(event.target.value)}
        />
      </div>
      <div>
        <label
          htmlFor="cohort-quota"
          className="mb-1 block text-sm font-medium"
        >
          名額（留空是不限）
        </label>
        <Input
          id="cohort-quota"
          type="number"
          min={1}
          max={5000}
          inputMode="numeric"
          value={quota}
          onChange={(event) => setQuota(event.target.value)}
          placeholder="不限"
          className="w-32"
        />
      </div>
      <div>
        <label
          htmlFor="cohort-expiry"
          className="mb-1 block text-sm font-medium"
        >
          最後一天（留空是不限期限）
        </label>
        <Input
          id="cohort-expiry"
          type="date"
          value={date}
          onChange={(event) => setDate(event.target.value)}
          className="w-44"
        />
      </div>
      <Button
        type="submit"
        variant="outline"
        disabled={save.isPending || !name.trim()}
      >
        儲存設定
      </Button>
      {message && (
        <output className="text-sm text-muted-foreground">{message}</output>
      )}
    </form>
  )
}
