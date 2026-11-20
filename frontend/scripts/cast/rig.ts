// 二頭身角色的骨架：所有角色共用同一副身體、臉和五種姿勢，只換膚色、髮型、衣服、配件。
// 畫布 200×240，頭中心 (100, 80)、半徑 52，腳底在 y=226。

import type { Pose } from "../../src/components/cards/cardArtManifest"
import { compact, n, type Shape, shapes, stroke, withShade } from "./svg"

export const INK = "#3A2C26"
const BLUSH = "#EE9A86"
const SWEAT = "#8EC5E0"
const TONGUE = "#E8737A"
const WHITE = "#FFFDF8"
const PHONE = "#454A57"
const PHONE_SCREEN = "#E8EFF0"
const GOLD = "#E2B44C"

export const G = {
  cx: 100,
  cy: 80,
  r: 52,
  shY: 134,
  hemY: 194,
  shHalf: 28,
  hemHalf: 34,
  legTop: 188,
  footY: 226,
  armW: 13,
}

export type HairStyle =
  | "perm"
  | "bald"
  | "bob"
  | "spiky"
  | "slick"
  | "ponytail"
  | "long"
  | "wavy"
  | "bun"
  | "capped"

export type TopKind =
  | "cardigan"
  | "shirt"
  | "blazer"
  | "school"
  | "polo"
  | "apron"
  | "sweater"
  | "jacket"
  | "vest"
  | "uniform"

export type Extra =
  | "headset"
  | "police-cap"
  | "backpack"
  | "lanyard"
  | "nametag"

export interface CharacterSpec {
  skin: string
  skinShade: string
  hair: string
  hairShade: string
  hairStyle: HairStyle
  brow?: string
  thickBrows?: boolean
  lashes?: boolean
  glasses?: string
  mustache?: string
  /** 頭髮沒蓋住耳朵的角色要畫耳朵 */
  ears?: boolean
  top: string
  topShade: string
  topKind: TopKind
  /** 裡面的上衣或襯衫 */
  inner?: string
  /** 袖子顏色（預設同上衣） */
  sleeve?: string
  shortSleeves?: boolean
  /** 領帶、領巾、掛繩、圍裙、背包 */
  accent?: string
  accentShade?: string
  bottom: "pants" | "shorts" | "skirt"
  legs: string
  legsShade: string
  shoes: string
  extras?: Extra[]
}

// ---- 以頭為單位的座標：(0, 0) 是頭的中心，1 是頭的半徑 ----
const hx = (x: number) => G.cx + x * G.r
const hy = (y: number) => G.cy + y * G.r
/** 把以頭為單位的路徑（只用 M L C Q Z 與成對座標）換成畫布座標 */
const hpath = (d: string) =>
  compact(
    d.replace(
      /(-?\d*\.?\d+)\s+(-?\d*\.?\d+)/g,
      (_, x: string, y: string) => `${n(hx(Number(x)))} ${n(hy(Number(y)))}`,
    ),
  )
const D = (d: string): Shape => ({ d: hpath(d) })
const C = (x: number, y: number, rad: number): Shape => ({
  circle: [hx(x), hy(y), rad * G.r],
})
const E = (x: number, y: number, rx: number, ry: number): Shape => ({
  ellipse: [hx(x), hy(y), rx * G.r, ry * G.r],
})

// ---------------------------------------------------------------- 頭髮

interface HairLayers {
  /** 頭和身體後面（長髮、包頭、馬尾） */
  back: string
  /** 頭髮的陰影，畫在頭之前，從頭髮邊緣露出一點 */
  under: string
  /** 蓋在頭上 */
  front: string
}

function permParts(): Shape[] {
  const parts: Shape[] = [
    D(
      "M -1 0.05 C -1.04 -0.75 -0.58 -1.08 0 -1.08 C 0.58 -1.08 1.04 -0.75 1 0.05 Q 0.62 -0.6 0 -0.52 Q -0.62 -0.6 -1 0.05 Z",
    ),
    E(0, -0.45, 0.92, 0.55),
  ]
  for (let i = 0; i <= 8; i++) {
    const a = ((190 + i * 20) * Math.PI) / 180
    parts.push(C(Math.cos(a) * 0.98, -0.08 + Math.sin(a) * 0.98, 0.27))
  }
  parts.push(C(-1, 0.18, 0.22), C(1, 0.18, 0.22))
  parts.push(C(-0.42, -0.55, 0.24), C(0.05, -0.62, 0.26), C(0.5, -0.52, 0.22))
  return parts
}

