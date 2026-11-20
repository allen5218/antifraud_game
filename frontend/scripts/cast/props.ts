// 九個道具，畫布 120×120。和角色同一套畫風：沒有描邊、深一階的顏色往右下偏一點當陰影。

import type { PropId } from "../../src/components/cards/cardArtManifest"
import { INK } from "./rig"
import { n, seeded, shapes, withShade } from "./svg"

const WHITE = "#FFFDF8"
const TEAL = "#6F9A92"
const TEAL_D = "#5A817A"
const RED = "#D2694F"
const GOLD = "#E2B45A"
const GOLD_D = "#C99A3E"

const groundShadow = (cx: number, cy: number, rx: number) =>
  shapes([{ ellipse: [cx, cy, rx, 4] }], INK, ' opacity=".12"')

function phone(): string {
  return `${withShade([{ rect: [34, 10, 52, 100, 10] }], "#454A57", "#33363F", 3, 3)}${shapes([{ rect: [39, 20, 42, 78, 5] }], "#E8EFF0")}${shapes([{ rect: [52, 14, 16, 3, 1.5] }], "#E8EFF0", ' opacity=".5"')}${shapes([{ rect: [44, 30, 26, 11, 5.5] }, { rect: [44, 62, 20, 11, 5.5] }], "#FFFFFF")}${shapes([{ rect: [50, 46, 26, 11, 5.5] }], "#9CC3A0")}${shapes([{ rect: [52, 102, 16, 2.6, 1.3] }], "#E8EFF0", ' opacity=".6"')}${shapes([{ circle: [84, 14, 8] }], RED)}`
}

function chat(): string {
  const back = `M30 16h36a16 16 0 0 1 16 16v14a16 16 0 0 1-16 16H34l-12 10 3-12a16 16 0 0 1-11-14V32a16 16 0 0 1 16-16Z`
  const front = `M56 50h36a16 16 0 0 1 16 16v12a16 16 0 0 1-16 16h-2l3 12-12-12H56a16 16 0 0 1-16-16V66a16 16 0 0 1 16-16Z`
  return `${withShade([{ d: back }], TEAL, TEAL_D, 2, 3)}${shapes(
    [{ circle: [34, 39, 4] }, { circle: [48, 39, 4] }, { circle: [62, 39, 4] }],
    WHITE,
  )}${withShade([{ d: front }], WHITE, "#D9D1C4", 2, 3)}${shapes(
    [{ rect: [52, 62, 40, 5, 2.5] }, { rect: [52, 74, 28, 5, 2.5] }],
    "#C9C2B6",
  )}`
}

/** ATM 本體，場景 atm-corner 也拿來用 */
export function atmBody(): string {
  let s = groundShadow(60, 114, 44)
  s += shapes(
    [{ d: "M24 22h72v86a4 4 0 0 1-4 4H28a4 4 0 0 1-4-4Z" }],
    "#ECE7DF",
  )
  s += shapes([{ d: "M84 26h10v82a3 3 0 0 1-3 3h-7Z" }], "#D0C9BD")
  s += shapes([{ d: "M22 8a5 5 0 0 1 5-5h66a5 5 0 0 1 5 5v18H22Z" }], TEAL)
  s += shapes([{ rect: [46, 10, 28, 9, 2.5] }], "#FFFFFF", ' opacity=".9"')
  s += shapes([{ rect: [49, 13, 22, 2, 1] }], TEAL)
  s += shapes([{ rect: [30, 33, 52, 30, 3] }], "#9FC9C6")
  s += shapes(
    [{ rect: [36, 39, 22, 4, 2] }, { rect: [62, 53, 16, 6, 2] }],
    "#FFFFFF",
    ' opacity=".85"',
  )
  s += shapes([{ rect: [36, 47, 32, 4, 2] }], "#FFFFFF", ' opacity=".6"')
  s += shapes([{ rect: [31, 69, 34, 34, 3] }], "#D0C9BD")
  const keys: [number, number, number, number, number][] = []
  for (let row = 0; row < 3; row++)
    for (let col = 0; col < 3; col++)
      keys.push([34 + col * 10, 72 + row * 7, 8, 5, 1.4])
  s += shapes(
    keys.map((k) => ({ rect: k })),
    "#FBF8F2",
  )
  // 台灣 ATM 鍵盤最下排：取消紅、更正黃、確認綠
  s += shapes([{ rect: [34, 94, 8, 5, 1.4] }], RED)
  s += shapes([{ rect: [44, 94, 8, 5, 1.4] }], GOLD)
  s += shapes([{ rect: [54, 94, 8, 5, 1.4] }], "#7FAE7C")
  s += shapes([{ rect: [70, 72, 18, 5, 2] }, { rect: [69, 88, 20, 8, 2] }], INK)
  s += shapes([{ circle: [91, 74.5, 1.6] }], "#7FAE7C")
  s += shapes([{ rect: [72, 90, 14, 2, 1] }], "#FFFFFF", ' opacity=".35"')
  return s
}

