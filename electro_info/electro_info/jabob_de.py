#%%


import requests
from aux import get_proxy_dc
cookies = {
    'session': '959eebe5-b346-4fda-b22d-6c2b23d56991',
    '_referrer': '',
    'SID': '62e4t7t3p631lmfqvn6er4n071',
    '_autuserid2': '7584940819155584205',
    '_webcare_consentid': 'bbea0340-db8e-11f0-9497-edb7673d633a',
    'cookieconsent_status': 'deny',
    'cookieconsent_mode': '[]',
}

headers = {
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'accept-language': 'es-419,es;q=0.9,en;q=0.8',
    'priority': 'u=0, i',
    'referer': 'https://www.jacob.de/apple/?_gl=1*1wfrxrm*_up*MQ..*_ga*MTk0MDEyMTkxMy4xNzY2MDA2NjUy*_ga_R0PTJHPWFP*czE3NjYwMDY2NTEkbzEkZzAkdDE3NjYwMDY2NTEkajYwJGwwJGgw',
    'sec-ch-ua': '"Chromium";v="142", "Google Chrome";v="142", "Not_A Brand";v="99"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"macOS"',
    'sec-fetch-dest': 'document',
    'sec-fetch-mode': 'navigate',
    'sec-fetch-site': 'same-origin',
    'sec-fetch-user': '?1',
    'upgrade-insecure-requests': '1',
    'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36',
    # 'cookie': 'session=959eebe5-b346-4fda-b22d-6c2b23d56991; _referrer=; SID=62e4t7t3p631lmfqvn6er4n071; _autuserid2=7584940819155584205; _webcare_consentid=bbea0340-db8e-11f0-9497-edb7673d633a; cookieconsent_status=deny; cookieconsent_mode=[]',
}

response = requests.get(
    'https://www.jacob.de/apple/?facets[in_stock][1]=on&page=2&_gl=1*1sh8kww*_up*MQ..*_ga*MTk0MDEyMTkxMy4xNzY2MDA2NjUy*_ga_R0PTJHPWFP*czE3NjYwMDY2NTEkbzEkZzEkdDE3NjYwMDY2NjgkajQzJGwwJGgw',
    # cookies=cookies,
    headers=headers,
    proxies=get_proxy_dc()
)

response.text.find('Apple Mac mini')

# %%

import requests

cookies = {
    'session': '959eebe5-b346-4fda-b22d-6c2b23d56991',
    '_referrer': '',
    'SID': '62e4t7t3p631lmfqvn6er4n071',
    '_autuserid2': '7584940819155584205',
    '_webcare_consentid': 'bbea0340-db8e-11f0-9497-edb7673d633a',
    'cookieconsent_status': 'deny',
    'cookieconsent_mode': '[]',
}

headers = {
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'accept-language': 'es-419,es;q=0.9,en;q=0.8',
    'priority': 'u=0, i',
    'referer': 'https://www.jacob.de/apple/?facets[in_stock][1]=on&page=2&_gl=1*1sh8kww*_up*MQ..*_ga*MTk0MDEyMTkxMy4xNzY2MDA2NjUy*_ga_R0PTJHPWFP*czE3NjYwMDY2NTEkbzEkZzEkdDE3NjYwMDY2NjgkajQzJGwwJGgw',
    'sec-ch-ua': '"Chromium";v="142", "Google Chrome";v="142", "Not_A Brand";v="99"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"macOS"',
    'sec-fetch-dest': 'document',
    'sec-fetch-mode': 'navigate',
    'sec-fetch-site': 'same-origin',
    'sec-fetch-user': '?1',
    'upgrade-insecure-requests': '1',
    'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36',
    # 'cookie': 'session=959eebe5-b346-4fda-b22d-6c2b23d56991; _referrer=; SID=62e4t7t3p631lmfqvn6er4n071; _autuserid2=7584940819155584205; _webcare_consentid=bbea0340-db8e-11f0-9497-edb7673d633a; cookieconsent_status=deny; cookieconsent_mode=[]',
}


from aux import get_proxy_dc

response = requests.get(
    'https://www.jacob.de/produkte/apple-mac-mini-mu9d3d-a-artnr-100516471.html?_gl=1*oapim6*_up*MQ..*_ga*MTk0MDEyMTkxMy4xNzY2MDA2NjUy*_ga_R0PTJHPWFP*czE3NjYwMDY2NTEkbzEkZzEkdDE3NjYwMDY2OTUkajE2JGwwJGgw',
    proxies=get_proxy_dc(),
    headers=headers,
)

response.text.find('ENERGY STAR-qualifiziert')
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
