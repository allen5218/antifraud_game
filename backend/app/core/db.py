from sqlmodel import Session, create_engine, select

from app import crud
from app.core.config import settings
from app.game.seed import seed_mascot_items, seed_pretest_questions
from app.models import PropertyTier, User, UserCreate

engine = create_engine(str(settings.SQLALCHEMY_DATABASE_URI))

PROPERTY_TIERS_SEED = [
    (1, "雅房", "tier-1", 1000, 5, 1),
    (2, "套房", "tier-2", 5000, 35, 1),
    (3, "兩房公寓", "tier-3", 25000, 250, 2),
    (4, "三房公寓", "tier-4", 100000, 1200, 3),
    (5, "別墅", "tier-5", 300000, 4200, 5),
    (6, "豪宅", "tier-6", 1000000, 15000, 10),
]


def seed_property_tiers(session: Session) -> None:
    for id_, name, svg, price, income, unlock in PROPERTY_TIERS_SEED:
        if session.get(PropertyTier, id_):
            continue
        session.add(
            PropertyTier(
                id=id_,
                name=name,
                svg_key=svg,
                price=price,
                daily_income=income,
                unlock_level=unlock,
            )
        )
    session.commit()


# make sure all SQLModel models are imported (app.models) before initializing DB
# otherwise, SQLModel might fail to initialize relationships properly
# for more details: https://github.com/fastapi/full-stack-fastapi-template/issues/28


def init_db(session: Session) -> None:
    # Tables should be created with Alembic migrations
    # But if you don't want to use migrations, create
    # the tables un-commenting the next lines
    # from sqlmodel import SQLModel

    # This works because the models are already imported and registered from app.models
    # SQLModel.metadata.create_all(engine)

    user = session.exec(
        select(User).where(User.email == settings.FIRST_SUPERUSER)
    ).first()
    if not user:
        user_in = UserCreate(
            email=settings.FIRST_SUPERUSER,
            password=settings.FIRST_SUPERUSER_PASSWORD,
            is_superuser=True,
        )
        user = crud.create_user(session=session, user_create=user_in)

    seed_pretest_questions(session)
    seed_mascot_items(session)
    seed_property_tiers(session)
