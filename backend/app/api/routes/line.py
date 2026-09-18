from typing import Any
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

router = APIRouter(prefix="/line", tags=["line"])

class LineReportRequest(BaseModel):
    message_text: str
    sender_id: str | None = None

class LineReportResponse(BaseModel):
    is_scam: bool
    risk_score: int
    red_flags: list[str]
    reward_cash: int
    reward_xp: int
    explanation: str

@router.post("/verify-report", response_model=LineReportResponse)
def verify_line_reported_message(payload: LineReportRequest) -> Any:
    """
    LINE 轉傳查核 Bot API：
    接收玩家轉傳的可疑 LINE 訊息，由 AI Agent 評估風險並回傳結果與發放獎勵
    """
    text = payload.message_text.lower()
    
    # Simple rule-based & agent simulation for red flag detection
    red_flags = []
    if any(k in text for k in ["飆股", "保證獲利", "加 line", "飆股社團", "領取股票"]):
        red_flags.append("投資詐欺 / 假飆股社團引誘")
    if any(k in text for k in ["解除分期", "atm", "誤設", "扣款異常"]):
        red_flags.append("解除分期付款 (ATM) 詐騙")
    if any(k in text for k in ["包裹", "點擊連結", "實名認證", "雙倍扣款"]):
        red_flags.append("假網拍 / 簡訊釣魚連結")
        
    is_scam = len(red_flags) > 0
    risk_score = 95 if is_scam else 10
    
    explanation = (
        "發現典型詐騙誘爆詞與紅旗！警政署提醒：任何要求加私 Line 領取飆股、操作 ATM 或點擊簡訊驗證連結均為詐騙。"
        if is_scam
        else "經初步比對未發現明確已知紅旗，但仍請保持警覺，避免交付個人敏感資料或進行未授權轉帳。"
    )

    return LineReportResponse(
        is_scam=is_scam,
        risk_score=risk_score,
        red_flags=red_flags if is_scam else ["資訊正常"],
        reward_cash=500 if is_scam else 100,
        reward_xp=50 if is_scam else 10,
        explanation=explanation,
    )

@router.post("/webhook")
async def line_webhook(request: Request):
    """
    LINE Official Account Webhook Handler
    """
    return {"status": "ok", "message": "LINE Webhook received"}
