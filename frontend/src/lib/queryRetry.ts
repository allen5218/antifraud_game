import { ApiError } from "@/client"

/**
 * 查詢失敗要不要重試。4xx 是伺服器明確拒絕（檢測進行中、等級不足、找不到），
 * 重試只會讓玩家多看幾秒轉圈；斷線與 5xx 照預設最多重試三次。
 */
export function shouldRetryQuery(
  failureCount: number,
  error: unknown,
): boolean {
  if (error instanceof ApiError && error.status >= 400 && error.status < 500) {
    return false
  }
  return failureCount < 3
}
