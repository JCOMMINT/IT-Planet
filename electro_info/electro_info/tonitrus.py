#%%

import requests
from aux import get_proxy_dc

cookies = {
    'JTLSHOP': 'tg7l85gkml6h5omsjtoi5aofj9',
    '_gcl_au': '1.1.1721821978.1765836319',
    '_ga': 'GA1.1.1451136426.1765836319',
    '__zlcmid': '1V7o8qwGLMSAJRs',
    '_ga_9S35ZDLMD8': 'GS2.1.s1765836319$o1$g1$t1765836359$j20$l0$h1862907472',
    '_clsk': '',
    '_clck': '',
}

headers = {
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'accept-language': 'en-US,en;q=0.9',
    'priority': 'u=0, i',
    'referer': 'https://www.tonitrus.com/Server_1_s2',
    'sec-ch-ua': '"Chromium";v="142", "Google Chrome";v="142", "Not_A Brand";v="99"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"macOS"',
    'sec-fetch-dest': 'document',
    'sec-fetch-mode': 'navigate',
    'sec-fetch-site': 'same-origin',
    'sec-fetch-user': '?1',
    'upgrade-insecure-requests': '1',
    'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36',
    # 'cookie': 'JTLSHOP=tg7l85gkml6h5omsjtoi5aofj9; _gcl_au=1.1.1721821978.1765836319; _ga=GA1.1.1451136426.1765836319; __zlcmid=1V7o8qwGLMSAJRs; _ga_9S35ZDLMD8=GS2.1.s1765836319$o1$g1$t1765836359$j20$l0$h1862907472; _clsk=; _clck=',
}

response = requests.get('https://www.tonitrus.com/Router_11',
                        # cookies=cookies,
                        proxies=get_proxy_dc(),
                        headers=headers)
response.text.find('A9K-16T/8-B ')

#%%

import requests

cookies = {
    'JTLSHOP': 'pp1238o7dvcl0a8glrg0mb76be',
    '_gcl_au': '1.1.1668576489.1766101002',
    '_ga': 'GA1.1.1186060899.1766101003',
    '__zlcmid': '1VAo9JpZ8rUJPXr',
    '_ga_9S35ZDLMD8': 'GS2.1.s1766101003$o1$g1$t1766101010$j53$l0$h777609972',
    '_clsk': '',
    '_clck': '',
}

headers = {
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'accept-language': 'es-419,es;q=0.9,en;q=0.8',
    'priority': 'u=0, i',
    'sec-ch-ua': '"Google Chrome";v="143", "Chromium";v="143", "Not A(Brand";v="24"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"macOS"',
    'sec-fetch-dest': 'document',
    'sec-fetch-mode': 'navigate',
    'sec-fetch-site': 'none',
    'sec-fetch-user': '?1',
    'upgrade-insecure-requests': '1',
    'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36',
    # 'cookie': 'JTLSHOP=pp1238o7dvcl0a8glrg0mb76be; _gcl_au=1.1.1668576489.1766101002; _ga=GA1.1.1186060899.1766101003; __zlcmid=1VAo9JpZ8rUJPXr; _ga_9S35ZDLMD8=GS2.1.s1766101003$o1$g1$t1766101010$j53$l0$h777609972; _clsk=; _clck=',
}

response = requests.get('https://www.tonitrus.com/A9K-16T-8-B_17',
                        proxies=get_proxy_dc(),
                        headers=headers)

response.text.find('A9K-16T/8-B')

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
