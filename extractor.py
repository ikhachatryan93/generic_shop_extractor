#! /bin/env python
from os import path, sep
import sys
import platform

dir_path = path.dirname(path.realpath(__file__))
sys.path.insert(0, dir_path + sep + "drivers")
sys.path.insert(0, dir_path + sep + "modules")

try:
    from pyvirtualdisplay import Display

    if "Linux" in platform.system():
        display = Display(visible=1, size=(800, 600))
        display.start()
except:
    pass

import utilities
import shop


def get_url(params, index):
    return params["urls"][index]


def extract(url):
    print("Obtaining information for: {}".format(url))

    driver = utilities.setup_browser(utilities.Configs.get("driver"))
    driver.get(url)

    extracted_data = shop.extract(driver, utilities.Configs.get("threads"))

    # utilities.append_into_file("done_list.txt", keyword)
    return extracted_data


def main():
    items_info = []

    params = utilities.read_excel_file("input_urls.xlsx")
    for index in range(len(params["urls"])):
        url = get_url(params, index)
        items_info += extract(url)
        print("writing output file")
        utilities.write_output("output_items.xlsx", items_info)


if __name__ == "__main__":
    main()
