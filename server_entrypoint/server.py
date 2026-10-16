"""Game server helpers: SteamCMD updates and the >8 player workaround."""

from __future__ import annotations

import logging
import os
import re
import subprocess

logger = logging.getLogger(__name__)

STEAMCMD_PATH = "/home/steam/steamcmd/steamcmd.sh"
INSTALL_DIR = "/app"
VERSION_FILE = "/version"

#: The base game only allows up to this many players via server_config.sii.
SUPPORTED_MAX_PLAYERS = 8
#: Beyond this the config_ds.cfg workaround is not known to work at all.
HARD_MAX_PLAYERS = 64


def get_version(version_file: str = VERSION_FILE) -> str:
    """Return the container build version written by CI into ``/version``."""
    try:
        with open(version_file, "r") as f:
            return f.readline().strip()
    except OSError:
        return "unknown"


def server_files_exist(executable_path) -> bool:
    """Check whether the main server executable is already present."""
    if not executable_path:
        return False
    return os.path.isfile(executable_path)


def update_server(app_id: str, branch: str = None) -> bool:
    """Download/update the dedicated server via SteamCMD.

    Returns ``True`` if steamcmd reported a successful exit code.
    """
    logger.info("Updating game server (App ID: %s)...", app_id)
    # Keep the historical single-line steamcmd invocation semantics.
    shell_command = (
        f"{STEAMCMD_PATH} +force_install_dir {INSTALL_DIR} +login anonymous "
        f"+app_update {app_id}"
        + (f" -beta {branch}" if branch else "")
        + " +quit"
    )
    logger.debug("Running: %s", shell_command)
    result = subprocess.run(shell_command, shell=True)
    return result.returncode == 0


def get_current_max_players(config_ds_path: str) -> int:
    """Read ``g_max_convoy_size`` from config_ds.cfg, or 0 if unavailable."""
    if not os.path.isfile(config_ds_path):
        return 0
    with open(config_ds_path, "r") as f:
        for line in f:
            if "g_max_convoy_size" in line:
                match = re.search(r"\d+", line)
                if match:
                    return int(match.group(0))
    return 0


def apply_max_player_workaround(config_ds_path: str, max_players: int) -> None:
    """Unlock more than 8 players by patching ``config_ds.cfg`` read-only.

    The game overwrites ``g_max_convoy_size`` in config_ds.cfg on every start,
    so we rewrite it and then strip write permissions to lock the value in.
    """
    logger.info("You requested more than %d players. Trying a workaround to enable this...",
                SUPPORTED_MAX_PLAYERS)
    if max_players > HARD_MAX_PLAYERS:
        logger.warning("You requested more than %d players. This probably won't work! "
                       "Warranty is out the window!", HARD_MAX_PLAYERS)

    if get_current_max_players(config_ds_path) == max_players:
        logger.info("Requested player count already in config_ds. No changes necessary.")
        return

    if not os.path.isfile(config_ds_path):
        logger.warning("config_ds.cfg does not exist. This is probably since this is the first start.")
        logger.warning("Please restart the container `docker compose restart` to apply player limit workaround.")
        return

    os.chmod(config_ds_path, 0o600)
    with open(config_ds_path, "r") as f:
        lines = f.readlines()

    for idx, line in enumerate(lines):
        if "g_max_convoy_size" in line:
            lines[idx] = re.sub(r"\d+", str(max_players), line)

    try:
        with open(config_ds_path, "w") as fw:
            fw.writelines(lines)
    except OSError as exc:
        logger.error("config_ds.cfg not writable: %s", exc)
        return

    logger.info("config_ds.cfg modified and written.")
    # Lock the file so the game cannot reset the convoy size on startup.
    os.chmod(config_ds_path, 0o400)


def ds_config_path_for(server_config_path: str) -> str:
    """Derive the config_ds.cfg path next to a server_config.sii file."""
    return server_config_path.replace("server_config.sii", "config_ds.cfg")
