from selenium.webdriver.chrome.options import Options
from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from pathlib import Path
import csv
import time
import numpy as np

website: str = "https://www.foodguessr.com/game/random"
chrome_path = Path(__file__).parent / "chrome_driver" / "chrome"

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

def extract_dish_and_countries(page_text):
    """
    Extracts the dish name and countries of origin from raw webpage text.
    
    Args:
        page_text (str): The raw text content from the webpage
        
    Returns:
        tuple: (dish_name, countries_list) where countries_list is a list of strings
    """
    # List of known countries (can be expanded)
    known_countries = {
        "Afghanistan", "Albania", "Algeria", "Andorra", "Angola", "Argentina", "Armenia", 
        "Australia", "Austria", "Azerbaijan", "Bahamas", "Bahrain", "Bangladesh", "Barbados", 
        "Belarus", "Belgium", "Belize", "Benin", "Bhutan", "Bolivia", "Bosnia and Herzegovina", 
        "Botswana", "Brazil", "Brunei", "Bulgaria", "Burkina Faso", "Burundi", "Cambodia", 
        "Cameroon", "Canada", "Cape Verde", "Central African Republic", "Chad", "Chile", "China", 
        "Colombia", "Comoros", "Congo", "Costa Rica", "Croatia", "Cuba", "Cyprus", "Czech Republic", 
        "Czechia", "Denmark", "Djibouti", "Dominica", "Dominican Republic", "Ecuador", "Egypt", 
        "El Salvador", "Equatorial Guinea", "Eritrea", "Estonia", "Eswatini", "Ethiopia", "Fiji", 
        "Finland", "France", "Gabon", "Gambia", "Georgia", "Germany", "Ghana", "Greece", "Grenada", 
        "Guatemala", "Guinea", "Guinea-Bissau", "Guyana", "Haiti", "Honduras", "Hungary", "Iceland", 
        "India", "Indonesia", "Iran", "Iraq", "Ireland", "Israel", "Italy", "Jamaica", "Japan", 
        "Jordan", "Kazakhstan", "Kenya", "Kiribati", "Kuwait", "Kyrgyzstan", "Laos", "Latvia", 
        "Lebanon", "Lesotho", "Liberia", "Libya", "Liechtenstein", "Lithuania", "Luxembourg", 
        "Madagascar", "Malawi", "Malaysia", "Maldives", "Mali", "Malta", "Marshall Islands", 
        "Mauritania", "Mauritius", "Mexico", "Micronesia", "Moldova", "Monaco", "Mongolia", 
        "Montenegro", "Morocco", "Mozambique", "Myanmar", "Namibia", "Nauru", "Nepal", "Netherlands", 
        "New Zealand", "Nicaragua", "Niger", "Nigeria", "North Korea", "North Macedonia", "Norway", 
        "Oman", "Pakistan", "Palau", "Palestine", "Panama", "Papua New Guinea", "Paraguay", "Peru", 
        "Philippines", "Poland", "Portugal", "Qatar", "Romania", "Russia", "Rwanda", "Saint Kitts and Nevis", 
        "Saint Lucia", "Saint Vincent and the Grenadines", "Samoa", "San Marino", "Sao Tome and Principe", 
        "Saudi Arabia", "Senegal", "Serbia", "Seychelles", "Sierra Leone", "Singapore", "Slovakia", 
        "Slovenia", "Solomon Islands", "Somalia", "South Africa", "South Korea", "South Sudan", "Spain", 
        "Sri Lanka", "Sudan", "Suriname", "Sweden", "Switzerland", "Syria", "Taiwan", "Tajikistan", 
        "Tanzania", "Thailand", "Timor-Leste", "Togo", "Tonga", "Trinidad and Tobago", "Tunisia", 
        "Turkey", "Turkmenistan", "Tuvalu", "Uganda", "Ukraine", "United Arab Emirates", "United Kingdom", 
        "United States", "Uruguay", "Uzbekistan", "Vanuatu", "Vatican City", "Venezuela", "Vietnam", 
        "Yemen", "Zambia", "Zimbabwe",
        "Hong Kong", "Macau", "Palestine", "Puerto Rico", "Greenland", "Faroe Islands", "French Guiana", "Gibraltar",
        "Isle of Man", "Jersey", "Guernsey", "Aruba", "Curacao", "Sint Maarten", "Bonaire", "Saba", "Saint Barthélemy",
        "Saint Martin", "Saint Pierre and Miquelon", "Wallis and Futuna", "Western Sahara", "Kosovo", "Antigua and Barbuda", "Curaçao",
        "Saint Helena, Ascension and Tristan da Cunha", "Cook Islands", "Niue", "Tokelau", "Åland Islands", "Ivory Coast", "Côte d'Ivoire",
        "French Southern and Antarctic Lands", "Réunion", "Mayotte", "Guadaloupe", "Martinique", "Saint Pierre and Miquelon",
        "Bermuda", "British Virgin Islands", "Falkland Islands", "Montserrat", "Turks and Caicos Islands", "Virgin Islands",
        "Guadalope", "Cayman Islands", "Republic of the Congo", "São Tomé and Príncipe", "DR Congo", "American Samoa",  "French Polynesia",
    }
    
    lines = [line.strip() for line in page_text.split('\n') if line.strip()]
    
    # Find "Report an issue"
    report_issue_idx = None
    for i, line in enumerate(lines):
        if "Report an issue" in line:
            report_issue_idx = i
            break
    
    if report_issue_idx is None:
        return None, [], []
    
    # Find the last navigation element (e.g., "Next slide", "Previous slide") before "Report an issue"
    nav_idx = None
    for i in range(report_issue_idx - 1, -1, -1):
        if "slide" in lines[i].lower():
            nav_idx = i
            break
    
    if nav_idx is None:
        nav_idx = 1  # No navigation found, start 2 lines in???? #############################################################
        # copyright seems to be 2 lines long....
    
    # Lines between navigation and "Report an issue" contain dish name and countries
    content_lines = lines[nav_idx + 1 : report_issue_idx]
    
    if not content_lines:
        return None, [], []
    
    # First line is dish name
    dish_name = content_lines[0]
    
    # Split the remaining lines into countries and alternate names
    countries = [line for line in content_lines[1:] if line in known_countries]
    alternate_names = [line for line in content_lines[1:] if line and line not in known_countries]
    
    return dish_name, countries, alternate_names

def extract_ingredients(page_text):
    """
    Extracts the ingredients section from raw webpage text.
    
    Args:
        page_text (str): The raw text content from the webpage
        
    Returns:
        str: The ingredients text, or None if not found
    """
    if "Ingredients" in page_text:
        # Split by "Ingredients" and get the part after it
        ingredients_section = page_text.split("Ingredients")[1]
        ingredients_text = ingredients_section.split("Pass")[0]
        
        return ingredients_text.strip()
    
    return None


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

# Append extracted data to data.csv
csv_path = Path(__file__).parent / "data.csv"
if not csv_path.exists():
    with csv_path.open("w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["dish_name", "countries_of_origin", "ingredients", "alternate_names"])

with csv_path.open("a", newline="", encoding="utf-8") as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow([
        dish_name or "",
        "; ".join(countries) if countries else "",
        ingredients_text or "",
        "; ".join(alternate_names) if alternate_names else ""
    ])

driver.quit()