function hairLayers(s: CharacterSpec): HairLayers {
  const c = s.hair
  const sh = s.hairShade
  const front = (parts: Shape[]) => ({
    under: `<g transform="translate(2 4)">${shapes(parts, sh)}</g>`,
    front: shapes(parts, c),
  })
  switch (s.hairStyle) {
    case "perm":
      return { back: "", ...front(permParts()) }
    case "bald": {
      const tufts = [
        E(-0.93, -0.04, 0.17, 0.3),
        E(0.93, -0.04, 0.17, 0.3),
        C(-0.86, -0.32, 0.15),
        C(0.86, -0.32, 0.15),
      ]
      const f = front(tufts)
      return {
        back: "",
        under: f.under,
        front: `${f.front}${shapes([E(-0.36, -0.62, 0.18, 0.09)], "#FFFFFF", ' opacity=".45"')}`,
      }
    }
    case "bob": {
      const back = [
        D(
          "M -1.12 -0.05 Q -1.2 0.82 -0.88 0.84 L 0.88 0.84 Q 1.2 0.82 1.12 -0.05 Z",
        ),
        C(0, -0.1, 1.1),
      ]
      return {
        back: withShade(back, c, sh, 2, 3),
        ...front([
          D(
            "M -1.06 0.55 C -1.16 -0.55 -0.62 -1.12 0.02 -1.1 C 0.68 -1.1 1.16 -0.6 1.06 0.55 L 0.86 0.55 C 0.9 0.05 0.82 -0.28 0.66 -0.42 C 0.3 -0.3 -0.1 -0.42 -0.42 -0.62 C -0.62 -0.4 -0.86 -0.1 -0.86 0.55 Z",
          ),
        ]),
      }
    }
    case "spiky":
      return {
        back: "",
        ...front([
          D(
            "M -1.02 0.1 C -1.08 -0.5 -0.8 -0.95 -0.4 -1.05 L -0.3 -1.3 L -0.05 -1.08 L 0.15 -1.32 L 0.32 -1.06 L 0.62 -1.22 L 0.66 -0.95 C 0.95 -0.8 1.08 -0.4 1.02 0.1 L 0.9 0.1 C 0.88 -0.2 0.8 -0.35 0.7 -0.42 L 0.45 -0.32 L 0.3 -0.48 L 0.05 -0.36 L -0.15 -0.5 L -0.38 -0.36 L -0.6 -0.45 C -0.8 -0.35 -0.9 -0.1 -0.9 0.1 Z",
          ),
        ]),
      }
    case "slick": {
      const f = front([
        D(
          "M -1.02 0.05 C -1.08 -0.65 -0.6 -1.1 0.05 -1.1 C 0.7 -1.1 1.1 -0.65 1.02 0.05 L 0.9 0.05 C 0.9 -0.25 0.8 -0.42 0.62 -0.5 C 0.2 -0.6 -0.25 -0.54 -0.48 -0.64 C -0.78 -0.5 -0.9 -0.25 -0.9 0.05 Z",
        ),
      ])
      return {
        back: "",
        under: f.under,
        front: `${f.front}${stroke(hpath("M -0.46 -1.04 Q -0.5 -0.84 -0.48 -0.66"), sh, 2.4)}${stroke(hpath("M 0.1 -0.98 Q 0.45 -0.98 0.66 -0.78"), "#FFFFFF", 3, ' opacity=".35"')}`,
      }
    }
    case "ponytail": {
      const tail = [
        D(
          "M 0.66 -0.78 C 1.32 -0.96 1.52 -0.12 1.22 0.38 C 1.06 0.04 0.96 -0.3 0.68 -0.52 Z",
        ),
      ]
      const f = front([
        D(
          "M -1.02 0.15 C -1.1 -0.6 -0.6 -1.1 0 -1.1 C 0.6 -1.1 1.1 -0.6 1.02 0.15 L 0.9 0.15 C 0.88 -0.2 0.75 -0.4 0.55 -0.48 C 0.3 -0.42 0.12 -0.5 0 -0.62 C -0.12 -0.5 -0.3 -0.42 -0.55 -0.48 C -0.75 -0.4 -0.88 -0.2 -0.9 0.15 Z",
        ),
      ])
      return {
        back: withShade(tail, c, sh, 2, 3),
        under: f.under,
        front: `${f.front}${shapes([C(0.8, -0.72, 0.1)], s.accent ?? "#D9644A")}`,
      }
    }
    case "long": {
      const back = [
        D(
          "M -1.1 -0.2 C -1.2 0.6 -1.16 1.25 -0.96 1.46 L 0.96 1.46 C 1.16 1.25 1.2 0.6 1.1 -0.2 Z",
        ),
        C(0, -0.1, 1.1),
      ]
      return {
        back: withShade(back, c, sh, 2, 3),
        ...front([
          D(
            "M -1.04 0.75 C -1.16 -0.5 -0.66 -1.1 0 -1.1 C 0.66 -1.1 1.16 -0.5 1.04 0.75 L 0.84 0.75 C 0.86 0.1 0.72 -0.35 0.38 -0.52 C 0.2 -0.58 0.06 -0.7 0 -0.8 C -0.06 -0.7 -0.2 -0.58 -0.38 -0.52 C -0.72 -0.35 -0.86 0.1 -0.84 0.75 Z",
          ),
        ]),
      }
    }
    case "wavy":
      return {
        back: "",
        ...front([
          D(
            "M -1.02 0.1 C -1.15 -0.45 -0.95 -0.95 -0.55 -1.08 C -0.35 -1.3 0.05 -1.32 0.25 -1.15 C 0.55 -1.3 0.95 -1.12 0.98 -0.78 C 1.12 -0.55 1.08 -0.2 1.02 0.1 L 0.9 0.1 C 0.88 -0.2 0.8 -0.36 0.66 -0.44 C 0.4 -0.3 0 -0.32 -0.3 -0.52 C -0.48 -0.38 -0.62 -0.34 -0.76 -0.36 C -0.86 -0.2 -0.9 -0.05 -0.9 0.1 Z",
          ),
          E(-0.93, 0.12, 0.1, 0.2),
          E(0.93, 0.12, 0.1, 0.2),
        ]),
      }
    case "bun": {
      const bun = [C(0, -1.08, 0.34)]
      const f = front([
        D(
          "M -1 0.1 C -1.08 -0.62 -0.6 -1.1 0.05 -1.1 C 0.7 -1.1 1.1 -0.62 1 0.1 L 0.9 0.1 C 0.88 -0.22 0.78 -0.42 0.6 -0.52 C 0.3 -0.6 -0.1 -0.58 -0.35 -0.78 C -0.6 -0.55 -0.86 -0.3 -0.9 0.1 Z",
        ),
      ])
      return {
        back: withShade(bun, c, sh, 2, 3),
        under: f.under,
        front: f.front,
      }
    }
    case "capped":
      return {
        back: "",
        ...front([
          D(
            "M -1 0.12 C -1.06 -0.3 -0.98 -0.5 -0.84 -0.56 L -0.7 -0.5 C -0.82 -0.3 -0.88 -0.1 -0.88 0.12 Z",
          ),
          D(
            "M 1 0.12 C 1.06 -0.3 0.98 -0.5 0.84 -0.56 L 0.7 -0.5 C 0.82 -0.3 0.88 -0.1 0.88 0.12 Z",
          ),
        ]),
      }
  }
}

