import type { WeaknessDetail } from "@/client"

interface WeaknessAnalysisProps {
  weaknesses: WeaknessDetail[]
  strengths: string[]
}

export function WeaknessAnalysis({
  weaknesses,
  strengths,
}: WeaknessAnalysisProps) {
  return (
    <div className="space-y-4">
      {weaknesses.length > 0 && (
        <div>
          <h3 className="mb-2 text-sm font-medium text-muted-foreground">
            需要加強
          </h3>
          <div className="space-y-2">
            {weaknesses.map((w) => (
              <div
                key={w.tag}
                className="rounded-lg border border-orange-500/20 bg-orange-500/5 p-3"
              >
                <div className="flex items-center justify-between">
                  <span className="font-medium text-orange-600 dark:text-orange-400">
                    {w.label}
                  </span>
                  <span className="text-sm text-muted-foreground">
                    答錯 {w.count} 題
                  </span>
                </div>
                <p className="mt-1 text-sm text-muted-foreground">
                  {w.suggestion}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}

      {strengths.length > 0 && (
        <div>
          <h3 className="mb-2 text-sm font-medium text-muted-foreground">
            表現優秀
          </h3>
          <div className="flex flex-wrap gap-2">
            {strengths.map((tag) => (
              <span
                key={tag}
                className="rounded-full bg-green-500/10 px-3 py-1 text-sm font-medium text-green-600 dark:text-green-400"
              >
                {tag}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
