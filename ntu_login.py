from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import time
import os
from dotenv import load_dotenv

def setup_driver():
    """Setup and return the Chrome WebDriver with appropriate options"""
    options = webdriver.ChromeOptions()
    options.add_argument('--disable-extensions')
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


if __name__ == "__main__":
    # Load environment variables
    load_dotenv()
    
    # Get credentials and index number from environment variables
    username = os.getenv("NTU_USERNAME")
    password = os.getenv("NTU_PASSWORD")
    old_index = os.getenv("OLD_INDEX")
    desired_index = os.getenv("DESIRED_INDEX")
    
    if not username or not password:
        print("Please set NTU_USERNAME and NTU_PASSWORD environment variables")
    elif not old_index:
        print("Please set OLD_INDEX environment variables")


    # Initialize the driver
    driver = setup_driver()
    print("Browser launched successfully")

    # Initial login
    if login_to_stars(driver, username, password):
        # If login successful and index number provided, try to find it
        radio_button = find_index_radio(driver, old_index)
        if radio_button:
            radio_button.click()
        if enter_swap_screen(driver):
            select_new_index(driver, desired_index)

        time.sleep(5)
        


        pass
