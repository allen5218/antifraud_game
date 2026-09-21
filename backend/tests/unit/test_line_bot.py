import base64
import hashlib
import hmac
import pytest
from app.core.line_bot import line_bot_service


def test_line_bot_signature_verification():
    body = "test_body"
    secret = line_bot_service.channel_secret
    if secret:
        # Valid signature
        digest = hmac.new(secret.encode("utf-8"), body.encode("utf-8"), hashlib.sha256).digest()
        sig = base64.b64encode(digest).decode("utf-8")
        assert line_bot_service.verify_signature(body, sig) is True
        # Invalid signature
        assert line_bot_service.verify_signature(body, "invalid_signature") is False
    else:
        assert line_bot_service.verify_signature(body, "any_sig") is True


def test_line_bot_build_quick_reply():
    items = [("檢舉詐騙", "檢舉"), ("165 查證", "查證"), ("安全退出", "退出")]
    qr = line_bot_service.build_quick_reply(items)
    assert "items" in qr
    assert len(qr["items"]) == 3
    assert qr["items"][0]["action"]["label"] == "檢舉詐騙"
    assert qr["items"][0]["action"]["text"] == "檢舉"


def test_line_bot_create_welcome_flex():
    flex = line_bot_service.create_welcome_flex()
    assert flex["type"] == "flex"
    assert "反詐大師" in flex["altText"]
    assert flex["contents"]["type"] == "bubble"
    assert flex["contents"]["header"]["backgroundColor"] == "#06C755"


def test_line_bot_create_verdict_dossier_flex():
    flags = [
        {"tag": "authority", "label": "權威服從", "detail": "自稱地檢署檢察官"},
        {"tag": "time_pressure", "label": "時間壓力", "detail": "要求今日內完成轉帳"},
    ]
    inoculation = {
        "debrief": "對方利用權威身分與緊急時間限制劫持思考。",
        "countermeasure": "遇檢警要求匯款一律親撥 165 核實。",
    }
    flex = line_bot_service.create_verdict_dossier_flex(
        display_name="假檢察官張專員",
        true_role="scam",
        outcome="win_report",
        flags=flags,
        cash_delta=500,
        xp_delta=100,
        provenance="165 官方通報案例",
        inoculation=inoculation,
    )
    assert flex["type"] == "flex"
    assert "識破成功" in flex["altText"]
    bubble = flex["contents"]
    assert bubble["header"]["backgroundColor"] == "#059669"
    # Check that analysis is included (把分析給我們)
    body_texts = [
        item.get("text", "")
        for item in bubble["body"]["contents"]
        if "text" in item
    ]
    assert any("心理說服槓桿與認知煞車解密" in t for t in body_texts)
