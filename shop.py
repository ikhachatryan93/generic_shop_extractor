import sys
import logging
import threading
import time

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

from bs4 import BeautifulSoup
from urllib.request import urljoin
from urllib.request import urlopen

from item import Item
import utilities

drivers = []
max_num_threads = utilities.Configs.get("max_browsers")
total_pagins = 0

# for security reasons
assert (max_num_threads < 30)

for j in range(max_num_threads):
    drivers.append({"driver": utilities.setup_browser(), "status": "free"})


def click_next_pagination(driver):
    logging.info("Extracting items list")
    wait = WebDriverWait(driver, 5)

    pagin_xpath = utilities.Configs.get("pagination_xpath")

    next_page = wait.until(EC.presence_of_element_located((By.XPATH, pagin_xpath)))

    # scroll into Next Page button
    driver.execute_script("return arguments[0].scrollIntoView(false);", next_page)
    # driver.execute_script("window.scrollBy(0, 150);")

    utilities.click(driver, next_page)
    click_next_pagination.counter += 1


click_next_pagination.counter = 0


def get_item_signature():
    item_html_class = utilities.Configs.get('item_html_class')
    if not item_html_class:
        logging.error('''Please specify item's css in configs.txt file!''')
        exit(1)

    item_html_class = item_html_class.lstrip('.')

    item_html_tag = utilities.Configs.get("item_html_tag")
    if not item_html_tag:
        logging.error('''Please specify item's HTML element in configs.txt file!''')
        exit(1)

    return item_html_tag, item_html_class


def get_item_urls(driver):
    urls = []
    testing = utilities.Configs.get("testing")

    item_html_tag, item_html_css = get_item_signature()

    website_domain = urljoin(driver.current_url, '/')
    while True:
        soup = BeautifulSoup(driver.page_source, "lxml")
        items = soup.findAll(item_html_tag, {"class", item_html_css})
        for item in items:
            try:
                urls.append(urljoin(website_domain, item.a["href"]))
            except:
                pass

        if testing:
            break

        try:
            time.sleep(utilities.Configs.get("wait_before_pagination"))
            click_next_pagination(driver)
            time.sleep(utilities.Configs.get("wait_after_pagination"))
        except TimeoutException:
            logging.info("Completed pagination process. Total paginations {}".format(click_next_pagination.counter))
            break

    driver.quit()

    old_num = len(urls)
    filtered = set(urls)
    logging.info(
        "Url extraction is done. Total {} items have been filtered from {} extracted".format(len(filtered), old_num))

    return filtered


def get_free_driver():
    while True:
        time.sleep(0.2)
        for i in range(len(drivers)):
            if drivers[i]["status"] == "free":
                drivers[i]["status"] = "used"
                return drivers[i]["driver"], i


def extract_item(url, items_info, try_again=True):
    driver, i = get_free_driver()
    driver.get(url)
    time.sleep(1)
    try:
        item = Item(driver)
        item.extract()
        items_info.append(item.info)
    except Exception as e:
        logging.critical(str(e) + ". while getting information from " + url)
        if try_again:
            logging.info("Trying again")
            extract_item(url, items_info, try_again=False)

    drivers[i]["status"] = "free"


def extract(driver, threads_num):
    shop_urls = get_item_urls(driver)
    items_info = []

    max_extr_items = utilities.Configs.get("max_items_extract")

    trds = []
    i = 0
    total = len(shop_urls)

    for url in shop_urls:

        if i >= max_extr_items:
            print("Reached maximum number of extractions specified in configs.txt file")
            break
        i += 1
        sys.stdout.write("\r[Extracting: {}/{}]".format(i, total))
        sys.stdout.flush()
        time.sleep(0.3)
        t = threading.Thread(target=extract_item, args=(url, items_info))
        t.daemon = True
        t.start()
        trds.append(t)
        while threading.active_count() > threads_num:
            time.sleep(0.2)

    for t in trds:
        t.join(10)

    for d in drivers:
        d["driver"].quit()

    return items_info
