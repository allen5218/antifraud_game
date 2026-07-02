"""弱點標籤共用文案(前測/滑卡/遊戲/情境模擬共用)。"""

WEAKNESS_TAGS: set[str] = {
    "time_pressure",
    "authority",
    "greed",
    "social_proof",
    "trust_building",
}

WEAKNESS_LABELS: dict[str, str] = {
    "time_pressure": "時間壓力",
    "authority": "權威服從",
    "greed": "貪念誘惑",
    "social_proof": "社會認同",
    "trust_building": "信任建立",
}

WEAKNESS_SUGGESTIONS: dict[str, str] = {
    "time_pressure": "遇到「限時」「緊急」等話術時，先深呼吸，給自己 24 小時冷靜期",
    "authority": "不要因為對方自稱專家或官員就輕信，主動查證對方身份",
    "greed": "記住「高報酬必伴隨高風險」，保證獲利幾乎都是詐騙",
    "social_proof": "不要因為「很多人都在做」就跟風，獨立思考很重要",
    "trust_building": "即使對方展示了真實資訊，也不代表整件事是真的",
}
