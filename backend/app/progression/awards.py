"""賽季的榮譽收藏：獎盃依榜別永久保存，前三級另有吉祥物外觀。能力獎勵（信譽）在 seasons.py 發。"""

import uuid
from collections.abc import Sequence

from sqlmodel import Session

from app.progression.models import PlayerCollectible, SeasonFinalRow


def grant_season_extras(
    session: Session,
    user_id: uuid.UUID,
    season_id: uuid.UUID,
    tier: str,
    final_rows: Sequence[SeasonFinalRow],
) -> None:
    for row in final_rows:
        if row.user_id != user_id or row.award_tier == "unqualified":
            continue
        board_name = {"accuracy": "正確率", "speed": "速度", "power": "養成競技"}[
            row.board
        ]
        session.add(
            PlayerCollectible(
                user_id=user_id,
                item_key=f"trophy_{row.board}_{season_id}",
                kind="trophy",
                name=f"{board_name}第 {row.display_rank} 名紀念獎盃",
                source_season_id=season_id,
            )
        )
    if tier in {"tier_1", "tier_2", "tier_3"}:
        session.add(
            PlayerCollectible(
                user_id=user_id,
                item_key=f"skin_{season_id}",
                kind="pet_skin",
                name={"tier_1": "冠軍星光", "tier_2": "菁英極光", "tier_3": "勇者光環"}[
                    tier
                ],
                source_season_id=season_id,
            )
        )
