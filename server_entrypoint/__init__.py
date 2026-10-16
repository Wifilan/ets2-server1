"""Package for the ETS2/ATS Convoy dedicated server container entrypoint.

The package is split into small, single-responsibility modules:

- :mod:`server_entrypoint.config`  -- environment handling & SII generation
- :mod:`server_entrypoint.server`  -- game server update / player-limit logic
- :mod:`server_entrypoint.main`    -- orchestration (``python -m server_entrypoint``)
"""

__version__ = "0.0.0"
