"""STARS login helpers."""

from __future__ import annotations

from selenium.common.exceptions import WebDriverException
from selenium.webdriver.common.by import By

from config import Credentials
from helpers.browser import wait_for_clickable, wait_for_planner


STARS_LOGIN_URL = (
    "https://wish.wis.ntu.edu.sg/pls/webexe/ldap_login.login?"
    "w_url=https://wish.wis.ntu.edu.sg/pls/webexe/aus_stars_planner.main"
)


def login_to_stars(driver, credentials: Credentials, timeout: float) -> bool:
    """Log in and wait until the STARS planner page is ready."""
    username_locator = (
        By.XPATH,
        "/html/body/div[3]/div/div/section[2]/div/div/center[1]/form/"
        "table/tbody/tr/td/table/tbody/tr[2]/td[2]/input",
    )
    password_locator = (
        By.XPATH,
        "/html/body/div[3]/div/div/section[2]/div/div/form/center[1]/table/"
        "tbody/tr/td/table/tbody/tr[3]/td[2]/input",
    )

    try:
        driver.get(STARS_LOGIN_URL)
        username_field = wait_for_clickable(driver, username_locator, timeout)
        if username_field is None:
            print("Username field was not found.")
            return False
        username_field.send_keys(credentials.username)
        username_field.submit()

        password_field = wait_for_clickable(driver, password_locator, timeout)
        if password_field is None:
            print("Password field was not found.")
            return False
        password_field.send_keys(credentials.password)
        password_field.submit()

        if wait_for_planner(driver, timeout):
            print("Logged in to STARS.")
            return True
        print("Login did not reach the STARS planner. Check the credentials and page.")
        return False
    except WebDriverException as error:
        print(f"Login failed: {error}")
        return False
