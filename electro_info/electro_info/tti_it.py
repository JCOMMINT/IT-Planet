#%%

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

BASE_URL = "https://www.tti.com"

def extract_part_links(html: str):
    soup = BeautifulSoup(html, "html.parser")
    results = []

    rows = soup.select("tr.c-part-search__table-row")

    for row in rows:
        link = row.select_one("a[name='t-part-search-manufacturer-number']")
        if not link:
            continue

        part_number = link.get_text(strip=True)
        relative_url = link.get("href")

        results.append({
            "part_number": part_number,
            "relative_url": relative_url,
            "absolute_url": urljoin(BASE_URL, relative_url)
        })

    return results
from aux import get_proxy_dc

def get_info_by_page(page):
    cookies = {
        'visid_incap_2587712': 'sfdELyWVRiaRRBBg1zdHwxjZOWkAAAAAQUIPAAAAAAAAM0Jo9vAGTBt/QNnpiC4q',
        'cookieNecessary': 'true',
        'cookiePerformance': 'true',
        'cookiePersonalization': 'true',
        'cookieMarketing': 'true',
        '_pxvid': '7d951445-d607-11f0-a0cc-0c8f57c49ced',
        'nlbi_2587712': 'LmjCPSRiU1AawPhQL026UQAAAACYvlE5xaScI1bf3DKZKF0D',
        'incap_ses_8224_2587712': 'Kl6aS4APV3tTnWPV6IQhcugiQ2kAAAAAuh7lAEZzX4FAD8jY9jQy3Q==',
        'AMCVS_474027E253DB53E90A490D4E%40AdobeOrg': '1',
        'AMCV_474027E253DB53E90A490D4E%40AdobeOrg': '1075005958%7CMCIDTS%7C20440%7CMCMID%7C77670064873010431491933567254647709142%7CMCAAMLH-1766612329%7C4%7CMCAAMB-1766612329%7CRKhpRz8krg2tLO6pguXWp5olkAcUniQYPHaMWWgdJ3xzPWQmdj0y%7CMCOPTOUT-1766014729s%7CNONE%7CMCAID%7CNONE%7CvVersion%7C4.4.1',
        'partSearchObject': '%7B%22c%22%3A%22connectors%22%7D',
        's_cc': 'true',
        'pxcts': 'c73375e4-db90-11f0-abd1-6e8c6eee51d8',
        '_pxhd': 'G-QeIBy-1zwI2GLPXr-Bj4B6xLE6SVP4MkMU5THhcIFSTnSkF9mTl1WjuM5ZkW7o5-MYUDnwOG-/yXE9aw2dug==:N5dyzIGQccUOff2XF4lRyUssxmK1VKmMmu-3A2hsZxgUe7iDAppxIk6Gx40oQiZ1Lk2UmE8alJNlnbBdxlJFVVL0U70ZwsMre7lR1luPWWo=',
        '_gcl_au': '1.1.1952447325.1766007531',
        '_ga': 'GA1.1.747242929.1766007531',
        '_clck': '3k7ujb%5E2%5Eg1x%5E0%5E2171',
        '_uetsid': 'c76f72c0db9011f0af7031094069895c',
        '_uetvid': '30dc9760d69811f08bf59b7550261e73',
        '_clsk': '10tdtxb%5E1766007617091%5E2%5E1%5Ee.clarity.ms%2Fcollect',
        '_px3': '034b3bbe47e003d12ac3de2b7f4dc622c57143a5000011543b25862e670983d1:P7MJJQubi04aG+cfrvARplnPoemUfR3yTgURTAg3/WOwUtbT38bUYHz/xtJrwO7S+TSOko/NN94HLVLxlICN4A==:1000:hF0czrh+BhiksXH2BTJMrtBveJ9yesPYIPNPCFQJwivGTqp9xhvyoxNzYz+S8kUQy4eKY29MEw5y7eetgSHMroD0iAlRd0Jx2kElRLPH8LFjUCADYNPrkVqB3BJnCVcEeY7WFMGQvHZzbsoedjuVDzNqEbP5v9GMbLdZTdbQlGughQGXcn7IpZnn+6gN9W+FBQCWo/WHjFokLTgYIcTYlQUn2zIDN3Tua9lzkK5acY0bZrly9Mt4SEW8ic8VYWLe0hKX2iRYO0U8FHSmcunm1HGXfj3EaHKv0w3GDWnIUPnFETzrqNhvue0pZkXJNry/LBmH3U/tnTg8KHX2phgXcA5xhf816UoyFY+uaXKx5Y2hNaifJ/Yleafi93zhiqDj6kehXguNj1KrLLquzgjudg==',
        '_ga_DZLYG7VYSV': 'GS2.1.s1766007531$o1$g1$t1766007625$j51$l0$h1999999671',
        's_sq': 'ttiproduction%3D%2526c.%2526a.%2526activitymap.%2526page%253Dhttps%25253A%25252F%25252Fwww.tti.com%25252Fcontent%25252Fttiinc%25252Fen%25252Fapps%25252Fpart-search.html%25253Fc%25253Dconnectors%2526link%253D2%2526region%253DpartSearchContainer%2526.activitymap%2526.a%2526.c%2526pid%253Dhttps%25253A%25252F%25252Fwww.tti.com%25252Fcontent%25252Fttiinc%25252Fen%25252Fapps%25252Fpart-search.html%25253Fc%25253Dconnectors%2526oid%253Dhttps%25253A%25252F%25252Fwww.tti.com%25252Fcontent%25252Fttiinc%25252Fen%25252Fapps%25252Fpart-search.html%25253Fc%25253Dconnectors%252526p%25253D2%2526ot%253DA',
    }

    headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Accept-Language': 'es-419,es;q=0.9,en;q=0.8',
        'Connection': 'keep-alive',
        'Referer': 'https://www.tti.com/content/ttiinc/en/apps/part-search.html?c=connectors',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'same-origin',
        'Sec-Fetch-User': '?1',
        'Upgrade-Insecure-Requests': '1',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36',
        'sec-ch-ua': '"Chromium";v="142", "Google Chrome";v="142", "Not_A Brand";v="99"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"macOS"',
        # 'Cookie': 'visid_incap_2587712=sfdELyWVRiaRRBBg1zdHwxjZOWkAAAAAQUIPAAAAAAAAM0Jo9vAGTBt/QNnpiC4q; cookieNecessary=true; cookiePerformance=true; cookiePersonalization=true; cookieMarketing=true; _pxvid=7d951445-d607-11f0-a0cc-0c8f57c49ced; nlbi_2587712=LmjCPSRiU1AawPhQL026UQAAAACYvlE5xaScI1bf3DKZKF0D; incap_ses_8224_2587712=Kl6aS4APV3tTnWPV6IQhcugiQ2kAAAAAuh7lAEZzX4FAD8jY9jQy3Q==; AMCVS_474027E253DB53E90A490D4E%40AdobeOrg=1; AMCV_474027E253DB53E90A490D4E%40AdobeOrg=1075005958%7CMCIDTS%7C20440%7CMCMID%7C77670064873010431491933567254647709142%7CMCAAMLH-1766612329%7C4%7CMCAAMB-1766612329%7CRKhpRz8krg2tLO6pguXWp5olkAcUniQYPHaMWWgdJ3xzPWQmdj0y%7CMCOPTOUT-1766014729s%7CNONE%7CMCAID%7CNONE%7CvVersion%7C4.4.1; partSearchObject=%7B%22c%22%3A%22connectors%22%7D; s_cc=true; pxcts=c73375e4-db90-11f0-abd1-6e8c6eee51d8; _pxhd=G-QeIBy-1zwI2GLPXr-Bj4B6xLE6SVP4MkMU5THhcIFSTnSkF9mTl1WjuM5ZkW7o5-MYUDnwOG-/yXE9aw2dug==:N5dyzIGQccUOff2XF4lRyUssxmK1VKmMmu-3A2hsZxgUe7iDAppxIk6Gx40oQiZ1Lk2UmE8alJNlnbBdxlJFVVL0U70ZwsMre7lR1luPWWo=; _gcl_au=1.1.1952447325.1766007531; _ga=GA1.1.747242929.1766007531; _clck=3k7ujb%5E2%5Eg1x%5E0%5E2171; _uetsid=c76f72c0db9011f0af7031094069895c; _uetvid=30dc9760d69811f08bf59b7550261e73; _clsk=10tdtxb%5E1766007617091%5E2%5E1%5Ee.clarity.ms%2Fcollect; _px3=034b3bbe47e003d12ac3de2b7f4dc622c57143a5000011543b25862e670983d1:P7MJJQubi04aG+cfrvARplnPoemUfR3yTgURTAg3/WOwUtbT38bUYHz/xtJrwO7S+TSOko/NN94HLVLxlICN4A==:1000:hF0czrh+BhiksXH2BTJMrtBveJ9yesPYIPNPCFQJwivGTqp9xhvyoxNzYz+S8kUQy4eKY29MEw5y7eetgSHMroD0iAlRd0Jx2kElRLPH8LFjUCADYNPrkVqB3BJnCVcEeY7WFMGQvHZzbsoedjuVDzNqEbP5v9GMbLdZTdbQlGughQGXcn7IpZnn+6gN9W+FBQCWo/WHjFokLTgYIcTYlQUn2zIDN3Tua9lzkK5acY0bZrly9Mt4SEW8ic8VYWLe0hKX2iRYO0U8FHSmcunm1HGXfj3EaHKv0w3GDWnIUPnFETzrqNhvue0pZkXJNry/LBmH3U/tnTg8KHX2phgXcA5xhf816UoyFY+uaXKx5Y2hNaifJ/Yleafi93zhiqDj6kehXguNj1KrLLquzgjudg==; _ga_DZLYG7VYSV=GS2.1.s1766007531$o1$g1$t1766007625$j51$l0$h1999999671; s_sq=ttiproduction%3D%2526c.%2526a.%2526activitymap.%2526page%253Dhttps%25253A%25252F%25252Fwww.tti.com%25252Fcontent%25252Fttiinc%25252Fen%25252Fapps%25252Fpart-search.html%25253Fc%25253Dconnectors%2526link%253D2%2526region%253DpartSearchContainer%2526.activitymap%2526.a%2526.c%2526pid%253Dhttps%25253A%25252F%25252Fwww.tti.com%25252Fcontent%25252Fttiinc%25252Fen%25252Fapps%25252Fpart-search.html%25253Fc%25253Dconnectors%2526oid%253Dhttps%25253A%25252F%25252Fwww.tti.com%25252Fcontent%25252Fttiinc%25252Fen%25252Fapps%25252Fpart-search.html%25253Fc%25253Dconnectors%252526p%25253D2%2526ot%253DA',
    }

    params = {
        'c': 'connectors',
        'p': page,
    }

    response = requests.get(
        'https://www.tti.com/content/ttiinc/en/apps/part-search.html?c=connectors/audio-video-connectors',
        proxies=get_proxy_dc(),
        headers=headers,
        params=params
    )

    return response.text

