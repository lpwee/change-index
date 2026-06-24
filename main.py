"""Interactive command-line launcher for the NTU STARS automations."""

from __future__ import annotations

import sys

from add_drop import change_index_pairs_concurrently
from helpers.authentication import login_to_stars
from helpers.browser import close_driver, setup_driver
from helpers.index_pairs import load_index_pairs
from stars import (
    REQUEST_COMPLETED,
    REQUEST_RELOGIN,
    request_courses_until_added,
)
from config import ConfigurationError, StarsConfig, load_credentials


STARS_CHOICE = "1"
ADD_DROP_CHOICE = "2"


def choose_workflow() -> str | None:
    """Prompt until the user selects a workflow or closes standard input."""
    while True:
        print("\nChoose a STARS workflow:")
        print("  1. STARS — retry selected course registration")
        print("  2. Add/Drop — change paired course indexes")
        try:
            choice = input("Enter 1 or 2: ").strip()
        except EOFError:
            print("\nNo workflow selected.")
            return None
        if choice in {STARS_CHOICE, ADD_DROP_CHOICE}:
            return choice
        print("Please enter 1 or 2.")


def main() -> int:
    try:
        workflow = choose_workflow()
    except KeyboardInterrupt:
        print("\nCancelled.")
        return 130
    if workflow is None:
        return 2

    try:
        credentials = load_credentials()
        config = StarsConfig.from_environment()
        if workflow == STARS_CHOICE:
            pairs = None
        else:
            pairs = load_index_pairs()
    except ConfigurationError as error:
        print(f"Configuration error: {error}", file=sys.stderr)
        return 2

    if workflow == STARS_CHOICE:
        driver = setup_driver(config.headless)
        try:
            while True:
                if not login_to_stars(
                    driver, credentials, config.page_timeout_seconds
                ):
                    return 1
                result = request_courses_until_added(
                    driver,
                    config=config,
                )
                if result == REQUEST_COMPLETED:
                    return 0
                if result == REQUEST_RELOGIN:
                    print("Retrying STARS from a fresh login after page expiration.")
                    continue
                return 1
        finally:
            close_driver(driver)

    # Add/Drop creates and owns one WebDriver per configured pair.
    if workflow == ADD_DROP_CHOICE:
        return int(not change_index_pairs_concurrently(credentials, pairs, config))

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
