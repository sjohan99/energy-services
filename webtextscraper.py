from utils import *
import asyncio
from time import time


class WebTextScraper:

    def __init__(self, base_url, save_nr, organization_name, min_seconds_between_requests=2):
        self.base_url = base_url
        self.save_nr = save_nr
        self.organization_name = organization_name
        self.min_seconds_between_requests = min_seconds_between_requests
        self.url_text_content_dict_complete = dict()
        self.url_text_content_dict_unique = dict()
        self.explored_urls = set()
        self.ignored_urls = set()
        self.unique_strings = set()
        self.previous_request_time = time()

    async def start(self):
        await self.scrape(self.base_url)

    def save(self):
        create_dir('complete')
        create_dir('unique_only')
        write_file(f'complete/{self.save_nr}{self.organization_name}', self.url_text_content_dict_complete, self.base_url)
        write_file(f'unique_only/{self.save_nr}{self.organization_name}', self.url_text_content_dict_unique, self.base_url)

    async def scrape(self, url):
        """
        Recursively scrapes the text-data from any URL found in the resulting HTML-document for the input-parameter url
        Uses global variable to keep track of explored URLs as to not recurse infinitely.
        Works slowly (default 2 second interval between requests) as to hopefully not get rate-limited
        :param url: URL-address of the site you want to scrape
        :return: Nothing, instead saves found data in instance attribute variables as a key-value pair of URL -> Content
        """
        await self.wait_to_avoid_rate_limiting()
        self.add_url_as_explored(url)
        print(f'INFO: fetched urls for {self.organization_name}: {len(self.explored_urls) // 2}')
        soup = try_to_get_soup_parser(url)
        if soup is None:
            return
        text = get_all_text_from_soup(soup)
        self.add_strings_to_save_dicts(url, text)
        links = self.get_all_href_links(soup, self.base_url)
        for link in links:
            if link not in self.explored_urls:
                await self.scrape(link)

    async def wait_to_avoid_rate_limiting(self):
        wait_time = self.get_wait_time_seconds(time())
        await asyncio.sleep(wait_time)  # Sleep as to not get rate-limited by host
        self.previous_request_time = time()

    def get_wait_time_seconds(self, now):
        time_passed = now - self.previous_request_time
        time_remaining = self.min_seconds_between_requests - time_passed
        return max(0, time_remaining)

    @staticmethod
    def join_strings(strings):
        return '\n'.join(strings)

    def extract_new_unique_strings(self, strings):
        new_unique_strings = {string for string in strings if string not in self.unique_strings}
        self.unique_strings.update(new_unique_strings)
        return new_unique_strings

    def add_strings_to_save_dicts(self, url, strings):
        unique_strings = self.extract_new_unique_strings(strings)
        self.url_text_content_dict_complete[url] = self.join_strings(strings)
        self.url_text_content_dict_unique[url] = self.join_strings(unique_strings)

    def add_url_as_explored(self, url):
        self.explored_urls.add(url)
        if url.endswith('/'):
            self.explored_urls.add(url[:-1])
        else:
            self.explored_urls.add(url + '/')

    def clean_url(self, url: str):
        """
        Removes unwanted parts of the url, such as queries. Adds URLs to ignore list if they end with a file-extension,
        such as .pdf. If URL ends with a file extension BASE is returned instead.
        :param url: URL to clean
        :return: cleaned URL.
        """
        url = clean_query(url)
        if url in self.ignored_urls:
            return self.base_url
        if is_file_link(url, self.base_url):
            print(f'Download link found, adding to ignores. URL was: {url}')
            self.ignored_urls.add(url)
            return self.base_url
        return url

    def get_all_href_links(self, soup, base_url):
        """
        Parses the soup-object for all href-elements in the HTML-document and returns all URLs found.
        If the link starts with a slash '/' that means the link belongs to the base_url and is as such
        concatenated with base_url.

        The links found are cleaned to reduce search space.
        :param soup: soup-object with html parser
        :param base_url: The original URL for the site u want to scrape (no sub-paths)
        :return: All links found in soup-object
        """
        links = set()
        for data in soup.find_all(href=True):
            raw_link = data['href']
            link = None
            if raw_link.startswith('/'):
                link = f'{base_url}{data["href"]}'
            elif raw_link.startswith(base_url):
                link = data['href']
            if link:
                link = self.clean_url(link)
                links.add(link)

        return links

