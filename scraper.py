from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By

from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from time import sleep

import subprocess

import requests

# Bemærk at følgende er skræddersyet til mit setup, og kræver sikkert noget justering
PASS_NAME = "microsoftonline.com"
PASS_INFO = subprocess.run(["pass", "show", PASS_NAME], capture_output=True, check=True, text=True).stdout.split('\n')

LOGIN_EMAIL = PASS_INFO[1][7:] # EMAIL til microsoft authentication (AU-ID)
LOGIN_PASSWORD = PASS_INFO[0] # PASSWORD til microsoft authentication (Koden dertilhørende)

driver = webdriver.Firefox()

driver.implicitly_wait(4)

driver.get("https://mitstudie.au.dk")

driver.find_element(By.ID, "cookiescript_reject").click()
sleep(1)
driver.find_element(By.CLASS_NAME, "button--large").click()
email_input = driver.find_element(By.ID, "i0116")
email_input.clear()
email_input.send_keys(LOGIN_EMAIL, Keys.RETURN)

password_input = driver.find_element(By.ID, "i0118")
password_input.clear()
password_input.send_keys(LOGIN_PASSWORD)

sleep(2) # man skal åbenbart vente lidt, idk
driver.find_element(By.ID, "idSIButton9").click() # fordi retur åbenbart ikke virker ved passwords, idk

# Her skal man opnå otp-koden.
pass_otp = subprocess.run(["pass", "otp", PASS_NAME], capture_output=True, check=True, text=True).stdout

otp_input = driver.find_element(By.ID, "idTxtBx_SAOTCC_OTC")
otp_input.clear()
otp_input.send_keys(pass_otp)

sleep(1) # man skal vist stadig vente lidt

driver.find_element(By.ID, "idSubmit_SAOTCC_Continue").click() # retur virker stadigvæk ikke

sleep(1)

driver.get("https://brightspace.au.dk/d2l/le/lessons/108494/units/1434212") # statistik kurset
iframe = driver.find_element(By.CLASS_NAME, "d2l-fra-iframe").find_element(By.TAG_NAME, "iframe")
driver.switch_to.frame(iframe)

tree = driver.find_element(By.CLASS_NAME, "navigation-tree") # denne indeholder alt i menuen til venstre
menus = tree.find_elements(By.CLASS_NAME, "navigation-item") # vi er for nu kun interesserede i ugesedler
for item in menus:
    if item.get_attribute("data-objectid") == "1434212":
        print("Found item")
        break

ugesedler = item.find_element(By.CLASS_NAME, "unit").find_elements(By.CLASS_NAME, "navigation-item")

ugesedler_url = []
for ugesedddel in ugesedler:
    ugesedler_url.append(
            "https://brightspace.au.dk/d2l/api/hm/sequences/108494/activity/" + ugesedddel.get_attribute("data-objectid")
    )

d2lcookie1 = driver.get_cookie("d2lSessionVal")
d2lcookie2 = driver.get_cookie("d2lSecureSessionVal")
driver.quit()

def get_ugeseddel(session, fetch_url):
    print(f"Fetching pdf-data from {fetch_url}")
    r = session.get(fetch_url)
    json = r.json()
    pdf_url = json["entities"][2]["entities"][0]["links"][0]["href"]
    #filename = json["entities"][2]["entities"][0]["properties"]["name"]
    filename = json["properties"]["title"] + ".pdf"
    print(f"Fetching pdf from {pdf_url} and saving to {filename}")
    pdf_response = session.get(pdf_url)
    with open(f"scraped/{filename}", "wb") as f:
        f.write(pdf_response.content)

with requests.Session() as s:
    #requests.utils.add_dict_to_cookiejar(s.cookies, d2lcookie1)
    #requests.utils.add_dict_to_cookiejar(s.cookies, d2lcookie2)

    #s.cookies.set(**d2lcookie1)
    #s.cookies.set(**d2lcookie2)

    s.cookies.set(d2lcookie1["name"], d2lcookie1["value"])
    s.cookies.set(d2lcookie2["name"], d2lcookie2["value"])

    for url in ugesedler_url:
        get_ugeseddel(s, url)
