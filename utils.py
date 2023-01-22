import urllib.error

import aiohttp
from bs4 import BeautifulSoup
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


async def download_html_async(url, aio_session):
    async with aio_session.get(url) as resp:
        return await resp.text()


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


async def try_to_get_soup_parser_async(url, aio_session):
    """
    Tries to download content from URL and create soup-object. If the content is unable to be decoded or something went
    wrong with the HTTP request then the errors are handled and None is returned
    :param url: URL to get soup-object for
    :param aio_session: a aiohttp ClientSession to perform requests with
    :return: soup-object if successful, None if not.
    """
    try:
        soup = await get_soup_parser_for_html_async(url, aio_session)
        return soup
    except UnicodeDecodeError as e:
        handle_decode_error(e, url)
        return None
    except urllib.error.HTTPError as e:
        handle_http_error(e, url)
        return None
    except aiohttp.ClientResponseError as e:
        print(f'url: {url}. error: {e}')
        return None


def handle_http_error(e, url):
    print(f'Unexpected {type(e)} error at url: {url}, info below')
    print(e)


def handle_decode_error(e, url):
    print(f'Got {type(e)} at url: {url}')
    print(e)


async def get_soup_parser_for_html_async(url, aio_session):
    content = await download_html_async(url, aio_session)
    return BeautifulSoup(content, features="html.parser")


def is_file_link(url, base_url):
    """
    Uses a simple regex pattern to find links containing BASE and ending in a file extension except .html
    :param url: URL to check
    :param base_url: URL of the base domain
    :return: True if url ends with a file extension (other than .html), otherwise false
    """
    if url.endswith('.html') or url.lower().endswith('.htm') or url.lower().endswith('css'):
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
