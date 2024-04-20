import time
import requests
import pandas as pd
import csv
from selenium import webdriver
from selenium.common import NoSuchElementException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support import expected_conditions as ec
from bs4 import BeautifulSoup

service = Service()
options = Options()
options.add_argument("--headless")

driver = webdriver.Chrome(service=service, options=options)
url = input("Enter the MEP's 'Contributions to plenary debates' page URL: ")

driver.get(url)
# Handle cookie popup
try:
    time.sleep(1)
    cookie_button = WebDriverWait(driver, 5).until(
        ec.element_to_be_clickable((By.XPATH, "//button[@class='epjs_agree']")))
    cookie_button.click()
except NoSuchElementException:
    pass  # Continue even if the cookie popup is not present or not clickable

links = list()

# Fetch the links to the speeches
while True:
    try:
        time.sleep(0.50)
        button = WebDriverWait(driver, 5).until(
            ec.presence_of_element_located((By.XPATH, "//button[normalize-space()='Load more']"))).click()

        elems = driver.find_elements(By.XPATH, "//a[@href]")
        href_links = [e.get_attribute("href") for e in elems if "doceo" in e.get_attribute("href")]

        # Add links to the list
        links.extend(href_links)

        # Check if the "Load more" button is visible
        button = WebDriverWait(driver, 5).until(
        ec.visibility_of_element_located((By.XPATH, "//button[normalize-space()='Load more']")))
    except (NoSuchElementException, TimeoutException):
        elems = driver.find_elements(By.XPATH, "//a[@href]")
        href_links = [e.get_attribute("href") for e in elems if "doceo" in e.get_attribute("href")]

        # Add remaining links to the list
        links.extend(href_links)

        webpage_links_count = len([e for e in elems if "doceo" in e.get_attribute("href")])
        fetched_links_count = len(href_links)
        print("Number of links on the webpage:", webpage_links_count)
        print("Number of links fetched:", fetched_links_count)
        if webpage_links_count == fetched_links_count:
            print("All links have been fetched successfully.")
        else:
            print("Mismatch: Some links may not have been fetched.")
        break

speeches = list()

# Scrape speeches
for link in links:
    speech_r = requests.get(link)
    speech_soup = BeautifulSoup(speech_r.content, 'html.parser')
    speech_element = speech_soup.find('p', class_='contents')
    speech = speech_element.get_text(strip=True)
    speeches.append(speech)

# Save speeches to CSV file
csv_filename = "speeches.csv"
with open(csv_filename, "w", newline="", encoding="utf-8") as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(["Speech"])
    writer.writerows([[speech] for speech in speeches])

print("Speeches have been saved to", csv_filename)

# Read the CSV file into a DataFrame
df = pd.read_csv("speeches.csv")

# Drop duplicates based on the 'Speech' column
df.drop_duplicates(subset='Speech', inplace=True)

# Save the result back to the CSV file
df.to_csv("speeches_no_duplicates.csv", index=False)

print("Duplicates removed and saved to speeches_no_duplicates.csv")
