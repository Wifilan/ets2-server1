"""Unit tests for the server_entrypoint package (stdlib unittest only)."""

import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from server_entrypoint.config import ServerConfig, generate_moderator_list, is_truthy  # noqa: E402
from server_entrypoint.server import (  # noqa: E402
    apply_max_player_workaround,
    ds_config_path_for,
    get_current_max_players,
    server_files_exist,
)


class IsTruthyTests(unittest.TestCase):
    def test_true_values(self):
        for value in ("yes", "YES", " true ", "On", "1"):
            self.assertTrue(is_truthy(value), value)

    def test_false_values(self):
        for value in ("no", "false", "0", "", "maybe"):
            self.assertFalse(is_truthy(value), value)


class ModeratorListTests(unittest.TestCase):
    def test_empty_env_split_yields_zero(self):
        self.assertEqual(generate_moderator_list([""]), "moderator_list: 0")

    def test_multiple_moderators(self):
        out = generate_moderator_list(["1028371289", "1247129874"])
        self.assertIn("moderator_list: 2", out)
        self.assertIn(" moderator_list[0]: 1028371289", out)
        self.assertIn(" moderator_list[1]: 1247129874", out)


class ConfigGenerationTests(unittest.TestCase):
    def test_sii_output_contains_expected_keys(self):
        cfg = ServerConfig(
            name="Test Server",
            description="desc",
            welcome_message="welcome",
            password="secret",
            max_players=16,
            moderators=["1", "2"],
        )
        sii = cfg.to_sii()
        self.assertTrue(sii.startswith("SiiNunit\n{\nserver_config : _nameless.44c.eab0 {\n"))
        self.assertIn(' lobby_name: "Test Server"', sii)
        self.assertIn(" max_players: 16", sii)
        self.assertIn(" player_damage: true", sii)
        self.assertIn(" timezones: 0", sii)
        self.assertIn("moderator_list: 2", sii)
        self.assertTrue(sii.endswith("\n}\n}\n"))

    def test_write_to_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "server_config.sii")
            cfg = ServerConfig(config_file_path=path)
            self.assertTrue(cfg.write_to_file())
            with open(path) as f:
                self.assertIn("SiiNunit", f.read())

    def test_int_parsing_falls_back_on_bad_input(self):
        old = os.environ.get("ETS_SERVER_MAX_PLAYERS")
        os.environ["ETS_SERVER_MAX_PLAYERS"] = "not-a-number"
        try:
            self.assertEqual(ServerConfig().max_players, 8)
        finally:
            if old is None:
                del os.environ["ETS_SERVER_MAX_PLAYERS"]
            else:
                os.environ["ETS_SERVER_MAX_PLAYERS"] = old


class MaxPlayerWorkaroundTests(unittest.TestCase):
    def _write_ds_cfg(self, tmp, value=8):
        path = os.path.join(tmp, "config_ds.cfg")
        with open(path, "w") as f:
            f.write(f'g_max_convoy_size : "{value}"\n')
        return path

    def test_reads_current_value(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = self._write_ds_cfg(tmp, 8)
            self.assertEqual(get_current_max_players(path), 8)

    def test_missing_file_returns_zero(self):
        self.assertEqual(get_current_max_players("/nonexistent/config_ds.cfg"), 0)

    def test_patch_and_lock(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = self._write_ds_cfg(tmp, 8)
            apply_max_player_workaround(path, 16)
            self.assertEqual(get_current_max_players(path), 16)
            mode = oct(os.stat(path).st_mode & 0o777)
            self.assertEqual(mode, "0o400")

    def test_no_change_when_already_set(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = self._write_ds_cfg(tmp, 16)
            os.chmod(path, 0o400)
            apply_max_player_workaround(path, 16)
            # File untouched: still read-only and unchanged.
            self.assertEqual(oct(os.stat(path).st_mode & 0o777), "0o400")

    def test_first_start_missing_file_does_not_raise(self):
        """Regression: old code crashed with AttributeError on missing file."""
        with tempfile.TemporaryDirectory() as tmp:
            apply_max_player_workaround(os.path.join(tmp, "config_ds.cfg"), 16)

    def test_no_digits_line_is_skipped(self):
        """Regression: old get_current_max_players crashed on digit-less lines."""
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "config_ds.cfg")
            with open(path, "w") as f:
                f.write('g_max_convoy_size_without_digits : "x"\n')
            self.assertEqual(get_current_max_players(path), 0)

    def test_ds_path_derivation(self):
        self.assertEqual(
            ds_config_path_for("/data/server_config.sii"), "/data/config_ds.cfg"
        )


class ServerFilesExistTests(unittest.TestCase):
    def test_none_path(self):
        self.assertFalse(server_files_exist(None))

    def test_existing_file(self):
        with tempfile.NamedTemporaryFile() as f:
            self.assertTrue(server_files_exist(f.name))


if __name__ == "__main__":
    unittest.main()