// ---------------------------------------------------------------- 臉

interface FaceSpec {
  eyes: "open" | "happy" | "narrow"
  brows: "calm" | "up" | "worried" | "raised"
  mouth: "smile" | "talk" | "grin" | "frown" | "flat"
  sweat?: boolean
}

const FACES: Record<Pose, FaceSpec> = {
  neutral: { eyes: "open", brows: "calm", mouth: "smile" },
  "talking-phone": { eyes: "open", brows: "calm", mouth: "talk" },
  worried: { eyes: "open", brows: "worried", mouth: "frown", sweat: true },
  happy: { eyes: "happy", brows: "up", mouth: "grin" },
  suspicious: { eyes: "narrow", brows: "raised", mouth: "flat" },
}

function face(s: CharacterSpec, pose: Pose): string {
  const { cx, cy, r } = G
  const f = FACES[pose]
  const ex = r * 0.36
  const ey = cy + r * 0.1
  const ew = r * 0.09
  const eh = r * 0.12
  const sw = r * 0.06
  const brow = s.brow ?? INK
  const line = (d: string, color = INK, w = sw) => stroke(d, color, w)
  let out = ""
  out += shapes(
    [
      { circle: [cx - r * 0.56, cy + r * 0.36, r * 0.11] },
      { circle: [cx + r * 0.56, cy + r * 0.36, r * 0.11] },
    ],
    BLUSH,
    ' opacity=".6"',
  )
  for (const side of [-1, 1]) {
    const x = cx + side * ex
    if (f.eyes === "open") {
      out += shapes([{ ellipse: [x, ey, ew, eh] }], INK)
      out += shapes(
        [{ circle: [x + ew * 0.35, ey - eh * 0.4, ew * 0.38] }],
        "#FFFFFF",
      )
    } else if (f.eyes === "happy") {
      out += line(
        `M${n(x - ew * 1.4)} ${n(ey + eh * 0.3)}Q${n(x)} ${n(ey - eh * 1.4)} ${n(x + ew * 1.4)} ${n(ey + eh * 0.3)}`,
      )
    } else {
      out += `<path d="M${n(x - ew * 1.2)} ${n(ey - eh * 0.1)}A${n(ew * 1.2)} ${n(eh * 0.8)} 0 0 0 ${n(x + ew * 1.2)} ${n(ey - eh * 0.1)}Z" fill="${INK}"/>`
      out += line(
        `M${n(x - ew * 1.6)} ${n(ey - eh * 0.15)}L${n(x + ew * 1.6)} ${n(ey - eh * 0.15)}`,
      )
    }
    // 睫毛：眼睛外側往上翹一筆
    if (s.lashes && f.eyes !== "happy") {
      const ox = x + side * ew * 0.85
      out += line(
        `M${n(ox)} ${n(ey - eh * 0.55)}L${n(ox + side * ew * 0.8)} ${n(ey - eh * 1.05)}`,
        INK,
        sw * 0.8,
      )
    }
    // 眉毛：inner 是靠近臉中間那一端
    const by = ey - r * 0.32
    const bw = r * 0.13
    const inner = x - side * bw
    const outer = x + side * bw
    const bwid = s.thickBrows ? r * 0.1 : sw
    if (f.brows === "calm")
      out += line(
        `M${n(outer)} ${n(by + 1)}Q${n(x)} ${n(by - 3)} ${n(inner)} ${n(by + 1)}`,
        brow,
        bwid,
      )
    if (f.brows === "up")
      out += line(
        `M${n(outer)} ${n(by - 1)}Q${n(x)} ${n(by - 6)} ${n(inner)} ${n(by - 1)}`,
        brow,
        bwid,
      )
    if (f.brows === "worried")
      out += line(
        `M${n(outer)} ${n(by + 2)}Q${n(x)} ${n(by - 1)} ${n(inner)} ${n(by - 6)}`,
        brow,
        bwid,
      )
    if (f.brows === "raised")
      out +=
        side < 0
          ? line(
              `M${n(outer)} ${n(by + 3)}L${n(inner)} ${n(by + 3)}`,
              brow,
              bwid,
            )
          : line(
              `M${n(inner)} ${n(by)}Q${n(x)} ${n(by - 9)} ${n(outer)} ${n(by - 3)}`,
              brow,
              bwid,
            )
  }
  if (s.glasses) {
    const gr = r * 0.21
    const gw = r * 0.045
    out += `<g fill="#fff" fill-opacity=".22" stroke="${s.glasses}" stroke-width="${n(gw)}"><circle cx="${n(cx - ex)}" cy="${n(ey)}" r="${n(gr)}"/><circle cx="${n(cx + ex)}" cy="${n(ey)}" r="${n(gr)}"/></g>`
    out += stroke(
      `M${n(cx - ex + gr)} ${n(ey)}Q${n(cx)} ${n(ey - gr * 0.5)} ${n(cx + ex - gr)} ${n(ey)}`,
      s.glasses,
      gw,
    )
  }
  // 鼻子
  const ny = cy + r * 0.3
  out += stroke(
    `M${n(cx - r * 0.06)} ${n(ny)}Q${n(cx)} ${n(ny + r * 0.07)} ${n(cx + r * 0.06)} ${n(ny)}`,
    s.skinShade,
    sw,
  )
  // 嘴巴（有鬍子的往下移一點）
  const my = cy + r * (s.mustache ? 0.58 : 0.5)
  const mw = r * 0.14
  if (f.mouth === "smile")
    out += line(
      `M${n(cx - mw)} ${n(my)}Q${n(cx)} ${n(my + mw * 0.9)} ${n(cx + mw)} ${n(my)}`,
    )
  if (f.mouth === "talk") {
    out += shapes([{ ellipse: [cx, my + 2, mw * 0.7, mw * 0.62] }], INK)
    out += shapes(
      [{ ellipse: [cx, my + 2 + mw * 0.32, mw * 0.42, mw * 0.24] }],
      TONGUE,
    )
  }
  if (f.mouth === "grin") {
    out += `<path d="M${n(cx - mw * 1.2)} ${n(my - 1)}Q${n(cx)} ${n(my + mw * 2)} ${n(cx + mw * 1.2)} ${n(my - 1)}Z" fill="${INK}" stroke="${INK}" stroke-width="${n(sw)}" stroke-linejoin="round"/>`
    out += shapes(
      [{ ellipse: [cx, my + mw * 0.62, mw * 0.55, mw * 0.26] }],
      TONGUE,
    )
  }
  if (f.mouth === "frown")
    out += line(
      `M${n(cx - mw)} ${n(my + 3)}Q${n(cx - mw * 0.4)} ${n(my - 2)} ${n(cx)} ${n(my + 1)}Q${n(cx + mw * 0.4)} ${n(my + 4)} ${n(cx + mw)} ${n(my - 1)}`,
    )
  if (f.mouth === "flat")
    out += line(`M${n(cx - mw)} ${n(my + 2)}L${n(cx + mw * 0.9)} ${n(my - 1)}`)
  if (s.mustache)
    out += shapes(
      [
        D(
          "M -0.24 0.44 Q -0.12 0.32 0 0.4 Q 0.12 0.32 0.24 0.44 Q 0.2 0.54 0 0.48 Q -0.2 0.54 -0.24 0.44 Z",
        ),
      ],
      s.mustache,
    )
  if (f.sweat) {
    const sx = cx + r * 0.86
    const sy = cy - r * 0.38
    out += `<path d="M${n(sx)} ${n(sy - r * 0.2)}Q${n(sx + r * 0.13)} ${n(sy)} ${n(sx)} ${n(sy + r * 0.08)}Q${n(sx - r * 0.13)} ${n(sy)} ${n(sx)} ${n(sy - r * 0.2)}Z" fill="${SWEAT}"/>`
  }
  return out
}

