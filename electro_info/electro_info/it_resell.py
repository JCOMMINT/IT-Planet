#%%

import requests
from aux import get_proxy_dc


cookies = {
    'localization': 'DE',
    'localization': 'DE',
    'cart_currency': 'EUR',
    '_shopify_y': '55998352-1635-4a29-8111-8e94ac875184',
    '_shopify_analytics': ':AZskBVdMAAEA0yNBSPwlFXj3IBjMNjFqwAmUaAngMj2Xq2YVVMVzHEhUkZc22UOyKD7JRyk:',
    'custom_user_id': '55998352-1635-4a29-8111-8e94ac875184',
    'currency': 'EUR',
    'soundestID': '20251215215809-bi2NqmjkpHc5tZ6eVBjb77Vj06fZIvmD6vPYYnkfQ0WR3KcpW',
    'omnisendSessionID': 'KjFDWFVNQWscq1-20251215215809',
    '_prefixboxIntegrationVariant': '',
    '_pfbx_application_information': '8d022096-6122-40cd-b7bb-6b1650273e27',
    '_pfbuid': 'c11c74a2-ae3f-3c46-6957-f592c301c7be',
    '_pfbsesid': '0e92273f-592c-b041-4c2e-056dabc58355',
    '_gcl_au': '1.1.842580682.1765835890',
    '_fbp': 'fb.1.1765835889853.187355412692610522',
    'omnisendShopifyCart': '{}',
    '_pandectes_gdpr': 'eyJzdGF0dXMiOiJhbGxvdyIsInRpbWVzdGFtcCI6MTc2NTgzNTg5MiwicHJlZmVyZW5jZXMiOjAsImlkIjoiNjk0MDg0NzU0ODkwZDlmMjZmOWZlMDFmIn0=',
    '_ga': 'GA1.1.1055122328.1765835895',
    'translation-lab-lang': 'en',
    '_shopify_s': '8bbe5c91-c3cf-4cab-b449-e71cb794be39',
    '_ga_QXQ01L8KEM': 'GS2.1.s1765835943$o1$g1$t1765835956$j47$l0$h0',
    '_ga_LZ7XDSGF6D': 'GS2.1.s1765835895$o1$g1$t1765835956$j60$l0$h0',
    'productSortView': 'grid',
    '_shopify_essential': ':AZskBVY5AAEAhPykBYtxRz43bb2tSV29LLV4_nv30qk8Dl5iUMIWowLTU533x87SuxGFmH3HlCTruTPpo335gF9bxGy6LTN15arPl2HL1ZJzS87TEI6RiTlz3T_EE6HflS1yAc93khGVC2Q46rRZOl-c7tycvMe3TzF53eFzaR8o91_h2BLhL6rpR9kqpmXfet4e5wAwJfrWa6ykLL4ielqltmZwyGXzicO-8LL_jr0PhLwQ3E9K1o8I7dYUe2zSUiuDxGMeMlmmfE7RVe8gvz3HWy6EE3tBlAz-og6CwircofP5oK9jmD19JSsSbLuTPtH2KbIWACXcCsGm1nwyG-2soSzBDPKBZpCH3-Eme8bTP6AvvtU1TEsI:',
    'keep_alive': 'eyJ2IjoyLCJ0cyI6MTc2NTgzNTk1NzEzMSwiZW52Ijp7IndkIjowLCJ1YSI6MSwiY3YiOjEsImJyIjoxfSwiYmh2Ijp7Im1hIjowLCJjYSI6MCwia2EiOjAsInNhIjowLCJrYmEiOjAsInRhIjowLCJ0IjowLCJubSI6MCwibXMiOjAsIm1qIjowLCJtc3AiOjAsInZjIjowLCJjcCI6MCwicmMiOjAsImtqIjowLCJraSI6MCwic3MiOjAsInNqIjowLCJzc20iOjAsInNwIjowLCJ0cyI6MCwidGoiOjAsInRwIjowLCJ0c20iOjB9LCJzZXMiOnsicCI6MywicyI6MTc2NTgzNTg4OTE2NiwiZCI6NjV9fQ%3D%3D',
}

