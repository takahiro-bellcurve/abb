import re
import lxml
import requests
from io import StringIO
import scrapy
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule


class OnedaySpider(CrawlSpider):
    name = "oneday"
    start_urls = [
        "https://job.rikunabi.com/2025/search/pre/internship/result/?freeword=&isc=r21rcna00253&toplink=search"]

    rules = (Rule(LinkExtractor(restrict_xpaths="//li[@class='ts-p-search-cassetteList-item js-p-clickableCassetteList-item']//h2[@class='ts-p-_cassette-title']/a"), callback='parse_item'),
             Rule(LinkExtractor(
                  restrict_xpaths="//a[@class='ts-p-search-pager01-list-item ts-p-search-pager01-list-item_next']"), follow=True),
             )

    def parse_recruit_info(self, response):
        html_source = lxml.html.parse(StringIO(response.text))
        number_of_hires = "\n".join(html_source.xpath(
            "//table[contains(@class,'ts-p-mod-dataTable02')]//th[text()='採用人数']/following-sibling::td/text()"
        ))
        recruit_occupation = "\n".join(html_source.xpath(
            "//h2[text()='モデルケース']/following-sibling::h3/text()"
        ))
        salary = "\n".join(html_source.xpath(
            "//table[contains(@class,'ts-p-mod-dataTable02')]//th[text()='初年度']/following-sibling::td/text()"
        ))

        return {
            "number_of_hires": number_of_hires,
            "recruit_occupation": recruit_occupation,
            "salary": salary,
        }

    def parse_item(self, response):
        company_name = response.xpath(
            "//h1/a/text()"
        ).get()

        company_page_url = response.url

        contact_box = response.xpath(
            "//h2[text()='連絡先']/following-sibling::div//text()"
        ).getall()
        contact = "".join(contact_box).replace("\t", "")

        phone_number_pattern_list = [
            r"\d{4}-\d{3}-\d{3}",
            r"\d{3}-\d{3}-\d{4}",
            r"\d{3}-\d{2}-\d{4}",
            r"\d{2}-\d{4}-\d{4}",
        ]
        phone_numbers = []
        for phone_number_pattern in phone_number_pattern_list:
            matched_numbers = re.findall(phone_number_pattern, contact)
            if matched_numbers:
                phone_numbers.extend(matched_numbers)
        phone_number = "\n".join(phone_numbers)

        emails = []
        matched_emails = re.findall(r"[\w\.-]+@[\w\.-]+", contact)
        if matched_emails:
            emails.extend(matched_emails)
        email = "\n".join(emails)

        recruit_info_link_path = response.xpath(
            "//div[@class='ts-p-company-upperArea-optionTabArea']//a[contains(text(), '昨年の')]/@href"
        ).get()

        if recruit_info_link_path is None:
            yield {
                "会社名": company_name,
                "電話番号": phone_number,
                "email": email,
                "contact": contact,
                "昨年度採用人数": "詳細情報は取得できませんでした。リクナビ会社ページリンクから確認してください。",
                "募集職種": "詳細情報は取得できませんでした。リクナビ会社ページリンクから確認してください。",
                "給料": "詳細情報は取得できませんでした。リクナビ会社ページリンクから確認してください。",
                "リクナビ会社ページリンク": company_page_url,
            }
            return

        recruit_info_link = f"https://job.rikunabi.com{recruit_info_link_path}"
        recruit_info_response = requests.get(recruit_info_link)
        recruit_info = self.parse_recruit_info(
            recruit_info_response)

        yield {
            "会社名": company_name,
            "電話番号": phone_number,
            "email": email,
            "contact": contact,
            "昨年度採用人数": recruit_info["number_of_hires"],
            "募集職種": recruit_info["recruit_occupation"],
            "給料": recruit_info["salary"],
            "リクナビ会社ページリンク": company_page_url,
        }
