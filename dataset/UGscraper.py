from urllib.request import urlopen
from bs4 import BeautifulSoup as soup
import pickle
import pandas as pd
import json
import os


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
        if result['tab_access_type'] != 'public' or \
                result['rating'] < 1.5 or \
                result['status'] != 'approved':
            break

        name = result['song_name']
        artist = result['artist_name']
        url = result['tab_url']
        page_results.append((name, artist, url))

    return page_results, pagination, total_results


def get_urls():
    cur_page = 1
    cur_page_url = f'https://www.ultimate-guitar.com/explore?live%5B%5D=0&order=rating_desc&page={cur_page}&part%5B%5D=&type%5B%5D=Pro'

    page_soup = url2soup(cur_page_url)

    page_results, pagination, total_results = get_page_results(page_soup)
    df = pd.DataFrame(page_results, columns=['Title', 'Artist', 'URL'])
    print(f'Page #{cur_page}\tData collected: {df}')

    try:
        while cur_page*pagination['per_page'] <= total_results:
            cur_page += 1
            cur_page_url = f'https://www.ultimate-guitar.com/explore?live%5B%5D=0&order=hitstotal_desc&page={cur_page}&part%5B%5D=&type%5B%5D=Pro'
            page_soup = url2soup(cur_page_url)

            page_results, pagination, total_results = get_page_results(page_soup)
            temp_df = pd.DataFrame(page_results, columns=['Title', 'Artist', 'URL'])
            df = df.append(temp_df, ignore_index=True)
            print(f'Page #{cur_page}\tData collected: {df}')
            df.to_csv('results.csv')
    finally:
        df.to_csv('results.csv')


if __name__ == '__main__':
    get_urls()