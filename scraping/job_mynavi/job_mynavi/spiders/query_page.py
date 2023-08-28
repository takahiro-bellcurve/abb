import requests
from lxml import html

import scrapy
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule


class QueryPageSpider(CrawlSpider):
    name = "query_page"
    allowed_domains = ["job.mynavi.jp"]
    start_urls = ["https://job.mynavi.jp/24/pc/search/query.html?WR:1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,41,42,43,44,45,46,47,99/"]

    rules = (
        Rule(LinkExtractor(restrict_xpaths=(
            "//div[@class='mainpagePnation corp upper']//li/a")), follow=True),
        Rule(LinkExtractor(restrict_xpaths=(
            "//div[@class='boxSearchresultEach corp label js-add-examination-list']//h3/a")), callback="parse_item", follow=True),
    )

    def parse_item(self, response):
        job_mynavi_url = response.url
        company_name = response.xpath("//title/text()").get()
        postal_code = response.xpath(
            "//th[text()='本社郵便番号']/following-sibling::td/text()").get()
        company_address = response.xpath(
            "//th[text()='本社所在地']/following-sibling::td/text()").get()
        company_tel = response.xpath(
            "//th[text()='本社電話番号']/following-sibling::td/text()").get()
        number_of_hires = ("\n").join(response.xpath(
            "//th[text()='採用実績（人数）']/following-sibling::td/text()").getall())

        occupation = self.fetch_occupation(response)

        yield {
            "company_name": company_name,
            "postal_code": postal_code,
            "company_address": company_address,
            "company_tel": company_tel,
            "occupation": occupation,
            "number_of_hires": number_of_hires,
            "job_mynavi_url": job_mynavi_url,
        }

        # email
        # employee_scale

    def fetch_occupation(self, response):
        employment_page_link = response.xpath(
            "//div[@id='headerWrap']//li[@class='employment']/a/@href").get()
        employment_page_response = requests.get(
            "https://job.mynavi.jp" + employment_page_link)
        employment_page_tree = html.fromstring(employment_page_response.text)

        occupation = employment_page_tree.xpath(
            "//tr[@id='shokushu']/td[@class='sameSize']/span[@class='title']/text()")[0]

        return occupation
