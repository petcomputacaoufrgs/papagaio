from urllib.request import urlopen
from bs4 import BeautifulSoup as soup
from http_request_randomizer.requests.proxy.requestProxy import RequestProxy
import pickle
import pandas as pd
import logging
import json
import time

# req_proxy = RequestProxy()
# proxies = req_proxy.get_proxy_list()
logging.getLogger("http_request_randomizer.requests.parsers.PremProxyParser").setLevel(logging.CRITICAL)

proxies = {
    1: 'http://131.108.118.27:8080',
    2: 'http://36.89.194.113:40252',
    3: 'http://170.210.4.222:37490',
    4: 'http://200.116.198.177:35184',
    5: 'http://136.228.141.154:80'
}


def url2soup(url):
    client = urlopen(url)
    page_html = client.read()
    client.close()
    return soup(page_html, 'html.parser')


# calculate amount of pages to iterate
def page_counter(pagination, total_results):
    return total_results // pagination['per_page']


def read_page(page_soup):
    filt = page_soup.body.find('div', {'class': 'js-store'}).get('data-content')
    filt = str(filt)
    filt = filt.replace("&quot;", "'")

    filt = json.loads(filt)

    pagination = filt['store']['page']['data']['pagination']
    total_results = filt['store']['page']['data']['totalResults']
    results = filt['store']['page']['data']['data']['tabs']

    return pagination, total_results, results


def get_page_results(page_soup):
    pagination, total_results, results = read_page(page_soup)
    page_results = []
    for result in results:
        # if result['tab_access_type'] != 'public' or \
        #     result['rating'] < 1.5 or \
        #         result['status'] != 'approved':
        #     break

        name = result['song_name']
        artist = result['artist_name']
        url = result['tab_url']
        page_results.append((name, artist, url, False))

    return page_results, pagination, total_results


def get_urls():
    # PROXY = proxies[0].get_address()
    PROXY = proxies[1]
    print(f'[PROXY CHANGED TO {PROXY}]')

    cur_page = 1

    # all_tabs_todays_popular = f'https://www.ultimate-guitar.com/explore?order=hitsdailygroup_desc&page={cur_page}&type%5B%5D=Pro'
    # all_pro_tabs = f'https://www.ultimate-guitar.com/explore?order=hitstotal_desc&page={cur_page}&type%5B%5D=Pro'

    piano_most_popular = f'https://www.ultimate-guitar.com/explore?instruments%5B%5D=1&order=hitstotal_desc&page={cur_page}&type%5B%5D=Pro'
    alto_sax_most_popular = f'https://www.ultimate-guitar.com/explore?instruments[]=65&order=hitstotal_desc&page={cur_page}&type[]=Pro'
    fingered_bass_most_popular = f'https://www.ultimate-guitar.com/explore?instruments[]=33&order=hitstotal_desc&page={cur_page}&type[]=Pro'
    electric_guitar_most_popular = f'https://www.ultimate-guitar.com/explore?instruments[]=26&order=hitstotal_desc&page={cur_page}&type[]=Pro'

    page_soup = url2soup(electric_guitar_most_popular)

    page_results, pagination, total_results = get_page_results(page_soup)

    df = pd.DataFrame(page_results, columns=['Title', 'Artist', 'URL', 'Check'])

    print(f'Page #{cur_page}\nGot {len(page_results)} results\nData collected: {df}')

    while cur_page * pagination['per_page'] <= total_results:

        if cur_page % 3 == 0:
            PROXY = proxies[cur_page % len(proxies) + 1]
            print(f'[PROXY CHANGED TO {PROXY}]')

        cur_page += 1
        cur_page_url = f'https://www.ultimate-guitar.com/explore?instruments[]=26&order=hitstotal_desc&page={cur_page}&type[]=Pro'
        page_soup = url2soup(cur_page_url)

        page_results, pagination, total_results = get_page_results(page_soup)
        temp_df = pd.DataFrame(page_results, columns=['Title', 'Artist', 'URL', 'Check'])
        df = df.append(temp_df, ignore_index=True)
        print(f'Page #{cur_page}\nGot {len(page_results)} results\nData collected: {df}')
        df.to_csv('results/electric_guitar_results.csv')


if __name__ == '__main__':
    get_urls()
