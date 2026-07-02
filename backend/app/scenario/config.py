"""情境模擬(E)集中設定:經濟數值、名字池、正當訊號、回合/場次上限。"""

from dataclasses import dataclass

MAX_TURNS = 10
SCENARIO_DAILY_LIMIT_PER_TYPE = 3
SCAM_RATIO = 0.5


@dataclass(frozen=True)
class ScenarioEconomyConfig:
    stake_loss: int
    reward_win: int
    reward_legit: int
    penalty_misreport: int


SCENARIO_ECONOMY: dict[str, ScenarioEconomyConfig] = {
    "investment": ScenarioEconomyConfig(12000, 1500, 800, 300),
    "romance": ScenarioEconomyConfig(10000, 1500, 800, 300),
    "atm": ScenarioEconomyConfig(8000, 1200, 700, 300),
    "shopping": ScenarioEconomyConfig(6000, 1000, 600, 250),
    "fake-sale": ScenarioEconomyConfig(6000, 1000, 600, 250),
}

# scam/legit 共用同一池,避免「名字 ↔ 角色」相關性洩題
DISPLAY_NAME_POOL: dict[str, list[str]] = {
    "investment": ["Kevin", "阿哲", "Vivian"],
    "shopping": ["小魚", "Lily", "阿凱"],
    "fake-sale": ["客服 Amber", "客服 Leo", "客服 Ryan"],
    "romance": ["Alex", "Sunny", "Joe"],
    "atm": ["客服 Peggy", "客服 Mark", "客服 Judy"],
}

# legit 結局揭曉卡的「正當訊號」文案(確定性、非 LLM)
LEGIT_SIGNALS: dict[str, list[str]] = {
    "investment": [
        "主動揭露風險與費用，不保證獲利",
        "走銀行／官方 App 正式流程，不要求私人轉帳",
        "不催促，尊重你考慮與拒絕的權利",
    ],
    "shopping": [
        "只走平台金流，不引導站外匯款",
        "商品現況如實描述，價格合理有依據",
        "說明鑑賞期與退貨流程，不製造急迫感",
    ],
    "fake-sale": [
        "所有流程在平台站內完成，不要求加 LINE",
        "不收任何「解鎖費／保證金」",
        "主動提醒站外聯繫與先付款都是詐騙特徵",
    ],
    "romance": [
        "願意視訊、見面，不找藉口迴避",
        "從不談匯款、代收包裹或投資",
        "交往節奏自然，不刻意天天養感情",
    ],
    "atm": [
        "不要求操作 ATM 或提供卡號、OTP",
        "歡迎掛斷後回撥官方客服查證",
        "主動提醒可撥打 165 反詐騙專線",
    ],
}
