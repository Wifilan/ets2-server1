"""Environment-driven configuration for the Convoy dedicated server.

Reads ``ETS_SERVER_*`` environment variables and generates the
``server_config.sii`` file consumed by the game server (SCS SII format).
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger(__name__)

#: Values accepted as "true" when parsing boolean environment variables.
TRUTHY_VALUES = frozenset({"yes", "true", "on", "1"})

DEFAULT_CONFIG_FILE_PATH = "/home/steam/.local/share/Euro Truck Simulator 2/server_config.sii"


def is_truthy(value: str) -> bool:
    """Return ``True`` if *value* is "yes", "true", "on" or "1" (case insensitive)."""
    return value.strip().lower() in TRUTHY_VALUES


def env_bool(name: str, default: str) -> bool:
    """Read an environment variable as a boolean flag."""
    return is_truthy(os.getenv(name, default))


def env_int(name: str, default: int) -> int:
    """Read an environment variable as an integer, falling back on bad input."""
    raw = os.getenv(name, str(default))
    try:
        return int(raw)
    except ValueError:
        logger.warning("Invalid integer value %r for %s, using default %d", raw, name, default)
        return default


def generate_moderator_list(mod_list: list) -> str:
    """Generate the ``moderator_list`` block required by ``server_config.sii``.

    Example::

        >>> print(generate_moderator_list(["1028371289", "1247129874"]))
        moderator_list: 2
         moderator_list[0]: 1028371289
         moderator_list[1]: 1247129874
    """
    # A single empty string comes from splitting an unset env variable.
    if not mod_list or (len(mod_list) == 1 and not mod_list[0].strip()):
        return "moderator_list: 0"

    out_str = f"moderator_list: {len(mod_list)}\n"
    for i, mod in enumerate(mod_list):
        out_str += f" moderator_list[{i}]: {str(mod).strip()}\n"

    return out_str


@dataclass
class ServerConfig:
    """All tunables of the dedicated server, populated from the environment."""

    steam_app_id: str = field(default_factory=lambda: os.getenv("APP_ID", ""))
    executable_path: Optional[str] = field(default_factory=lambda: os.getenv("EXECUTABLE"))
    config_file_path: str = field(
        default_factory=lambda: os.getenv("ETS_SERVER_CONFIG_FILE_PATH", DEFAULT_CONFIG_FILE_PATH)
    )
    write_config: bool = field(default_factory=lambda: env_bool("ETS_SERVER_WRITE_CONFIG", "true"))
    update_on_start: bool = field(default_factory=lambda: env_bool("ETS_SERVER_UPDATE_ON_START", "true"))
    branch: Optional[str] = field(default_factory=lambda: os.getenv("ETS_SERVER_BRANCH"))

    name: str = field(default_factory=lambda: os.getenv("ETS_SERVER_NAME", "Euro Truck Simulator 2 Docker Server"))
    description: str = field(default_factory=lambda: os.getenv("ETS_SERVER_DESCRIPTION", ""))
    welcome_message: str = field(default_factory=lambda: os.getenv("ETS_SERVER_WELCOME_MESSAGE", ""))
    password: str = field(default_factory=lambda: os.getenv("ETS_SERVER_PASSWORD", ""))
    logon_token: str = field(default_factory=lambda: os.getenv("ETS_SERVER_LOGON_TOKEN", ""))

    max_players: int = field(default_factory=lambda: env_int("ETS_SERVER_MAX_PLAYERS", 8))
    max_vehicles_total: int = field(default_factory=lambda: env_int("ETS_SERVER_MAX_VEHICLES_TOTAL", 100))
    max_ai_vehicles_player: int = field(default_factory=lambda: env_int("ETS_SERVER_MAX_AI_VEHICLES_PLAYER", 50))
    max_ai_vehicles_player_spawn: int = field(
        default_factory=lambda: env_int("ETS_SERVER_MAX_AI_VEHICLES_PLAYER_SPAWN", 50)
    )

    server_port: int = field(default_factory=lambda: env_int("ETS_SERVER_PORT", 27015))
    query_port: int = field(default_factory=lambda: env_int("ETS_SERVER_QUERY_PORT", 27016))
    connection_virtual_port: int = field(default_factory=lambda: env_int("ETS_SERVER_CONNECTION_VIRTUAL_PORT", 100))
    query_virtual_port: int = field(default_factory=lambda: env_int("ETS_SERVER_QUERY_VIRTUAL_PORT", 101))

    player_damage: bool = field(default_factory=lambda: env_bool("ETS_SERVER_PLAYER_DAMAGE", "true"))
    traffic: bool = field(default_factory=lambda: env_bool("ETS_SERVER_TRAFFIC", "true"))
    hide_in_company: bool = field(default_factory=lambda: env_bool("ETS_SERVER_HIDE_IN_COMPANY", "false"))
    hide_colliding: bool = field(default_factory=lambda: env_bool("ETS_SERVER_HIDE_COLLIDING", "true"))
    force_speed_limiter: bool = field(default_factory=lambda: env_bool("ETS_SERVER_FORCE_SPEEDLIMITER", "false"))
    mods_optioning: bool = field(default_factory=lambda: env_bool("ETS_SERVER_MODS_OPTIONING", "false"))
    timezones: bool = field(default_factory=lambda: env_bool("ETS_SERVER_TIMEZONES", "false"))
    service_no_collision: bool = field(default_factory=lambda: env_bool("ETS_SERVER_SERVICE_NO_COLLISION", "false"))
    in_menu_ghosting: bool = field(default_factory=lambda: env_bool("ETS_SERVER_IN_MENU_GHOSTING", "false"))
    name_tags: bool = field(default_factory=lambda: env_bool("ETS_SERVER_NAME_TAGS", "true"))
    friends_only: bool = field(default_factory=lambda: env_bool("ETS_SERVER_FRIENDS_ONLY", "false"))
    show_server: bool = field(default_factory=lambda: env_bool("ETS_SERVER_SHOW_SERVER", "true"))

    moderators: list = field(default_factory=lambda: os.getenv("ETS_SERVER_MODERATORS", "").split(","))

    @classmethod
    def from_env(cls) -> "ServerConfig":
        """Build the configuration from the current process environment."""
        return cls()

    def to_sii(self) -> str:
        """Render the ``server_config.sii`` document.

        Conforms to the SCS SII scheme (which sadly is not published...).
        The odd indentation of some lines must be kept exactly as-is,
        otherwise the game refuses to parse the file.
        """
        moderator_list_generated = generate_moderator_list(self.moderators)

        def yes_no(value: bool) -> str:
            return "true" if value else "false"

        sii = f"""SiiNunit
{{
server_config : _nameless.44c.eab0 {{
 lobby_name: "{self.name}"
 description: "{self.description}"
 welcome_message: "{self.welcome_message}"
 password: "{self.password}"
 max_players: {self.max_players}
 max_vehicles_total: {self.max_vehicles_total}
 max_ai_vehicles_player: {self.max_ai_vehicles_player}
 max_ai_vehicles_player_spawn: {self.max_ai_vehicles_player_spawn}
 connection_virtual_port: {self.connection_virtual_port}
 query_virtual_port: {self.query_virtual_port}
 connection_dedicated_port: {self.server_port}
 query_dedicated_port: {self.query_port}
 server_logon_token: "{self.logon_token}"
 player_damage: {yes_no(self.player_damage)}
 traffic: {yes_no(self.traffic)}
 hide_in_company: {yes_no(self.hide_in_company)}
 hide_colliding: {yes_no(self.hide_colliding)}
 force_speed_limiter: {yes_no(self.force_speed_limiter)}
 mods_optioning: {yes_no(self.mods_optioning)}
 timezones: {int(self.timezones)}
 service_no_collision: {yes_no(self.service_no_collision)}
 in_menu_ghosting: {yes_no(self.in_menu_ghosting)}
 name_tags: {yes_no(self.name_tags)}
 friends_only: {yes_no(self.friends_only)}
 show_server: {yes_no(self.show_server)}
 {moderator_list_generated}
}}
}}
"""
        return sii

    def write_to_file(self) -> bool:
        """Write the generated SII config to :attr:`config_file_path`.

        Returns ``True`` on success.
        """
        logger.info("Writing config file...")
        config = self.to_sii()
        try:
            with open(self.config_file_path, "w") as f:
                f.write(config)
                f.flush()
        except OSError as exc:
            logger.error("Could not write config file (%s): %s", self.config_file_path, exc)
            return False

        logger.info("Config file written.")
        return True
