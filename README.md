# ets2-ats-convoy-server-docker

Docker images for dedicated **Convoy multiplayer servers** of
*Euro Truck Simulator 2* and *American Truck Simulator*, built on top of
[`cm2network/steamcmd`](https://hub.docker.com/r/cm2network/steamcmd).

The server is configured entirely through environment variables; a small
Python entrypoint generates the game's `server_config.sii` and (optionally)
downloads/updates the server files via SteamCMD before launching.

## Quick start

```yaml
services:
  ets2-server:
    image: wifilan/ets2-convoy-server
    container_name: ets2-server
    restart: unless-stopped
    tty: true
    network_mode: host # important to make the game appear in the server list
    environment:
      - "ETS_SERVER_NAME=My Server"
      - "ETS_SERVER_PASSWORD=abc123"
      - "ETS_SERVER_MAX_PLAYERS=8"
```

For **American Truck Simulator** use the image `wifilan/ats-convoy-server`
(the environment variables are identical, they keep the historical `ETS_`
prefix for compatibility).

> **Note:** `network_mode: host` is required for the server to show up in the
> in-game server list (the server cannot determine its external IP behind NAT).
> If you join via the *direct join token* printed in the logs at startup, plain
> port mapping (`27015/tcp+udp`, `27016/tcp+udp`) also works.

### Volumes

| Path | Purpose |
|------|---------|
| `/app` | Server binaries & libraries (only mount if you know what you are doing — can cause permission issues) |
| `/home/steam/.local/share/Euro Truck Simulator 2` | Save data, mod list (`server_packages.*`), banlist. Mount to persist bans/mods. |
| `/home/steam/.local/share/American Truck Simulator` | Same, but for ATS |

## Configuration (environment variables)

| Variable | Default | Description |
|----------|---------|-------------|
| `ETS_SERVER_WRITE_CONFIG` | `true` | Generate & write `server_config.sii` on startup |
| `ETS_SERVER_UPDATE_ON_START` | `true` | Run SteamCMD `app_update` before starting |
| `ETS_SERVER_BRANCH` | *(none)* | Steam branch/channel to install (e.g. a beta depot) |
| `ETS_SERVER_NAME` | `Euro Truck Simulator 2 Docker Server` | Lobby name |
| `ETS_SERVER_DESCRIPTION` | *(empty)* | Server description |
| `ETS_SERVER_WELCOME_MESSAGE` | *(empty)* | Message shown on join |
| `ETS_SERVER_PASSWORD` | *(empty)* | Join password |
| `ETS_SERVER_MAX_PLAYERS` | `8` | Convoy size limit (>8 see workaround below) |
| `ETS_SERVER_MAX_VEHICLES_TOTAL` | `100` | Total vehicle slots |
| `ETS_SERVER_MAX_AI_VEHICLES_PLAYER` | `50` | AI vehicles per player |
| `ETS_SERVER_MAX_AI_VEHICLES_PLAYER_SPAWN` | `50` | AI vehicles at player spawn |
| `ETS_SERVER_PORT` | `27015` | Dedicated connection port |
| `ETS_SERVER_QUERY_PORT` | `27016` | Dedicated query port |
| `ETS_SERVER_CONNECTION_VIRTUAL_PORT` | `100` | Virtual connection port |
| `ETS_SERVER_QUERY_VIRTUAL_PORT` | `101` | Virtual query port |
| `ETS_SERVER_LOGON_TOKEN` | *(empty)* | Steam logon token for the server account |
| `ETS_SERVER_MODERATORS` | *(empty)* | Comma-separated Steam IDs of moderators |
| `ETS_SERVER_PLAYER_DAMAGE` | `true` | Player vehicle damage |
| `ETS_SERVER_TRAFFIC` | `true` | Traffic simulation |
| `ETS_SERVER_HIDE_IN_COMPANY` | `false` | Hide players in company view |
| `ETS_SERVER_HIDE_COLLIDING` | `true` | Hide colliding trailers |
| `ETS_SERVER_FORCE_SPEEDLIMITER` | `false` | Force speed limiter on |
| `ETS_SERVER_MODS_OPTIONING` | `false` | Allow optional mods |
| `ETS_SERVER_TIMEZONES` | `false` | Enable timezones |
| `ETS_SERVER_SERVICE_NO_COLLISION` | `false` | No collision at service points |
| `ETS_SERVER_IN_MENU_GHOSTING` | `false` | Ghosting while in menu |
| `ETS_SERVER_NAME_TAGS` | `true` | Show name tags |
| `ETS_SERVER_FRIENDS_ONLY` | `false` | Restrict to friends |
| `ETS_SERVER_SHOW_SERVER` | `true` | Advertise server in the public list |
| `ETS_SERVER_CONFIG_FILE_PATH` | `<savegame dir>/server_config.sii` | Where the SII config is written |
| `DEBUG` | *(unset)* | Any value enables debug logging |

Boolean variables accept `yes`, `true`, `on` or `1` (case insensitive).

### More than 8 players

The base game hard-caps the convoy size at 8. When `ETS_SERVER_MAX_PLAYERS`
is greater than 8, the entrypoint patches `g_max_convoy_size` inside
`config_ds.cfg` and locks the file read-only (`chmod 400`) so the game cannot
reset it. On the very first start `config_ds.cfg` does not exist yet — restart
the container once (`docker compose restart`) for the workaround to apply.
Values above 64 are not guaranteed to work.

## Repository layout

```
├── Dockerfile                  # shared image definition (build args switch ETS2 <-> ATS)
├── entrypoint.sh               # container entrypoint: seed packages, run python, exec server
├── ets_server_entrypoint.py    # thin backwards-compatible wrapper script
├── server_entrypoint/          # actual implementation package
│   ├── config.py               #   env parsing + server_config.sii generation
│   ├── server.py               #   SteamCMD update + max-player workaround
│   └── main.py                 #   orchestration (python -m server_entrypoint)
├── default_packages/           # stock server_packages.{sii,dat} per game
│   ├── ets2/
│   └── ats/
├── tests/                      # unit tests (stdlib unittest)
└── .github/workflows/          # CI: build & push both images
```

### Building locally

```bash
echo devel > VERSION                       # the Dockerfile copies VERSION -> /version

# ETS2 (default build args)
docker build -t ets2-convoy-server .

# ATS
docker build -t ats-convoy-server . \
  --build-arg APP_ID=2239530 \
  --build-arg SAVEGAME_LOCATION="/home/steam/.local/share/American Truck Simulator/" \
  --build-arg EXECUTABLE=/app/bin/linux_x64/amtrucks_server \
  --build-arg DEFAULT_PACKAGES=default_packages/ats
```

### Running tests

```bash
python3 -m unittest discover -s tests -v
```

## License

[MIT](LICENSE)
