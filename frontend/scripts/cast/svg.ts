// SVG 字串小工具：數字取一位小數、把幾個形狀用同一個顏色畫出來。

export const n = (v: number) => {
  const r = Math.round(v * 10) / 10
  return Object.is(r, -0) ? 0 : r
}

export type Shape =
  | { d: string }
  | { circle: [number, number, number] }
  | { ellipse: [number, number, number, number] }
  | { rect: [number, number, number, number, number?] }
  | { line: string; w: number }

/** 用同一個填色畫一組形狀；line 是以粗線畫成的形狀（手臂、腿） */
export function shapes(parts: Shape[], fill: string, extra = ""): string {
  return parts
    .map((p) => {
      if ("line" in p)
        return `<path d="${p.line}" fill="none" stroke="${fill}" stroke-width="${n(p.w)}" stroke-linecap="round" stroke-linejoin="round"${extra}/>`
      if ("circle" in p) {
        const [cx, cy, r] = p.circle
        return `<circle cx="${n(cx)}" cy="${n(cy)}" r="${n(r)}" fill="${fill}"${extra}/>`
      }
      if ("ellipse" in p) {
        const [cx, cy, rx, ry] = p.ellipse
        return `<ellipse cx="${n(cx)}" cy="${n(cy)}" rx="${n(rx)}" ry="${n(ry)}" fill="${fill}"${extra}/>`
      }
      if ("rect" in p) {
        const [x, y, w, h, rx] = p.rect
        return `<rect x="${n(x)}" y="${n(y)}" width="${n(w)}" height="${n(h)}"${rx ? ` rx="${n(rx)}"` : ""} fill="${fill}"${extra}/>`
      }
      return `<path d="${p.d}" fill="${fill}"${extra}/>`
    })
    .join("")
}

/** 一條線（不填色） */
export const stroke = (d: string, color: string, w: number, extra = "") =>
  `<path d="${d}" fill="none" stroke="${color}" stroke-width="${n(w)}" stroke-linecap="round" stroke-linejoin="round"${extra}/>`

/** 二頭身畫風的陰影：同樣的形狀往右下偏一點、用深一階的顏色墊在底下 */
export const withShade = (
  parts: Shape[],
  fill: string,
  shade: string,
  dx = 2,
  dy = 4,
) =>
  `<g transform="translate(${dx} ${dy})">${shapes(parts, shade)}</g>${shapes(parts, fill)}`

/** 輸出一個 SVG 檔（固定顏色，不跟主題換色；CardArt 用 <image> 疊起來） */
export function svgDoc(w: number, h: number, body: string): string {
  return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${w} ${h}" width="${w}" height="${h}">${body}</svg>\n`
}

/** 把路徑字串裡多餘的空白收掉 */
export const compact = (d: string) => d.replace(/\s+/g, " ").trim()

/** 以固定種子產生的亂數，讓每次產生的圖都一樣 */
export function seeded(seed: number) {
  let s = seed >>> 0
  return () => {
    s = (s * 1664525 + 1013904223) >>> 0
    return s / 2 ** 32
  }
}
