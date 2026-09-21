/**
 * Error normalization and centralized auth error management.
 * Conforms to Brief 13: Honest Auth & Runtime States.
 */

export type ErrorCategory = "auth" | "version" | "network" | "unknown"

export interface NormalizedError {
  category: ErrorCategory
  status?: number
  message: string
  action: "login" | "reload" | "retry"
  canRetry: boolean
  originalError: unknown
}

export function isDemoMode(): boolean {
  if (typeof window === "undefined") return false
  return (
    window.localStorage.getItem("demo_mode") === "true" ||
    (typeof import.meta !== "undefined" && import.meta.env?.VITE_DEMO_MODE === "true")
  )
}

export function normalizeError(err: unknown): NormalizedError {
  let status: number | undefined
  let message = ""

  if (err && typeof err === "object") {
    // 1. ApiError or standard response object
    if ("status" in err && typeof (err as { status: unknown }).status === "number") {
      status = (err as { status: number }).status
    } else if (
      "response" in err &&
      err.response &&
      typeof err.response === "object" &&
      "status" in err.response &&
      typeof (err.response as { status: unknown }).status === "number"
    ) {
      status = (err.response as { status: number }).status
    }

    // 2. Extract error message or detail
    if ("body" in err && err.body && typeof err.body === "object") {
      const detail = (err.body as { detail?: unknown }).detail
      if (typeof detail === "string") {
        message = detail
      } else if (
        Array.isArray(detail) &&
        detail.length > 0 &&
        typeof detail[0] === "object" &&
        detail[0]?.msg
      ) {
        message = String(detail[0].msg)
      }
    }

    if (!message && "message" in err && typeof (err as { message: unknown }).message === "string") {
      message = (err as { message: string }).message
    }
  }

  // Only invalid authentication ends the session; locked resources may return 403.
  if (status === 401) {
    return {
      category: "auth",
      status,
      message: message || "登入憑證已失效，請重新登入",
      action: "login",
      canRetry: false,
      originalError: err,
    }
  }

  // 404: Version mismatch or missing endpoint/resource
  if (status === 404) {
    return {
      category: "version",
      status,
      message: message || "系統版本不相符或伺服器資源已更新，請重新載入網頁",
      action: "reload",
      canRetry: true,
      originalError: err,
    }
  }

  // 5xx or offline / NetworkError
  const isOffline = typeof navigator !== "undefined" && !navigator.onLine
  const isServerError = status !== undefined && status >= 500
  const isNetworkMessage = /network|failed to fetch|load failed|econnrefused/i.test(message)

  if (isOffline || isServerError || isNetworkMessage) {
    return {
      category: "network",
      status,
      message: message || "伺服器暫時無法連線，請檢查網路連線或稍後重試",
      action: "retry",
      canRetry: true,
      originalError: err,
    }
  }

  return {
    category: "unknown",
    status,
    message: message || "發生未預期的錯誤，請稍後再試",
    action: "retry",
    canRetry: true,
    originalError: err,
  }
}

/**
 * Handle authentication failure by clearing stored auth credentials and redirecting to login.
 * Guarantees NO redirect loops if already on the login page.
 */
export function handleAuthFailure(err?: unknown): boolean {
  if (err !== undefined) {
    const norm = normalizeError(err)
    if (norm.category !== "auth") {
      return false
    }
  }

  if (typeof window !== "undefined") {
    try {
      window.localStorage.removeItem("access_token")
      window.localStorage.removeItem("demo_mode")
    } catch {
      // Ignore storage errors in restricted contexts
    }

    // Prevent redirect loops
    if (window.location.pathname !== "/login") {
      window.location.assign("/login")
    }
  }

  return true
}
