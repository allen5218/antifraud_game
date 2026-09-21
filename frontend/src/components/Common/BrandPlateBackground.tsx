export function BrandPlateBackground() {
  return (
    <div className="absolute inset-0 pointer-events-none overflow-hidden select-none">
      <svg
        className="w-full h-full object-cover"
        viewBox="0 0 720 900"
        preserveAspectRatio="xMidYMid slice"
        xmlns="http://www.w3.org/2000/svg"
      >
        <defs>
          {/* Deep slate-to-obsidian vignette glow */}
          <radialGradient id="plateCoreGlow" cx="50%" cy="50%" r="65%">
            <stop offset="0%" stopColor="#1e293b" stopOpacity="0.55" />
            <stop offset="45%" stopColor="#0f172a" stopOpacity="0.3" />
            <stop offset="100%" stopColor="#020617" stopOpacity="0" />
          </radialGradient>

          {/* Micro-engraved dot matrix watermark */}
          <pattern
            id="securityDots"
            width="28"
            height="28"
            patternUnits="userSpaceOnUse"
          >
            <circle cx="14" cy="14" r="0.6" fill="rgba(255, 255, 255, 0.04)" />
          </pattern>
        </defs>

        {/* Ambient atmospheric backlight */}
        <rect width="100%" height="100%" fill="url(#plateCoreGlow)" />

        {/* Micro-dot security watermark field */}
        <rect width="100%" height="100%" fill="url(#securityDots)" />

        {/* Outer Copperplate Archival Border */}
        <rect
          x="32"
          y="32"
          width="656"
          height="836"
          fill="none"
          stroke="rgba(255, 255, 255, 0.08)"
          strokeWidth="1"
        />

        {/* Inner Fine Guilloché / Ruled Border */}
        <rect
          x="42"
          y="42"
          width="636"
          height="816"
          fill="none"
          stroke="rgba(255, 255, 255, 0.04)"
          strokeWidth="0.75"
          strokeDasharray="4 4"
        />

        {/* Classical Inset Corner Flourishes */}
        <g stroke="rgba(255, 255, 255, 0.12)" strokeWidth="1" fill="none">
          {/* Top Left */}
          <path d="M32 54 L54 32 M38 54 L54 38" />
          <circle cx="48" cy="48" r="1.5" fill="rgba(255, 255, 255, 0.25)" />

          {/* Top Right */}
          <path d="M688 54 L666 32 M682 54 L666 38" />
          <circle cx="672" cy="48" r="1.5" fill="rgba(255, 255, 255, 0.25)" />

          {/* Bottom Left */}
          <path d="M32 846 L54 868 M38 846 L54 862" />
          <circle cx="48" cy="852" r="1.5" fill="rgba(255, 255, 255, 0.25)" />

          {/* Bottom Right */}
          <path d="M688 846 L666 868 M682 846 L666 862" />
          <circle cx="672" cy="852" r="1.5" fill="rgba(255, 255, 255, 0.25)" />
        </g>

        {/* Antique Celestial Astrolabe / Coordinate Rings centered at (360, 450) */}
        <g
          transform="translate(360, 450)"
          stroke="rgba(255, 255, 255, 0.065)"
          fill="none"
        >
          {/* Concentric Spherical / Coordinate Circles */}
          <circle r="325" strokeWidth="0.75" strokeDasharray="3 6" />
          <circle r="295" strokeWidth="0.5" />
          <circle r="291" strokeWidth="0.5" strokeDasharray="1 4" />
          <circle r="255" strokeWidth="0.5" strokeDasharray="8 8" />
          <circle r="200" strokeWidth="0.4" strokeDasharray="2 4" />

          {/* Meridian Crosshairs (Cardinal Axes) */}
          <line
            x1="-345"
            y1="0"
            x2="345"
            y2="0"
            strokeWidth="0.5"
            strokeDasharray="4 8"
          />
          <line
            x1="0"
            y1="-345"
            x2="0"
            y2="345"
            strokeWidth="0.5"
            strokeDasharray="4 8"
          />

          {/* Diagonal Astrological / Geometric Ray Guides (45 deg) */}
          <line
            x1="-245"
            y1="-245"
            x2="245"
            y2="245"
            strokeWidth="0.4"
            strokeDasharray="2 8"
          />
          <line
            x1="-245"
            y1="245"
            x2="245"
            y2="-245"
            strokeWidth="0.4"
            strokeDasharray="2 8"
          />

          {/* Quadrant Micro Degree Tick Marks along the 295px circle */}
          <g stroke="rgba(255, 255, 255, 0.09)" strokeWidth="0.75">
            <line x1="290" y1="0" x2="300" y2="0" />
            <line x1="-290" y1="0" x2="-300" y2="0" />
            <line x1="0" y1="290" x2="0" y2="300" />
            <line x1="0" y1="-290" x2="0" y2="-300" />

            {/* 30-degree, 60-degree ticks */}
            <line x1="255.5" y1="147.5" x2="264.1" y2="152.5" />
            <line x1="147.5" y1="255.5" x2="152.5" y2="264.1" />
            <line x1="-147.5" y1="255.5" x2="-152.5" y2="264.1" />
            <line x1="-255.5" y1="147.5" x2="-264.1" y2="152.5" />
            <line x1="-255.5" y1="-147.5" x2="-264.1" y2="-152.5" />
            <line x1="-147.5" y1="-255.5" x2="-152.5" y2="-264.1" />
            <line x1="147.5" y1="-255.5" x2="152.5" y2="-264.1" />
            <line x1="255.5" y1="-147.5" x2="264.1" y2="-152.5" />
          </g>
        </g>
      </svg>
    </div>
  )
}
