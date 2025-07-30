import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import time
import os
import csv
import random
from itertools import product
import platform

# --- Custom Exception for Safe Restarts ---
class RestartBrowserException(Exception):
    pass

# --- Credentials ---
username = "Nahaspuma"
password = "Desperado/191*"

# --- Paths ---
if platform.system() == "Windows":
    path = "C:\\Users\\maxim\\Dropbox\\Projects\\ny_census_1925"
else:  # macOS or others
    path = "/Users/maxmonert/Library/CloudStorage/Dropbox/Projects/ny_census_1925"

# --- output path ---
output_path = os.path.join(path, "data", "census_25_files")
os.makedirs(output_path, exist_ok=True)

# --- Helper to load names ---
def load_names(file_path):
    with open(file_path, 'r') as f:
        return [line.split()[0] for line in f if line.strip()]

os.path.join(path, "data", "input_name_lists", "dist.all.last.txt")
os.path.join(path, "data", "input_name_lists","dist.male.first.txt")
os.path.join(path, "data", "input_name_lists","dist.female.first.txt")

# --- Load names ---
last_names = load_names(os.path.join(path, "data", "input_name_lists", "dist.all.last.txt"))
male_first_names = load_names(os.path.join(path, "data", "input_name_lists","dist.male.first.txt"))
female_first_names = load_names(os.path.join(path, "data", "input_name_lists","dist.female.first.txt"))

# --- Setup browser ---
def start_driver():
    driver = uc.Chrome()
    wait = WebDriverWait(driver, 20)
    return driver, wait

driver, wait = start_driver()

# --- Auto-Freeze Recovery ---
freeze_counter = 0

def safe_find_element(by, locator, timeout=20):
    global freeze_counter
    try:
        element = WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((by, locator))
        )
        freeze_counter = 0
        return element
    except TimeoutException:
        print(f"⚠️ Timeout finding {locator}. Refreshing...")
        freeze_counter += 1
        driver.refresh()
        time.sleep(random.uniform(5, 7))
        if freeze_counter >= 3:
            restart_browser()
        return None

def safe_click(by, locator, timeout=20):
    global freeze_counter
    try:
        button = WebDriverWait(driver, timeout).until(
            EC.element_to_be_clickable((by, locator))
        )
        button.click()
        freeze_counter = 0
    except TimeoutException:
        print(f"⚠️ Timeout clicking {locator}. Refreshing...")
        freeze_counter += 1
        driver.refresh()
        time.sleep(random.uniform(5, 7))
        if freeze_counter >= 3:
            restart_browser()

def restart_browser():
    global driver, wait, freeze_counter
    print("🔁 Too many freezes. Restarting browser...")
    try:
        driver.quit()
    except Exception:
        pass
    time.sleep(5)
    driver, wait = start_driver()
    login()
    freeze_counter = 0

# --- Login ---
def login():
    driver.get("https://www.familysearch.org/en/search/collection/1937489")
    time.sleep(random.uniform(2, 4))

    # ✅ Always dismiss TrustArc cookie banner if present
    try:
        accept_btn = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.ID, "truste-consent-button"))
        )
        accept_btn.click()
        print("✅ Accepted cookies banner")
        time.sleep(random.uniform(1, 2))
    except Exception:
        pass  # No banner = fine

    # ✅ Click Sign In safely using JS to avoid intercepts
    try:
        sign_in_button = safe_find_element(By.ID, "signInLink")
        if sign_in_button:
            try:
                driver.execute_script("arguments[0].click();", sign_in_button)
                time.sleep(random.uniform(42, 3))
            except Exception as e:
                print(f"⚠️ Sign In click failed: {e}")
    except Exception as e:
        print(f"⚠️ Could not find Sign In button: {e}")

    # ✅ Enter login credentials
    try:
        email_input = safe_find_element(By.ID, "userName")
        password_input = safe_find_element(By.ID, "password")

        if email_input and password_input:
            email_input.send_keys(username)
            password_input.send_keys(password)

            login_btn = safe_find_element(By.ID, "login")
            if login_btn:
                driver.execute_script("arguments[0].click();", login_btn)
                time.sleep(random.uniform(5, 7))
    except Exception:
        print("❌ Login form did not appear or failed.")

# --- Logout ---
def logout():
    try:
        driver.get("https://www.familysearch.org/en/")
        time.sleep(random.uniform(2, 3))

        # Click the user avatar / portrait
        profile_icon = safe_find_element(By.XPATH, "//div[contains(@class, 'avatarCss_a9t6mc5')]")
        if profile_icon:
            driver.execute_script("arguments[0].click();", profile_icon)
            time.sleep(random.uniform(1, 2))

            # Click "Sign Out"
            sign_out_button = safe_find_element(By.XPATH, "//span[contains(text(), 'Sign Out')]")
            if sign_out_button:
                driver.execute_script("arguments[0].click();", sign_out_button)
                time.sleep(random.uniform(3, 5))
                print("✅ Logged out")

    except Exception as e:
        print(f"⚠️ Logout failed: {e}")

