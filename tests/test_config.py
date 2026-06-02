from pathlib import Path

import pytest

from invgate_service_desk_mcp.config import Config, ConfigError


def test_loads_from_env_vars():
    env = {
        "INVGATE_BASE_URL": "https://acme.sd.cloud.invgate.net",
        "INVGATE_API_TOKEN": "tok-123",
    }

    config = Config.load(env=env, config_path=Path("/does/not/exist.toml"))

    assert config.base_url == "https://acme.sd.cloud.invgate.net"
    assert config.api_token == "tok-123"


def test_loads_from_toml_when_env_missing(tmp_path):
    config_file = tmp_path / "config.toml"
    config_file.write_text(
        'base_url = "https://from-toml.sd.cloud.invgate.net"\n'
        'api_token = "tok-toml"\n'
    )

    config = Config.load(env={}, config_path=config_file)

    assert config.base_url == "https://from-toml.sd.cloud.invgate.net"
    assert config.api_token == "tok-toml"


def test_env_vars_win_over_toml(tmp_path):
    config_file = tmp_path / "config.toml"
    config_file.write_text(
        'base_url = "https://from-toml.sd.cloud.invgate.net"\n'
        'api_token = "tok-toml"\n'
    )
    env = {"INVGATE_API_TOKEN": "tok-env"}

    config = Config.load(env=env, config_path=config_file)

    assert config.base_url == "https://from-toml.sd.cloud.invgate.net"  # from TOML
    assert config.api_token == "tok-env"  # env overrides TOML


def test_strips_trailing_slash_from_base_url():
    env = {
        "INVGATE_BASE_URL": "https://acme.sd.cloud.invgate.net/",
        "INVGATE_API_TOKEN": "tok-123",
    }

    config = Config.load(env=env, config_path=Path("/does/not/exist.toml"))

    assert config.base_url == "https://acme.sd.cloud.invgate.net"


def test_raises_when_base_url_missing():
    env = {"INVGATE_API_TOKEN": "tok-123"}

    with pytest.raises(ConfigError, match="base_url"):
        Config.load(env=env, config_path=Path("/does/not/exist.toml"))


def test_raises_when_api_token_missing():
    env = {"INVGATE_BASE_URL": "https://acme.sd.cloud.invgate.net"}

    with pytest.raises(ConfigError, match="api_token"):
        Config.load(env=env, config_path=Path("/does/not/exist.toml"))


def test_writes_disabled_by_default():
    env = {
        "INVGATE_BASE_URL": "https://acme.sd.cloud.invgate.net",
        "INVGATE_API_TOKEN": "tok-123",
    }

    config = Config.load(env=env, config_path=Path("/does/not/exist.toml"))

    assert config.enable_writes is False


@pytest.mark.parametrize("value", ["1", "true", "TRUE", "yes", "on"])
def test_enable_writes_from_env_truthy(value):
    env = {
        "INVGATE_BASE_URL": "https://acme.sd.cloud.invgate.net",
        "INVGATE_API_TOKEN": "tok-123",
        "INVGATE_ENABLE_WRITES": value,
    }

    config = Config.load(env=env, config_path=Path("/does/not/exist.toml"))

    assert config.enable_writes is True


@pytest.mark.parametrize("value", ["0", "false", "no", ""])
def test_enable_writes_from_env_falsy(value):
    env = {
        "INVGATE_BASE_URL": "https://acme.sd.cloud.invgate.net",
        "INVGATE_API_TOKEN": "tok-123",
        "INVGATE_ENABLE_WRITES": value,
    }

    config = Config.load(env=env, config_path=Path("/does/not/exist.toml"))

    assert config.enable_writes is False


def test_enable_writes_from_toml(tmp_path):
    config_file = tmp_path / "config.toml"
    config_file.write_text(
        'base_url = "https://from-toml.sd.cloud.invgate.net"\n'
        'api_token = "tok-toml"\n'
        "enable_writes = true\n"
    )

    config = Config.load(env={}, config_path=config_file)

    assert config.enable_writes is True


def test_telemetry_disabled_by_default():
    config = Config.load(
        {"INVGATE_BASE_URL": "https://x.invgate.net", "INVGATE_API_TOKEN": "t"},
        config_path=Path("/does/not/exist.toml"),
    )
    assert config.telemetry_enabled is False
    assert config.telemetry_detail == "metadata"


def test_telemetry_enabled_and_detail_from_env():
    config = Config.load(
        {
            "INVGATE_BASE_URL": "https://x.invgate.net",
            "INVGATE_API_TOKEN": "t",
            "INVGATE_TELEMETRY": "1",
            "INVGATE_TELEMETRY_DETAIL": "ids",
        },
        config_path=Path("/does/not/exist.toml"),
    )
    assert config.telemetry_enabled is True
    assert config.telemetry_detail == "ids"


def test_telemetry_detail_invalid_falls_back_to_metadata():
    config = Config.load(
        {
            "INVGATE_BASE_URL": "https://x.invgate.net",
            "INVGATE_API_TOKEN": "t",
            "INVGATE_TELEMETRY_DETAIL": "bogus",
        },
        config_path=Path("/does/not/exist.toml"),
    )
    assert config.telemetry_detail == "metadata"
