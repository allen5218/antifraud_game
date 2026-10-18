import { useLayoutEffect, useRef, useState } from "react"
import { layoutStage, type Size, type StageLayout } from "./stage"

/** 量房間外框的大小，算出舞台的縮放與位移；外框大小變了（轉向、網址列收起）就重算。 */
export function useStageLayout(world: Size) {
  const ref = useRef<HTMLDivElement>(null)
  const [layout, setLayout] = useState<StageLayout>({ scale: 0, x: 0, y: 0 })
  const [view, setView] = useState({ width: 0, height: 0 })
  const { width, height } = world
  useLayoutEffect(() => {
    const element = ref.current
    if (!element) return
    const update = () => {
      setView({ width: element.clientWidth, height: element.clientHeight })
      setLayout(
        layoutStage(
          { width, height },
          element.clientWidth,
          element.clientHeight,
        ),
      )
    }
    update()
    if (typeof ResizeObserver === "undefined") return
    const observer = new ResizeObserver(update)
    observer.observe(element)
    return () => observer.disconnect()
  }, [width, height])
  return { ref, layout, view }
}
