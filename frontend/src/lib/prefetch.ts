import type { QueryClient, QueryKey } from "@tanstack/react-query"

type EnsureOptions = Parameters<QueryClient["ensureQueryData"]>[0]

/**
 * 換頁前先把下一頁要的資料抓進快取：已經有就不再抓、不等結果。
 * 抓失敗不在這裡處理，進頁面時頁面自己的查詢會重試或顯示錯誤。
 * 正式環境每個請求往返要零點幾秒到一秒，點下去才開始抓會讓選單感覺遲鈍。
 */
export function warmQueries(
  queryClient: QueryClient,
  // 各頁查詢的資料型別不同，這裡只轉交給 ensureQueryData
  queries: ReadonlyArray<{ queryKey: QueryKey }>,
): void {
  for (const query of queries) {
    queryClient.ensureQueryData(query as EnsureOptions).catch(() => {})
  }
}

const preloaded = new Set<string>()

/** 圖片先抓進瀏覽器快取，進頁面時就不會一張張冒出來。同一張只抓一次。 */
export function preloadImages(urls: string[]): void {
  for (const url of urls) {
    if (preloaded.has(url)) continue
    preloaded.add(url)
    const img = new Image()
    img.decoding = "async"
    img.src = url
  }
}

export function propertyArtSrc(svgKey: string): string {
  return `/assets/property/${svgKey}.webp`
}
