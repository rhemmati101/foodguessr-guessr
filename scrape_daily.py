from selenium.webdriver.chrome.options import Options
from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from pathlib import Path
import csv
import time
import numpy as np

from datetime import datetime

from scrape import extract_dish_and_countries, extract_ingredients

website: str = "https://www.foodguessr.com/game/daily"
chrome_path = Path(__file__).parent / "chrome_driver" / "chrome"

info_list = []

# Configure Chrome options
chrome_options = Options()
chrome_options.binary_location = str(chrome_path)
chrome_options.add_argument("--headless=new")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-setuid-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--disable-extensions")
chrome_options.add_argument("--disable-plugins")
chrome_options.add_argument("--no-first-run")
chrome_options.add_argument("--no-default-browser-check")

driver = webdriver.Chrome(options=chrome_options)


driver.get(website)

for _ in range(3):
    # Wait for the page to load
    time.sleep(np.random.uniform(1.5, 3))

    #try to fail the game, then extract dish name and countries of origin
    i = 1
    max_attempts = 5
    while driver.current_url == website and "Description" in driver.page_source and i <= max_attempts:
        actions = ActionChains(driver)

        actions.send_keys("s")
        actions.perform()
        time.sleep(0.2)
        
        actions = ActionChains(driver)
        actions.send_keys("a")
        actions.perform()
        time.sleep(0.2)
        
        actions = ActionChains(driver)
        actions.send_keys(Keys.ENTER)
        actions.perform()

        time.sleep(0.2)
        i += 1

    print(f"Exited loop after {i-1} attempts.")

    time.sleep(1.5)  # Wait a moment for the page to update

    page_text = driver.find_element(By.TAG_NAME, 'body').text
    print(page_text.partition("Pass")[0])

    # Extract dish name, countries, and alternate names
    dish_name, countries, alternate_names = extract_dish_and_countries(page_text)
    print(f"Dish Name: {dish_name}")
    print(f"Countries of Origin: {countries}")
    print(f"Alternate Names: {alternate_names}")

    try:
        ingredients_text = extract_ingredients(page_text)
        print(f"Ingredients: {ingredients_text}")
    except Exception as e:
        ingredients_text = None
        print(f"Error extractingingredients: {e}")

    info_list.append({
        "dish_name":dish_name, 
        "countries_of_origin":countries, 
        "ingredients": ingredients_text, 
        "alternate_names":alternate_names
    })

    # go to next page
    time.sleep(1)
    actions = ActionChains(driver)
    actions.send_keys(Keys.ENTER)
    actions.perform()

# Append extracted data to daily_data.csv
csv_path = Path(__file__).parent / "data/daily_data.csv"

if not csv_path.exists():
    with csv_path.open("w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["date", "dish_name", "countries_of_origin", "ingredients"])


with csv_path.open("a", newline="", encoding="utf-8") as csvfile:
    current_date = datetime.now().strftime("%-m/%-d/%Y")

    writer = csv.writer(csvfile)
    for info in info_list:
        name, countries_oo, ingredients, alt_names = info['dish_name'], info['countries_of_origin'], info['ingredients'], info['alternate_names']
        # exclude alternate names here, not necessary (helped w debugging before though)
        writer.writerow([
            current_date,
            name or "",
            "; ".join(countries_oo) if countries_oo else "",
            ingredients or "",
        ])

driver.quit()