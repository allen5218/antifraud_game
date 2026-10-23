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
        # 官方列為暗語、但日常常用的詞，沒有使用毒品的說法就不擋
        "嗨，你今天吃飯了嗎",
        "這件衣服還有貨嗎",
        "冰塊加多一點，謝謝",
        "我想喝杯冰沙",
        "SK-II 神仙水是正品嗎",
        "我家的貓一直喵喵叫",
        "這個草莓好甜",
        "我在練四號球",
        "孫悟空好帥",
        "小朋友在吹氣球",
        "你這招很屌",
        "從台中出發要多久",
        "我愛愛情電影",
        "他應召入伍了",
        "週末去室內射箭",
        "我們店無套餐優惠",
        "週末去拉KTV嗎",
        "我喜歡 pink 粉色系",
        "這瓶 5kg 水很重",
        "我小孩有吃利他能",
        "可以先包養我嗎",
        "我不要傳私密照",
        "我們用新的 method 計算",
        "這份 document 很長",
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
        # 毒品學名、俗稱與暗語（食藥署、法務部反毒大本營）
        "你有甲基苯丙胺嗎",
        "要不要冰毒",
        "我有阿德拉可以分你",
        "安公子一包多少",
        "來點K仔",
        "要不要拉K",
        "有沒有喵喵粉",
        "喪屍煙彈很嗨",
        "依托咪酯哪裡買",
        "上頭菸試試",
        "毒咖啡包",
        "彩虹菸",
        "一起吸笑氣",
        "我有FM2",
        "失身水",
        "G水",
        "呼麻嗎",
        "哈草",
        "海洛因",
        "四號仔",
        "古柯鹼",
        "一粒沙",
        "搖腳丸",
        "魔菇",
        "芬太尼",
        "找藥頭",
        "want some weed",
        "got adderall",
        # 暗語＋使用毒品的說法
        "要不要來點冰嗨一下",
        "四號打一管",
        "咖啡包一起嗨",
        "這草吸一口就茫了",
        # 色情與性交易暗語
        "約P嗎",
        "砲友",
        "嘿咻",
        "啪啪啪",
        "瑟瑟",
        "外送茶多少錢",
        "有茶訊嗎",
        "吃魚喝茶",
        "援交",
        "叫小姐",
        "口爆",
        "打手槍",
        "18禁",
        "幼女",
        "send nudes and porn",
        "f.u.c.k",
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
