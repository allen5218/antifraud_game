import { useQuery } from "@tanstack/react-query"
import { useState } from "react"
import { LoginService } from "@/client"
import { Button } from "@/components/ui/button"
import {
  challengeFor,
  makeVerifier,
  OAUTH_LABELS,
  type OAuthProvider,
  savePending,
} from "@/lib/oauth"

/** 後端有設金鑰的那幾家才顯示;一家都沒有就什麼都不畫 */
export function OAuthButtons() {
  const { data } = useQuery({
    queryKey: ["oauth", "providers"],
    queryFn: () => LoginService.listProviders(),
    staleTime: 5 * 60_000,
    retry: false,
  })
  const [busy, setBusy] = useState<OAuthProvider | null>(null)
  const [failed, setFailed] = useState(false)
  const providers = (data?.providers ?? []).filter(
    (p): p is OAuthProvider => p === "google" || p === "line",
  )
  if (providers.length === 0) return null

  const go = async (provider: OAuthProvider) => {
    setBusy(provider)
    setFailed(false)
    try {
      const verifier = makeVerifier()
      const { authorize_url, state } = await LoginService.start({
        provider,
        requestBody: { code_challenge: await challengeFor(verifier) },
      })
      savePending({ provider, state, verifier })
      window.location.assign(authorize_url)
    } catch {
      setBusy(null)
      setFailed(true)
    }
  }

  return (
    <div className="flex flex-col gap-2">
      <div className="flex items-center gap-2 text-xs text-muted-foreground">
        <span className="h-px flex-1 bg-border" />
        或
        <span className="h-px flex-1 bg-border" />
      </div>
      {providers.map((provider) => (
        <Button
          key={provider}
          type="button"
          variant="outline"
          disabled={busy !== null}
          onClick={() => go(provider)}
        >
          {busy === provider ? "前往登入…" : OAUTH_LABELS[provider]}
        </Button>
      ))}
      {failed && (
        <p role="alert" className="text-center text-xs text-scam">
          現在無法前往登入，請稍後再試。
        </p>
      )}
    </div>
  )
}
