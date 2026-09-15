import asyncio

from liquidity_scanner.config import get_settings
from liquidity_scanner.db.session import init_engine
from liquidity_scanner.logging import configure_logging, get_logger
from liquidity_scanner.scheduler.scheduler import ProbeScheduler  # noqa: PLC0415

configure_logging()
logger = get_logger(__name__)


async def main() -> None:
    settings = get_settings()
    init_engine()
    if not settings.enable_scheduler:
        logger.info("scheduler_disabled")
        while True:
            await asyncio.sleep(3600)
        return

    scheduler = ProbeScheduler(settings)
    await scheduler.sync_registry()
    scheduler.start()
    logger.info("worker_running")
    while True:
        await asyncio.sleep(3600)


if __name__ == "__main__":
    asyncio.run(main())
