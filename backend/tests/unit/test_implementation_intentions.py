import pytest
from app.core.implementation_intentions import (
    REFLEX_CARDS_CATALOG,
    compute_equipped_bonuses,
    get_all_reflex_cards,
    get_reflex_card,
)


def test_reflex_cards_catalog() -> None:
    cards = get_all_reflex_cards()
    assert len(cards) == 5
    for c in cards:
        assert c.if_trigger.startswith("IF:")
        assert c.then_action.startswith("THEN:")
        assert c.brake_latency_bonus >= 2.0
        assert 0.2 <= c.damage_mitigation_rate <= 0.35
        assert c.far_transfer_multiplier >= 1.25


def test_get_single_reflex_card() -> None:
    card = get_reflex_card("authority_audit")
    assert card is not None
    assert card.weakness_tag == "authority"
    assert "165" in card.then_action


def test_compute_equipped_bonuses() -> None:
    # No cards equipped
    empty_res = compute_equipped_bonuses([])
    assert empty_res["total_brake_latency"] == 0.0
    assert empty_res["equipped_count"] == 0
    assert empty_res["far_transfer_multiplier"] == 1.0

    # 2 cards equipped
    res = compute_equipped_bonuses(["time_pressure_brake", "authority_audit"])
    assert res["total_brake_latency"] == 5.5
    assert res["equipped_count"] == 2
    assert res["tag_mitigations"]["time_pressure"] == 0.25
    assert res["tag_mitigations"]["authority"] == 0.30
    assert res["far_transfer_multiplier"] == 1.40
