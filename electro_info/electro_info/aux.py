#%%
import random

def get_proxy_dc_pw():

    ip_num = random.random()

    # username = 'brd-customer-hl_14d32bce-zone-datacenter_proxy1'
    # password = 'ymg5cg3a1z33'

    username = 'brd-customer-hl_44df54b0-zone-datacenter_proxy1'
    password = 'hjzi3a2a4k1m'

    proxies ={
            "server": "brd.superproxy.io:22225",
            "username": f"{username}-session-"+str(ip_num),
            "password": password
            }
    return proxies

def get_proxy_res_pw():

    ip_num = random.random()

    # username = 'brd-customer-hl_14d32bce-zone-datacenter_proxy1'
    # password = 'ymg5cg3a1z33'

    username = 'brd-customer-hl_14d32bce-zone-residential_proxy1'
    password = 'd0fh393blkuv'

    proxies ={
            "server": "brd.superproxy.io:22225",
            "username": f"{username}-session-"+str(ip_num),
            "password": password
            }
    return proxies


def get_proxy_dc(country=None)-> dict:
    """
    It returns a dictionary with the keys 'http' and 'https' and the values are the proxy address to use the datacenter proxy
    :return: A dictionary with the keys 'http' and 'https' and the values are the entry variable.
    """

    if country:
        username = f'brd-customer-hl_14d32bce-zone-datacenter_proxy1-country-{country}'

    else:
        username = 'brd-customer-hl_14d32bce-zone-datacenter_proxy1'
    
    password = 'ymg5cg3a1z33'

        
    # username = 'brd-customer-hl_435d7aea-zone-residential-country-co'
    # password = '3be0a9mtx4y5'

    port = 22225
    session_id = random.random()
    super_proxy_url = ('http://%s-session-%s:%s@zproxy.lum-superproxy.io:%d' %
        (username, session_id, password, port))
    proxy_handler = {
        'http': super_proxy_url,
        'https': super_proxy_url,
    } 
    return proxy_handler


def get_proxy_unbloker()-> dict:
    """
    It returns a dictionary with the keys 'http' and 'https' and the values are the proxy address to use the datacenter proxy
    :return: A dictionary with the keys 'http' and 'https' and the values are the entry variable.
    """




    username = 'brd-customer-hl_14d32bce-zone-unblocker1-country-us'
    password = 'glfj6x2x3tcr'

    # username = 'brd-customer-hl_435d7aea-zone-residential-country-co'
    # password = '3be0a9mtx4y5'

    port = 22225
    session_id = random.random()
    super_proxy_url = ('http://%s-session-%s:%s@zproxy.lum-superproxy.io:%d' %
        (username, session_id, password, port))
    proxy_handler = {
        'http': super_proxy_url,
        'https': super_proxy_url,
    } 
    return proxy_handler

def get_proxy_res()-> dict:
    """
    It returns a dictionary with the keys 'http' and 'https' and the values are the proxy address to use the datacenter proxy
    :return: A dictionary with the keys 'http' and 'https' and the values are the entry variable.
    """

    username = 'brd-customer-hl_14d32bce-zone-residential_proxy1-country-us'
    password = 'd0fh393blkuv'

    # username = 'brd-customer-hl_435d7aea-zone-residential-country-co'
    # password = '3be0a9mtx4y5'

    port = 22225
    session_id = random.random()
    super_proxy_url = ('http://%s-session-%s:%s@zproxy.lum-superproxy.io:%d' %
        (username, session_id, password, port))
    proxy_handler = {
        'http': super_proxy_url,
        'https': super_proxy_url,
    } 
    return proxy_handler
# %%
