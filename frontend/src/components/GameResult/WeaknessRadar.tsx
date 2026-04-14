import {
  PolarAngleAxis,
  PolarGrid,
  PolarRadiusAxis,
  Radar,
  RadarChart,
  ResponsiveContainer,
} from "recharts"
import type { WeaknessDetail } from "@/client"

interface WeaknessRadarProps {
  weaknesses: WeaknessDetail[]
}

export function WeaknessRadar({ weaknesses }: WeaknessRadarProps) {
  const data = weaknesses.map((w) => ({
    type: w.label,
    wrongCount: w.count,
    fullMark: Math.max(...weaknesses.map((x) => x.count), 3),
  }))

  return (
    <div className="rounded-xl border bg-card p-4 shadow-sm">
      <h3 className="mb-2 text-center text-sm font-medium text-muted-foreground">
        弱點分析
      </h3>
      <ResponsiveContainer width="100%" height={280}>
        <RadarChart data={data} cx="50%" cy="50%" outerRadius="70%">
          <PolarGrid stroke="hsl(var(--border))" />
          <PolarAngleAxis
            dataKey="type"
            tick={{ fontSize: 11, fill: "hsl(var(--foreground))" }}
          />
          <PolarRadiusAxis
            angle={90}
            tick={{ fontSize: 10, fill: "hsl(var(--muted-foreground))" }}
          />
          <Radar
            name="答錯次數"
            dataKey="wrongCount"
            stroke="hsl(var(--destructive))"
            fill="hsl(var(--destructive))"
            fillOpacity={0.3}
          />
        </RadarChart>
      </ResponsiveContainer>
    </div>
  )
}
