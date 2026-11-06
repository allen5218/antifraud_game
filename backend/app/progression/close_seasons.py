"""十四天競技賽季關帳 CLI 與排程任務。

功能：
1. 掃描所有已到期 (ends_at <= now) 且尚未 finalized 的賽季。
2. 凍結三榜最終行快照至 season_final_row。
3. 判定參賽門檻，計算玩家跨三榜的最佳 tier。
4. 發放槽位圖紙碎片與稱號，寫入 season_award（防重複領獎、中斷可續跑）。
5. 標記賽季為 finalized。
"""

import argparse
import logging
import signal
import sys
from threading import Event

from sqlmodel import Session

from app.core.db import engine
from app.progression.seasons import close_expired_seasons

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger("close_seasons")


def main() -> int:
    parser = argparse.ArgumentParser(description="關閉到期賽季並發放獎勵")
    parser.add_argument("--watch", action="store_true")
    parser.add_argument("--interval", type=int, default=60)
    args = parser.parse_args()
    if args.interval < 1:
        parser.error("interval must be positive")
    stop = Event()
    signal.signal(signal.SIGTERM, lambda *_: stop.set())
    signal.signal(signal.SIGINT, lambda *_: stop.set())
    while not stop.is_set():
        try:
            with Session(engine) as session:
                closed = close_expired_seasons(session)
            logger.info("關帳檢查完成，處理 %d 期", len(closed))
        except Exception:
            logger.exception("關帳失敗，下次檢查會接續未完成項目")
            if not args.watch:
                return 1
        if not args.watch:
            break
        stop.wait(args.interval)
    return 0


if __name__ == "__main__":
    sys.exit(main())
