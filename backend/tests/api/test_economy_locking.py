import threading
import uuid

from sqlmodel import Session

from app.core.db import engine
from app.economy import service
from app.models import User


def _create_user(*, cash: int) -> uuid.UUID:
    with Session(engine) as session:
        user = User(
            email=f"lock-{uuid.uuid4()}@example.com",
            hashed_password="not-used",
            cash=cash,
        )
        session.add(user)
        session.commit()
        session.refresh(user)
        return user.id


def _delete_user(user_id: uuid.UUID) -> None:
    with Session(engine) as session:
        user = session.get(User, user_id)
        if user is not None:
            session.delete(user)
            session.commit()


def test_lock_user_reloads_value_changed_by_another_session() -> None:
    user_id = _create_user(cash=100)
    try:
        with Session(engine) as stale_session:
            stale_user = stale_session.get(User, user_id)
            assert stale_user is not None
            assert stale_user.cash == 100

            with Session(engine) as writer_session:
                fresh_user = writer_session.get(User, user_id)
                assert fresh_user is not None
                fresh_user.cash = 175
                writer_session.add(fresh_user)
                writer_session.commit()

            locked_user = service.lock_user(stale_session, stale_user)

            assert locked_user is stale_user
            assert locked_user.cash == 175
            stale_session.rollback()
    finally:
        _delete_user(user_id)


def test_lock_user_serializes_concurrent_cash_changes() -> None:
    user_id = _create_user(cash=1_000)
    loaded = threading.Barrier(2)
    failures: list[BaseException] = []

    def change_cash(delta: int) -> None:
        try:
            with Session(engine) as session:
                user = session.get(User, user_id)
                assert user is not None
                # 兩條連線都先載入相同舊值，刻意重現 request dependency 的行為。
                loaded.wait(timeout=5)
                locked_user = service.lock_user(session, user)
                service.adjust_cash(locked_user, delta, reason="concurrency_test")
                session.add(locked_user)
                session.commit()
        except BaseException as exc:
            failures.append(exc)

    try:
        threads = [
            threading.Thread(target=change_cash, args=(-12_000,)),
            threading.Thread(target=change_cash, args=(200,)),
        ]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(timeout=10)

        assert all(not thread.is_alive() for thread in threads)
        assert failures == []
        with Session(engine) as session:
            user = session.get(User, user_id)
            assert user is not None
            assert user.cash == -10_800
    finally:
        _delete_user(user_id)
