import { AxiosError } from "axios"
import type { ApiError } from "./client"

/**
 * 後端(template 的帳號相關 API)回的錯誤訊息是英文。API 與後端測試都依賴原文,
 * 所以在顯示這一層翻成中文;沒列到的訊息照原文顯示,不會被吞掉。
 */
const BACKEND_MESSAGES: Record<string, string> = {
  "Incorrect email or password": "電子郵件或密碼不正確",
  "Inactive user": "這個帳號已停用",
  "Invalid token": "連結已失效，請重新申請",
  "Incorrect password": "目前的密碼不正確",
  "New password cannot be the same as the current one":
    "新密碼不能和目前的一樣",
  "The user with this email already exists in the system":
    "這個電子郵件已經註冊過了",
  "User with this email already exists": "這個電子郵件已經註冊過了",
  "The user with this username does not exist in the system":
    "找不到這個電子郵件的帳號",
  "Super users are not allowed to delete themselves": "管理員帳號不能刪除自己",
  "The user doesn't have enough privileges": "你沒有權限做這件事",
  "Could not validate credentials": "登入已過期，請重新登入",
  "User not found": "找不到這個帳號",
  "Network Error": "連不上伺服器，請檢查網路",
}

export function translateMessage(message: string): string {
  return BACKEND_MESSAGES[message.replace(/\.$/, "")] ?? message
}

function extractErrorMessage(err: ApiError): string {
  if (err instanceof AxiosError) {
    return translateMessage(err.message)
  }

  const errDetail = (err.body as any)?.detail
  if (Array.isArray(errDetail) && errDetail.length > 0) {
    return translateMessage(errDetail[0].msg)
  }
  return errDetail ? translateMessage(errDetail) : "發生錯誤，請稍後再試"
}

export const handleError = function (
  this: (msg: string) => void,
  err: ApiError,
) {
  const errorMessage = extractErrorMessage(err)
  this(errorMessage)
}

export const getInitials = (name: string): string => {
  return name
    .split(" ")
    .slice(0, 2)
    .map((word) => word[0])
    .join("")
    .toUpperCase()
}
