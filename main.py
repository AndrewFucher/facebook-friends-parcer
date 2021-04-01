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
from config import FRIENDS_FILE_PATH, CHROME_DRIVER_PATH, USERNAME_TO_SEARCH
from constants import FRIEND_DATA_FORMAT, LOGIN_URL, FRIENDS_URL, PROFILE_URL


def login(driver: webdriver.Chrome):
    goToLoginPage(driver)

    wait = WebDriverWait(driver, 10)

    wait.until(EC.visibility_of_element_located((By.ID, "email")))
    driver.find_element_by_id("email").send_keys(LOGIN_USERNAME)
    driver.find_element_by_id("pass").send_keys(LOGIN_PASSWORD)
    driver.find_element_by_id("loginbutton").click()


def goToLoginPage(driver: webdriver.Chrome):
    driver.get(LOGIN_URL)


def goToProfilePage(driver: webdriver.Chrome):
    wait = WebDriverWait(driver, 10)
    try:
        wait.until(EC.visibility_of_element_located((By.XPATH, '//a[@href="/me/"]')))
        driver.find_element_by_xpath('//a[@href="/me/"]').click()
    except TimeoutException:
        driver.find_element_by_xpath('//a[@href="/bookmarks/"]').click()
        try:
            wait.until(
                EC.visibility_of_any_elements_located(
                    (By.XPATH, '//a[@href="{}"]'.format(PROFILE_URL.format(USERNAME_TO_SEARCH)))
                )
            )
            driver.find_elements_by_xpath('//a[@href="{}"]'.format(PROFILE_URL.format(USERNAME_TO_SEARCH)))[
                -1
            ].click()
        except TimeoutException:
            print("Nothing can be done")
            sys.exit(1)


def openFriendsList(driver: webdriver.Chrome):
    wait = WebDriverWait(driver, 10)

    wait.until(
        EC.visibility_of_element_located(
            (By.XPATH, '//a[@href="{}"]'.format(FRIENDS_URL.format(USERNAME_TO_SEARCH)))
        )
    )

    driver.find_element_by_xpath('//a[@href="{}"]'.format(FRIENDS_URL.format(USERNAME_TO_SEARCH))).click()


def getFriendsList(driver: webdriver.Chrome) -> List[WebElement]:
    goToProfilePage(driver)
    openFriendsList(driver)

    wait = WebDriverWait(driver, 10)
    wait.until(
        EC.visibility_of_element_located(
            (By.XPATH, "//div[contains(@data-pagelet, 'ProfileAppSection_0')]")
        )
    )
    num_of_loaded_friends = len(getFriendsListWebElementCollection(driver))
    while True:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        try:
            wait.until(
                lambda d: len(getFriendsListWebElementCollection(driver))
                > num_of_loaded_friends
            )
            num_of_loaded_friends = len(getFriendsListWebElementCollection(driver))
        except TimeoutException:
            break  # no more friends loaded

    return getFriendsListWebElementCollection(driver)


def getFriendsListWebElementCollection(driver: webdriver.Chrome) -> List[WebElement]:
    """Return collection of web elements - elements with friends"""
    return driver.find_elements_by_xpath(
        "//div[@data-pagelet='ProfileAppSection_0']/div[1]/div[1]/div[1]/div[1]/div[3]/div"
    )


def processFriendsList(web_elements: List[WebElement]):
    """Extract <name, surname and other name>, <link to facebook account> from web elemets"""
    result_list: List[str] = []
    for i in web_elements:
        result_list.append(
            FRIEND_DATA_FORMAT.format(
                i.find_element_by_xpath(".//div[2]/div[1]/a/span").get_attribute(
                    "innerText"
                ),
                i.find_element_by_xpath(".//div[2]/div[1]/a").get_attribute("href"),
            )
        )
    return result_list


def parseFriends(driver: webdriver.Chrome):
    login(driver)
    data = getFriendsList(driver)
    processed_data = processFriendsList(data)

    return processed_data


def saveDataToFile(data: List[str]) -> None:
    with open(FRIENDS_FILE_PATH, "w", encoding="utf-8") as file:
        for record in data:
            file.write(record)
            file.write("\n")


def getDriver() -> webdriver.Chrome:
    """Getting driver"""
    chrome_options = webdriver.ChromeOptions()
    prefs = {"profile.default_content_setting_values.notifications": 2}
    chrome_options.add_experimental_option("prefs", prefs)

    driver = webdriver.Chrome(
        executable_path=CHROME_DRIVER_PATH, chrome_options=chrome_options
    )

    return driver


def workflow():
    driver = getDriver()
    friend_list = parseFriends(driver)
    saveDataToFile(friend_list)

    driver.close()


if __name__ == "__main__":
    try:
        workflow()
    except Exception as exc:
        tb = sys.exc_info()[2]
        print(exc.with_traceback())