# response.text.find('0472720001')
#%%

def get_discovery(page):
    try:
        print(page)
        html = get_info_by_page(page)
        pages = extract_part_links(html)
        return pages
    except Exception as e:
        print(page, e)


#%%
nums = list(range(1, 51))
nums

#%%
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed

with ThreadPoolExecutor(max_workers=25) as executor:
    new_parsed_result = list(
            executor.map(get_discovery, nums),
        )


#%%

new_parsed_result_ = []

for i in new_parsed_result:
    new_parsed_result_ += i

len(new_parsed_result_)
#%%

import requests

cookies = {
    'visid_incap_2587712': 'sfdELyWVRiaRRBBg1zdHwxjZOWkAAAAAQUIPAAAAAAAAM0Jo9vAGTBt/QNnpiC4q',
    'cookieNecessary': 'true',
    'cookiePerformance': 'true',
    'cookiePersonalization': 'true',
    'cookieMarketing': 'true',
    '_pxvid': '7d951445-d607-11f0-a0cc-0c8f57c49ced',
    'nlbi_2587712': 'LmjCPSRiU1AawPhQL026UQAAAACYvlE5xaScI1bf3DKZKF0D',
    'incap_ses_8224_2587712': 'Kl6aS4APV3tTnWPV6IQhcugiQ2kAAAAAuh7lAEZzX4FAD8jY9jQy3Q==',
    'AMCVS_474027E253DB53E90A490D4E%40AdobeOrg': '1',
    'AMCV_474027E253DB53E90A490D4E%40AdobeOrg': '1075005958%7CMCIDTS%7C20440%7CMCMID%7C77670064873010431491933567254647709142%7CMCAAMLH-1766612329%7C4%7CMCAAMB-1766612329%7CRKhpRz8krg2tLO6pguXWp5olkAcUniQYPHaMWWgdJ3xzPWQmdj0y%7CMCOPTOUT-1766014729s%7CNONE%7CMCAID%7CNONE%7CvVersion%7C4.4.1',
    's_cc': 'true',
    'pxcts': 'c73375e4-db90-11f0-abd1-6e8c6eee51d8',
    '_pxhd': 'G-QeIBy-1zwI2GLPXr-Bj4B6xLE6SVP4MkMU5THhcIFSTnSkF9mTl1WjuM5ZkW7o5-MYUDnwOG-/yXE9aw2dug==:N5dyzIGQccUOff2XF4lRyUssxmK1VKmMmu-3A2hsZxgUe7iDAppxIk6Gx40oQiZ1Lk2UmE8alJNlnbBdxlJFVVL0U70ZwsMre7lR1luPWWo=',
    '_gcl_au': '1.1.1952447325.1766007531',
    '_ga': 'GA1.1.747242929.1766007531',
    '_clck': '3k7ujb%5E2%5Eg1x%5E0%5E2171',
    'partSearchObject': '%7B%22c%22%3A%22connectors%22%2C%22p%22%3A%222%22%7D',
    '_uetsid': 'c76f72c0db9011f0af7031094069895c',
    '_uetvid': '30dc9760d69811f08bf59b7550261e73',
    '_clsk': '10tdtxb%5E1766007638508%5E3%5E1%5Ee.clarity.ms%2Fcollect',
    's_sq': 'ttiproduction%3D%2526c.%2526a.%2526activitymap.%2526page%253Dhttps%25253A%25252F%25252Fwww.tti.com%25252Fcontent%25252Fttiinc%25252Fen%25252Fapps%25252Fpart-search.html%25253Fc%25253Dconnectors%252526p%25253D2%2526link%253D0643201319%2526region%253Dparts-img%2526.activitymap%2526.a%2526.c%2526pid%253Dhttps%25253A%25252F%25252Fwww.tti.com%25252Fcontent%25252Fttiinc%25252Fen%25252Fapps%25252Fpart-search.html%25253Fc%25253Dconnectors%252526p%25253D2%2526oid%253Dhttps%25253A%25252F%25252Fwww.tti.com%25252Fcontent%25252Fttiinc%25252Fen%25252Fapps%25252Fpart-detail.html%25253FpartsNumber%25253D64320-1319%252526mfgShortname%25253DMOL%252526%2526ot%253DA',
    '_ga_DZLYG7VYSV': 'GS2.1.s1766007531$o1$g1$t1766007758$j60$l0$h1999999671',
    '_px3': '0eca5c0e2c0007fcc74e439a71d9cb349f6e6e5fac9bc6372f8aba801ec5f1c0:P6zULfp46Yz8qgxluJetw/ShvX0phNDn/MPX7CDHQOSW6cc1Opi17HbnuFqFFjCfZYEX5omMmvFrCyrTpFYWRQ==:1000:mgb12Zvsp2aM35eNtHu5oX81pYwYaW5KQdQRBafQlFDLPvX5RuKIBYJ9SxcWDpwW97k/w51JWIbI5wa0Xp27l9pF2dhSjN0N00q/cDHPXcdnPIU8rHJIt1eeJCNMZzbKMcwf51lYO5enFV5DPEwLdCoyaycW9RhCFg8JQpDXvFTFU4V9gnRJRh04xes+Yrh0thoDJHEtDKSoMifzAYXJWVBw1X30Nn9r6hGMxznb6TAdtIvzl4BKcPcVbmMbxA4DMTkZxU6Dw1Owy4hft/pNGEivQSLbgbLVXIDNNXNWsUakLJvlSjQ4ZZldkphWWpasD1n7FRpDy3LI9id/32idG0K1KWIFvf6WTe/OZdI06TONJRkjKt24QIKVZL+ADqo+VNeSS4gJqT0ZNEyKd/DAwuY/nTSvRNJjZitgcKkQfxMm/vF4rkwNq4Tv+OheuVsM',
}

