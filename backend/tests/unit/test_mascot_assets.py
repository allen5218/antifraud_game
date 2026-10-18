"""每隻上架的吉祥物都要有四個姿勢的圖檔，價格由低到高、柴犬免費。"""

from pathlib import Path

import pytest

from app.game.seed import MASCOT_ITEMS

PUBLIC = Path(__file__).resolve().parents[3] / "frontend" / "public"
POSES = ("base", "point", "cheer", "think")


@pytest.mark.parametrize("item", MASCOT_ITEMS, ids=lambda item: str(item["name"]))
def test_every_mascot_has_all_four_poses(item: dict[str, str | int]) -> None:
    image_url = str(item["image_url"])
    assert image_url.startswith("/assets/mascot/")
    assert image_url.endswith("/base.webp")
    folder = PUBLIC / image_url.removeprefix("/").removesuffix("base.webp")
    for pose in POSES:
        assert (folder / f"{pose}.webp").is_file(), f"{item['name']} 缺 {pose}.webp"


def test_shop_has_many_mascots_shiba_free_and_unique() -> None:
    names = [str(item["name"]) for item in MASCOT_ITEMS]
    assert len(names) >= 10
    assert len(set(names)) == len(names)
    assert len({item["image_url"] for item in MASCOT_ITEMS}) == len(names)
    costs = {str(item["name"]): int(item["cost"]) for item in MASCOT_ITEMS}
    assert costs["柴犬"] == 0
    assert all(cost > 0 for name, cost in costs.items() if name != "柴犬")
    assert all(item["category"] == "mascot" for item in MASCOT_ITEMS)