function parcel(): string {
  return `${groundShadow(58, 104, 46)}${shapes([{ d: "M18 44h62v56H18Z" }], "#D9A86C")}${shapes([{ d: "M80 44l20-14v56l-20 14Z" }], "#C08F55")}${shapes([{ d: "M18 44l20-14h62L80 44Z" }], "#E8BE85")}${shapes(
    [{ d: "M42 44l20-14h10L52 44Z" }, { rect: [42, 44, 10, 56] }],
    "#F1DDB2",
  )}${shapes([{ rect: [56, 64, 18, 14, 1.5] }], WHITE)}${shapes(
    [{ rect: [59, 68, 12, 2, 1] }, { rect: [59, 72, 8, 2, 1] }],
    "#C9C2B6",
  )}`
}

function card(): string {
  const c = (x: number, y: number, fill: string, shade: string, rot: number) =>
    `<g transform="rotate(${rot} ${x + 34} ${y + 22})">${withShade([{ rect: [x, y, 68, 44, 6] }], fill, shade, 2, 3)}${shapes([{ rect: [x + 8, y + 14, 13, 10, 2] }], GOLD)}${shapes([{ rect: [x + 8, y + 31, 34, 4, 2] }], "#FFFFFF", ' opacity=".75"')}${shapes([{ rect: [x + 46, y + 31, 14, 4, 2] }], "#FFFFFF", ' opacity=".5"')}${shapes([{ d: `M${x + 48} ${y + 10}q6-4 12 0q-6 4-12 0Z` }], "#FFFFFF", ' opacity=".7"')}</g>`
  return `${c(14, 24, RED, "#B0533C", -12)}${c(36, 50, "#5E8FB0", "#4A7697", 6)}`
}

function laptop(): string {
  return `${withShade([{ rect: [24, 20, 72, 52, 5] }], "#454A57", "#33363F", 2, 3)}${shapes([{ rect: [29, 25, 62, 42, 2] }], "#CFE3E8")}${shapes([{ rect: [29, 25, 62, 8, 2] }], TEAL)}${shapes(
    [
      { rect: [34, 38, 24, 4, 2] },
      { rect: [34, 46, 40, 4, 2] },
      { rect: [34, 54, 30, 4, 2] },
    ],
    "#FFFFFF",
  )}${shapes([{ d: "M18 74h84l8 12a3 3 0 0 1-3 4H13a3 3 0 0 1-3-4Z" }], "#C9CDD3")}${shapes([{ d: "M10 86h100v1a3 3 0 0 1-3 3H13a3 3 0 0 1-3-3Z" }], "#AEB3BA")}${shapes([{ rect: [50, 77, 20, 4, 2] }], "#AEB3BA")}`
}

