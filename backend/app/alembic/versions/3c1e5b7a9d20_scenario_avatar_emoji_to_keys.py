"""scenario avatar: emoji -> illustration keys

情境聯絡人的頭貼從 emoji 換成插圖。新場次由 AVATAR_POOL 直接給代號;
這裡把既有場次存的 emoji 換成同一格位置的代號(舊池與新池一一對應),
收件匣裡的舊對話才不會顯示成通用圖示。

Revision ID: 3c1e5b7a9d20
Revises: 97fd54061f12
Create Date: 2026-09-25 09:10:00.000000

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "3c1e5b7a9d20"
down_revision = "97fd54061f12"
branch_labels = None
depends_on = None

# 改版前的 AVATAR_POOL,順序即代號的編號
OLD_POOL: dict[str, list[str]] = {
    "investment": ["🧑‍💼", "📊", "💹"],
    "shopping": ["🛍️", "📦", "🧸"],
    "fake-sale": ["🛎️", "📮", "🧑‍💻"],
    "romance": ["🙂", "🌻", "📷"],
    "atm": ["☎️", "🎧", "📞"],
}

_UPDATE = sa.text(
    "UPDATE scenario_session SET avatar = :new "
    "WHERE fraud_type = :fraud_type AND avatar = :old"
)


def _pairs() -> list[tuple[str, str, str]]:
    return [
        (fraud_type, emoji, f"{fraud_type}-{n}")
        for fraud_type, emojis in OLD_POOL.items()
        for n, emoji in enumerate(emojis, start=1)
    ]


def upgrade():
    conn = op.get_bind()
    for fraud_type, emoji, key in _pairs():
        conn.execute(_UPDATE, {"fraud_type": fraud_type, "old": emoji, "new": key})


def downgrade():
    conn = op.get_bind()
    for fraud_type, emoji, key in _pairs():
        conn.execute(_UPDATE, {"fraud_type": fraud_type, "old": key, "new": emoji})
