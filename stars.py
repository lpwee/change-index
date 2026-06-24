"""Retry an already-selected course registration request in NTU STARS."""

from __future__ import annotations

import time

from selenium.common.exceptions import (
    StaleElementReferenceException,
    UnexpectedAlertPresentException,
    WebDriverException,
)

from helpers.browser import (
    accept_alert_if_present,
    button_is_available,
    button_locator,
    wait_for_planner,
)
from config import StarsConfig


REGISTRATION_NOT_OPEN_ALERT = "not allowed to register for course now"
PAGE_EXPIRED_ALERT = "this page has expired"

REQUEST_BUTTON_LABEL = "Add (Register) Selected Course(s)"
ADD_BUTTON_LABEL = "Confirm to add course(s)"
RETRY_BUTTON_LABEL = "Back to Timetable"
REQUEST_COMPLETED = "completed"
REQUEST_RELOGIN = "relogin"
REQUEST_FAILED = "failed"

def is_registration_not_open_alert(alert_text: str) -> bool:
    """Return whether STARS says that registration is currently closed."""
    return REGISTRATION_NOT_OPEN_ALERT in alert_text.casefold()

def is_page_expired_alert(alert_text: str) -> bool:
    """Return whether STARS says that the current server page has expired."""
    return PAGE_EXPIRED_ALERT in alert_text.casefold()

def dismiss_registration_window_alert(
    driver, config: StarsConfig, fallback_alert_text: str | None = None
) -> str | None:
    """Close the registration-window alert and classify the reason for it."""
    # Chrome can dismiss an alert itself while raising
    # UnexpectedAlertPresentException. In that case Selenium exposes the text
    # on the exception, so retain it as a fallback for classification.
    alert_text = (
        accept_alert_if_present(driver, config.alert_timeout_seconds)
        or fallback_alert_text
    )
    if alert_text is None:
        return None
    if is_registration_not_open_alert(alert_text):
        print("Registration is not open yet. Waiting in the logged-in timetable.")
        return "registration_not_open"
    if is_page_expired_alert(alert_text):
        print("STARS says this page has expired. Starting a fresh logged-in session.")
        return "page_expired"
    print(f"STARS showed an unexpected alert: {alert_text}")
    return "unexpected_alert"


def click_stars_button(driver, label: str, config: StarsConfig) -> str:
    """Click one STARS button after its page and alerts have settled.

    Native alerts and STARS page replacements can occur before any of the
    three buttons is found. Polling the alert and the button together avoids
    Selenium's brittle ``element_to_be_clickable`` transition behaviour.
    """
    deadline = time.monotonic() + config.page_timeout_seconds
    locator = button_locator(label)

    while time.monotonic() < deadline:
        alert_result = dismiss_registration_window_alert(driver, config)
        if alert_result is not None:
            return alert_result

        try:
            by, selector = locator
            buttons = driver.find_elements(by, selector)
            for button in buttons:
                # A null element is a ChromeDriver transition artefact. Treat
                # it like a stale element and poll again instead of crashing.
                if button is None:
                    continue
                if not button.is_displayed() or not button.is_enabled():
                    continue
                button.click()
                print(f"Clicked: {label}")
                return "clicked"
        except UnexpectedAlertPresentException as error:
            return (
                dismiss_registration_window_alert(driver, config, error.alert_text)
                or "failed"
            )
        except (
            AttributeError,
            StaleElementReferenceException,
            TypeError,
            WebDriverException,
        ):
            # The DOM is still being replaced. Retry until it settles or the
            # ordinary per-page timeout expires.
            pass

        time.sleep(config.poll_interval_seconds)

    print(f"Button not available after page transition: {label!r}")
    return "failed"


def wait_for_add_outcome(driver, config: StarsConfig) -> str:
    """Wait for a rejection page or a conclusive successful page.

    STARS is inconsistent about the exact success copy, so the absence of its
    explicit rejection state after the confirmation page has settled is treated
    as success. This mirrors the existing manual workflow: only "Not Added."
    should trigger another request.
    """

    deadline = time.monotonic() + config.page_timeout_seconds
    while time.monotonic() < deadline:
        alert_result = dismiss_registration_window_alert(driver, config)
        if alert_result is not None:
            return alert_result
        try:
            if button_is_available(driver, RETRY_BUTTON_LABEL):
                return "retry"
            page = driver.page_source.lower()
            if "not added." in page:
                return "retry"
            if any(
                phrase in page
                for phrase in ("successfully added", "course(s) added", "registration successful")
            ):
                return "completed"
            # Some successful requests return directly to the timetable.
            if button_is_available(driver, REQUEST_BUTTON_LABEL):
                return "completed"
        except UnexpectedAlertPresentException as error:
            return (
                dismiss_registration_window_alert(driver, config, error.alert_text)
                or "failed"
            )
        except WebDriverException as error:
            print(f"Could not read the STARS result page: {error}")
            return "failed"
        time.sleep(config.poll_interval_seconds)
    return "completed"


def resume_after_closed_registration_window(driver, config: StarsConfig) -> bool:
    """Wait for Close to return to the planner, then retry without re-login."""
    if not wait_for_planner(driver, config.page_timeout_seconds):
        print("Closing the registration-window alert did not return to the timetable.")
        return False
    if config.retry_delay_seconds:
        time.sleep(config.retry_delay_seconds)
    return True



def request_courses_until_added(
    driver,
    *,
    config: StarsConfig,
) -> str:
    """Press the three STARS buttons until the request is added or cannot run."""
    attempt = 1
    while (
        config.max_request_attempts == 0
        or attempt <= config.max_request_attempts
    ):
        print(f"Starting STARS request attempt {attempt}.")
        request_result = click_stars_button(driver, REQUEST_BUTTON_LABEL, config)
        if request_result != "clicked":
            if request_result == "page_expired":
                return REQUEST_RELOGIN
            if request_result == "registration_not_open" and resume_after_closed_registration_window(
                driver, config
            ):
                continue
            return REQUEST_FAILED
        add_result = click_stars_button(driver, ADD_BUTTON_LABEL, config)
        if add_result != "clicked":
            if add_result == "page_expired":
                return REQUEST_RELOGIN
            if add_result == "registration_not_open" and resume_after_closed_registration_window(
                driver, config
            ):
                continue
            return REQUEST_FAILED

        result = wait_for_add_outcome(driver, config)
        if result == "page_expired":
            return REQUEST_RELOGIN
        if result == "registration_not_open":
            if resume_after_closed_registration_window(driver, config):
                continue
            return REQUEST_FAILED
        if result == "completed":
            print("STARS request finished without a 'Not Added.' response.")
            return REQUEST_COMPLETED
        if result != "retry":
            return REQUEST_FAILED

        print("STARS reported 'Not Added.'; returning to the timetable.")
        retry_result = click_stars_button(driver, RETRY_BUTTON_LABEL, config)
        if retry_result == "page_expired":
            return REQUEST_RELOGIN
        if retry_result != "clicked":
            if retry_result == "registration_not_open" and resume_after_closed_registration_window(
                driver, config
            ):
                continue
            return REQUEST_FAILED
        if config.retry_delay_seconds:
            time.sleep(config.retry_delay_seconds)
        attempt += 1

    print(
        "Reached MAX_REQUEST_ATTEMPTS="
        f"{config.max_request_attempts} before the course was added."
    )
    return REQUEST_FAILED
