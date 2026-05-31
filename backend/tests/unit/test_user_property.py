import uuid
from datetime import datetime

from app.models import UserProperty


def test_user_property_defaults() -> None:
    p = UserProperty(user_id=uuid.uuid4(), tier_id=2)
    assert p.tier_id == 2
    assert p.sold_at is None
    assert p.sold_price is None
    assert isinstance(p.id, uuid.UUID)
    assert isinstance(p.purchased_at, datetime)
