"""Configuration parsing helpers for paired Add/Drop index changes."""

from __future__ import annotations

import os
from collections.abc import Mapping

from config import ConfigurationError


def parse_index_pairs(
    current_indexes: str | None,
    desired_indexes: str | None,
) -> list[tuple[str, str]]:
    """Parse positional CURRENT_INDEX/DESIRED_INDEX comma-separated pairs."""

    def split(value: str | None, variable_name: str) -> list[str]:
        if value is None or not value.strip():
            raise ConfigurationError(f"Set {variable_name} in .env.")
        indexes = [index.strip() for index in value.split(",")]
        if not indexes or any(not index for index in indexes):
            raise ConfigurationError(
                f"{variable_name} must be a comma-separated list without empty values."
            )
        return indexes

    current = split(current_indexes, "CURRENT_INDEX")
    desired = split(desired_indexes, "DESIRED_INDEX")
    if len(current) != len(desired):
        raise ConfigurationError(
            "CURRENT_INDEX and DESIRED_INDEX must contain the same number of values."
        )
    return list(zip(current, desired, strict=True))


def load_index_pairs(
    environment: Mapping[str, str] = os.environ,
) -> list[tuple[str, str]]:
    """Load paired Add/Drop indexes after dotenv has been loaded."""
    return parse_index_pairs(
        environment.get("CURRENT_INDEX"), environment.get("DESIRED_INDEX")
    )
