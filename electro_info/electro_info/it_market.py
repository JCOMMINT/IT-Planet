#%%

import requests
from aux import get_proxy_dc
cookies = {
    'timezone': 'America/Bogota',
    'session-': 'MRjJycNLgy5sN-uwT16MV7KIhaEKa7yYXh4FLyiShDEAJ-2WIPYGesuJcHdX8lC7',
    'maxia-is-net': '0',
    '_ga': 'GA1.1.108900785.1765834695',
    '_gcl_au': '1.1.975364253.1765834769',
    'FPID': 'FPID2.2.xSM1m6MZxXDRNcIBMvpcVl26V%2ByNLUQHsU5hlyoIYHE%3D.1765834695',
    'FPLC': 'w7LOmsKqH9jUYDdM28nbBSGHASTtFdE6Ibn%2BRp1IXwfa4h08GHRYa%2BhfyyzadBssK5iczogTyd9eGOsFgOluyq%2F4StpGbpBW6PEE8%2BzaGyPjrJoBr32Zt6S50ANefA%3D%3D',
    'FPAU': '1.1.975364253.1765834769',
    'FPGSID': '1.1765834770.1765834770.G-79NXQ9DTRQ.68GppwjJw_sWjRphJEkQRg',
    '_ga_TW512S1V9Q': 'GS2.1.s1765834695$o1$g1$t1765834776$j53$l0$h0',
    '_ga_123456': 'GS2.1.s1765834770$o1$g1$t1765834776$j54$l0$h1679252574',
}

headers = {
    'accept': '*/*',
    'accept-language': 'en-US,en;q=0.9',
    'content-type': 'application/json',
    'priority': 'u=1, i',
    'referer': 'https://it-market.com/de/switches',
    'sec-ch-ua': '"Chromium";v="142", "Google Chrome";v="142", "Not_A Brand";v="99"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"macOS"',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-origin',
    'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36',
    'x-requested-with': 'XMLHttpRequest',
    # 'cookie': 'timezone=America/Bogota; session-=MRjJycNLgy5sN-uwT16MV7KIhaEKa7yYXh4FLyiShDEAJ-2WIPYGesuJcHdX8lC7; maxia-is-net=0; _ga=GA1.1.108900785.1765834695; _gcl_au=1.1.975364253.1765834769; FPID=FPID2.2.xSM1m6MZxXDRNcIBMvpcVl26V%2ByNLUQHsU5hlyoIYHE%3D.1765834695; FPLC=w7LOmsKqH9jUYDdM28nbBSGHASTtFdE6Ibn%2BRp1IXwfa4h08GHRYa%2BhfyyzadBssK5iczogTyd9eGOsFgOluyq%2F4StpGbpBW6PEE8%2BzaGyPjrJoBr32Zt6S50ANefA%3D%3D; FPAU=1.1.975364253.1765834769; FPGSID=1.1765834770.1765834770.G-79NXQ9DTRQ.68GppwjJw_sWjRphJEkQRg; _ga_TW512S1V9Q=GS2.1.s1765834695$o1$g1$t1765834776$j53$l0$h0; _ga_123456=GS2.1.s1765834770$o1$g1$t1765834776$j54$l0$h1679252574',
}

params = {
    'min-price': '0',
    'no-aggregations': '1',
    'order': 'topseller',
    'p': '2',
    'slots': '47ea1de08e8b450aa9f98fed3e385920',
}

response = requests.get(
    'https://it-market.com/de/widgets/cms/navigation/6141b19183c08b080429a5b82ec2cb83',
    params=params,
    # cookies=cookies,
    headers=headers,
    proxies=get_proxy_dc()
)

response

response.text.find('Juniper EX43')
# %%

import requests

