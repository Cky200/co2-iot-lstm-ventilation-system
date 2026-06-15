"""CLI entrypoint for Phase 5 firmware."""

from __future__ import annotations

import asyncio
import logging

from .app import FirmwareApp
from .config import AppConfig
from .logging_config import configure_logging


def main() -> None:
    config = AppConfig()
    configure_logging(config.log_level)
    try:
        asyncio.run(FirmwareApp(config).run())
    except KeyboardInterrupt:
        pass
    except Exception:
        logging.getLogger(__name__).exception("Firmware crashed")
        raise


if __name__ == "__main__":
    main()
