import { useEffect, useRef, useState } from "react"

interface AnimatedAcanthusEyeProps {
  className?: string
}

export function AnimatedAcanthusEye({ className = "" }: AnimatedAcanthusEyeProps) {
  const canvasRef = useRef<HTMLCanvasElement | null>(null)
  const containerRef = useRef<HTMLDivElement | null>(null)
  const [parallax, setParallax] = useState({ x: 0, y: 0 })

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return
    const ctx = canvas.getContext("2d")
    if (!ctx) return

    let animationFrameId: number
    let time = 0

    // High resolution virtual canvas space for the pupil (480 x 480)
    const vSize = 480
    const cx = vSize / 2
    const cy = vSize / 2
    const rimRadius = 145

    const updateCanvasDPI = () => {
      const dpr = Math.min(window.devicePixelRatio || 1, 2)
      const rect = canvas.getBoundingClientRect()
      if (rect.width > 0 && rect.height > 0) {
        canvas.width = Math.round(rect.width * dpr)
        canvas.height = Math.round(rect.height * dpr)
      }
    }

    updateCanvasDPI()
    window.addEventListener("resize", updateCanvasDPI)

    // Helper: Draw single blooming Acanthus petal that rolls outward over the rim
    const drawBloomingPetal = (
      r: number,
      radialAngle: number,
      tangentRollAngle: number,
      scale: number,
      curlFactor: number,
      flipRatio: number,
      opacity: number
    ) => {
      if (opacity <= 0.02) return

      ctx.save()
      ctx.translate(cx, cy)
      ctx.rotate(radialAngle) // 1. Point along radial ray
      ctx.translate(r, 0)     // 2. Travel outward radially
      ctx.rotate(tangentRollAngle) // 3. Align along circle circumference + outward roll tilt
      ctx.scale(scale, scale)
      ctx.globalAlpha = opacity

      // Solid pure white leaf body
      ctx.fillStyle = "#ffffff"
      ctx.strokeStyle = "#ffffff"
      ctx.lineWidth = 1.2
      ctx.lineCap = "round"
      ctx.lineJoin = "round"

      const outFlare = 16 * flipRatio
      const tipX = 52 + flipRatio * 14
      const tipY = -12 * curlFactor - outFlare

      ctx.beginPath()
      ctx.moveTo(0, 0)
      // Inner curved profile
      ctx.bezierCurveTo(8, 2, 16, 4, 26, 2)
      ctx.bezierCurveTo(22, 6, 28, 8, 38, 5)
      // Tip volute rolling outward over contour
      ctx.bezierCurveTo(tipX - 6, tipY * 0.7, tipX + 4, tipY * 0.9, tipX, tipY)
      ctx.bezierCurveTo(tipX + 6, tipY + 8, tipX - 4, tipY + 14, tipX - 12, tipY + 8)
      // Return outer sweep with acanthus dentil notches
      ctx.bezierCurveTo(tipX - 18, tipY + 2, 32, -6 - outFlare * 0.5, 20, -4)
      ctx.bezierCurveTo(14, -8, 6, -5, 0, 0)
      ctx.closePath()

      ctx.fill()
      ctx.stroke()

      // Fine black engraving midrib & feathery hatchings
      ctx.strokeStyle = "#020617"
      ctx.lineWidth = 1.6
      ctx.beginPath()
      ctx.moveTo(1, 0)
      ctx.quadraticCurveTo(20, 0, tipX - 6, tipY + 4)
      ctx.stroke()

      ctx.lineWidth = 0.85
      ctx.beginPath()
      ctx.moveTo(10, 1)
      ctx.lineTo(16, 4)
      ctx.moveTo(18, 1)
      ctx.lineTo(26, 5)
      ctx.moveTo(28, 2)
      ctx.lineTo(35, 5)

      ctx.moveTo(12, -2)
      ctx.lineTo(17, -5)
      ctx.moveTo(22, -2)
      ctx.lineTo(28, -6)
      ctx.stroke()

      ctx.restore()
    }

    // Main 60 FPS Render Loop for Living Pupil
    const render = () => {
      const dpr = Math.min(window.devicePixelRatio || 1, 2)
      const rect = canvas.getBoundingClientRect()
      if (rect.width > 0 && rect.height > 0) {
        const scale = (rect.width * dpr) / vSize
        ctx.save()
        ctx.scale(scale, scale)
        ctx.clearRect(0, 0, vSize, vSize)

        // Clip strictly within the pupil circle + gentle feather
        ctx.save()
        ctx.beginPath()
        ctx.arc(cx, cy, rimRadius + 18, 0, Math.PI * 2)
        ctx.closePath()
        ctx.clip()

        // 12 radial baroque acanthus arms, 4 continuous outward waves
        const numArms = 12
        const numWaves = 4

        for (let w = 0; w < numWaves; w++) {
          // Continuous outward phase [0, 1)
          const wavePhase = (time * 0.18 + w / numWaves) % 1.0

          // Radial expansion: starts at center core (r=12) and blooms over the rim (r=165)
          const currentR = 12 + wavePhase * (rimRadius + 20)

          // Leaf scale starts compact and blooms
          const petalScale = 0.38 + wavePhase * 0.72

          // Opacity envelope: brilliant at center, luminous across rim, dissolves softly past rim
          let opacity = 0.0
          if (wavePhase < 0.15) {
            opacity = wavePhase / 0.15
          } else if (wavePhase < 0.72) {
            opacity = 1.0
          } else {
            opacity = Math.max(0, 1.0 - (wavePhase - 0.72) / 0.28)
          }

          // Outward flip ratio ("從放大鏡的輪廓翻出來"):
          // Petal flips and curls backward as it reaches and crosses the circular rim!
          const flipRatio = Math.min(1.0, Math.max(0, (currentR - (rimRadius - 35)) / 45))
          const curl = 0.45 + Math.sin(wavePhase * Math.PI) * 0.8

          for (let i = 0; i < numArms; i++) {
            const baseAngle = (i / numArms) * Math.PI * 2
            // Logarithmic spiral drift + continuous gentle rotation
            const spiralDrift = Math.log(currentR + 10) * 0.75
            const totalAngle = baseAngle + spiralDrift + time * 0.06

            // Tangent along circumference + outward roll angle
            const tangentRoll = Math.PI * 0.5 + flipRatio * 0.48

            drawBloomingPetal(
              currentR,
              totalAngle,
              tangentRoll,
              petalScale,
              curl,
              flipRatio,
              opacity
            )
          }
        }

        ctx.restore() // End clip

        // Slender Glass Bezel Inner Stroke
        ctx.strokeStyle = "rgba(255, 255, 255, 0.85)"
        ctx.lineWidth = 2.0
        ctx.beginPath()
        ctx.arc(cx, cy, rimRadius - 2, 0, Math.PI * 2)
        ctx.stroke()

        // Convex Glass Optical Reflection Sweeps (Upper-Left arc)
        const glintShift = Math.sin(time * 0.75) * 0.12
        ctx.strokeStyle = "rgba(255, 255, 255, 0.95)"
        ctx.lineWidth = 3.2
        ctx.beginPath()
        ctx.arc(cx, cy, rimRadius - 14, Math.PI * (0.68 + glintShift), Math.PI * (0.95 + glintShift))
        ctx.stroke()

        ctx.strokeStyle = "rgba(255, 255, 255, 0.45)"
        ctx.lineWidth = 1.6
        ctx.beginPath()
        ctx.arc(cx, cy, rimRadius - 24, Math.PI * (0.74 + glintShift), Math.PI * (0.89 + glintShift))
        ctx.stroke()

        // Pure Crystal Center Focal Point Dot (Breathes gently)
        const dotPulse = 3.2 + Math.sin(time * 1.5) * 0.8
        ctx.fillStyle = "#ffffff"
        ctx.beginPath()
        ctx.arc(cx, cy, dotPulse, 0, Math.PI * 2)
        ctx.fill()

        ctx.restore()
      }

      time += 0.016
      animationFrameId = requestAnimationFrame(render)
    }

    render()

    return () => {
      cancelAnimationFrame(animationFrameId)
      window.removeEventListener("resize", updateCanvasDPI)
    }
  }, [])

  // Interactive 2.5D Parallax Mouse Handlers
  const handleMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
    const rect = containerRef.current?.getBoundingClientRect()
    if (!rect) return
    const normX = ((e.clientX - rect.left) / rect.width - 0.5) * 2
    const normY = ((e.clientY - rect.top) / rect.height - 0.5) * 2
    setParallax({ x: normX * 12, y: normY * 12 })
  }

  const handleMouseLeave = () => {
    setParallax({ x: 0, y: 0 })
  }

  return (
    <div
      ref={containerRef}
      onMouseMove={handleMouseMove}
      onMouseLeave={handleMouseLeave}
      className={`relative w-full max-w-[560px] aspect-square flex items-center justify-center select-none transition-transform duration-300 ease-out ${className}`}
      style={{
        transform: `perspective(1000px) rotateX(${-parallax.y * 0.3}deg) rotateY(${parallax.x * 0.3}deg)`,
      }}
    >
      {/* 1. Dynamic 60 FPS Living Outward-Unfurling Pupil Canvas */}
      <div
        className="absolute z-0 w-[30.5%] aspect-square flex items-center justify-center pointer-events-none transition-transform duration-150 ease-out"
        style={{
          left: "49.4%",
          top: "48.8%",
          transform: `translate(-50%, -50%) translate(${parallax.x * 0.4}px, ${parallax.y * 0.4}px)`,
        }}
      >
        <canvas
          ref={canvasRef}
          className="w-full h-full object-contain filter drop-shadow-[0_0_25px_rgba(255,255,255,0.3)]"
        />
      </div>

      {/* 2. Classical Baroque Copperplate Engraving Hero Artwork with Slender Handle */}
      <img
        src="/assets/images/brand-hero-slender-living.png"
        alt="反詐大師 · 古典全視透鏡之眼"
        className="w-full h-full object-contain relative z-10 pointer-events-none select-none filter drop-shadow-[0_0_40px_rgba(255,255,255,0.22)] transition-transform duration-200 ease-out"
        style={{
          transform: `translate(${parallax.x * 0.15}px, ${parallax.y * 0.15}px)`,
        }}
      />
    </div>
  )
}
