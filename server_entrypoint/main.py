"""Entrypoint orchestration for the Convoy dedicated server container.

Run as ``python -m server_entrypoint`` (or via the thin wrapper script
``ets_server_entrypoint.py``) from the container's ``entrypoint.sh``.
"""

from __future__ import annotations

import logging
import os
import sys

from server_entrypoint.config import ServerConfig
from server_entrypoint.server import (
    SUPPORTED_MAX_PLAYERS,
    apply_max_player_workaround,
    ds_config_path_for,
    get_version,
    server_files_exist,
    update_server,
)

logger = logging.getLogger("server_entrypoint")


def setup_logging() -> None:
    """Configure root logging; DEBUG level when the ``DEBUG`` env var is set."""
    debug = os.getenv("DEBUG") is not None
    level = logging.DEBUG if debug else logging.INFO
    fmt = "%(asctime)s [%(levelname)s]: %(message)s"
    if debug:
        fmt += " [%(funcName)s]"
    logging.basicConfig(stream=sys.stdout, level=level, format=fmt, datefmt="%H:%M:%S")
    if debug:
        logger.debug("DEBUG MODE ENABLED!")


def run(config: ServerConfig) -> int:
    """Execute the full startup sequence. Returns a process exit code."""
    logger.info("Docker Container Version: %s", get_version())

    config_written = False
    if config.write_config:
        config_written = config.write_to_file()

    should_update = config.update_on_start or not server_files_exist(config.executable_path)
    if should_update:
        if update_server(config.steam_app_id, config.branch):
            logger.info("Update done.")
        else:
            logger.warning("Server update failed; trying to start with existing files anyway.")
    else:
        logger.info("Skipping server update. To update set 'ETS_SERVER_UPDATE_ON_START=true'.")

    if config_written and config.max_players > SUPPORTED_MAX_PLAYERS:
        apply_max_player_workaround(ds_config_path_for(config.config_file_path), config.max_players)

    return 0


def main(argv=None) -> int:
    """CLI entry point."""
    setup_logging()
    config = ServerConfig.from_env()
    return run(config)


if __name__ == "__main__":
    sys.exit(main())
