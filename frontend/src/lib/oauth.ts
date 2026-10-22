/**
 * Google／LINE 登入的前端這一半(授權碼＋PKCE)。
 *
 * 出發前產生 code_verifier,只把它的 SHA-256(code_challenge)交給後端放進授權網址;
 * verifier 和後端給的 state 存在這個分頁的 sessionStorage,回呼頁比對 state 一致
 * 才把授權碼和 verifier 送回後端,擋掉別人拿自己的授權碼騙你登入成他的帳號。
 */

export type OAuthProvider = "google" | "line"

export const OAUTH_LABELS: Record<OAuthProvider, string> = {
  google: "用 Google 登入",
  line: "用 LINE 登入",
}

const STORAGE_KEY = "oauth_pending"

function base64url(bytes: Uint8Array): string {
  let text = ""
  for (const b of bytes) text += String.fromCharCode(b)
  return btoa(text).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "")
}

export function makeVerifier(): string {
  return base64url(crypto.getRandomValues(new Uint8Array(48)))
}

export async function challengeFor(verifier: string): Promise<string> {
  const digest = await crypto.subtle.digest(
    "SHA-256",
    new TextEncoder().encode(verifier),
  )
  return base64url(new Uint8Array(digest))
}

type Pending = { provider: OAuthProvider; state: string; verifier: string }

export function savePending(pending: Pending): void {
  sessionStorage.setItem(STORAGE_KEY, JSON.stringify(pending))
}

/** 取出並清掉;同一個授權碼只能用一次,重新整理回呼頁不會再送一次 */
export function takePending(): Pending | null {
  const raw = sessionStorage.getItem(STORAGE_KEY)
  sessionStorage.removeItem(STORAGE_KEY)
  if (!raw) return null
  try {
    return JSON.parse(raw) as Pending
  } catch {
    return null
  }
}

export const OAUTH_ERRORS: Record<string, string> = {
  email_in_use:
    "這個 Google 帳號的 Email 已經註冊過了，請改用 Email 和密碼登入。",
  oauth_state_invalid: "登入逾時或連結不對，請回登入頁再試一次。",
  oauth_failed: "沒有完成登入，請再試一次。",
  oauth_disabled: "目前沒有開放這種登入方式。",
}
