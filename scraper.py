from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver import ActionChains
from selenium.webdriver.support.wait import WebDriverWait
from langchain.docstore.document import Document
import time

# URL = "https://www.artisan.co"

def scrape_dynamic_content(URL):

    """Scrapes dynamic data from home webpage and returns it - custom to Artisan"""

    chrome_options = Options()
    chrome_options.add_argument("--headless")
    driver = webdriver.Chrome(service = Service(ChromeDriverManager().install()), options = chrome_options)

    driver.get(URL)
    # waiter = WebDriverWait(driver=driver, timeout=120, poll_frequency=1)

    actions = ActionChains(driver)

    count = 1
    
    xpath = '//div[@id="__next"]/main/div[1]/div[1]/div/section[4]/div/section/div[2]/button[{number}]'
    header_xpath = '//*[@id="__next"]/main/div[1]/div[1]/div/section[4]/div/section/div[3]/div[2]/p[1]'
    content_xpath = '//*[@id="__next"]/main/div[1]/div[1]/div/section[4]/div/section/div[3]/div[2]/p[2]'

    # init_text = ""

    content_store = []
    while True:
        new_content = ""
        try:
            button = driver.find_element(By.XPATH, xpath.format(number = count))
            actions.move_to_element(button)
            try:
                actions.click()
                actions.perform()
                print(button.text)
                new_content += button.text
            except Exception as m:
                print(m)
                print(button.text)
                pass
            count += 1
            time.sleep(5)


            # waiter.until(lambda drv: drv.find_element(By.XPATH, header_xpath).text != init_text)
            header = driver.find_element(By.XPATH, header_xpath).text
            content = driver.find_element(By.XPATH, content_xpath).text

            new_content += "\n" + header + "\n" + content
            paragraph = Document(page_content = new_content)
            content_store.append(paragraph)
            """NOTE: There is an issue here where buttons 4 and 5 are being clicked but for some reason the text does not get updated"""
            # print(header, "\n", content)
            # init_text = header
        except Exception as e:
            print(e)
            break
    
    return content_store