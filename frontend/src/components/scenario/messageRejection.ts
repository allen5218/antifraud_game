/** 一則訊息的字數上限，和後端 app/scenario/input_guard.py 的 MAX_CHARS 一致 */
export const MESSAGE_MAX_CHARS = 200

/** 後端擋下玩家訊息時的提示；擋下的訊息不扣回覆次數。不是這類錯誤回傳 null */
export function messageRejection(code: string | undefined): string | null {
  switch (code) {
    case "message_blocked":
      return "這段訊息有不適合的內容，請換個說法。不扣回覆次數。"
    case "message_too_long":
      return `訊息太長了，請在 ${MESSAGE_MAX_CHARS} 字以內。`
    case "message_garbled":
      return "這段訊息看不懂，重複的字或特殊符號太多，請換個說法。"
    case "message_empty":
      return "訊息是空的，打點字再送出。"
    default:
      return null
  }
}