headers = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'Accept-Language': 'es-419,es;q=0.9,en;q=0.8',
    'Cache-Control': 'max-age=0',
    'Connection': 'keep-alive',
    'Referer': 'https://www.tti.com/content/ttiinc/en/apps/part-detail.html?partsNumber=64320-1319&mfgShortname=MOL&productId=244690712',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'same-origin',
    'Upgrade-Insecure-Requests': '1',
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36',
    'sec-ch-ua': '"Chromium";v="142", "Google Chrome";v="142", "Not_A Brand";v="99"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"macOS"',
    # 'Cookie': 'visid_incap_2587712=sfdELyWVRiaRRBBg1zdHwxjZOWkAAAAAQUIPAAAAAAAAM0Jo9vAGTBt/QNnpiC4q; cookieNecessary=true; cookiePerformance=true; cookiePersonalization=true; cookieMarketing=true; _pxvid=7d951445-d607-11f0-a0cc-0c8f57c49ced; nlbi_2587712=LmjCPSRiU1AawPhQL026UQAAAACYvlE5xaScI1bf3DKZKF0D; incap_ses_8224_2587712=Kl6aS4APV3tTnWPV6IQhcugiQ2kAAAAAuh7lAEZzX4FAD8jY9jQy3Q==; AMCVS_474027E253DB53E90A490D4E%40AdobeOrg=1; AMCV_474027E253DB53E90A490D4E%40AdobeOrg=1075005958%7CMCIDTS%7C20440%7CMCMID%7C77670064873010431491933567254647709142%7CMCAAMLH-1766612329%7C4%7CMCAAMB-1766612329%7CRKhpRz8krg2tLO6pguXWp5olkAcUniQYPHaMWWgdJ3xzPWQmdj0y%7CMCOPTOUT-1766014729s%7CNONE%7CMCAID%7CNONE%7CvVersion%7C4.4.1; s_cc=true; pxcts=c73375e4-db90-11f0-abd1-6e8c6eee51d8; _pxhd=G-QeIBy-1zwI2GLPXr-Bj4B6xLE6SVP4MkMU5THhcIFSTnSkF9mTl1WjuM5ZkW7o5-MYUDnwOG-/yXE9aw2dug==:N5dyzIGQccUOff2XF4lRyUssxmK1VKmMmu-3A2hsZxgUe7iDAppxIk6Gx40oQiZ1Lk2UmE8alJNlnbBdxlJFVVL0U70ZwsMre7lR1luPWWo=; _gcl_au=1.1.1952447325.1766007531; _ga=GA1.1.747242929.1766007531; _clck=3k7ujb%5E2%5Eg1x%5E0%5E2171; partSearchObject=%7B%22c%22%3A%22connectors%22%2C%22p%22%3A%222%22%7D; _uetsid=c76f72c0db9011f0af7031094069895c; _uetvid=30dc9760d69811f08bf59b7550261e73; _clsk=10tdtxb%5E1766007638508%5E3%5E1%5Ee.clarity.ms%2Fcollect; s_sq=ttiproduction%3D%2526c.%2526a.%2526activitymap.%2526page%253Dhttps%25253A%25252F%25252Fwww.tti.com%25252Fcontent%25252Fttiinc%25252Fen%25252Fapps%25252Fpart-search.html%25253Fc%25253Dconnectors%252526p%25253D2%2526link%253D0643201319%2526region%253Dparts-img%2526.activitymap%2526.a%2526.c%2526pid%253Dhttps%25253A%25252F%25252Fwww.tti.com%25252Fcontent%25252Fttiinc%25252Fen%25252Fapps%25252Fpart-search.html%25253Fc%25253Dconnectors%252526p%25253D2%2526oid%253Dhttps%25253A%25252F%25252Fwww.tti.com%25252Fcontent%25252Fttiinc%25252Fen%25252Fapps%25252Fpart-detail.html%25253FpartsNumber%25253D64320-1319%252526mfgShortname%25253DMOL%252526%2526ot%253DA; _ga_DZLYG7VYSV=GS2.1.s1766007531$o1$g1$t1766007758$j60$l0$h1999999671; _px3=0eca5c0e2c0007fcc74e439a71d9cb349f6e6e5fac9bc6372f8aba801ec5f1c0:P6zULfp46Yz8qgxluJetw/ShvX0phNDn/MPX7CDHQOSW6cc1Opi17HbnuFqFFjCfZYEX5omMmvFrCyrTpFYWRQ==:1000:mgb12Zvsp2aM35eNtHu5oX81pYwYaW5KQdQRBafQlFDLPvX5RuKIBYJ9SxcWDpwW97k/w51JWIbI5wa0Xp27l9pF2dhSjN0N00q/cDHPXcdnPIU8rHJIt1eeJCNMZzbKMcwf51lYO5enFV5DPEwLdCoyaycW9RhCFg8JQpDXvFTFU4V9gnRJRh04xes+Yrh0thoDJHEtDKSoMifzAYXJWVBw1X30Nn9r6hGMxznb6TAdtIvzl4BKcPcVbmMbxA4DMTkZxU6Dw1Owy4hft/pNGEivQSLbgbLVXIDNNXNWsUakLJvlSjQ4ZZldkphWWpasD1n7FRpDy3LI9id/32idG0K1KWIFvf6WTe/OZdI06TONJRkjKt24QIKVZL+ADqo+VNeSS4gJqT0ZNEyKd/DAwuY/nTSvRNJjZitgcKkQfxMm/vF4rkwNq4Tv+OheuVsM',
}