headers = {
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'accept-language': 'en-US,en;q=0.9',
    'priority': 'u=0, i',
    'referer': 'https://www.it-resell.com/en/collections/cisco-router',
    'sec-ch-ua': '"Chromium";v="142", "Google Chrome";v="142", "Not_A Brand";v="99"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"macOS"',
    'sec-fetch-dest': 'document',
    'sec-fetch-mode': 'navigate',
    'sec-fetch-site': 'same-origin',
    'sec-fetch-user': '?1',
    'upgrade-insecure-requests': '1',
    'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36',
    # 'cookie': 'localization=DE; localization=DE; cart_currency=EUR; _shopify_y=55998352-1635-4a29-8111-8e94ac875184; _shopify_analytics=:AZskBVdMAAEA0yNBSPwlFXj3IBjMNjFqwAmUaAngMj2Xq2YVVMVzHEhUkZc22UOyKD7JRyk:; custom_user_id=55998352-1635-4a29-8111-8e94ac875184; currency=EUR; soundestID=20251215215809-bi2NqmjkpHc5tZ6eVBjb77Vj06fZIvmD6vPYYnkfQ0WR3KcpW; omnisendSessionID=KjFDWFVNQWscq1-20251215215809; _prefixboxIntegrationVariant=; _pfbx_application_information=8d022096-6122-40cd-b7bb-6b1650273e27; _pfbuid=c11c74a2-ae3f-3c46-6957-f592c301c7be; _pfbsesid=0e92273f-592c-b041-4c2e-056dabc58355; _gcl_au=1.1.842580682.1765835890; _fbp=fb.1.1765835889853.187355412692610522; omnisendShopifyCart={}; _pandectes_gdpr=eyJzdGF0dXMiOiJhbGxvdyIsInRpbWVzdGFtcCI6MTc2NTgzNTg5MiwicHJlZmVyZW5jZXMiOjAsImlkIjoiNjk0MDg0NzU0ODkwZDlmMjZmOWZlMDFmIn0=; _ga=GA1.1.1055122328.1765835895; translation-lab-lang=en; _shopify_s=8bbe5c91-c3cf-4cab-b449-e71cb794be39; _ga_QXQ01L8KEM=GS2.1.s1765835943$o1$g1$t1765835956$j47$l0$h0; _ga_LZ7XDSGF6D=GS2.1.s1765835895$o1$g1$t1765835956$j60$l0$h0; productSortView=grid; _shopify_essential=:AZskBVY5AAEAhPykBYtxRz43bb2tSV29LLV4_nv30qk8Dl5iUMIWowLTU533x87SuxGFmH3HlCTruTPpo335gF9bxGy6LTN15arPl2HL1ZJzS87TEI6RiTlz3T_EE6HflS1yAc93khGVC2Q46rRZOl-c7tycvMe3TzF53eFzaR8o91_h2BLhL6rpR9kqpmXfet4e5wAwJfrWa6ykLL4ielqltmZwyGXzicO-8LL_jr0PhLwQ3E9K1o8I7dYUe2zSUiuDxGMeMlmmfE7RVe8gvz3HWy6EE3tBlAz-og6CwircofP5oK9jmD19JSsSbLuTPtH2KbIWACXcCsGm1nwyG-2soSzBDPKBZpCH3-Eme8bTP6AvvtU1TEsI:; keep_alive=eyJ2IjoyLCJ0cyI6MTc2NTgzNTk1NzEzMSwiZW52Ijp7IndkIjowLCJ1YSI6MSwiY3YiOjEsImJyIjoxfSwiYmh2Ijp7Im1hIjowLCJjYSI6MCwia2EiOjAsInNhIjowLCJrYmEiOjAsInRhIjowLCJ0IjowLCJubSI6MCwibXMiOjAsIm1qIjowLCJtc3AiOjAsInZjIjowLCJjcCI6MCwicmMiOjAsImtqIjowLCJraSI6MCwic3MiOjAsInNqIjowLCJzc20iOjAsInNwIjowLCJ0cyI6MCwidGoiOjAsInRwIjowLCJ0c20iOjB9LCJzZXMiOnsicCI6MywicyI6MTc2NTgzNTg4OTE2NiwiZCI6NjV9fQ%3D%3D',
}

params = {
    'page': '3',
}

response = requests.get('https://www.it-resell.com/en/collections/cisco-router',
                        params=params,
                        cookies=cookies,
                        proxies=get_proxy_dc(),
                        headers=headers)

response


response.text.find('882658357008')
# %%


import requests

headers = {
    'Referer': 'https://www.it-resell.com/en/collections/cisco-router?page=3',
    'Upgrade-Insecure-Requests': '1',
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36',
    'sec-ch-ua': '"Chromium";v="142", "Google Chrome";v="142", "Not_A Brand";v="99"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"macOS"',
}

response = requests.get(
    'https://www.it-resell.com/en/collections/cisco-router/products/cisco-c1921-adsl2-m-k9',
    headers=headers,
    proxies=get_proxy_dc(),
)

response.text.find('882658357008')
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
