/** 邀請頁暫存的訪客憑證。同一個人重開邀請網址時可以接著玩，登出時要全部清掉。 */
export const INVITE_SESSION_PREFIX = "invite_session:"

export function clearInviteSessions(storage: Storage = localStorage): void {
  const keys: string[] = []
  for (let i = 0; i < storage.length; i++) {
    const key = storage.key(i)
    if (key?.startsWith(INVITE_SESSION_PREFIX)) keys.push(key)
  }
  for (const key of keys) storage.removeItem(key)
}
