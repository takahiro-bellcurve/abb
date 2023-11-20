from time import sleep

import requests
from lxml import html
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.select import Select
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager


start_urls = "https://job.mynavi.jp/24/pc/search/query.html?WR:1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,41,42,43,44,45,46,47,99/"


def parse_item(response):
    job_mynavi_url = response.url
    source = html.fromstring(response.text)
    company_name = source.xpath("//title/text()")[0]
    postal_code = source.xpath(
        "//th[text()='本社郵便番号']/following-sibling::td/text()")[0]
    company_address = source.xpath(
        "//th[text()='本社所在地']/following-sibling::td/text()")[0]
    company_tel = source.xpath(
        "//th[text()='本社電話番号']/following-sibling::td/text()")[0]
    number_of_hires = ("\n").join(source.xpath(
        "//th[text()='採用実績（人数）']/following-sibling::td/text()"))

    occupation = fetch_occupation(response)

    return {
        "company_name": company_name,
        "postal_code": postal_code,
        "company_address": company_address,
        "company_tel": company_tel,
        "occupation": occupation,
        "number_of_hires": number_of_hires,
        "job_mynavi_url": job_mynavi_url,
    }


def fetch_occupation(response):
    employment_page_link = response.xpath(
        "//div[@id='headerWrap']//li[@class='employment']/a/@href")[0]
    employment_page_response = requests.get(
        "https://job.mynavi.jp" + employment_page_link)
    employment_page_tree = html.fromstring(employment_page_response.text)

    occupation = employment_page_tree.xpath(
        "//tr[@id='shokushu']/td[@class='sameSize']/span[@class='title']/text()")
    if occupation:
        occupation = occupation[0]

    return occupation


def main():
    options = Options()
    options.add_argument('--no-sandbox')
    options.add_argument('--headless')
    driver = webdriver.Chrome(service=ChromeService(
        ChromeDriverManager().install()), options=options)
    driver.get(start_urls)
    sleep(6)

    fetch_data = []
    i = 0
    while driver.find_element(By.XPATH, "//div[@class='mainpagePnation corp upper']//ul[@class='leftRight']/li[contains(@class, 'right')]/@class") == "right":
        i += 1
        print(i)
        corp_links = driver.find_elements(
            By.XPATH, "//div[@class='boxSearchresultEach corp label js-add-examination-list']//h3/a/@href")
        for corp_link in corp_links:
            origin = "https://job.mynavi.jp"
            response = requests.get(origin + corp_link)
            data = parse_item(response)
            fetch_data.append(data)
            sleep(0.7)

        if i % 20 == 0:
            df = pd.DataFrame(fetch_data)
            df.to_csv(f"mynavi_{i}.csv", index=False)
        next_page = driver.find_element(
            By.XPATH, "//div[@class='mainpagePnation corp upper']//ul[@class='leftRight']/li[contains(@class, 'right')]")
        next_page.click()
        sleep(4)


if __name__ == "__main__":
    main()
