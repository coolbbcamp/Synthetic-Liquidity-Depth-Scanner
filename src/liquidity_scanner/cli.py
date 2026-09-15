import argparse
import asyncio

from liquidity_scanner.config import get_settings
from liquidity_scanner.db.session import get_session_factory, init_engine
from liquidity_scanner.logging import configure_logging, get_logger
from liquidity_scanner.registry.service import RegistryService

configure_logging()
logger = get_logger(__name__)


async def cmd_sync_registry() -> None:
    settings = get_settings()
    init_engine()
    factory = get_session_factory()
    async with factory() as session:
        service = RegistryService(settings, session)
        result = await service.sync()
        logger.info("registry_synced", **result)


def main() -> None:
    parser = argparse.ArgumentParser(prog="lds")
    parser.add_argument("command", choices=["sync-registry"])
    args = parser.parse_args()
    if args.command == "sync-registry":
        asyncio.run(cmd_sync_registry())


if __name__ == "__main__":
    main()
