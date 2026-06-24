from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
import os
from dotenv import load_dotenv

REQUEST_BUTTON_LABEL = "Add (Register) Selected Course(s)"
ADD_BUTTON_LABEL = "Confirm to add course(s)"
RETRY_BUTTON_LABEL = "Back to Timetable"
DEFAULT_WAIT_SECONDS = 10
MAX_REQUEST_ATTEMPTS = 100

def setup_driver():
    """Setup and return the Chrome WebDriver with appropriate options"""
    options = webdriver.ChromeOptions()
    options.add_argument('--disable-extensions')
    # options.add_argument('--headless=new')  # Run in headless mode
    # options.add_argument('--disable-gpu')  # Required for some systems
    # options.add_argument('--no-sandbox')  # Required for some systems
    # options.add_argument('--disable-dev-shm-usage')  # Required for some systems
    return webdriver.Chrome(options=options)

def login_to_stars(driver, username, password):
    """
    Automated login to NTU STARS Planner
    
    Args:
        driver: Selenium WebDriver instance
        username (str): Your NTU username
        password (str): Your NTU password
    
    Returns:
        bool: True if login successful, False otherwise
    """
    # URL for NTU STARS Planner login
    url = "https://wish.wis.ntu.edu.sg/pls/webexe/ldap_login.login?w_url=https://wish.wis.ntu.edu.sg/pls/webexe/aus_stars_planner.main"
    
    try:
        # Navigate to the login page
        driver.get(url)
        print("Navigated to login page")
        
        # Wait for the username field to be present using full XPath (max 10 seconds)
        username_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "/html/body/div[3]/div/div/section[2]/div/div/center[1]/form/table/tbody/tr/td/table/tbody/tr[2]/td[2]/input"))
        )
        
        # Input username and submit
        username_field.send_keys(username)
        username_field.submit()
        print("Username submitted")

        # Wait for the password field to be present using full XPath (max 10 seconds)
        password_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "/html/body/div[3]/div/div/section[2]/div/div/form/center[1]/table/tbody/tr/td/table/tbody/tr[3]/td[2]/input"))
        )
        password_field.send_keys(password)
        password_field.submit()
        print("Password form submitted")
        
        # Wait for successful login (check for planner form)
        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "form[action='AUS_STARS_PLANNER.planner'][method='post']"))
            )
            print("Successfully logged in!")
            return True
            
        except TimeoutException:
            print("Login might have failed. Please check your credentials.")
            return False
        
    except Exception as e:
        print(f"An error occurred during login: {str(e)}")
        return False

def button_locator(label):
    """Match common button/input patterns by their visible label."""
    xpath = (
        "//input[(@type='submit' or @type='button') and @value=\"%s\"]"
        "|//button[normalize-space()=\"%s\"]"
        "|//a[normalize-space()=\"%s\"]"
    ) % (label, label, label)
    return By.XPATH, xpath

def click_button_by_label(driver, label, description, timeout=DEFAULT_WAIT_SECONDS):
    """Wait for a labeled button-like element, then click it."""
    try:
        button = WebDriverWait(driver, timeout).until(
            EC.element_to_be_clickable(button_locator(label))
        )
        button.click()
        print(f"Clicked {description}")
        return True
    except TimeoutException:
        print(f"{description} was not found or was not clickable")
        return False
    except Exception as e:
        print(f"An error occurred while clicking {description}: {str(e)}")
        return False

def on_request_page(driver):
    """Return True when the first request button is currently available."""
    try:
        locator_type, locator_value = button_locator(REQUEST_BUTTON_LABEL)
        buttons = driver.find_elements(locator_type, locator_value)
        return any(button.is_displayed() and button.is_enabled() for button in buttons)
    except WebDriverException as e:
        print(f"Could not verify request page state: {str(e)}")
        return False

def wait_for_request_result(driver, timeout=DEFAULT_WAIT_SECONDS):
    """Wait for either a retryable rejection or a successful completion page."""
    try:
        WebDriverWait(driver, timeout).until(
            lambda current_driver: "Not Added." in current_driver.page_source
            or "Successfully" in current_driver.page_source
            or on_request_page(current_driver)
        )
    except TimeoutException:
        print("Timed out while waiting for the request result page")
        return None
    except WebDriverException as e:
        print(f"Browser error while waiting for request result: {str(e)}")
        return None

    try:
        return "Not Added." in driver.page_source
    except WebDriverException as e:
        print(f"Could not read the result page: {str(e)}")
        return None

def request_index_until_added(driver, max_attempts=MAX_REQUEST_ATTEMPTS):
    """Continuously click the configured labeled buttons until the request finishes."""
    attempt = 1

    while attempt <= max_attempts:
        print(f"Starting request attempt {attempt}")
        if not on_request_page(driver):
            print("Request button is not available on the current page")
            return False

        if not click_button_by_label(
            driver,
            REQUEST_BUTTON_LABEL,
            f"'{REQUEST_BUTTON_LABEL}' button",
        ):
            return False

        if not click_button_by_label(
            driver,
            ADD_BUTTON_LABEL,
            f"'{ADD_BUTTON_LABEL}' button",
        ):
            return False

        was_not_added = wait_for_request_result(driver)
        if was_not_added is None:
            print("Request result could not be determined")
            return False

        if not was_not_added:
            print("Request flow finished without a 'Not Added.' message.")
            return True

        print("Request was not added. Returning to the planner to try again.")
        if click_button_by_label(
            driver,
            RETRY_BUTTON_LABEL,
            f"'{RETRY_BUTTON_LABEL}' button",
        ):
            try:
                WebDriverWait(driver, DEFAULT_WAIT_SECONDS).until(
                    lambda current_driver: on_request_page(current_driver)
                )
                print("Returned to planner page")
            except TimeoutException:
                print("Retry button clicked, but the planner page did not load in time")
                return False
        else:
            print("Retry button was unavailable; trying to rebuild the request flow from the current page")

        attempt += 1

    print(f"Reached the retry limit of {max_attempts} attempts")
    return False


if __name__ == "__main__":
    # Load environment variables
    load_dotenv()
    
    # Get credentials from environment variables
    username = os.getenv("NTU_USERNAME")
    password = os.getenv("NTU_PASSWORD")
    
    if not username or not password:
        print("Please set NTU_USERNAME and NTU_PASSWORD environment variables")
    else:
        # Initialize the driver only when the required credentials are available.
        driver = setup_driver()
        print("Browser launched successfully")

        if login_to_stars(driver, username, password):
            if request_index_until_added(driver):
                print("Index request process completed")
            else:
                print("Index request process stopped before completion")
