"""Gollwitzer (1999) 執行意圖 (Implementation Intentions) 認知反射卡核心系統。

心理學依據:
Peter M. Gollwitzer (1999) "Implementation Intentions: Strong Effects of Simple Plans"
American Psychologist, 54(7), 493-503.
將抽象防詐知識轉化為具體的條件式情境反應劇本:
IF (遭遇特定誘餌情境) -> THEN (自動化啟動批判查核與冷靜中斷)。
"""

from __future__ import annotations

from typing import Any
from pydantic import BaseModel


class ReflexCardDefinition(BaseModel):
    id: str
    name: str
    weakness_tag: str
    title_label: str
    if_trigger: str
    then_action: str
    psychological_basis: str
    passive_bonus_text: str
    brake_latency_bonus: float  # 延長踩煞車冷靜時長 (秒)
    damage_mitigation_rate: float  # 降低情境失誤損失比例 (0.0 - 1.0)
    far_transfer_multiplier: float  # 遠遷移非題庫題目之辨別率加成


REFLEX_CARDS_CATALOG: dict[str, ReflexCardDefinition] = {
    "time_pressure_brake": ReflexCardDefinition(
        id="time_pressure_brake",
        name="時間壓力·冷靜煞車卡",
        weakness_tag="time_pressure",
        title_label="即時中斷反射",
        if_trigger="IF: 對方以倒數計時、緊急扣款、限時取消等話術催促立即操作",
        then_action="THEN: 強制關閉視窗冷靜 15 分鐘，並主動撥打官方或家人電話反查",
        psychological_basis="Loewenstein 內臟狀態理論：用人為摩擦力 (Friction) 中斷焦慮情緒對前額葉皮質的劫持",
        passive_bonus_text="時間壓力類題型決策煞車 +2.5秒，誤判損失降低 25%",
        brake_latency_bonus=2.5,
        damage_mitigation_rate=0.25,
        far_transfer_multiplier=1.35,
    ),
    "authority_audit": ReflexCardDefinition(
        id="authority_audit",
        name="司法權威·雙向求證卡",
        weakness_tag="authority",
        title_label="官方溯源反射",
        if_trigger="IF: 對方自稱檢察官、警官、法院人員，宣稱偵查不公開或要求監管帳戶",
        then_action="THEN: 立即掛斷電話，拒絕加入任何通訊軟體，自行進線 165 反詐騙諮詢專線",
        psychological_basis="Milgram 服從實驗反制：打破對權威符號的被動盲從，建立獨立公務渠道查證習慣",
        passive_bonus_text="權威服從類題型決策煞車 +3.0秒，誤判損失降低 30%",
        brake_latency_bonus=3.0,
        damage_mitigation_rate=0.30,
        far_transfer_multiplier=1.40,
    ),
    "greed_freeze": ReflexCardDefinition(
        id="greed_freeze",
        name="高利誘惑·零信原則卡",
        weakness_tag="greed",
        title_label="利益脫鉤反射",
        if_trigger="IF: 遭遇宣稱穩賺不賠、內線明牌、保證獲利或代操翻倍之投資邀約",
        then_action="THEN: 視為 100% 惡意詐騙，拒絕轉帳至非金管會核准之私人帳戶或假平台",
        psychological_basis="Kahneman 展望理論：識破誘餌利用損失厭惡與貪婪偏差所製造的非理性承擔風險",
        passive_bonus_text="貪念誘惑類題型決策煞車 +2.0秒，誤判損失降低 25%",
        brake_latency_bonus=2.0,
        damage_mitigation_rate=0.25,
        far_transfer_multiplier=1.30,
    ),
    "social_proof_verify": ReflexCardDefinition(
        id="social_proof_verify",
        name="群眾認同·獨立覆核卡",
        weakness_tag="social_proof",
        title_label="去從眾化反射",
        if_trigger="IF: 看到社群狂熱曬單、聊天群組大量成員宣稱已提領大筆獲利",
        then_action="THEN: 假定群組全員為暗樁水軍，立即登入金管會或投信投顧公會官網查核合法登記",
        psychological_basis="Asch 從眾實驗抗體：建立獨立客觀資料庫查詢，消除盲目跟隨群體常模的虛假安全感",
        passive_bonus_text="社會認同類題型決策煞車 +2.2秒，誤判損失降低 25%",
        brake_latency_bonus=2.2,
        damage_mitigation_rate=0.25,
        far_transfer_multiplier=1.32,
    ),
    "trust_refuse": ReflexCardDefinition(
        id="trust_refuse",
        name="人設信任·財務底線卡",
        weakness_tag="trust_building",
        title_label="金錢隔離反射",
        if_trigger="IF: 網路上認識之交友對象或虛擬好友，在建立信任感後提及金錢借貸、代買或投資",
        then_action="THEN: 堅守絕對財務底線，秉持「談感情可以，碰金錢立即封鎖」原則",
        psychological_basis="Cialdini 互惠與喜好槓桿阻斷：將情感交流與金錢決策進行物理級神經隔離",
        passive_bonus_text="信任建立類題型決策煞車 +2.8秒，誤判損失降低 30%",
        brake_latency_bonus=2.8,
        damage_mitigation_rate=0.30,
        far_transfer_multiplier=1.38,
    ),
}


def get_all_reflex_cards() -> list[ReflexCardDefinition]:
    """取得所有可用認知反射卡清單。"""
    return list(REFLEX_CARDS_CATALOG.values())


def get_reflex_card(card_id: str) -> ReflexCardDefinition | None:
    """依 card_id 取得指定反射卡定義。"""
    return REFLEX_CARDS_CATALOG.get(card_id)


def compute_equipped_bonuses(equipped_card_ids: list[str]) -> dict[str, Any]:
    """計算玩家當前裝備反射卡帶來的被動抗性加成。"""
    total_brake_latency = 0.0
    tag_mitigations: dict[str, float] = {}
    far_transfer_boost = 1.0

    for card_id in equipped_card_ids:
        card = REFLEX_CARDS_CATALOG.get(card_id)
        if not card:
            continue
        total_brake_latency += card.brake_latency_bonus
        tag_mitigations[card.weakness_tag] = max(
            tag_mitigations.get(card.weakness_tag, 0.0),
            card.damage_mitigation_rate,
        )
        far_transfer_boost = max(far_transfer_boost, card.far_transfer_multiplier)

    return {
        "total_brake_latency": round(total_brake_latency, 2),
        "tag_mitigations": tag_mitigations,
        "far_transfer_multiplier": round(far_transfer_boost, 2),
        "equipped_count": len(equipped_card_ids),
    }
