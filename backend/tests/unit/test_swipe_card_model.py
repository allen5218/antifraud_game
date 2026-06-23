from app.models import SwipeCard


def test_swipe_card_defaults():
    c = SwipeCard(
        scenario="老師說這檔三天漲 30%，先轉一筆鎖額度",
        source_label="投資群組 飆股VIP·林老師",
        is_scam=True,
        fraud_type="investment",
        weakness_tags=["authority", "greed", "time_pressure"],
        explanation="保證高報酬+催促匯款到指定帳戶是典型投資詐騙",
    )
    assert c.is_scam is True
    assert c.fraud_type == "investment"
    assert "greed" in c.weakness_tags
    assert c.difficulty == 1
