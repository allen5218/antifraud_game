import base64
import hashlib
import hmac
import logging
from typing import Any
import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


class LineBotService:
    """
    Production-grade LINE Messaging API & Webhook Handler for Scenario Dialogue
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
            hashlib.sha256,
        ).digest()
        expected_signature = base64.b64encode(hash_digest).decode("utf-8")
        return hmac.compare_digest(expected_signature, signature)

    def build_quick_reply(self, items: list[tuple[str, str]]) -> dict[str, Any]:
        """
        Builds LINE Quick Reply container from a list of (label, text) tuples.
        """
        return {
            "items": [
                {
                    "type": "action",
                    "action": {
                        "type": "message",
                        "label": label[:20],
                        "text": text[:300],
                    },
                }
                for label, text in items
            ]
        }

    def create_text_message(
        self, text: str, quick_replies: list[tuple[str, str]] | None = None
    ) -> dict[str, Any]:
        """
        Creates standard LINE Text message with optional Quick Reply buttons.
        """
        msg: dict[str, Any] = {"type": "text", "text": text}
        if quick_replies:
            msg["quickReply"] = self.build_quick_reply(quick_replies)
        return msg

    def create_welcome_flex(self) -> dict[str, Any]:
        """
        Creates introductory Flex Message for National Collegiate Anti-Fraud League.
        """
        return {
            "type": "flex",
            "altText": "【反詐大師】LINE 官方防詐實境訓練頻道",
            "contents": {
                "type": "bubble",
                "header": {
                    "type": "box",
                    "layout": "vertical",
                    "backgroundColor": "#06C755",
                    "paddingTop": "16px",
                    "paddingBottom": "16px",
                    "contents": [
                        {
                            "type": "text",
                            "text": "反詐大師 · 官方實境對話",
                            "color": "#FFFFFF",
                            "weight": "bold",
                            "size": "lg",
                        },
                        {
                            "type": "text",
                            "text": "大專生雙歷程防詐免疫力競賽專用頻道",
                            "color": "#E8F8F0",
                            "size": "xs",
                            "margin": "xs",
                        },
                    ],
                },
                "body": {
                    "type": "box",
                    "layout": "vertical",
                    "spacing": "md",
                    "contents": [
                        {
                            "type": "text",
                            "text": "歡迎進入真實通訊防詐攻防。請選擇欲挑戰的詐騙實境，直接與擬真對象對話：",
                            "wrap": True,
                            "size": "sm",
                            "color": "#2D3748",
                        },
                        {
                            "type": "box",
                            "layout": "vertical",
                            "spacing": "sm",
                            "margin": "md",
                            "contents": [
                                {
                                    "type": "button",
                                    "style": "primary",
                                    "color": "#06C755",
                                    "action": {
                                        "type": "message",
                                        "label": "挑戰：投資顧問高回報案",
                                        "text": "開始情境 invest",
                                    },
                                },
                                {
                                    "type": "button",
                                    "style": "secondary",
                                    "action": {
                                        "type": "message",
                                        "label": "挑戰：假檢警資產凍結案",
                                        "text": "開始情境 authority",
                                    },
                                },
                                {
                                    "type": "button",
                                    "style": "secondary",
                                    "action": {
                                        "type": "message",
                                        "label": "挑戰：網購簡訊認證案",
                                        "text": "開始情境 shopping",
                                    },
                                },
                            ],
                        },
                    ],
                },
                "footer": {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                        {
                            "type": "text",
                            "text": "提示：對話中請依直覺溝通；隨時輸入「下判斷」或點選快捷鍵結束並評分。",
                            "size": "xxs",
                            "color": "#A0AEC0",
                            "align": "center",
                            "wrap": True,
                        }
                    ],
                },
            },
        }

    def create_verdict_dossier_flex(
        self,
        display_name: str,
        true_role: str,
        outcome: str,
        flags: list[dict[str, Any]],
        cash_delta: int,
        xp_delta: int,
        provenance: str | None = None,
        inoculation: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Creates post-scenario academic forensic dossier Flex Message (把分析給我們).
        """
        is_win = "win" in outcome
        header_color = "#059669" if is_win else "#DC2626"
        result_title = "識破成功！防詐免疫力提升" if is_win else "遭遇詐騙陷阱（已啟動防護覆盤）"

        flag_contents = []
        for f in flags[:4]:
            tag_label = f.get("label", "關鍵警訊")
            detail_text = f.get("detail", "")
            flag_contents.append(
                {
                    "type": "box",
                    "layout": "horizontal",
                    "spacing": "sm",
                    "margin": "sm",
                    "contents": [
                        {
                            "type": "text",
                            "text": f"[{tag_label}]",
                            "size": "xs",
                            "color": "#B45309",
                            "weight": "bold",
                            "flex": 3,
                        },
                        {
                            "type": "text",
                            "text": detail_text,
                            "size": "xs",
                            "color": "#374151",
                            "wrap": True,
                            "flex": 7,
                        },
                    ],
                }
            )

        body_contents: list[dict[str, Any]] = [
            {
                "type": "box",
                "layout": "horizontal",
                "contents": [
                    {
                        "type": "text",
                        "text": "對象真實身份",
                        "size": "xs",
                        "color": "#6B7280",
                    },
                    {
                        "type": "text",
                        "text": f"{'詐騙集團成員' if true_role == 'scam' else '正當聯絡人'} ({display_name})",
                        "size": "xs",
                        "weight": "bold",
                        "color": "#111827",
                        "align": "end",
                    },
                ],
            },
            {
                "type": "box",
                "layout": "horizontal",
                "margin": "xs",
                "contents": [
                    {
                        "type": "text",
                        "text": "資產獎懲變動",
                        "size": "xs",
                        "color": "#6B7280",
                    },
                    {
                        "type": "text",
                        "text": f"{'+' if cash_delta >= 0 else ''}${cash_delta} · +{xp_delta} XP",
                        "size": "xs",
                        "weight": "bold",
                        "color": "#059669" if cash_delta >= 0 else "#DC2626",
                        "align": "end",
                    },
                ],
            },
            {"type": "separator", "margin": "md"},
            {
                "type": "text",
                "text": "【對話偵查線索與紅旗】",
                "size": "xs",
                "weight": "bold",
                "color": "#1F2937",
                "margin": "md",
            },
        ]
        body_contents.extend(flag_contents)

        if inoculation:
            debrief_text = inoculation.get("debrief") or inoculation.get("mechanism") or "系統記錄雙歷程認知煞車反應。"
            body_contents.extend(
                [
                    {"type": "separator", "margin": "md"},
                    {
                        "type": "text",
                        "text": "【心理說服槓桿與認知煞車解密】",
                        "size": "xs",
                        "weight": "bold",
                        "color": "#B45309",
                        "margin": "md",
                    },
                    {
                        "type": "text",
                        "text": debrief_text,
                        "size": "xxs",
                        "color": "#4B5563",
                        "wrap": True,
                        "margin": "xs",
                    },
                ]
            )

        if provenance:
            body_contents.append(
                {
                    "type": "text",
                    "text": f"真實案例來源：{provenance}",
                    "size": "xxs",
                    "color": "#9CA3AF",
                    "margin": "md",
                }
            )

        return {
            "type": "flex",
            "altText": f"【防詐診斷書】{result_title}",
            "contents": {
                "type": "bubble",
                "header": {
                    "type": "box",
                    "layout": "vertical",
                    "backgroundColor": header_color,
                    "paddingTop": "14px",
                    "paddingBottom": "14px",
                    "contents": [
                        {
                            "type": "text",
                            "text": result_title,
                            "color": "#FFFFFF",
                            "weight": "bold",
                            "size": "md",
                        }
                    ],
                },
                "body": {
                    "type": "box",
                    "layout": "vertical",
                    "contents": body_contents,
                },
                "footer": {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                        {
                            "type": "button",
                            "style": "primary",
                            "color": "#06C755",
                            "action": {
                                "type": "message",
                                "label": "開啟下一個防詐情境",
                                "text": "換一個",
                            },
                        }
                    ],
                },
            },
        }

    def create_agent_id_card_flex(
        self,
        agent_name: str,
        agent_code: str,
        cash: int,
        level: int,
        direct_url: str,
    ) -> dict[str, Any]:
        """
        Creates an official Agent Digital ID Card Flex message with a one-click magic login URL.
        """
        return {
            "type": "flex",
            "altText": "【反詐大師】您的探員數位身分證",
            "contents": {
                "type": "bubble",
                "header": {
                    "type": "box",
                    "layout": "vertical",
                    "backgroundColor": "#0F172A",
                    "paddingTop": "16px",
                    "paddingBottom": "16px",
                    "contents": [
                        {
                            "type": "text",
                            "text": "反詐大師 · 探員數位身分證",
                            "color": "#FFFFFF",
                            "weight": "bold",
                            "size": "md",
                        },
                        {
                            "type": "text",
                            "text": "大專生雙歷程認知防衛總部官方核發",
                            "color": "#94A3B8",
                            "size": "xxs",
                            "margin": "xs",
                        },
                    ],
                },
                "body": {
                    "type": "box",
                    "layout": "vertical",
                    "spacing": "md",
                    "contents": [
                        {
                            "type": "box",
                            "layout": "horizontal",
                            "contents": [
                                {"type": "text", "text": "探員代號", "size": "xs", "color": "#64748B", "flex": 3},
                                {"type": "text", "text": agent_code, "size": "xs", "weight": "bold", "color": "#0F172A", "flex": 5},
                            ],
                        },
                        {
                            "type": "box",
                            "layout": "horizontal",
                            "contents": [
                                {"type": "text", "text": "學員身分", "size": "xs", "color": "#64748B", "flex": 3},
                                {"type": "text", "text": agent_name, "size": "xs", "weight": "bold", "color": "#0F172A", "flex": 5},
                            ],
                        },
                        {
                            "type": "box",
                            "layout": "horizontal",
                            "contents": [
                                {"type": "text", "text": "防詐階級", "size": "xs", "color": "#64748B", "flex": 3},
                                {"type": "text", "text": f"Lv.{level} 正式調查員", "size": "xs", "weight": "bold", "color": "#2563EB", "flex": 5},
                            ],
                        },
                        {
                            "type": "box",
                            "layout": "horizontal",
                            "contents": [
                                {"type": "text", "text": "初始資產", "size": "xs", "color": "#64748B", "flex": 3},
                                {"type": "text", "text": f"NT$ {cash:,}", "size": "xs", "weight": "bold", "color": "#059669", "flex": 5},
                            ],
                        },
                        {"type": "separator", "margin": "md"},
                        {
                            "type": "text",
                            "text": "本身分證已綁定您的 LINE 官方帳號。點擊下方按鈕即可免密碼直通 Web 總部，所有破案進度與資產雙向即時同步。",
                            "size": "xxs",
                            "color": "#64748B",
                            "wrap": True,
                        },
                    ],
                },
                "footer": {
                    "type": "box",
                    "layout": "vertical",
                    "spacing": "sm",
                    "contents": [
                        {
                            "type": "button",
                            "style": "primary",
                            "color": "#06C755",
                            "action": {
                                "type": "uri",
                                "label": "進入 Web 版總部（免密碼直通）",
                                "uri": direct_url,
                            },
                        },
                        {
                            "type": "button",
                            "style": "secondary",
                            "action": {
                                "type": "message",
                                "label": "開始防詐實境對話",
                                "text": "換一個",
                            },
                        },
                    ],
                },
            },
        }

    async def reply_message(self, reply_token: str, messages: list[dict[str, Any]]) -> bool:
        """
        Send reply message back to user via LINE Messaging API
        """
        if not self.channel_access_token:
            logger.info("LINE_CHANNEL_ACCESS_TOKEN not set. Running in local simulation mode.")
            return True

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.channel_access_token}",
        }
        payload = {
            "replyToken": reply_token,
            "messages": messages,
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(f"{self.api_url}/reply", json=payload, headers=headers)
                if response.status_code != 200:
                    logger.error(f"LINE Reply Error ({response.status_code}): {response.text}")
                    return False
                return True
        except Exception as e:
            logger.error(f"LINE Reply Exception: {e}")
            return False

    async def push_message(self, to_user_id: str, messages: list[dict[str, Any]]) -> bool:
        """
        Send proactive push message to a specific LINE user.
        """
        if not self.channel_access_token:
            logger.info("LINE_CHANNEL_ACCESS_TOKEN not set. Push simulated.")
            return True

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.channel_access_token}",
        }
        payload = {
            "to": to_user_id,
            "messages": messages,
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(f"{self.api_url}/push", json=payload, headers=headers)
                return response.status_code == 200
        except Exception as e:
            logger.error(f"LINE Push Exception: {e}")
            return False


line_bot_service = LineBotService()
