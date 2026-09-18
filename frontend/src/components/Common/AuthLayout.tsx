import { Appearance } from "@/components/Common/Appearance"

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
              src="/assets/images/brand-icon-dark.png"
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

      {/* Right: Brand hero — deep dark slate with glowing Acanthus Magnifying Eye */}
      <div className="bg-slate-950 relative hidden lg:flex lg:flex-col lg:items-center lg:justify-center gap-6 p-12 overflow-hidden">
        {/* Subtle white radial glow behind logo */}
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,_rgba(255,255,255,0.07)_0%,_transparent_65%)] pointer-events-none" />
        <img
          src="/assets/images/brand-hero.png"
          alt="反詐大師"
          className="w-96 max-w-md h-auto relative z-10 drop-shadow-[0_0_45px_rgba(255,255,255,0.22)] transition-all hover:scale-[1.02] duration-700 rounded-3xl"
        />
        <div className="relative z-10 text-center">
          <h1 className="text-4xl font-extrabold text-white tracking-[0.2em]">
            反詐大師
          </h1>
          <p className="mt-3 text-sm text-slate-400 font-medium tracking-[0.35em]">
            洞見詐術 · 守護資產
          </p>
        </div>
      </div>
    </div>
  )
}
