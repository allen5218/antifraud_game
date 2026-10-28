import { useMutation, useQueryClient } from "@tanstack/react-query"
import { QrCode } from "lucide-react"
import { QRCodeCanvas } from "qrcode.react"
import { useRef, useState } from "react"
import type { ClassroomPublic } from "@/client"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { downloadFile } from "@/lib/download"
import { classApi } from "./classroomApi"

/** 邀請：QR code、網址、班級代碼、下載圖片、停止加入；改班名也放這裡 */
export function ClassInvite({ classroom }: { classroom: ClassroomPublic }) {
  const queryClient = useQueryClient()
  const canvas = useRef<HTMLCanvasElement>(null)
  const [name, setName] = useState(classroom.name)
  const url = `${window.location.origin}/class/${classroom.token}`
  const update = useMutation({
    mutationFn: (body: { name?: string; is_open?: boolean }) =>
      classApi.update(classroom.id, body),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["classes"] }),
  })
  return (
    <div className="flex flex-col gap-3 text-sm">
      <p>
        班級代碼{" "}
        <span className="font-mono text-2xl font-bold tracking-widest">
          {classroom.code}
        </span>
      </p>
      {/* QR code 固定黑格白底：深色模式的反色碼很多手機掃不出來，這是只用主題色的例外 */}
      <div className="self-start rounded-xl bg-white p-3">
        <QRCodeCanvas
          ref={canvas}
          value={url}
          size={220}
          marginSize={2}
          bgColor="#ffffff"
          fgColor="#000000"
          title={`${classroom.name}的加入班級 QR code`}
        />
      </div>
      <a href={url} className="break-all text-primary">
        {url}
      </a>
      <div className="flex flex-wrap gap-2">
        <Button
          variant="outline"
          onClick={() => {
            if (canvas.current)
              downloadFile(
                canvas.current.toDataURL("image/png"),
                `class-${classroom.code}.png`,
              )
          }}
        >
          <QrCode aria-hidden className="size-4" />
          下載邀請圖片
        </Button>
        <Button
          variant="outline"
          disabled={update.isPending}
          onClick={() => update.mutate({ is_open: !classroom.is_open })}
        >
          {classroom.is_open ? "停止加入" : "重新開放加入"}
        </Button>
      </div>
      {!classroom.is_open && (
        <p className="text-muted-foreground">
          已停止加入：新的學生進不來，已經在班上的不受影響。
        </p>
      )}
      <form
        className="flex flex-wrap items-end gap-2"
        onSubmit={(event) => {
          event.preventDefault()
          if (name.trim() && name.trim() !== classroom.name)
            update.mutate({ name: name.trim() })
        }}
      >
        <div className="flex min-w-0 flex-1 flex-col gap-1">
          <label htmlFor="class-rename" className="font-medium">
            班級名稱
          </label>
          <Input
            id="class-rename"
            value={name}
            maxLength={100}
            onChange={(event) => setName(event.target.value)}
          />
        </div>
        <Button type="submit" variant="outline" disabled={update.isPending}>
          改名
        </Button>
      </form>
    </div>
  )
}