def get_part_description(html: str):
    soup = BeautifulSoup(html, "html.parser")

    el = soup.select_one("div.c-part-detail__header-description")
    if not el:
        return None

    return el.get_text(strip=True)

from retry import retry
@retry(tries=3, delay=1)
def get_pdp_info(url_info):
    url = url_info['absolute_url']

    # params = {
    #     'partsNumber': '64320-1319',
    #     'mfgShortname': 'MOL',
    #     'productId': '244690712',
    # }

    response = requests.get(
        url,
        # 'https://www.tti.com/content/ttiinc/en/apps/part-detail.html',
        # params=params,
        proxies=get_proxy_dc(),
        headers=headers,
    )
    print(response)
    if response.status_code != 200:
        raise RuntimeError(
            f"Request failed with status {response.status_code}: {response.text[:200]}"
        )

    return response.text

#%%


def get_pdp_info_parsed(url_info):
    try:
        print(url_info['absolute_url'])
        html = get_pdp_info(url_info)
        get_part_desc_ = get_part_description(html)
        return get_part_desc_
    except Exception as e:
        print(e)#url_info['absolute_url'])


# %%


from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed

with ThreadPoolExecutor(max_workers=25) as executor:
    new_parsed_result_pdp = list(
            executor.map(get_pdp_info_parsed, new_parsed_result_),
        )
new_parsed_result_pdp

#%%

new_parsed_result_pdp_cleaned = []
for i in new_parsed_result_pdp:
    if i:
        new_parsed_result_pdp_cleaned.append(i)
# %%
len(new_parsed_result_pdp_cleaned)/len(new_parsed_result_pdp)
# %%
