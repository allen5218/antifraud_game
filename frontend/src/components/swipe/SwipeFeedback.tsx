interface Props {
  correct: boolean
  explanation: string
  weaknessTags: string[]
}

export function SwipeFeedback({ correct, explanation, weaknessTags }: Props) {
  return (
    <div
      className={`rounded-xl border p-3 text-xs ${
        correct ? "border-green-300 bg-green-50" : "border-red-300 bg-red-50"
      }`}
    >
      <div
        className={`font-bold ${correct ? "text-green-700" : "text-red-700"}`}
      >
        {correct ? "答對！" : "答錯"}
      </div>
      <p className="mt-1 text-muted-foreground">{explanation}</p>
      {weaknessTags.length > 0 && (
        <div className="mt-2 flex flex-wrap gap-1">
          {weaknessTags.map((t) => (
            <span
              key={t}
              className="rounded-full bg-muted px-2 py-0.5 text-[10px]"
            >
              {t}
            </span>
          ))}
        </div>
      )}
    </div>
  )
}
