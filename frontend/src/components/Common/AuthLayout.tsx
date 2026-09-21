import { Appearance } from "@/components/Common/Appearance"

interface AuthLayoutProps {
  children: React.ReactNode
}

export function AuthLayout({ children }: AuthLayoutProps) {
  return (
    <div className="grid min-h-svh lg:grid-cols-2 bg-[#04060c] font-['Plus_Jakarta_Sans',sans-serif]">
      {/* Left: Form area — deep black luxury layout */}
      <div className="flex flex-col justify-between p-8 sm:p-12 md:p-16 bg-[#04060c] text-white selection:bg-white selection:text-black shadow-2xl lg:shadow-none z-10 border-r border-slate-800/60">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <img
              src="/assets/images/brand-icon-dark-v1.png"
              alt="反詐大師"
              className="h-8 w-auto object-contain brightness-0 invert"
            />
            <span className="font-extrabold text-sm tracking-wider text-white">
              反詐大師
            </span>
          </div>
          <Appearance />
        </div>
        <div className="flex flex-1 items-center justify-center my-8">
          <div className="w-full max-w-sm">{children}</div>
        </div>
        <footer className="text-center text-xs text-slate-500 py-2">
          反詐大師 &copy; {new Date().getFullYear()} · 全民防詐培訓平台
        </footer>
      </div>

      {/* Right: Full-screen pure white crystalline quartz intaglio carving */}
      <div className="relative hidden lg:block w-full h-full min-h-svh overflow-hidden bg-[#e8ecf1]">
        <img
          src="/assets/images/brand-hero-quartz-3d.jpg"
          alt="反詐大師 · 純白石英立體陰刻之眼"
          className="w-full h-full object-cover object-center select-none pointer-events-none filter drop-shadow-sm"
        />
        {/* Soft crystalline raking lighting ambient overlay */}
        <div className="absolute inset-0 bg-gradient-to-r from-black/20 via-transparent to-transparent pointer-events-none" />
      </div>
    </div>
  )
}
