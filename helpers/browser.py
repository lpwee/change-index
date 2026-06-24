"""Browser setup, page-state, button, and alert helpers for STARS."""

from __future__ import annotations

from selenium import webdriver
from selenium.common.exceptions import (
    NoAlertPresentException,
    TimeoutException,
    UnexpectedAlertPresentException,
    WebDriverException,
)
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


def setup_driver(headless: bool = False):
    """Create a Chrome driver with the configured visibility."""
    options = webdriver.ChromeOptions()
    options.add_argument("--disable-extensions")
    if headless:
        options.add_argument("--headless=new")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
    return webdriver.Chrome(options=options)


def xpath_literal(value: str) -> str:
    """Return a safe XPath string literal for a value supplied from `.env`."""
    if '"' not in value:
        return f'"{value}"'
    if "'" not in value:
        return f"'{value}'"
    parts = value.split('"')
    return "concat(" + ", '\"', ".join(f'"{part}"' for part in parts) + ")"


def button_locator(label: str) -> tuple[str, str]:
    """Locate a submit, button, or link by its displayed label."""
    literal = xpath_literal(label)
    return (
        By.XPATH,
        "//input[(@type='submit' or @type='button') and @value=" + literal + "]"
        "|//button[normalize-space()=" + literal + "]"
        "|//a[normalize-space()=" + literal + "]",
    )


def wait_for_clickable(driver, locator: tuple[str, str], timeout: float):
    """Return a clickable element or None after the timeout expires."""
    try:
        return WebDriverWait(driver, timeout).until(EC.element_to_be_clickable(locator))
    except TimeoutException:
        return None


def click_button_by_label(driver, label: str, timeout: float) -> bool:
    """Click a button-like element matched by its label."""
    try:
        button = wait_for_clickable(driver, button_locator(label), timeout)
    except UnexpectedAlertPresentException:
        # Let workflow-specific code classify the alert.
        raise
    if button is None:
        print(f"Button not available: {label!r}")
        return False
    try:
        button.click()
        print(f"Clicked: {label}")
        return True
    except UnexpectedAlertPresentException:
        raise
    except WebDriverException as error:
        print(f"Could not click {label!r}: {error}")
        return False


def button_is_available(driver, label: str) -> bool:
    """Return whether a visible, enabled button with this label is on the page."""
    try:
        by, selector = button_locator(label)
        return any(
            button.is_displayed() and button.is_enabled()
            for button in driver.find_elements(by, selector)
        )
    except WebDriverException:
        return False


def planner_is_ready(driver) -> bool:
    """Return whether the logged-in timetable/planner controls are present."""
    try:
        return bool(
            driver.find_elements(By.CSS_SELECTOR, "select[name='opt']")
            or driver.find_elements(
                By.CSS_SELECTOR,
                "form[action='AUS_STARS_PLANNER.planner'][method='post']",
            )
        )
    except WebDriverException:
        return False


def wait_for_planner(driver, timeout: float) -> bool:
    """Wait until the timetable page is usable."""
    try:
        WebDriverWait(driver, timeout).until(planner_is_ready)
        return True
    except TimeoutException:
        return False


def accept_alert_if_present(driver, timeout: float) -> str | None:
    """Accept a browser alert and return its text, or return None when absent."""
    try:
        if timeout:
            alert = WebDriverWait(driver, timeout).until(EC.alert_is_present())
        else:
            alert = driver.switch_to.alert
        alert_text = alert.text
        print(f"Accepting alert: {alert_text}")
        alert.accept()
        return alert_text
    except (NoAlertPresentException, TimeoutException):
        return None
    except WebDriverException as error:
        print(f"Could not handle browser alert: {error}")
        return None


def close_driver(driver) -> None:
    """Close Chrome without masking the useful result of a run."""
    try:
        driver.quit()
    except WebDriverException:
        pass