cookies = {
    'timezone': 'America/Bogota',
    'session-': 'MRjJycNLgy5sN-uwT16MV7KIhaEKa7yYXh4FLyiShDEAJ-2WIPYGesuJcHdX8lC7',
    'maxia-is-net': '0',
    '_ga': 'GA1.1.108900785.1765834695',
    '_gcl_au': '1.1.975364253.1765834769',
    'FPID': 'FPID2.2.xSM1m6MZxXDRNcIBMvpcVl26V%2ByNLUQHsU5hlyoIYHE%3D.1765834695',
    'FPLC': 'w7LOmsKqH9jUYDdM28nbBSGHASTtFdE6Ibn%2BRp1IXwfa4h08GHRYa%2BhfyyzadBssK5iczogTyd9eGOsFgOluyq%2F4StpGbpBW6PEE8%2BzaGyPjrJoBr32Zt6S50ANefA%3D%3D',
    'FPAU': '1.1.975364253.1765834769',
    'FPGSID': '1.1765834770.1765834770.G-79NXQ9DTRQ.68GppwjJw_sWjRphJEkQRg',
    '_ga_TW512S1V9Q': 'GS2.1.s1765834695$o1$g1$t1765834776$j53$l0$h0',
    '_ga_123456': 'GS2.1.s1765834770$o1$g1$t1765834776$j54$l0$h1679252574',
}

headers = {
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'accept-language': 'en-US,en;q=0.9',
    'priority': 'u=0, i',
    'referer': 'https://it-market.com/de/switches?min-price=0&order=topseller&p=2',
    'sec-ch-ua': '"Chromium";v="142", "Google Chrome";v="142", "Not_A Brand";v="99"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"macOS"',
    'sec-fetch-dest': 'document',
    'sec-fetch-mode': 'navigate',
    'sec-fetch-site': 'same-origin',
    'sec-fetch-user': '?1',
    'upgrade-insecure-requests': '1',
    'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36',
    # 'cookie': 'timezone=America/Bogota; session-=MRjJycNLgy5sN-uwT16MV7KIhaEKa7yYXh4FLyiShDEAJ-2WIPYGesuJcHdX8lC7; maxia-is-net=0; _ga=GA1.1.108900785.1765834695; _gcl_au=1.1.975364253.1765834769; FPID=FPID2.2.xSM1m6MZxXDRNcIBMvpcVl26V%2ByNLUQHsU5hlyoIYHE%3D.1765834695; FPLC=w7LOmsKqH9jUYDdM28nbBSGHASTtFdE6Ibn%2BRp1IXwfa4h08GHRYa%2BhfyyzadBssK5iczogTyd9eGOsFgOluyq%2F4StpGbpBW6PEE8%2BzaGyPjrJoBr32Zt6S50ANefA%3D%3D; FPAU=1.1.975364253.1765834769; FPGSID=1.1765834770.1765834770.G-79NXQ9DTRQ.68GppwjJw_sWjRphJEkQRg; _ga_TW512S1V9Q=GS2.1.s1765834695$o1$g1$t1765834776$j53$l0$h0; _ga_123456=GS2.1.s1765834770$o1$g1$t1765834776$j54$l0$h1679252574',
}

response = requests.get('https://it-market.com/de/switches/gigabit/cisco/c9300-48p-e',
                        # cookies=cookies,
                            proxies=get_proxy_dc(),
                        headers=headers)

response.text.find('Ansprechpartner')
# %%


r = response
# Ensures body is available for later use (but loads it into memory)
data = r.content  # bytes
resp_bytes = len(data)

# Approx request bytes (still not wire-accurate)
req = r.request
method_line = f"{req.method} {req.path_url} HTTP/1.1\r\n"
headers = "".join(f"{k}: {v}\r\n" for k, v in req.headers.items())
body = req.body or b""
if isinstance(body, str):
    body = body.encode("utf-8", errors="ignore")

req_bytes_approx = len((method_line + headers + "\r\n").encode("utf-8")) + len(body)

gib = 1024 ** 3
result = {
    "status_code": r.status_code,
    "download_GiB": resp_bytes / gib,
    "upload_GiB_approx": req_bytes_approx / gib,
    "total_GiB_approx": (resp_bytes + req_bytes_approx) / gib,
}

result
# %%