// ---------------------------------------------------------------- 身體

function torsoPath(): string {
  const { cx, shY, hemY, shHalf, hemHalf } = G
  return `M${cx - shHalf} ${shY + 14}Q${cx - shHalf} ${shY} ${cx - shHalf + 14} ${shY}L${cx + shHalf - 14} ${shY}Q${cx + shHalf} ${shY} ${cx + shHalf} ${shY + 14}L${cx + hemHalf} ${hemY - 6}Q${cx + hemHalf} ${hemY} ${cx + hemHalf - 6} ${hemY}L${cx - hemHalf + 6} ${hemY}Q${cx - hemHalf} ${hemY} ${cx - hemHalf} ${hemY - 6}Z`
}

/** 左右對稱的一對：給左半邊的點，右半邊自動鏡像 */
function pair(points: [number, number][], fill: string): string {
  const { cx } = G
  const half = (sign: 1 | -1) =>
    `M${points.map(([x, y]) => `${n(cx + sign * x)} ${n(y)}`).join("L")}Z`
  return `<path d="${half(-1)}${half(1)}" fill="${fill}"/>`
}

function collar(fill: string): string {
  const { shY } = G
  return pair(
    [
      [14, shY - 2],
      [0, shY + 7],
      [5, shY + 15],
      [17, shY + 6],
    ],
    fill,
  )
}

