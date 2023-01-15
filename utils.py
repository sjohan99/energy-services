import sys
import urllib.error
from urllib import request
from bs4 import BeautifulSoup
from time import sleep
from datetime import datetime
import regex
import os
import requests


def create_dir(path):
    if not os.path.isdir(path):
        os.makedirs(path)


def write_file(path, url_content_dict, base_url):
    with open(path, 'w', encoding='utf-8') as f:
        f.write(f'CREATED AT: {datetime.now()}\nBASE DOMAIN: {base_url}')
    with open(path, 'a', encoding='utf-8') as f:
        for key, value in url_content_dict.items():
            f.write(f'\n\n\nSOURCE: {key}\n')
            f.write(value)


def download_pdf(url):
    response = requests.get(url)
    with open('holmen.pdf', 'wb') as f:
        f.write(response.content)


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
    web_content = response.read()
    return web_content


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


def handle_http_error(e, url):
    print(f'Unexpected {type(e)} error at url: {url}, info below')
    print(e)


def handle_decode_error(e, url):
    print(f'Got {type(e)} at url: {url}')
    print(e)


def get_soup_parser_for_html(url):
    """
    Downloads HTML-document and returns a BeautifulSoup object with an html parser
    :param url: URL to download from
    :return: BeautifulSoup object configured as html parser
    """
    content = download_html(url)
    return BeautifulSoup(content, features="html.parser")


def is_file_link(url, base_url):
    """
    Uses a simple regex pattern to find links containing BASE and ending in a file extension except .html
    :param url: URL to check
    :param base_url: URL of the base domain
    :return: True if url ends with a file extension (other than .html), otherwise false
    """
    if url.endswith('.html'):
        return False
    pattern = base_url + r'.*\..*$'
    match = regex.search(pattern, url)
    if match:
        return True
    return False


def get_all_text_from_soup(soup):
    """
    Gets all text-content available to end user in the HTML-document for the soup-parser and returns it as one string
    with a new-line between every instance of text.
    :param soup:
    :return: List of all stripped strings from soup-object
    """
    for data in soup(['style', 'script']):
        # Remove tags
        data.decompose()
    # return data by retrieving the tag content

    return [string for string in soup.stripped_strings]


# def is_energy_pdf(url):
#     wanted_pdf = "energi"
#     if regex.search(wanted_pdf, url):
#         return True
#     return False
