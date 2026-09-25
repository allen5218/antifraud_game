"""詐騙類型的中文名稱(後端用:練習重點的說明文字、給分析器的統計)。

前端另有一份給畫面用的(`frontend/src/lib/fraudTypes.ts`),兩邊的全名必須一致。
名稱跟著影片與題庫的講法:投資、假網拍、購物、假交友、解除分期。
"""

from app.models import FraudType

FRAUD_TYPE_LABELS: dict[str, str] = {
    FraudType.INVESTMENT.value: "投資詐騙",
    FraudType.FAKE_SALE.value: "假網拍",
    FraudType.SHOPPING.value: "購物詐騙",
    FraudType.ROMANCE.value: "假交友",
    FraudType.ATM.value: "解除分期",
}

FRAUD_TYPES: list[str] = [ft.value for ft in FraudType]