function topDetails(s: CharacterSpec): string {
  const { cx, shY, hemY, hemHalf } = G
  const inner = s.inner ?? WHITE
  const sh = s.topShade
  const accent = s.accent ?? INK
  const v = (depth: number, half: number) =>
    `<path d="M${cx - half} ${shY}L${cx + half} ${shY}L${cx} ${shY + depth}Z" fill="${inner}"/>`
  const dots = (pts: [number, number][], fill: string, r = 2.2) =>
    shapes(
      pts.map(([x, y]) => ({ circle: [x, y, r] as [number, number, number] })),
      fill,
    )
  switch (s.topKind) {
    case "cardigan":
      return `${v(30, 13)}${stroke(`M${cx} ${shY + 30}L${cx} ${hemY - 1}`, sh, 2.2)}${dots(
        [
          [cx + 5, shY + 40],
          [cx + 5, shY + 52],
        ],
        sh,
        2.6,
      )}`
    case "shirt":
      return `${stroke(`M${cx} ${shY + 6}L${cx} ${hemY - 1}`, sh, 2)}${dots(
        [
          [cx, shY + 20],
          [cx, shY + 34],
          [cx, shY + 48],
        ],
        WHITE,
        1.9,
      )}${shapes([{ rect: [cx + 7, shY + 14, 13, 12, 2] }], sh, ' opacity=".55"')}${collar(inner)}`
    case "school":
      return `${stroke(`M${cx} ${shY + 6}L${cx} ${hemY - 1}`, sh, 2)}${dots(
        [
          [cx, shY + 22],
          [cx, shY + 38],
        ],
        sh,
        1.9,
      )}${shapes(
        [
          { rect: [cx - 22, shY + 16, 12, 2.6, 1.3] },
          { rect: [cx - 22, shY + 21, 8, 2.2, 1.1] },
        ],
        "#4F6FA8",
      )}${collar(sh)}`
    case "blazer":
      return `${v(34, 14)}${pair(
        [
          [11, shY - 1],
          [1, shY + 6],
          [8, shY + 12],
        ],
        WHITE,
      )}${stroke(`M${cx - 14} ${shY}L${cx} ${shY + 34}M${cx + 14} ${shY}L${cx} ${shY + 34}`, sh, 3)}${dots([[cx + 3, shY + 44]], sh, 2.4)}${stroke(`M${cx - 23} ${shY + 46}h11M${cx + 12} ${shY + 46}h11`, sh, 2)}`
    case "polo":
      return `${pair(
        [
          [13, shY - 1],
          [2, shY + 5],
          [6, shY + 12],
          [16, shY + 5],
        ],
        sh,
      )}${shapes([{ rect: [cx - 3, shY + 3, 6, 18, 2] }], sh)}${dots(
        [
          [cx, shY + 9],
          [cx, shY + 16],
        ],
        WHITE,
        1.5,
      )}${shapes([{ circle: [cx + 14, shY + 17, 3] }], WHITE, ' opacity=".7"')}`
    case "apron": {
      const a = s.accent ?? "#7FA37A"
      return `${stroke(`M${cx - 9} ${shY}Q${cx} ${shY + 8} ${cx + 9} ${shY}`, sh, 2.5)}${stroke(
        `M${cx - 13} ${shY + 13}L${cx - 9} ${shY}M${cx + 13} ${shY + 13}L${cx + 9} ${shY}`,
        a,
        3,
      )}<path d="M${cx - 15} ${shY + 12}H${cx + 15}V${shY + 28}L${cx + hemHalf} ${hemY + 8}Q${cx + hemHalf} ${hemY + 12} ${cx + hemHalf - 4} ${hemY + 12}H${cx - hemHalf + 4}Q${cx - hemHalf} ${hemY + 12} ${cx - hemHalf} ${hemY + 8}L${cx - 15} ${shY + 28}Z" fill="${a}"/>${shapes([{ rect: [cx - 10, shY + 38, 20, 11, 2] }], s.accentShade ?? a)}`
    }
    case "sweater":
      return `${stroke(`M${cx - 11} ${shY}Q${cx} ${shY + 10} ${cx + 11} ${shY}`, sh, 3)}${shapes(
        [{ rect: [cx - hemHalf + 1, hemY - 7, hemHalf * 2 - 2, 6, 3] }],
        sh,
      )}${stroke(`M${cx - 8} ${shY + 16}V${shY + 44}M${cx + 8} ${shY + 16}V${shY + 44}`, sh, 2, ' opacity=".6"')}`
    case "jacket":
      return `<path d="M${cx - 11} ${shY}H${cx + 11}L${cx + 9} ${hemY}H${cx - 9}Z" fill="${inner}"/>${stroke(
        `M${cx - 8} ${shY}Q${cx} ${shY + 6} ${cx + 8} ${shY}`,
        "#D9D3C8",
        2,
      )}${stroke(`M${cx - 11} ${shY}L${cx - 9} ${hemY}M${cx + 11} ${shY}L${cx + 9} ${hemY}`, sh, 2)}${pair(
        [
          [11, shY - 2],
          [23, shY + 2],
          [12, shY + 20],
        ],
        sh,
      )}`
    case "vest":
      return `${v(28, 13)}${stroke(`M${cx - 13} ${shY}L${cx} ${shY + 28}M${cx + 13} ${shY}L${cx} ${shY + 28}`, sh, 2)}${dots(
        [
          [cx, shY + 36],
          [cx, shY + 48],
        ],
        "#E8E2D6",
      )}${pair(
        [
          [0, shY + 4],
          [10, shY - 1],
          [9, shY + 11],
        ],
        accent,
      )}${pair(
        [
          [1, shY + 6],
          [6, shY + 18],
          [1, shY + 16],
        ],
        accent,
      )}${shapes([{ circle: [cx, shY + 4, 3.4] }], s.accentShade ?? accent)}`
    case "uniform":
      return `${collar(sh)}${shapes(
        [
          {
            d: `M${cx - 4} ${shY + 5}H${cx + 4}L${cx + 5} ${shY + 30}L${cx} ${shY + 36}L${cx - 5} ${shY + 30}Z`,
          },
          { rect: [cx - 4, shY + 2, 8, 6, 2] },
          { rect: [cx - G.shHalf + 1, shY + 1, 13, 5, 2.5] },
          { rect: [cx + G.shHalf - 14, shY + 1, 13, 5, 2.5] },
          { rect: [cx - hemHalf + 1, hemY - 7, hemHalf * 2 - 2, 6] },
        ],
        accent,
      )}${shapes([{ rect: [cx + 9, shY + 16, 12, 4, 1.5] }], sh)}${shapes(
        [
          {
            d: `M${cx - 20} ${shY + 15}H${cx - 12}V${shY + 22}Q${cx - 12} ${shY + 25} ${cx - 16} ${shY + 27}Q${cx - 20} ${shY + 25} ${cx - 20} ${shY + 22}Z`,
          },
          { rect: [cx - 4, hemY - 8, 8, 8, 1.5] },
        ],
        GOLD,
      )}`
  }
}

