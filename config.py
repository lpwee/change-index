"""Environment configuration shared by the STARS scripts."""

from __future__ import annotations

import os
from dataclasses import dataclass
from collections.abc import Mapping

class ConfigurationError(ValueError):
    """Raised when required settings are missing or invalid."""


@dataclass(frozen=True)
class Credentials:
    username: str
    password: str


@dataclass(frozen=True)
class StarsConfig:
    """Runtime settings shared by the STARS and Add/Drop workflows."""

    page_timeout_seconds: float = 3.0
    alert_timeout_seconds: float = 5.0
    retry_delay_seconds: float = 0.0
    poll_interval_seconds: float = 0.2
    max_request_attempts: int = 0
    add_drop_retry_delay_seconds: float = 0.0
    add_drop_max_attempts: int = 0
    headless: bool = False

    @classmethod
    def from_environment(
        cls, environment: Mapping[str, str] | None = None
    ) -> "StarsConfig":
        """Build runtime settings from optional `.env` environment values."""
        environment = os.environ if environment is None else environment
        return cls(
            page_timeout_seconds=_positive_float(
                environment, "STARS_WAIT_SECONDS", cls.page_timeout_seconds
            ),
            alert_timeout_seconds=_positive_float(
                environment, "STARS_ALERT_WAIT_SECONDS", cls.alert_timeout_seconds
            ),
            retry_delay_seconds=_nonnegative_float(
                environment,
                "STARS_RETRY_DELAY_SECONDS",
                cls.retry_delay_seconds,
            ),
            poll_interval_seconds=_positive_float(
                environment,
                "STARS_POLL_INTERVAL_SECONDS",
                cls.poll_interval_seconds,
            ),
            max_request_attempts=_nonnegative_int(
                environment, "MAX_REQUEST_ATTEMPTS", cls.max_request_attempts
            ),
            add_drop_retry_delay_seconds=_nonnegative_float(
                environment,
                "ADD_DROP_RETRY_DELAY_SECONDS",
                cls.add_drop_retry_delay_seconds,
            ),
            add_drop_max_attempts=_nonnegative_int(
                environment,
                "ADD_DROP_MAX_ATTEMPTS",
                cls.add_drop_max_attempts,
            ),
            headless=_truthy(environment, "STARS_HEADLESS", cls.headless),
        )


def load_credentials() -> Credentials:
    """Load STARS credentials from the repository's .env file/environment."""
    try:
        from dotenv import load_dotenv
    except ImportError as error:
        raise ConfigurationError(
            "python-dotenv is not installed. Run the setup command in README.md."
        ) from error
    load_dotenv()
    username = os.getenv("NTU_USERNAME")
    password = os.getenv("NTU_PASSWORD")
    if not username or not password:
        raise ConfigurationError(
            "Set NTU_USERNAME and NTU_PASSWORD in .env before running a script."
        )
    return Credentials(username=username, password=password)


def _positive_float(environment: Mapping[str, str], name: str, default: float) -> float:
    """Read a positive floating-point setting from an environment mapping."""
    value = environment.get(name)
    if value is None or not value.strip():
        return default
    try:
        number = float(value)
    except ValueError as error:
        raise ConfigurationError(f"{name} must be a number.") from error
    if number <= 0:
        raise ConfigurationError(f"{name} must be greater than zero.")
    return number


def _nonnegative_float(
    environment: Mapping[str, str], name: str, default: float
) -> float:
    """Read a non-negative floating-point setting from an environment mapping."""
    value = environment.get(name)
    if value is None or not value.strip():
        return default
    try:
        number = float(value)
    except ValueError as error:
        raise ConfigurationError(f"{name} must be a number.") from error
    if number < 0:
        raise ConfigurationError(f"{name} cannot be negative.")
    return number


def _nonnegative_int(environment: Mapping[str, str], name: str, default: int) -> int:
    """Read a non-negative whole-number setting from an environment mapping."""
    value = environment.get(name)
    if value is None or not value.strip():
        return default
    try:
        number = int(value)
    except ValueError as error:
        raise ConfigurationError(f"{name} must be a whole number.") from error
    if number < 0:
        raise ConfigurationError(f"{name} cannot be negative.")
    return number


def _truthy(environment: Mapping[str, str], name: str, default: bool = False) -> bool:
    """Read a conventional boolean environment value."""
    value = environment.get(name)
    if value is None:
        return default
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off", ""}:
        return False
    raise ConfigurationError(f"{name} must be true or false.")
