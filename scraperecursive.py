import sys
import urllib.error
from urllib import request
from bs4 import BeautifulSoup
from time import sleep
from datetime import datetime
import regex

page_text_dict = dict()
explored = set()
ignored = set()
# BASE = r'https://www.holmen.com'
BASE = sys.argv[1]
SAVE_NAME = sys.argv[2] + '.txt'
strings = set()


def main():
    """
    Start program, runs scrape() to get all info then creates a file called according to SAVE_NAME
    and saves the data found in it.
    :return:
    """
    scrape(BASE)
    with open(SAVE_NAME, 'w', encoding='utf-8') as f:
        f.write(f'CREATED AT {datetime.now()}\n')
    with open(SAVE_NAME, 'a', encoding='utf-8') as f:
        for key, value in page_text_dict.items():
            f.write(f'\n\n\nSOURCE: {key}\n')
            f.write(value)

    print(f'DONE! Pulled data from {len(page_text_dict)} addresses')


def scrape(url):
    """
    Recursively scrapes the text-data from any URL found in the resulting HTML-document for the input-parameter url
    Uses global variable to keep track of explored URLs as to not recurse infinitely.
    Works slowly (2 second interval between requests) as to hopefully not get rate-limited
    :param url: URL-address of the site you want to scrape
    :return: Nothing, instead saves found data in global variable as a key-value pair of URL -> Content
    """
    sleep(2)  # Sleep as to not get rate-limited by host
    add_url_as_explored(url)
    print(f'INFO: size of explored = {len(explored) / 2}')
    soup = try_to_get_soup_parser(url)
    if soup is None:
        return
    text = get_all_text_from_soup(soup)
    links = get_all_href_links(soup, BASE)
    page_text_dict[url] = text
    for link in links:
        if link not in explored:
            scrape(link)


def try_to_get_soup_parser(url):
    """
    Tries to download content from URL and create soup-object. If the content is unable to be decoded or something went
    wrong with the HTTP request then the errors are handled and None is returned
    :param url: URL to get soup-object for
    :return: soup-object if successful, None if not.
    """
    try:
        soup = get_soup_parser_for_html(url)
        return soup
    except UnicodeDecodeError as e:
        handle_decode_error(e, url)
        return None
    except urllib.error.HTTPError as e:
        handle_http_error(e, url)
        return None


def add_url_as_explored(url):
    explored.add(url)
    if url.endswith('/'):
        explored.add(url[:-1])
    else:
        explored.add(url + '/')


def handle_http_error(e, url):
    print(f'Unexpected {type(e)} error at url: {url}, info below')
    print(e)


def handle_decode_error(e, url):
    print(f'Got {type(e)} at url: {url}')
    print(e)


def download_html(url):
    """
    Downloads and reads the HTML-document into a python string at the given url
    :param url: URL for the HTML-document to download
    :return: HTML-document as string
    """
    req = request.Request(
        url,
        headers={
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_4) AppleWebKit/603.1.30 (KHTML, like Gecko) Version/10.1 Safari/603.1.30'}
    )
    response = request.urlopen(req)
    web_content = response.read().decode('UTF-8')
    return web_content


def get_soup_parser_for_html(link):
    """
    Downloads HTML-document and returns a BeautifulSoup object with an html parser
    :param link:
    :return:
    """
    content = download_html(link)
    return BeautifulSoup(content, features="html.parser")


def get_all_href_links(soup, base_url):
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
            link = clean_url(link)
            links.add(link)

    return links


def clean_url(url: str):
    """
    Removes unwanted parts of the url, such as queries. Adds URLs to ignore list if they end with a file-extension,
    such as .pdf. If URL ends with a file extension BASE is returned instead.
    :param url: URL to clean
    :return: cleaned URL.
    """
    url = clean_query(url)
    if url in ignored:
        return BASE
    if is_file_link(url):
        print(f'Download link found, adding to ignores. URL was: {url}')
        ignored.add(url)
        return BASE
    return url


def clean_query(url):
    """
    Slices the string at the query-index (where '?' is) if there is one and returns the left part of the slice.
    :param url: url to clean
    :return:
    """
    query_index = url.rfind('?')
    if query_index != -1:
        url = url[:query_index]
    return url


def is_file_link(url):
    """
    Uses a simple regex pattern to find links containing BASE and ending in a file extension except .html
    :param url: URL to check
    :return: True if url ends with a file extension (other than .html), otherwise false
    """
    if url.endswith('.html'):
        return False
    pattern = BASE + r'.*\..*$'
    match = regex.search(pattern, url)
    if match:
        return True
    return False


def get_all_text_from_soup(soup):
    """
    Gets all text-content available to end user in the HTML-document for the soup-parser and returns it as one string
    with a new-line between every instance of text.
    :param soup:
    :return:
    """
    for data in soup(['style', 'script']):
        # Remove tags
        data.decompose()
    # return data by retrieving the tag content
    return '\n'.join(soup.stripped_strings)

if __name__ == '__main__':
    main()