function extrasFront(s: CharacterSpec): string {
  const { cx, shY } = G
  const accent = s.accent ?? INK
  let out = ""
  if (s.extras?.includes("lanyard")) {
    out += stroke(
      `M${cx - 8} ${shY}L${cx - 2} ${shY + 28}M${cx + 8} ${shY}L${cx + 2} ${shY + 28}`,
      accent,
      2.4,
    )
    out += shapes([{ rect: [cx - 7, shY + 26, 14, 18, 2] }], WHITE)
    out += shapes([{ rect: [cx - 7, shY + 26, 14, 5, 2] }], accent)
    out += shapes([{ rect: [cx - 4, shY + 33, 8, 7, 1] }], "#CFE0EF")
  }
  if (s.extras?.includes("nametag"))
    out += shapes([{ rect: [cx + 9, shY + 16, 13, 5, 1] }], "#E8C36A")
  if (s.extras?.includes("backpack"))
    out += stroke(
      `M${cx - 15} ${shY + 1}L${cx - 17} ${shY + 40}M${cx + 15} ${shY + 1}L${cx + 17} ${shY + 40}`,
      accent,
      5,
    )
  return out
}

function legs(s: CharacterSpec): string {
  const { cx, legTop, footY, hemY, hemHalf } = G
  let out = ""
  const leg = (x1: number, x2: number, y1: number, y2: number, w: number) => ({
    line: `M${x1} ${y1}L${x2} ${y2}`,
    w,
  })
  if (s.bottom === "pants") {
    out += shapes([leg(cx - 11, cx - 12, legTop, footY - 6, 17)], s.legsShade)
    out += shapes([leg(cx + 11, cx + 12, legTop, footY - 6, 17)], s.legs)
  } else if (s.bottom === "shorts") {
    out += shapes([leg(cx - 11, cx - 12, legTop, footY - 6, 12)], s.skinShade)
    out += shapes([leg(cx + 11, cx + 12, legTop, footY - 6, 12)], s.skin)
    out += shapes(
      [
        leg(cx - 12, cx - 12, footY - 15, footY - 6, 12.5),
        leg(cx + 12, cx + 12, footY - 15, footY - 6, 12.5),
      ],
      "#F4F1EA",
    )
    out += shapes(
      [leg(cx - 11, cx - 11, legTop - 4, legTop + 10, 19)],
      s.legsShade,
    )
    out += shapes([leg(cx + 11, cx + 11, legTop - 4, legTop + 10, 19)], s.legs)
  } else {
    out += shapes(
      [leg(cx - 10, cx - 11, hemY + 12, footY - 6, 11)],
      s.skinShade,
    )
    out += shapes([leg(cx + 10, cx + 11, hemY + 12, footY - 6, 11)], s.skin)
    out += `<path d="M${cx - hemHalf + 2} ${hemY - 14}H${cx + hemHalf - 2}L${cx + hemHalf + 5} ${hemY + 13}Q${cx + hemHalf + 5} ${hemY + 17} ${cx + hemHalf + 1} ${hemY + 17}H${cx - hemHalf - 1}Q${cx - hemHalf - 5} ${hemY + 17} ${cx - hemHalf - 5} ${hemY + 13}Z" fill="${s.legs}"/>`
  }
  out += shapes(
    [
      { ellipse: [cx - 15, footY - 2, 13, 6.5] },
      { ellipse: [cx + 15, footY - 2, 13, 6.5] },
    ],
    s.shoes,
  )
  out += shapes(
    [
      { ellipse: [cx - 15, footY + 2.2, 11, 2.2] },
      { ellipse: [cx + 15, footY + 2.2, 11, 2.2] },
    ],
    INK,
    ' opacity=".18"',
  )
  return out
}

