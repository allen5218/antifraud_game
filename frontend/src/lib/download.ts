/** 讓瀏覽器下載一個網址（圖片的 data URL 或 Blob URL） */
export function downloadFile(href: string, filename: string) {
  const link = document.createElement("a")
  link.href = href
  link.download = filename
  link.click()
}

/** 下載 CSV；前面加 BOM，試算表直接開才認得繁體中文 */
export function downloadCsv(data: string, filename: string) {
  const blob = new Blob(["﻿", data.replace(/^﻿/, "")], {
    type: "text/csv;charset=utf-8",
  })
  const url = URL.createObjectURL(blob)
  downloadFile(url, filename)
  // 保留到瀏覽器開始下載後再釋放。
  window.setTimeout(() => URL.revokeObjectURL(url), 1000)
}
