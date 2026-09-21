"""席爾迪尼 (Robert Cialdini) 七大說服槓桿透視鏡 (Weapons of Influence Scanner)。

學術依據:
Cialdini, R. B. (1984, 2021). Influence: Science and Practice & Pre-Suasion.
詐騙集團本質上即是高度精密化、產業化的說服槓桿操縱者。
本模組提供文字操縱特徵辨識，促成認知「遠遷移 (Far Transfer)」：
使玩家跳脫個別話術題目死記，直擊背後的 7 大心理武器架構。
"""

from __future__ import annotations

import re
from pydantic import BaseModel


class InfluenceCue(BaseModel):
    lever: str
    lever_name: str
    trigger_phrase: str
    psychological_trap: str
    counter_measure: str


INFLUENCE_LEVERS: dict[str, dict[str, str]] = {
    "authority": {
        "name": "權威服從 (Authority)",
        "trap": "以國家司法機關、檢警公文、金管會官員或專業頭銜製造階級壓迫，迫使大腦關閉質疑能力",
        "counter": "任何公務機關絕不會要求電話製作筆錄、遠端交出帳密或監管帳戶，應立即掛斷並進線 165 求證",
    },
    "scarcity": {
        "name": "稀缺急迫 (Scarcity)",
        "trap": "人為製造剩餘名額倒數、最後 15 分鐘、逾期凍結等時間壓力，引發錯失恐懼 (FOMO) 與非理性決策",
        "counter": "強制自我冷靜：所有合法行政或商業交易皆具備正規通知期，凡是催促立即操作者一律提高戒備",
    },
    "reciprocity": {
        "name": "互惠效應 (Reciprocity)",
        "trap": "先主動提供小恩小惠、免費報牌、禮券贈品或代墊保證金，觸發受害者『知恩圖報』的道德虧欠感",
        "counter": "認清天下沒有白吃的午餐，天上掉下來的無償利益背後必隱藏高額代價，果斷切斷不對等聯繫",
    },
    "social_proof": {
        "name": "社會認同 (Social Proof)",
        "trap": "在封閉社群由大量暗樁假帳號狂發獲利截圖、提領感謝文，營造『其他人都在賺只有我沒跟上』的虛假群眾背書",
        "counter": "群組內 99% 皆為同夥機器人，獨立透過政府公私名冊查驗，不將群體熱度作為真實性依據",
    },
    "consistency": {
        "name": "承諾一致 (Consistency)",
        "trap": "利用登門檻效應 (Foot-in-the-door)，從點擊連結、小額出金等微小承諾開始，逐步綁架沉沒成本",
        "counter": "勇於及時停損 (Sunk Cost Detachment)：一旦發現疑點，無論先前投入多少時間與金錢，立刻中止一切操作",
    },
    "liking": {
        "name": "喜好親近 (Liking)",
        "trap": "運用高顏值人設、偽造相同興趣、早晚貼心問候與訴說悲慘身世，建立人際好感以削弱防備心理",
        "counter": "虛擬身分容易偽造，在未透過現實第三方驗證前，始終將金錢決策與情感交流劃清界線",
    },
    "unity": {
        "name": "群體歸屬 (Unity)",
        "trap": "訴諸同鄉、同宗、校友、同宗教或特定政治立場的『自己人』意識，使受害者放下對圈內人的防範",
        "counter": "涉資不分親疏圈層，重大財務交易皆必須透過合約與官方金流信託履約，杜絕熟人偏誤",
    },
}

# 繁體中文高頻話術模式庫
PATTERN_RULES: list[tuple[str, str, str]] = [
    (
        "authority",
        r"(地檢署|檢察官|刑事局|警調|特偵組|分局|監管帳戶|涉嫌洗錢|公文傳真|拘提|保密原則|開庭)",
        "假冒公務權威話術",
    ),
    (
        "scarcity",
        r"(限時|立刻|最後.*名額|即刻凍結|逾期無效|倒數|搶先|手慢無|僅剩|緊急手續)",
        "製造急迫時間稀缺話術",
    ),
    (
        "reciprocity",
        r"(免費領取|送你.*飆股|老師代墊|贈金|好禮相贈|不用錢先試聽|無償提供)",
        "誘發心理虧欠互惠話術",
    ),
    (
        "social_proof",
        r"(大家都|學員已提領|萬人見證|群組.*曬單|大家都賺到|老學員獲利|全員一致好評)",
        "暗樁水軍從眾效應話術",
    ),
    (
        "consistency",
        r"(先投入.*試水|第一次.*成功出金|既然都已經.*不如再補|就差最後一步手續費)",
        "逐步綁架沉沒成本一致性話術",
    ),
    (
        "liking",
        r"(小哥哥|小姐姐|早安.*心疼你|我只跟你說|看到你就覺得投緣|想跟你一起生活)",
        "情感人設好感套路話術",
    ),
    (
        "unity",
        r"(我們都是.*同鄉|校友專屬|信徒大家庭|都是自己人|只有我們這個圈子才懂)",
        "圈子群體歸屬認同話術",
    ),
]


def scan_influence_cues(text: str) -> list[InfluenceCue]:
    """掃描輸入文字，回傳符合席爾迪尼 7 大說服槓桿之特徵與認知防護建議。"""
    detected_cues: list[InfluenceCue] = []
    seen_levers: set[str] = set()

    for lever, pattern, phrase_label in PATTERN_RULES:
        if lever in seen_levers:
            continue
        match = re.search(pattern, text)
        if match:
            seen_levers.add(lever)
            meta = INFLUENCE_LEVERS[lever]
            detected_cues.append(
                InfluenceCue(
                    lever=lever,
                    lever_name=meta["name"],
                    trigger_phrase=f"{phrase_label}：『{match.group(0)}』",
                    psychological_trap=meta["trap"],
                    counter_measure=meta["counter"],
                )
            )

    return detected_cues