function money(): string {
  const note = (
    rot: number,
    dx: number,
    dy: number,
    fill: string,
    shade: string,
  ) =>
    `<g transform="translate(${dx} ${dy}) rotate(${rot} 54 52)">${withShade([{ rect: [16, 34, 76, 38, 4] }], fill, shade, 2, 3)}${shapes([{ rect: [21, 39, 66, 28, 3] }], "#FFFFFF", ' opacity=".25"')}${shapes([{ circle: [38, 53, 8] }], "#FFFFFF", ' opacity=".55"')}${shapes([{ rect: [54, 46, 26, 4, 2] }, { rect: [54, 56, 18, 4, 2] }], "#FFFFFF", ' opacity=".55"')}</g>`
  const coin = (x: number, y: number) =>
    `${shapes([{ circle: [x + 1.5, y + 2.5, 11] }], GOLD_D)}${shapes([{ circle: [x, y, 11] }], GOLD)}${shapes([{ circle: [x, y, 6.5] }], GOLD_D, ' opacity=".55"')}`
  return `${note(-10, -2, -8, "#8FB7D9", "#759DC0")}${note(-2, 0, 2, "#8FB7D9", "#759DC0")}${note(6, 2, 12, "#7FAE9A", "#679682")}${coin(90, 92)}${coin(74, 100)}`
}

function house(): string {
  return `${groundShadow(60, 106, 46)}${shapes([{ rect: [78, 26, 11, 22] }], "#A6583B")}${shapes([{ rect: [24, 54, 72, 50] }], "#F2E2C8")}${shapes([{ rect: [78, 54, 18, 50] }], "#E4CFAE")}${withShade([{ d: "M14 60L60 22l46 38a4 4 0 0 1-5 6L60 33 19 66a4 4 0 0 1-5-6Z" }], "#C9714F", "#A6583B", 0, 3)}${shapes([{ rect: [51, 74, 18, 30, 3] }], "#8B5E3F")}${shapes([{ circle: [64, 90, 1.8] }], GOLD)}${shapes(
    [{ rect: [31, 66, 14, 13, 2] }, { rect: [76, 66, 14, 13, 2] }],
    "#CFE3EC",
  )}${shapes([{ rect: [37, 66, 2, 13] }, { rect: [82, 66, 2, 13] }], WHITE)}`
}

function qr(): string {
  // 長得像 QR code 但掃不出東西：三個定位方塊＋固定種子的亂數點
  const size = 21
  const cell = 3.2
  const ox = 26.4
  const oy = 26.4
  const rnd = seeded(20261120)
  const dark: boolean[][] = []
  for (let y = 0; y < size; y++) {
    dark.push([])
    for (let x = 0; x < size; x++) dark[y].push(rnd() < 0.46)
  }
  const finder = (fx: number, fy: number) => {
    for (let y = -1; y <= 7; y++)
      for (let x = -1; x <= 7; x++) {
        const gx = fx + x
        const gy = fy + y
        if (gx < 0 || gy < 0 || gx >= size || gy >= size) continue
        const ring = Math.max(Math.abs(x - 3), Math.abs(y - 3))
        dark[gy][gx] = ring === 3 || ring <= 1
      }
  }
  finder(0, 0)
  finder(14, 0)
  finder(0, 14)
  let d = ""
  for (let y = 0; y < size; y++) {
    let x = 0
    while (x < size) {
      if (!dark[y][x]) {
        x++
        continue
      }
      let run = 1
      while (x + run < size && dark[y][x + run]) run++
      d += `M${n(ox + x * cell)} ${n(oy + y * cell)}h${n(run * cell)}v${cell}h${n(-run * cell)}Z`
      x += run
    }
  }
  return `${withShade([{ rect: [18, 18, 84, 84, 8] }], WHITE, "#D9D1C4", 2, 3)}<path d="${d}" fill="${INK}"/>`
}

export const PROPS: Record<PropId, () => string> = {
  phone,
  chat,
  atm: atmBody,
  parcel,
  card,
  laptop,
  money,
  house,
  qr,
}
