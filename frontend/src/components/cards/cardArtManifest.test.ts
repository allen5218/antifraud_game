import { describe, expect, test } from "bun:test"
import { existsSync, readFileSync, statSync } from "node:fs"
import { join } from "node:path"
import {
  CAST_IDS,
  castHref,
  manifestJson,
  POSES,
  PROP_IDS,
  propHref,
  SCENE_IDS,
  sceneHref,
} from "./cardArtManifest"

const PUBLIC = join(import.meta.dir, "../../../public")
const file = (href: string) => join(PUBLIC, href)

const allHrefs = [
  ...SCENE_IDS.map(sceneHref),
  ...CAST_IDS.flatMap((id) => POSES.map((pose) => castHref(id, pose))),
  ...PROP_IDS.map(propHref),
]

describe("卡片插圖清單", () => {
  test("題庫共用的 id 一個都不能少", () => {
    expect(SCENE_IDS).toHaveLength(6)
    expect(CAST_IDS).toHaveLength(10)
    expect(POSES).toEqual([
      "neutral",
      "talking-phone",
      "worried",
      "happy",
      "suspicious",
    ])
    expect(PROP_IDS).toHaveLength(9)
  })

  test("manifest.json 和程式裡的清單一致（改清單後要重跑 scripts/cast/build.ts）", () => {
    const onDisk = JSON.parse(
      readFileSync(file("/assets/cast/manifest.json"), "utf8"),
    )
    expect(onDisk).toEqual(manifestJson())
  })

  test("每個場景、角色姿勢、道具都有圖", () => {
    const missing = allHrefs.filter((href) => !existsSync(file(href)))
    expect(missing).toEqual([])
  })

  // PWA 安裝時會預先下載所有 SVG，單檔要小
  test("每張圖都很小，也沒有腳本或外部連結", () => {
    for (const href of allHrefs) {
      if (!existsSync(file(href))) continue
      expect(statSync(file(href)).size).toBeLessThanOrEqual(12 * 1024)
      const svg = readFileSync(file(href), "utf8")
      expect(svg).not.toContain("<script")
      expect(svg).not.toMatch(/https?:\/\/(?!www\.w3\.org)/)
    }
  })

  test("授權說明在", () => {
    expect(existsSync(file("/assets/cast/LICENSES.md"))).toBe(true)
  })
})