// ---------------------------------------------------------------- 頭上的配件

function headwear(s: CharacterSpec): string {
  let out = ""
  if (s.extras?.includes("police-cap")) {
    const navy = s.accent ?? "#26334D"
    out += shapes(
      [D("M -0.92 -0.42 L -1.1 -0.98 Q 0 -1.36 1.1 -0.98 L 0.92 -0.42 Z")],
      navy,
    )
    out += shapes(
      [D("M -0.94 -0.6 L 0.94 -0.6 L 0.92 -0.42 L -0.92 -0.42 Z")],
      "#1C2638",
    )
    out += shapes(
      [D("M -0.9 -0.44 Q 0 -0.16 0.9 -0.44 Q 0 -0.32 -0.9 -0.44 Z")],
      "#1C2230",
    )
    out += shapes([C(0, -0.84, 0.13)], GOLD)
  }
  if (s.extras?.includes("headset")) {
    out += stroke(
      hpath("M -1.04 0.02 C -1.1 -1.2 1.1 -1.2 1.04 0.02"),
      "#4A4F5C",
      5,
    )
    out += shapes(
      [E(-1.02, 0.12, 0.14, 0.21), E(1.02, 0.12, 0.14, 0.21)],
      "#4A4F5C",
    )
    out += shapes(
      [E(-1.02, 0.12, 0.07, 0.12), E(1.02, 0.12, 0.07, 0.12)],
      "#6E7482",
    )
  }
  return out
}

function headsetMic(s: CharacterSpec): string {
  if (!s.extras?.includes("headset")) return ""
  return `${stroke(hpath("M -1 0.3 Q -0.9 0.72 -0.4 0.64"), "#4A4F5C", 3)}${shapes([E(-0.36, 0.63, 0.08, 0.06)], "#4A4F5C")}`
}

// ---------------------------------------------------------------- 手臂與姿勢

type Arm = [number, number, number, number, number, number]