# --- Scrape results on page ---
def scrape_all_results():
    records = []
    time.sleep(2)

    try:
        rows = driver.find_elements(By.XPATH, "//tr[contains(@data-testid, '/ark:/')]")
    except Exception:
        return records

    for i in range(len(rows)):
        try:
            rows = driver.find_elements(By.XPATH, "//tr[contains(@data-testid, '/ark:/')]")
            row = rows[i]
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", row)
            row.click()
            time.sleep(random.uniform(1.5, 2.5))

            record = {}
            try:
                table_rows = driver.find_elements(By.XPATH, "//table//tr")
                for table_row in table_rows:
                    try:
                        label = table_row.find_element(By.XPATH, "./th").text.strip()
                        if label == "Age":
                            try:
                                value = table_row.find_element(By.XPATH, ".//p/strong").text.strip()
                            except:
                                value = table_row.find_element(By.XPATH, ".//strong").text.strip()
                        else:
                            value = table_row.find_element(By.XPATH, "./td/strong").text.strip()
                        record[label] = value
                    except Exception:
                        continue
            except Exception as e:
                print(f"⚠️ Reading fields failed: {e}")

            records.append(record)

            try:
                close_button = safe_find_element(By.XPATH, "//button[@aria-label='Close']")
                if close_button:
                    close_button.click()
                    time.sleep(random.uniform(0.8, 1.5))
            except Exception as e:
                print(f"⚠️ Could not close popup: {e}")

        except Exception as e:
            print(f"❌ Row {i+1} failed: {e}")

    return records

def restart_browser():
    global driver, wait, freeze_counter
    print("🔁 Too many freezes. Restarting browser...")
    try:
        driver.quit()
    except Exception:
        pass
    time.sleep(5)
    driver, wait = start_driver()
    login()
    freeze_counter = 0
    raise RestartBrowserException("Browser restarted")
    
# --- Crash Recovery: detect already finished names ---
finished_names = set()
for file in os.listdir(output_path):
    if file.endswith(".csv"):
        finished_names.add(file.replace(".csv", "").lower())

# --- Main Loop ---
names_scraped = 0

for first, last in product(male_first_names + female_first_names, last_names):
    safe_first = first.replace(' ', '_')
    safe_last = last.replace(' ', '_')
    safe_name = f"{safe_first}_{safe_last}".lower()

    if safe_name in finished_names:
        print(f"⏭️ Skipping {first} {last} (already saved)")
        continue

    all_results = []

    if names_scraped > 0 and names_scraped % 100 == 0:
        restart_browser()

    login()

    try:
        print(f"\n🔵 Starting {first} {last}")

        first_name_input = safe_find_element(By.ID, "givenName")
        last_name_input = safe_find_element(By.ID, "surname")
        place_input = safe_find_element(By.ID, "anyPlace")

        if first_name_input and last_name_input and place_input:
            first_name_input.clear()
            first_name_input.send_keys(first)

            last_name_input.clear()
            last_name_input.send_keys(last)

            place_input.clear()
            place_input.send_keys("New York City")
            time.sleep(1)
            place_input.send_keys(Keys.DOWN)
            place_input.send_keys(Keys.ENTER)
            time.sleep(random.uniform(1, 2))

            safe_click(By.XPATH, "//button[@type='submit']")
            time.sleep(random.uniform(2, 3.5))

            try:
                page_info_text = safe_find_element(By.XPATH, "//p[contains(text(), 'of')]")
                max_pages = int(page_info_text.text.split('of')[-1].strip()) if page_info_text else 1
            except:
                max_pages = 1

            print(f"📖 {first} {last}: {max_pages} pages found.")

            for current_page in range(1, max_pages + 1):
                temp_results = scrape_all_results()
                all_results.extend(temp_results)

                if current_page < max_pages:
                    try:
                        page_input = safe_find_element(By.XPATH, "//input[@aria-label='Enter Page number']")
                        if page_input:
                            page_input.clear()
                            page_input.send_keys(str(current_page + 1))
                            page_input.send_keys(Keys.ENTER)
                            time.sleep(random.uniform(3.0, 5.0))
                    except Exception as e:
                        print(f"⚠️ Could not go to next page: {e}")
                        break

        if all_results:
            fieldnames = set()
            for rec in all_results:
                fieldnames.update(rec.keys())

            output_filename = os.path.join(output_path, f"{safe_first}_{safe_last}.csv")
            with open(output_filename, "w", newline="") as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=sorted(fieldnames))
                writer.writeheader()
                for row in all_results:
                    writer.writerow(row)
            print(f"💾 Saved {len(all_results)} results for {first} {last}")

    except RestartBrowserException:
        print(f"⏭️ Skipping {first} {last} after browser restart.")
        continue  # Skip to next name safely
    except Exception as e:
        print(f"❌ Major error for {first} {last}: {e}")

    names_scraped += 1
    logout()

print("\n📋 All names completed.")
driver.quit()