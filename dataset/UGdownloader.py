import time
import random
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.firefox_profile import FirefoxProfile
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from http_request_randomizer.requests.proxy.requestProxy import RequestProxy
import pandas as pd
import os
from time import sleep
import logging

DOWNLOAD_TIMEOUT = 10

req_proxy = RequestProxy()
proxies = req_proxy.get_proxy_list()

# brasa = [proxy for proxy in proxies if proxy.country == 'Brazil']
# PROXY = brasa[6].get_address()
# webdriver.DesiredCapabilities.FIREFOX['proxy'] = {
#     "httpProxy": PROXY,
#     "proxyType": "MANUAL",
# }



logging.getLogger("selenium.webdriver.remote.remote_connection").setLevel(logging.CRITICAL)
logging.getLogger("urllib3.connectionpool").setLevel(logging.CRITICAL)
logging.getLogger("http_request_randomizer.requests.parsers.PremProxyParser").setLevel(logging.CRITICAL)

# print(proxies[0].get_address())


def download_file(url, destination):
    options = Options()
    options.headless = False

    profile = FirefoxProfile()
    profile.set_preference("browser.download.folderList", 2)
    profile.set_preference("browser.download.manager.showWhenStarting", True)
    profile.set_preference("browser.download.dir", destination)
    profile.set_preference("browser.helperApps.neverAsk.saveToDisk", "application/octet-stream")
    profile.set_preference("browser.download.manager.quitBehavior", 0)

    driver = webdriver.Firefox(options=options, firefox_profile=profile)

    # try:
    driver.get(url)
    button = WebDriverWait(driver, DOWNLOAD_TIMEOUT).until(
        EC.presence_of_element_located(
            (By.XPATH,
             '//button/span[text()="DOWNLOAD Guitar Pro TAB" '
             'or text()="DOWNLOAD Power TAB"]'
             ))
    )
    driver.execute_script("arguments[0].click();", button)

    nFiles = len(os.listdir(destination))

    # kill firefox process after download completes or a timeout is reached
    print('Download started', end="", flush=True)
    downloading = True
    timeout = DOWNLOAD_TIMEOUT
    while downloading and timeout > 0:
        sleep(0.25)
        if len(os.listdir(destination)) > nFiles:
            downloading = False
        timeout -= 0.25
    driver.quit()
    # finally:
    #     driver.quit()

        
data = pd.DataFrame(pd.read_csv('results.csv'))
data.drop(str(data.columns[0]), axis=1, inplace=True)

n_songs = len(data)

data = data[450:500]

# print(data)
# input()

PROXY = proxies[0].get_address()
webdriver.DesiredCapabilities.FIREFOX['proxy'] = {
    "httpProxy": PROXY,
    "proxyType": "MANUAL",
}

for i, song in data.iterrows():

    title = song['Title'].replace('/', '').replace('.', '_')
    artist = song['Artist'].replace('/', '').replace('.', '_')
    url = song['URL']
    folder = f'{os.getcwd()}/gp_files/{artist}/'
    os.makedirs(folder, exist_ok=True)

    # change proxy every 5 downloads
    if i % 5 == 0:
        PROXY = proxies[len(proxies) % i].get_address()
        webdriver.DesiredCapabilities.FIREFOX['proxy'] = {
            "httpProxy": PROXY,
            "proxyType": "MANUAL",
        }
        print(f'[PROXY CHANGED TO {PROXY}]')

    start = time.time()
    print(f'[{i + 1}/{n_songs}] {url} -> ', end="", flush=True)
    download_file(url, folder)
    print(f' [DONE in {format((time.time() - start), ".2f")}s]')
