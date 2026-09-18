import { Appearance } from "@/components/Common/Appearance"
import { Logo } from "@/components/Common/Logo"

interface AuthLayoutProps {
  children: React.ReactNode
}

export function AuthLayout({ children }: AuthLayoutProps) {
  return (
    <div className="grid min-h-svh lg:grid-cols-2">
      {/* Left: Form area — clean white */}
      <div className="flex flex-col p-6 md:p-10">
        <div className="flex items-center justify-between">
          <Logo variant="icon" className="size-8" asLink={false} />
          <Appearance />
        </div>
        <div className="flex flex-1 items-center justify-center">
          <div className="w-full max-w-sm">{children}</div>
        </div>
        <footer className="text-center text-xs text-muted-foreground py-4">
          反詐大師 &copy; {new Date().getFullYear()}
        </footer>
      </div>

      {/* Right: Brand hero — dark slate */}
      <div className="bg-slate-950 relative hidden lg:flex lg:flex-col lg:items-center lg:justify-center gap-6 p-12">
        {/* Subtle radial glow behind logo */}
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,_rgba(255,255,255,0.06)_0%,_transparent_65%)]" />
        <img
          src="/assets/images/brand-icon-light.svg"
          alt="反詐大師"
          className="w-72 h-auto relative z-10 drop-shadow-[0_0_35px_rgba(255,255,255,0.2)] transition-all hover:scale-105 duration-500"
        />
        <div className="relative z-10 text-center">
          <h1 className="text-4xl font-extrabold text-white tracking-widest">反詐大師</h1>
          <p className="mt-3 text-sm text-slate-400 font-medium tracking-[0.3em]">洞見詐術 · 守護資產</p>
        </div>
      </div>
    </div>
  )
}
