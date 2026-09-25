import { BookOpen, CircleCheck, Flag } from "lucide-react"

/**
 * 揭曉時的一條線索:可疑的地方(旗子)或正常的跡象(打勾)。
 * 題組揭曉與情境結局卡共用,兩邊長得一樣玩家才會把它們當成同一種東西。
 */
export function SignalItem({
  suspicious,
  text,
  label,
}: {
  suspicious: boolean
  text: string
  /** 可疑時標出是哪一種話術 */
  label?: string
}) {
  const Icon = suspicious ? Flag : CircleCheck
  return (
    <li className="flex gap-1.5 text-xs leading-snug">
      <Icon
        aria-hidden
        className={`mt-px size-3.5 shrink-0 ${suspicious ? "text-scam" : "text-legit"}`}
      />
      <span>
        {text}
        {suspicious && label && (
          <span className="ml-1 whitespace-nowrap rounded bg-scam/15 px-1 py-0.5 text-[10px] font-bold text-scam">
            {label}
          </span>
        )}
      </span>
    </li>
  )
}

/** 題目或情境素材的出處。 */
export function Provenance({
  text,
  className = "",
}: {
  text: string
  className?: string
}) {
  return (
    <p
      className={`flex gap-1.5 rounded-lg bg-muted px-3 py-2 text-[11px] text-muted-foreground ${className}`}
    >
      <BookOpen aria-hidden className="mt-px size-3.5 shrink-0" />
      <span>{text}</span>
    </p>
  )
}
