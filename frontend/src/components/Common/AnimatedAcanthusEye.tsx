interface AnimatedAcanthusEyeProps {
  className?: string
}

export function AnimatedAcanthusEye({
  className = "",
}: AnimatedAcanthusEyeProps) {
  return (
    <div
      className={`relative w-full max-w-[480px] aspect-square flex items-center justify-center select-none ${className}`}
    >
      {/* Crystalline Pure White Quartz Stone Slab with Intaglio Engraving */}
      <div className="relative w-full h-full rounded-2xl overflow-hidden shadow-[0_30px_70px_-15px_rgba(0,0,0,0.85),0_0_50px_rgba(255,255,255,0.08)] ring-1 ring-white/20">
        <img
          src="/assets/images/brand-hero-quartz-clean.jpg"
          alt="反詐大師 · 純白石英陰刻之眼"
          className="w-full h-full object-cover select-none pointer-events-none"
        />
        {/* Soft crystalline rim bevel */}
        <div className="absolute inset-0 rounded-2xl ring-1 ring-inset ring-white/30 pointer-events-none" />
      </div>
    </div>
  )
}
