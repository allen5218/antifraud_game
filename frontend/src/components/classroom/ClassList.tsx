import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { Link } from "@tanstack/react-router"
import { ChevronRight } from "lucide-react"
import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { classApi } from "./classroomApi"

export const CLASSES_KEY = ["classes"] as const

/** 老師的班級列表與建班 */
export function ClassList() {
  const queryClient = useQueryClient()
  const [name, setName] = useState("")
  const classes = useQuery({ queryKey: CLASSES_KEY, queryFn: classApi.list })
  const create = useMutation({
    mutationFn: () => classApi.create(name.trim()),
    onSuccess: () => {
      setName("")
      queryClient.invalidateQueries({ queryKey: CLASSES_KEY })
    },
  })
  return (
    <div className="flex flex-col gap-4">
      <header>
        <h1 className="text-2xl font-bold">班級管理</h1>
        <p className="text-sm text-muted-foreground">
          建一個班，把 QR code 或班級代碼給學生，再出作業。
        </p>
      </header>
      <form
        className="flex flex-wrap items-end gap-2"
        onSubmit={(event) => {
          event.preventDefault()
          if (name.trim() && !create.isPending) create.mutate()
        }}
      >
        <div className="flex min-w-0 flex-1 flex-col gap-1 text-sm">
          <label htmlFor="class-new-name" className="font-medium">
            新班級名稱
          </label>
          <Input
            id="class-new-name"
            value={name}
            maxLength={100}
            placeholder="例如：三年二班"
            onChange={(event) => setName(event.target.value)}
          />
        </div>
        <Button type="submit" disabled={!name.trim() || create.isPending}>
          建立班級
        </Button>
      </form>
      {create.isError && (
        <p role="alert" className="text-sm text-scam">
          建立失敗，請再試一次。
        </p>
      )}
      {classes.isPending && <output>正在載入…</output>}
      {classes.isError && (
        <p role="alert" className="text-scam">
          讀不到班級，請再試一次。
        </p>
      )}
      {classes.data?.length === 0 && (
        <p className="text-muted-foreground">還沒有班級。</p>
      )}
      <ul className="grid gap-2 md:grid-cols-2">
        {classes.data?.map((c) => (
          <li key={c.id}>
            <Link
              to="/classes/$classId"
              params={{ classId: c.id }}
              className="flex items-center gap-3 rounded-xl border border-border bg-card p-3 text-sm transition hover:bg-accent"
            >
              <span className="flex min-w-0 flex-1 flex-col">
                <span className="truncate text-base font-bold">{c.name}</span>
                <span className="text-muted-foreground">
                  {c.member_count} 位學生・{c.assignment_count} 份作業
                  {c.pending_count > 0
                    ? `・${c.pending_count} 人還有作業沒做`
                    : ""}
                  {c.is_open ? "" : "・已停止加入"}
                </span>
              </span>
              <ChevronRight
                aria-hidden
                className="size-4 text-muted-foreground"
              />
            </Link>
          </li>
        ))}
      </ul>
    </div>
  )
}
