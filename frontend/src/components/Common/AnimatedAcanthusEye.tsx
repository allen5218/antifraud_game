interface AnimatedAcanthusEyeProps {
  className?: string
}

export function AnimatedAcanthusEye({ className = "" }: AnimatedAcanthusEyeProps) {
  return (
    <div
      className={`relative w-full max-w-[560px] aspect-square flex items-center justify-center select-none ${className}`}
    >
      <img
        src="/assets/images/brand-hero-master.png"
        alt="反詐大師 · 古典全視透鏡之眼"
        className="w-full h-full object-contain filter drop-shadow-[0_0_40px_rgba(255,255,255,0.22)] select-none pointer-events-none"
      />
    </div>
  )
}
