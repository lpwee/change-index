"""Add/drop index-change workflow used by the interactive STARS CLI."""

from __future__ import annotations

import time
from concurrent.futures import ThreadPoolExecutor, as_completed

from selenium.common.exceptions import UnexpectedAlertPresentException, WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select

from config import Credentials, StarsConfig
from helpers.authentication import login_to_stars
from helpers.browser import (
    accept_alert_if_present,
    button_is_available,
    button_locator,
    click_button_by_label,
    close_driver,
    setup_driver,
    wait_for_clickable,
    wait_for_planner,
    xpath_literal,
)


CHANGE_OPTION_VALUE = "C"
CHANGE_CONFIRMATION_LABEL = "Confirm to Change Index Number"
BACK_TO_TIMETABLE_LABEL = "Back to Timetable"


def change_one_index(
    driver, current_index: str, desired_index: str, config: StarsConfig
) -> bool:
    """Run the historical single-index flow once for one current/desired pair."""
    timeout = config.page_timeout_seconds
    current_locator = (
        By.XPATH,
        "//input[@type='radio' and @name='index_nmbr' and @value="
        + xpath_literal(current_index)
        + "]",
    )
    current_radio = wait_for_clickable(driver, current_locator, timeout)
    if current_radio is None:
        print(f"Current index {current_index!r} was not found in the timetable.")
        return False
    current_radio.click()
    print(f"Selected current index {current_index}.")

    action_select = wait_for_clickable(driver, (By.CSS_SELECTOR, "select[name='opt']"), timeout)
    if action_select is None:
        print("The planner's action selector was not found.")
        return False
    try:
        Select(action_select).select_by_value(CHANGE_OPTION_VALUE)
        go_button = wait_for_clickable(
            driver, (By.CSS_SELECTOR, "input[type='submit'][value='Go']"), timeout
        )
        if go_button is None:
            print("The 'Go' button was not found.")
            return False
        go_button.click()

        new_index_select = wait_for_clickable(
            driver, (By.CSS_SELECTOR, "select[name='new_index_nmbr']"), timeout
        )
        if new_index_select is None:
            print("The new-index selector was not found.")
            return False
        Select(new_index_select).select_by_value(desired_index)
        print(f"Selected desired index {desired_index}.")

        ok_button = wait_for_clickable(
            driver, (By.CSS_SELECTOR, "input[type='submit'][value='OK']"), timeout
        )
        if ok_button is None:
            print("The 'OK' button was not found.")
            return False
        ok_button.click()

        confirmation_button = wait_for_clickable(
            driver, button_locator(CHANGE_CONFIRMATION_LABEL), timeout
        )
        if confirmation_button is None:
            print("The Change Index confirmation button was not found.")
            return False
        try:
            confirmation_button.click()
            print(f"Clicked: {CHANGE_CONFIRMATION_LABEL}")
        except UnexpectedAlertPresentException:
            # The click itself may have opened the confirmation alert. The
            # action has been submitted, so accept it and continue.
            pass
        accept_alert_if_present(driver, timeout=config.alert_timeout_seconds)
        return True
    except WebDriverException as error:
        print(f"Could not change {current_index} to {desired_index}: {error}")
        return False


def return_to_timetable(driver, config: StarsConfig) -> bool:
    """Wait for the next planner page, using its return button when necessary."""
    timeout = config.page_timeout_seconds
    if wait_for_planner(driver, timeout):
        return True
    if button_is_available(driver, BACK_TO_TIMETABLE_LABEL):
        print("Returning to the timetable for the next index pair.")
        if not click_button_by_label(driver, BACK_TO_TIMETABLE_LABEL, timeout):
            return False
        return wait_for_planner(driver, timeout)
    print("STARS did not return to the timetable after the index-change confirmation.")
    return False


def retry_index_pair(
    credentials: Credentials,
    current_index: str,
    desired_index: str,
    config: StarsConfig,
) -> bool:
    """Run one pair in its own browser until STARS accepts the index change."""
    pair_label = f"{current_index} -> {desired_index}"
    driver = None
    attempt = 1
    try:
        driver = setup_driver(config.headless)
        while (
            config.add_drop_max_attempts == 0
            or attempt <= config.add_drop_max_attempts
        ):
            print(f"[{pair_label}] starting attempt {attempt}.")
            if login_to_stars(driver, credentials, config.page_timeout_seconds):
                changed = change_one_index(driver, current_index, desired_index, config)
                if changed and return_to_timetable(driver, config):
                    print(f"[{pair_label}] completed.")
                    return True

            print(f"[{pair_label}] not completed; retrying.")
            if config.add_drop_retry_delay_seconds:
                time.sleep(config.add_drop_retry_delay_seconds)
            attempt += 1

        print(
            f"[{pair_label}] reached ADD_DROP_MAX_ATTEMPTS="
            f"{config.add_drop_max_attempts}."
        )
        return False
    except WebDriverException as error:
        print(f"[{pair_label}] browser error: {error}")
        return False
    finally:
        if driver is not None:
            close_driver(driver)


def change_index_pairs_concurrently(
    credentials: Credentials,
    pairs: list[tuple[str, str]],
    config: StarsConfig,
) -> bool:
    """Run every configured index pair in a separate WebDriver concurrently."""
    print(f"Launching {len(pairs)} Add/Drop browser session(s).")
    results: list[bool] = []
    with ThreadPoolExecutor(max_workers=len(pairs)) as executor:
        futures = {
            executor.submit(
                retry_index_pair, credentials, current_index, desired_index, config
            ): (current_index, desired_index)
            for current_index, desired_index in pairs
        }
        for future in as_completed(futures):
            current_index, desired_index = futures[future]
            pair_label = f"{current_index} -> {desired_index}"
            try:
                results.append(future.result())
            except Exception as error:
                print(f"[{pair_label}] unhandled worker error: {error}")
                results.append(False)

    return all(results)
