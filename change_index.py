from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import time
import os
from dotenv import load_dotenv

REQUEST_BUTTON_XPATH = "//*[@id='top']/div/section[2]/div/div/p/table/tbody/tr[1]/td[2]/table/tbody/tr[12]/td/form/input[1]"
ADD_BUTTON_XPATH = "//*[@id='top']/div/section[2]/div/div/input[1]"
RETRY_BUTTON_XPATH = "//*[@id='xyz']/input[1]"

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

def find_index_radio(driver, index):
    """
    Find radio button for specific index number
    
    Args:
        driver: Selenium WebDriver instance
        index (str): The index number to find (e.g., "82877")
    
    Returns:
        WebElement: The radio button element if found, None otherwise
    """
    try:
        # Using CSS_SELECTOR to find input[type='radio'] with specific name and value
        radio_selector = f"input[type='radio'][name='index_nmbr'][value='{index}']"
        radio_button = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, radio_selector))
        )
        print(f"Found radio button for index number {index}")
        return radio_button
        
    except TimeoutException:
        print(f"Radio button with index {index} not found, has index already been swapped?")
        return None
    except Exception as e:
        print(f"An error occurred while finding index: {str(e)}")
        return None

def enter_swap_screen(driver):
    try:
        # First find the select element
        select_selector = "select[name='opt']"
        select_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, select_selector))
        )
        
        # Create Select object and select by value
        select = Select(select_element)
        select.select_by_value("C")
        print("Selected 'Change Index' option")
    except TimeoutException:
        print(f"'Change Index' option not found.")
        return None
    except Exception as e:
        print(f"An error occured while finding 'Change Index': {str(e)}")
        return None

    try: 
        # Find Go button
        go_selector = "input[type='submit'][value='Go']"
        go_button = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, go_selector))
        )
        print("'Go' button found")
        go_button.click()
        print("'Go' button clicked")

        time.sleep(10)

    except TimeoutException:
        print("'Go' button not found")
        return None
    except Exception as e:
        print(f"An error occurred while finding 'Go' button: {str(e)}")
        return None
    return True

def select_new_index(driver, desired_index):
    """
    Select a new index number from the dropdown and submit the form
    
    Args:
        driver: Selenium WebDriver instance
        desired_index (str): The desired index number to change to
    
    Returns:
        bool: True if successful, None if failed
    """

    # First find the select element
    try:
        select_selector = "select[name='new_index_nmbr']"
        select_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, select_selector))
        )
        
        # Create Select object and select by value
        select = Select(select_element)
        select.select_by_value(f"{desired_index}")
        print(f"Selected index no. {desired_index} option")

        # Find and click the submit button
        submit_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "input[type='submit'][value='OK']"))
        )
        submit_button.click()
        print("Form submitted successfully")
        
        return True

    except TimeoutException:
        print(f"Either index no. {desired_index} or submit button not found.")
        return None
    except Exception as e:
        print(f"An error occurred while processing the form: {str(e)}")
        return None


def click_xpath(driver, xpath, description, timeout=10):
    """Wait for an XPath-targeted button, then click it."""
    try:
        button = WebDriverWait(driver, timeout).until(
            EC.element_to_be_clickable((By.XPATH, xpath))
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


def request_index_until_added(driver):
    """Submit the request and retry from the planner whenever it is not added."""
    attempt = 1

    while True:
        print(f"Starting request attempt {attempt}")
        if not click_xpath(driver, REQUEST_BUTTON_XPATH, "request button"):
            return False

        if not click_xpath(driver, ADD_BUTTON_XPATH, "add button"):
            return False

        try:
            WebDriverWait(driver, 10).until(
                lambda current_driver: "Not Added." in current_driver.page_source
            )
        except TimeoutException:
            print("'Not Added.' did not appear; request flow finished.")
            return True

        print("Request was not added. Returning to the planner to try again.")
        if not click_xpath(driver, RETRY_BUTTON_XPATH, "retry button"):
            return False

        # The retry button returns to the logged-in planner page.
        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, REQUEST_BUTTON_XPATH))
            )
        except TimeoutException:
            print("Planner page did not load after retrying")
            return False

        attempt += 1


if __name__ == "__main__":
    # Load environment variables
    load_dotenv()
    
    # Get credentials and index number from environment variables
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
