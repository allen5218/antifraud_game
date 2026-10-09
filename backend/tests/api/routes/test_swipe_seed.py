from sqlmodel import Session, func, select

from app.core.db import SWIPE_CARDS_SEED, seed_swipe_cards
from app.models import SwipeCard


def test_reseeding_keeps_one_row_per_card_in_every_pool(db: Session) -> None:
    # 每次啟動都會同步一次；檢測卡（pool=exam）也要比對得到，不能每次都再新增
    seed_swipe_cards(db)
    seed_swipe_cards(db)
    for pool in ("practice", "exam"):
        expected = sum(1 for c in SWIPE_CARDS_SEED if c["pool"] == pool)
        keys = {c["seed_key"] for c in SWIPE_CARDS_SEED if c["pool"] == pool}
        count = db.exec(
            select(func.count())
            .select_from(SwipeCard)
            .where(SwipeCard.pool == pool, SwipeCard.seed_key.in_(keys))  # type: ignore[union-attr]
        ).one()
        assert count == expected
