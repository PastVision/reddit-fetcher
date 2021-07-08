import os
import requests
import datetime
from tqdm import tqdm
from func_timeout import func_timeout, FunctionTimedOut
import wget
from bs4 import BeautifulSoup


class RedFetch:
    URL = 'https://api.pushshift.io/reddit/submission/search'
    HEADER = {'User-Agent': 'Python requests - Redditstat.py'}

    def __init__(self, user: str = None, sub: str = None, limit: int = -1, downloadpath: str = None) -> None:
        self.user = user
        self.sub = sub
        self.urls = list()
        self.names = dict()
        self.limit = limit
        self.check()
        if downloadpath:
            self.download_path = downloadpath
        else:
            if sub:
                self.download_path = os.path.join(os.getcwd(), f'{sub}')
            else:
                self.download_path = os.path.join(os.getcwd(), f'{user}')
        print(f'User: {self.user}\n' *
              (True if self.user else False) + f'Sub: {self.sub}\n' *
              (True if self.sub else False) + f'Download Path: {self.download_path}')

    def check(self):
        if not (self.user or self.sub):
            print('ERROR!')
            quit(1)

    def fetch(self):
        print('Fetching Info...')
        last = int(datetime.datetime.now().timestamp())
        fetched = 0
        while True:
            params = {
                'size': 100,
                'subreddit': self.sub,
                'author': self.user,
                'before': last
            }
            response = requests.get(
                self.URL, params=params, headers=self.HEADER)
            content = response.json()
            for f in content['data']:
                self.urls.append(f['url'])
                self.names[f['url']] = f['author']
            if len(content['data']) < 100:
                fetched += len(content['data'])
                print(f'Fetched {fetched} URLs!')
                return
            else:
                last = content['data'][-1]['created_utc']
                fetched += 100

    def download(self):
        print(f'Downloading {len(set(self.urls))} files:')
        dl_count = 0
        sk_count = 0
        for url in tqdm(set(self.urls)):
            try:
                save_path = os.path.join(self.download_path, self.names[url])
                if 'ibb.co' in url and 'i.ibb.co' not in url:
                    print(f'IBB: {url}')
                    url = self.ibb(url)
                if not os.path.exists(save_path):
                    os.makedirs(save_path)
                name = func_timeout(240, wget.download,
                                    args=(url, save_path))
                dl_count += 1
            except FunctionTimedOut:
                print(f'Skipped {url}, Reason: TIMEOUT')
                with open(f'timeout.txt', 'at') as f:
                    f.write(url + '\n')
                sk_count += 1
            except Exception as e:
                print(f'Skipped {url}, Reason: {e}')
                sk_count += 1
        print(
            f'Success: {dl_count}/{len(set(self.urls))}\nFailed: {sk_count}/{len(set(self.urls))}')

    def ibb(self, url):
        html = requests.get(url).content.decode()
        soup = BeautifulSoup(html, 'html.parser')
        link = soup.find('a', {'class': 'btn btn-download default'})['href']
        return link


if __name__ == '__main__':
    fetcher = RedFetch(input('User: '), sub=input('Sub: '))
    fetcher.fetch()
    fetcher.download()
