import { INVITE_SESSION_PREFIX } from "@/lib/inviteSession"
import { classApi } from "./classroomApi"

const THIRTY_DAYS = 30 * 24 * 60 * 60 * 1000
const pending = new Map<string, Promise<string>>()

/**
 * 沒登入的人掃班級 QR：開免註冊帳號並加入班。憑證記在這個瀏覽器，
 * 同一個人再掃同一個 QR 會回到原本的帳號（登出時跟試測邀請一起清掉）。
 */
export async function redeemClassOnce(token: string): Promise<string> {
  const key = `${INVITE_SESSION_PREFIX}class:${token}`
  const saved = localStorage.getItem(key)
  if (saved) {
    try {
      const session = JSON.parse(saved) as {
        accessToken: string
        expiresAt: number
      }
      if (session.expiresAt > Date.now() && session.accessToken)
        return session.accessToken
    } catch {
      localStorage.removeItem(key)
    }
  }
  // StrictMode 重掛時共用同一個請求，避免開兩個帳號
  const existing = pending.get(token)
  if (existing) return existing
  const request = Promise.resolve(classApi.redeem(token))
    .then((result) => {
      localStorage.setItem(
        key,
        JSON.stringify({
          accessToken: result.access_token,
          expiresAt: Date.now() + THIRTY_DAYS,
        }),
      )
      return result.access_token
    })
    .finally(() => pending.delete(token))
  pending.set(token, request)
  return request
}
