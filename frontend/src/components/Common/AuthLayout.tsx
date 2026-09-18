import { Appearance } from "@/components/Common/Appearance"
import { AnimatedAcanthusEye } from "@/components/Common/AnimatedAcanthusEye"
import { BrandPlateBackground } from "@/components/Common/BrandPlateBackground"

interface AuthLayoutProps {
  children: React.ReactNode
}

export function AuthLayout({ children }: AuthLayoutProps) {
  return (
    <div className="grid min-h-svh lg:grid-cols-2 bg-slate-950 font-['Plus_Jakarta_Sans',sans-serif]">
      {/* Left: Form area — clean Cloudflare white layout */}
      <div className="flex flex-col justify-between p-8 sm:p-12 md:p-16 bg-white text-slate-900 selection:bg-slate-900 selection:text-white shadow-2xl lg:shadow-none z-10">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <img
              src="/assets/images/brand-icon-dark-v1.png"
              alt="反詐大師"
              className="h-8 w-auto object-contain"
            />
            <span className="font-extrabold text-sm tracking-wider text-slate-900">
              反詐大師
            </span>
          </div>
          <Appearance />
        </div>
        <div className="flex flex-1 items-center justify-center my-8">
          <div className="w-full max-w-sm">{children}</div>
        </div>
        <footer className="text-center text-xs text-slate-400 py-2">
          反詐大師 &copy; {new Date().getFullYear()} · 全民防詐培訓平台
        </footer>
      </div>

      {/* Right: Brand hero — classical copperplate archival plate with balanced proportions */}
      <div className="bg-slate-950 relative hidden lg:flex lg:flex-col lg:items-center lg:justify-center p-12 overflow-hidden">
        {/* Archival copperplate print background with celestial coordinates & double border */}
        <BrandPlateBackground />
        
        {/* Classical Magnifying Eye master artwork — elegant scaled proportion */}
        <AnimatedAcanthusEye className="w-[380px] max-w-md h-auto relative z-10" />
      </div>
    </div>
  )
}
