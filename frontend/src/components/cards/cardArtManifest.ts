// 日常卡片插圖的清單：題庫的 art 欄位只能用這裡的 id（不要改名，題庫那邊共用）。
// scripts/cast/build.ts 讀這份清單畫出 public/assets/cast/ 的 SVG 與 manifest.json。

export const ART_BASE = "/assets/cast"

export const SCENE_IDS = [
  "living-room",
  "street",
  "atm-corner",
  "shop",
  "office",
  "phone-screen",
] as const

export const CAST_IDS = [
  "grandma",
  "grandpa",
  "office-worker",
  "student",
  "fake-cs",
  "seller",
  "buyer",
  "stranger",
  "bank-clerk",
  "police",
] as const

export const POSES = [
  "neutral",
  "talking-phone",
  "worried",
  "happy",
  "suspicious",
] as const

export const PROP_IDS = [
  "phone",
  "chat",
  "atm",
  "parcel",
  "card",
  "laptop",
  "money",
  "house",
  "qr",
] as const

export type SceneId = (typeof SCENE_IDS)[number]
export type CastId = (typeof CAST_IDS)[number]
export type Pose = (typeof POSES)[number]
export type PropId = (typeof PROP_IDS)[number]

/** 大東西放在地上，手拿的小東西浮在角色旁邊（墊白色圓底） */
export const PROP_MOUNT: Record<PropId, "ground" | "float"> = {
  phone: "float",
  chat: "float",
  atm: "ground",
  parcel: "ground",
  card: "float",
  laptop: "float",
  money: "float",
  house: "ground",
  qr: "float",
}

/** 給寫題庫的人對照外觀與性別，題目文字要對得上 */
export const CAST_LOOKS: Record<CastId, string> = {
  grandma: "阿嬤：灰白燙捲短髮、眼鏡、陶土色開襟外套",
  grandpa: "阿公：禿頭、兩側灰髮、灰八字鬍、藍襯衫",
  "office-worker": "上班族女生：黑色鮑伯頭、深藍西裝外套、識別證掛繩",
  student: "高中男生：刺刺短髮、白制服襯衫、短褲、後背包",
  "fake-cs": "客服（男）：油頭、耳機麥克風、綠色 POLO 衫",
  seller: "賣家（女）：綁馬尾、圍裙",
  buyer: "買家（女）：長髮、黃色毛衣、牛仔褲",
  stranger: "網友（男）：蓬鬆捲髮、皮夾克",
  "bank-clerk": "行員（女）：包頭、深藍背心制服、橘色領巾",
  police: "警察（男）：警帽、淺藍制服襯衫、深藍褲",
}

/** 每張圖的座標範圍（SVG viewBox 的寬高） */
export const ART_VIEWBOX = {
  scene: [400, 300],
  cast: [200, 240],
  prop: [120, 120],
} as const

export const sceneHref = (id: SceneId) => `${ART_BASE}/scenes/${id}.svg`
export const castHref = (id: CastId, pose: Pose) =>
  `${ART_BASE}/cast/${id}/${pose}.svg`
export const propHref = (id: PropId) => `${ART_BASE}/props/${id}.svg`

export const isSceneId = (v: string): v is SceneId =>
  (SCENE_IDS as readonly string[]).includes(v)
export const isCastId = (v: string): v is CastId =>
  (CAST_IDS as readonly string[]).includes(v)
export const isPose = (v: string): v is Pose =>
  (POSES as readonly string[]).includes(v)
export const isPropId = (v: string): v is PropId =>
  (PROP_IDS as readonly string[]).includes(v)

/** 寫進 public/assets/cast/manifest.json 的內容（題庫與其他程式讀這份） */
export function manifestJson() {
  return {
    version: 1,
    style: "chibi-flat",
    viewBox: ART_VIEWBOX,
    paths: {
      scene: "scenes/<id>.svg",
      cast: "cast/<id>/<pose>.svg",
      prop: "props/<id>.svg",
    },
    scenes: [...SCENE_IDS],
    cast: Object.fromEntries(
      CAST_IDS.map((id) => [id, { poses: [...POSES], look: CAST_LOOKS[id] }]),
    ),
    props: Object.fromEntries(
      PROP_IDS.map((id) => [id, { mount: PROP_MOUNT[id] }]),
    ),
  }
}
