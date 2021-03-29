import sys
from time import sleep
from typing import List

from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from secret import LOGIN_USERNAME, LOGIN_PASSWORD
from config import USERNAME_TO_SEARCH, CHROME_DRIVER_PATH
from constants import LOGIN_URL, FRIENDS_URL, PROFILE_URL


def login(driver: webdriver.Chrome, url, username, password):
    driver.get(url)

    wait = WebDriverWait(driver, 10)

    wait.until(EC.visibility_of_element_located((By.ID, "email")))
    driver.find_element_by_id("email").send_keys(username)
    driver.find_element_by_id("pass").send_keys(password)
    driver.find_element_by_id("loginbutton").click()


def get_friends_list(driver: webdriver.Chrome) -> List[WebElement]:
    return driver.find_elements_by_xpath(
        "//div[@data-pagelet='ProfileAppSection_0']/div[1]/div[1]/div[1]/div[1]/div[3]/div"
    )


def parseFriends(driver: webdriver.Chrome, friends_url: str, profile_url: str):
    wait = WebDriverWait(driver, 5)
    try:
        wait.until(EC.visibility_of_element_located((By.XPATH, '//a[@href="/me/"]')))
        driver.find_element_by_xpath('//a[@href="/me/"]').click()
    except TimeoutException:
        driver.find_element_by_xpath('//a[@href="/bookmarks/"]').click()
        sleep(2)

        driver.find_elements_by_xpath('//a[@href="{}"]'.format(profile_url))[-1].click()

    wait.until(
        EC.visibility_of_element_located(
            (By.XPATH, '//a[@href="{}"]'.format(friends_url))
        )
    )

    driver.find_element_by_xpath('//a[@href="{}"]'.format(friends_url)).click()

    wait.until(
        EC.visibility_of_element_located(
            (By.XPATH, "//div[contains(@data-pagelet, 'ProfileAppSection_0')]")
        )
    )

    num_of_loaded_friends = len(get_friends_list(driver))
    while True:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        try:
            wait.until(lambda d: len(get_friends_list(driver)) > num_of_loaded_friends)
            num_of_loaded_friends = len(get_friends_list(driver))
        except TimeoutException:
            break  # no more friends loaded

    return get_friends_list(driver)


def workflow():
    chrome_options = webdriver.ChromeOptions()
    prefs = {"profile.default_content_setting_values.notifications": 2}
    chrome_options.add_experimental_option("prefs", prefs)

    driver = webdriver.Chrome(
        executable_path=CHROME_DRIVER_PATH, chrome_options=chrome_options
    )
    login(driver, LOGIN_URL, LOGIN_USERNAME, LOGIN_PASSWORD)

    a = parseFriends(
        driver,
        FRIENDS_URL.format(USERNAME_TO_SEARCH),
        PROFILE_URL.format(USERNAME_TO_SEARCH),
    )

    with open("friends.txt", "w", encoding="utf-8") as file:
        for i in a:
            file.write(
                "{}:{}\n".format(
                    i.find_element_by_xpath(".//div[2]/div[1]/a/span").get_attribute(
                        "innerText"
                    ),
                    i.find_element_by_xpath(".//div[2]/div[1]/a").get_attribute("href"),
                )
            )

    driver.close()


if __name__ == "__main__":
    try:
        workflow()
    except Exception as exc:
        tb = sys.exc_info()[2]
        print(exc.with_traceback())