"""情境對抗玩家輸入的檢查：毒品色情、海綿樣本、正常聊天不能誤擋。"""

import pytest

from app.scenario.input_guard import (
    MAX_CHARS,
    InputRejected,
    check_player_text,
    contains_blocked_term,
)


@pytest.mark.parametrize(
    "text",
    [
        "所以不約了?",
        "對我而言不重要 約嗎",
        "你在哪裡工作？可以視訊嗎😊",
        "哈哈哈哈哈哈哈哈哈哈哈哈",
        "我在做愛心活動，這週比較忙",
        "這是大麻煩耶",
        "我不會傳裸照給你",
        "你是不是想一夜情",
        "我住 Essex，現在要匯款到 ATM 嗎?",
        "OK, call me later 我等你",
        "價格 1,500 元可以嗎？運費 $60",
    ],
)
def test_normal_chat_passes(text: str) -> None:
    assert check_player_text(text)


@pytest.mark.parametrize(
    "text",
    [
        "要不要一起吸毒",
        "我有大麻要不要",
        "賣你K他命",
        "我們來做愛",
        "做 . 愛",
        "做　愛",
        "約砲嗎",
        "看A片",
        "want some cocaine",
        "lets have SEX",
        "ｓｅｘ",
    ],
)
def test_drugs_and_sexual_content_blocked(text: str) -> None:
    with pytest.raises(InputRejected) as rejected:
        check_player_text(text)
    assert rejected.value.code == "message_blocked"


@pytest.mark.parametrize(
    ("text", "code"),
    [
        ("", "message_empty"),
        ("   \n\t ", "message_empty"),
        ("​​​", "message_empty"),
        ("好" * (MAX_CHARS + 1), "message_too_long"),
        # 塞滿看不見字元：整理前就太長
        ("你好" + "​" * (MAX_CHARS * 2), "message_too_long"),
        ("啊" * 21, "message_garbled"),
        ("ꙮ" * 15 + "你好", "message_garbled"),
        ("∑∫∂√∞≈≠≤≥⊕⊗⊥∠∵∴ 你好", "message_garbled"),
    ],
)
def test_sponge_and_empty_inputs_rejected(text: str, code: str) -> None:
    with pytest.raises(InputRejected) as rejected:
        check_player_text(text)
    assert rejected.value.code == code


def test_text_is_normalized() -> None:
    assert check_player_text("  你好\n\n  請問​在嗎？ ") == "你好 請問在嗎?"
    assert check_player_text("好的" * (MAX_CHARS // 2)) == "好的" * (MAX_CHARS // 2)


def test_reply_filter_uses_same_terms() -> None:
    assert contains_blocked_term("要不要試試安非他命")
    assert not contains_blocked_term("等合約結束回台灣，一定見你")


def test_ai_reply_with_blocked_terms_is_rewritten() -> None:
    from app.scenario.agent import _text_reveals_identity

    assert "inappropriate" in _text_reveals_identity("我這裡有大麻，要不要試試")
    assert _text_reveals_identity("我這週工作比較忙，晚點聊") == []
