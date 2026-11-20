// 產生 public/assets/cast/ 的所有插圖與 manifest.json：cd frontend && bun scripts/cast/build.ts

import { mkdirSync, writeFileSync } from "node:fs"
import { dirname, join } from "node:path"
import { fileURLToPath } from "node:url"
import {
  ART_VIEWBOX,
  CAST_IDS,
  castHref,
  manifestJson,
  POSES,
  PROP_IDS,
  propHref,
  SCENE_IDS,
  sceneHref,
} from "../../src/components/cards/cardArtManifest"
import { CHARACTERS } from "./characters"
import { PROPS } from "./props"
import { drawCharacter } from "./rig"
import { SCENES } from "./scenes"
import { svgDoc } from "./svg"

const PUBLIC = fileURLToPath(new URL("../../public", import.meta.url))

function write(href: string, content: string) {
  const file = join(PUBLIC, href)
  mkdirSync(dirname(file), { recursive: true })
  writeFileSync(file, content)
}

const [sw, sh] = ART_VIEWBOX.scene
const [cw, ch] = ART_VIEWBOX.cast
const [pw, ph] = ART_VIEWBOX.prop

for (const id of SCENE_IDS) write(sceneHref(id), svgDoc(sw, sh, SCENES[id]()))
for (const id of CAST_IDS)
  for (const pose of POSES)
    write(
      castHref(id, pose),
      svgDoc(cw, ch, drawCharacter(CHARACTERS[id], pose)),
    )
for (const id of PROP_IDS) write(propHref(id), svgDoc(pw, ph, PROPS[id]()))
write(
  "/assets/cast/manifest.json",
  `${JSON.stringify(manifestJson(), null, 2)}\n`,
)

console.log(
  `寫好 ${SCENE_IDS.length} 個場景、${CAST_IDS.length * POSES.length} 張角色、${PROP_IDS.length} 個道具`,
)
