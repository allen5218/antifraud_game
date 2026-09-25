import { type RefObject, useEffect, useRef } from "react"

/**
 * 自己畫的對話框(aria-modal)打開時把焦點移進去,關掉時還給原本的元素。
 * 不移的話,鍵盤使用者按 Tab 會跑到背後的輸入框,螢幕閱讀器也不會念出對話框。
 * 對話框本身要加 tabIndex={-1} 才能接住焦點。
 */
export function useDialogFocus<T extends HTMLElement>(
  open: boolean,
): RefObject<T | null> {
  const ref = useRef<T>(null)
  useEffect(() => {
    if (!open) return
    const previous = document.activeElement as HTMLElement | null
    ref.current?.focus()
    return () => previous?.focus?.()
  }, [open])
  return ref
}
