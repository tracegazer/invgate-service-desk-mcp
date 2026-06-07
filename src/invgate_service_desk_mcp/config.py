"""Configuration loading: environment variables override a persistent TOML file."""

from __future__ import annotations

import logging
import sys
import tomllib
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

_log = logging.getLogger(__name__)

DEFAULT_CONFIG_PATH = Path.home() / ".config" / "invgate-service-desk-mcp" / "config.toml"


class ConfigError(Exception):
    """Raised when required configuration is missing or invalid."""


_TRUTHY = {"1", "true", "yes", "on"}
_TELEMETRY_DETAILS = {"metadata", "ids", "full"}

# Named write profiles → the set of domains whose write tools get registered.
# "support" deliberately excludes "kb": a support agent reads the KB but does not edit it.
WRITE_PROFILES: dict[str, frozenset[str]] = {
    "none": frozenset(),
    "support": frozenset({"incidents", "timetracking"}),
    "full": frozenset({"incidents", "kb", "timetracking"}),
}


@dataclass(frozen=True)
class Config:
    base_url: str
    api_token: str
    # InvGate SD authenticates with HTTP Basic: username + API token as password.
    # The username is "api" on standard instances; kept configurable for flexibility.
    api_username: str = "api"
    # Write tools are registered per-domain according to the resolved profile.
    # "none" (default) is read-only. `enable_writes` is the legacy alias for "full".
    write_profile: str = "none"
    enable_writes: bool = False
    # Derived in __post_init__ from write_profile (or enable_writes). Do not set directly.
    write_domains: frozenset[str] = frozenset()
    # Telemetry (OpenTelemetry) is off unless the operator opts in.
    telemetry_enabled: bool = False
    # Span attribute detail: "metadata" (default) | "ids" | "full". Metrics are
    # always low-cardinality regardless of this setting.
    telemetry_detail: str = "metadata"

    def __post_init__(self) -> None:
        if self.write_profile not in WRITE_PROFILES:
            valid = ", ".join(WRITE_PROFILES)
            raise ValueError(
                f"Invalid write profile {self.write_profile!r}. Valid: {valid}."
            )
        if self.write_profile != "none":
            domains = WRITE_PROFILES[self.write_profile]
        elif self.enable_writes:
            domains = WRITE_PROFILES["full"]
        else:
            domains = WRITE_PROFILES["none"]
        object.__setattr__(self, "write_domains", domains)

    def __repr__(self) -> str:
        return (
            f"Config(base_url={self.base_url!r}, api_token='***', "
            f"api_username={self.api_username!r}, write_profile={self.write_profile!r}, "
            f"telemetry_enabled={self.telemetry_enabled}, "
            f"telemetry_detail={self.telemetry_detail!r})"
        )

    @classmethod
    def load(
        cls,
        env: Mapping[str, str],
        config_path: Path = DEFAULT_CONFIG_PATH,
    ) -> "Config":
        """Resolve config from env vars (highest priority) falling back to TOML."""
        file_values = _read_toml(config_path)

        base_url = env.get("INVGATE_BASE_URL") or file_values.get("base_url")
        api_token = env.get("INVGATE_API_TOKEN") or file_values.get("api_token")
        api_username = (
            env.get("INVGATE_API_USERNAME")
            or file_values.get("api_username")
            or "api"
        )
        write_profile = _resolve_write_profile(env, file_values)
        telemetry_enabled = _resolve_truthy(
            env, file_values, "INVGATE_TELEMETRY", "telemetry_enabled"
        )
        telemetry_detail = (
            env.get("INVGATE_TELEMETRY_DETAIL")
            or file_values.get("telemetry_detail")
            or "metadata"
        )
        if telemetry_detail not in _TELEMETRY_DETAILS:
            telemetry_detail = "metadata"

        if not base_url:
            raise ConfigError(
                "Missing base_url. Set INVGATE_BASE_URL or 'base_url' in the config file."
            )
        if not api_token:
            raise ConfigError(
                "Missing api_token. Set INVGATE_API_TOKEN or 'api_token' in the config file."
            )
        if base_url.startswith("http://"):
            _log.warning(
                "base_url uses plain HTTP — credentials will be sent in cleartext. "
                "Use https:// in production."
            )

        return cls(
            base_url=base_url.rstrip("/"),
            api_token=api_token,
            api_username=api_username,
            write_profile=write_profile,
            telemetry_enabled=telemetry_enabled,
            telemetry_detail=telemetry_detail,
        )


def _resolve_enable_writes(env: Mapping[str, str], file_values: dict) -> bool:
    return _resolve_truthy(env, file_values, "INVGATE_ENABLE_WRITES", "enable_writes")


def _resolve_write_profile(env: Mapping[str, str], file_values: dict) -> str:
    """Resolve the write profile. Precedence: explicit profile > ENABLE_WRITES alias > none.

    A profile set alongside a truthy ENABLE_WRITES wins; we warn so the operator
    notices the alias is being ignored. An invalid profile string is left as-is so
    Config.__post_init__ fails fast with the full list of valid values.
    """
    raw = env.get("INVGATE_WRITE_PROFILE") or file_values.get("write_profile")
    profile = raw.strip().lower() if raw else None
    alias_full = _resolve_enable_writes(env, file_values)
    if profile is not None:
        if alias_full and profile != "full":
            print(
                "WARNING: both INVGATE_WRITE_PROFILE and INVGATE_ENABLE_WRITES are set; "
                f"using profile '{profile}' and ignoring INVGATE_ENABLE_WRITES.",
                file=sys.stderr,
            )
        return profile
    return "full" if alias_full else "none"


def _resolve_truthy(
    env: Mapping[str, str], file_values: dict, env_key: str, file_key: str
) -> bool:
    raw = env.get(env_key)
    if raw is not None:
        return raw.strip().lower() in _TRUTHY
    return bool(file_values.get(file_key, False))


def _read_toml(config_path: Path) -> dict:
    if not config_path.exists():
        return {}
    with config_path.open("rb") as fh:
        return tomllib.load(fh)