function arms(s: CharacterSpec, pose: Pose): Arm[] {
  const { cx, shY, shHalf } = G
  const left: Arm = [
    cx - shHalf + 6,
    shY + 9,
    cx - shHalf - 8,
    shY + 38,
    cx - shHalf - 4,
    shY + 60,
  ]
  const right: Arm = [
    cx + shHalf - 6,
    shY + 9,
    cx + shHalf + 8,
    shY + 38,
    cx + shHalf + 4,
    shY + 60,
  ]
  switch (pose) {
    case "neutral":
      return [left, right]
    case "talking-phone":
      // 戴耳機的客服按著耳機講話，其他人拿手機貼耳朵
      return s.extras?.includes("headset")
        ? [
            [
              cx - shHalf + 6,
              shY + 9,
              cx - shHalf - 26,
              shY + 14,
              hx(-1.08),
              hy(0.2),
            ],
            right,
          ]
        : [
            [
              cx - shHalf + 6,
              shY + 9,
              cx - shHalf - 26,
              shY + 18,
              hx(-0.8),
              hy(0.32),
            ],
            right,
          ]
    case "worried":
      return [
        [
          cx - shHalf + 6,
          shY + 9,
          cx - shHalf - 20,
          shY + 24,
          hx(-0.7),
          hy(0.46),
        ],
        [
          cx + shHalf - 6,
          shY + 9,
          cx + shHalf + 20,
          shY + 24,
          hx(0.7),
          hy(0.46),
        ],
      ]
    case "happy":
      return [
        [
          cx - shHalf + 6,
          shY + 9,
          cx - shHalf - 26,
          shY + 6,
          cx - shHalf - 22,
          shY - 26,
        ],
        [
          cx + shHalf - 6,
          shY + 9,
          cx + shHalf + 26,
          shY + 6,
          cx + shHalf + 22,
          shY - 26,
        ],
      ]
    case "suspicious":
      return [
        left,
        [
          cx + shHalf - 6,
          shY + 9,
          cx + shHalf + 24,
          shY + 30,
          hx(0.28),
          hy(0.86),
        ],
      ]
  }
}

function handset(x: number, y: number): string {
  const w = G.r * 0.36
  const h = G.r * 0.66
  return `<g transform="rotate(-18 ${n(x)} ${n(y)})">${shapes([{ rect: [x - w / 2, y - h / 2, w, h, w * 0.22] }], PHONE)}${shapes([{ rect: [x - w / 2 + 2, y - h / 2 + 3, w - 4, h - 7, w * 0.12] }], PHONE_SCREEN)}</g>`
}

function drawArms(s: CharacterSpec, pose: Pose): string {
  const sleeve = s.sleeve ?? s.top
  const { armW } = G
  let out = ""
  const list = arms(s, pose)
  if (pose === "talking-phone" && !s.extras?.includes("headset")) {
    const h = list[0]
    out += handset(h[4] + 6, h[5] - 9)
  }
  for (const [sx, sy, ex, ey, hx2, hy2] of list) {
    const d = `M${n(sx)} ${n(sy)}Q${n(ex)} ${n(ey)} ${n(hx2)} ${n(hy2)}`
    if (s.shortSleeves) {
      // 短袖：整隻手臂先畫皮膚，再畫靠肩膀那一段袖子
      out += shapes([{ line: d, w: armW - 1 }], s.skin)
      const t = 0.36
      const c1x = sx + (ex - sx) * t
      const c1y = sy + (ey - sy) * t
      const px = (1 - t) ** 2 * sx + 2 * (1 - t) * t * ex + t * t * hx2
      const py = (1 - t) ** 2 * sy + 2 * (1 - t) * t * ey + t * t * hy2
      out += shapes(
        [
          {
            line: `M${n(sx)} ${n(sy)}Q${n(c1x)} ${n(c1y)} ${n(px)} ${n(py)}`,
            w: armW + 2,
          },
        ],
        sleeve,
      )
    } else {
      out += shapes([{ line: d, w: armW }], sleeve)
    }
    out += shapes([{ circle: [hx2, hy2, armW * 0.58] }], s.skin)
  }
  return out
}

// ---------------------------------------------------------------- 整個角色

export function drawCharacter(s: CharacterSpec, pose: Pose): string {
  const { cx, cy, r, shY, footY, hemHalf } = G
  const hair = hairLayers(s)
  let out = ""
  // 地上的影子
  out += shapes(
    [{ ellipse: [cx, footY + 3, hemHalf + 10, 6] }],
    INK,
    ' opacity=".12"',
  )
  out += hair.back
  if (s.extras?.includes("backpack"))
    out += shapes(
      [{ rect: [cx - G.shHalf - 7, shY + 2, (G.shHalf + 7) * 2, 50, 12] }],
      s.accentShade ?? s.accent ?? INK,
    )
  out += legs(s)
  // 脖子
  out += shapes(
    [{ rect: [cx - 8, cy + r * 0.7, 16, shY - cy - r * 0.7 + 6] }],
    s.skinShade,
  )
  out += `<path d="${torsoPath()}" fill="${s.top}"/>`
  out += topDetails(s)
  out += extrasFront(s)
  if (s.ears)
    out += `${shapes([C(-0.98, 0.18, 0.17), C(0.98, 0.18, 0.17)], s.skin)}${shapes([C(-0.98, 0.18, 0.08), C(0.98, 0.18, 0.08)], s.skinShade)}`
  out += hair.under
  out += shapes([{ ellipse: [cx, cy, r, r * 0.97] }], s.skin)
  out += hair.front
  out += headwear(s)
  out += face(s, pose)
  out += headsetMic(s)
  // 手臂畫在頭之後，手才蓋得到臉
  out += drawArms(s, pose)
  return out
}
