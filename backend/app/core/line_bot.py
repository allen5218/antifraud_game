import base64
import hmac
import hashlib
import logging
from typing import Any
import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

class LineBotService:
    """
    Production-grade LINE Messaging API & Webhook Handler
    """

    def __init__(self):
        self.channel_secret = settings.LINE_CHANNEL_SECRET
        self.channel_access_token = settings.LINE_CHANNEL_ACCESS_TOKEN
        self.api_url = "https://api.line.me/v2/bot/message"

    def verify_signature(self, body: str, signature: str) -> bool:
        """
        Verify LINE Webhook Signature (HMAC-SHA256)
        """
        if not self.channel_secret:
            logger.warning("LINE_CHANNEL_SECRET is not configured; skipping signature check.")
            return True

        hash_digest = hmac.new(
            self.channel_secret.encode("utf-8"),
            body.encode("utf-8"),
            hashlib.sha256
        ).digest()
        expected_signature = base64.b64encode(hash_digest).decode("utf-8")
        return hmac.compare_digest(expected_signature, signature)

    async def reply_message(self, reply_token: str, messages: list[dict[str, Any]]) -> bool:
        """
        Send reply message back to user via LINE Messaging API
        """
        if not self.channel_access_token:
            logger.info("LINE_CHANNEL_ACCESS_TOKEN not set. Running in simulation mode.")
            return True

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.channel_access_token}",
        }
        payload = {
            "replyToken": reply_token,
            "messages": messages,
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(f"{self.api_url}/reply", json=payload, headers=headers)
            if response.status_code != 200:
                logger.error(f"LINE Reply Error ({response.status_code}): {response.text}")
                return False
            return True

line_bot_service = LineBotService()
