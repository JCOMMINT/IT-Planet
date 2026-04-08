#%%


import requests

cookies = {
    'shell#lang': 'en',
    'ASP.NET_SessionId': '4i0lofdoraq12ikvixxfpjnh',
    'arrowcurrency': 'isocode=USD&culture=en-US',
    'website#lang': 'en',
    'AKA_A2': 'A',
    'bm_ss': 'ab8e18ef4e',
    'RedirectFromLogin': '0',
    'sa-user-id': 's%253A0-c6666d79-0ed3-516c-747c-59e5af994c80.3%252B%252BfyUgoam4oac6m%252B5Er3GYZwNCClm9O1e%252FtMnN7xiI',
    'sa-user-id-v2': 's%253AxmZteQ7TUWx0fFnlr5lMgMh3OMc.qlfXN1wSgqyrvREfcm9RCMOs5DZaswvNUJWbPSBNsYU',
    'sa-user-id-v3': 's%253AAQAKIOOFHzJGRErkMLxpaJr6aoQyirbufkZUf0ia052okM-xEAMYAyCs-YfBBjABOgRvCwCpQgQ2gEkZ.7ma9dn7RLV9t3wWi%252FVfz1xWXiZbpRY39qBHypPXl%252Bd0',
    '_fwb': '181dyhElRbMGA5ADTPVo21V.1766006832397',
    'kndctr_90241DD164F13A460A495C3A_AdobeOrg_cluster': 'va6',
    'kndctr_90241DD164F13A460A495C3A_AdobeOrg_identity': 'CiY3NzY1MDk2NDk5MTczNjM5NTYwMTkzNjQ1OTkzMTE2NzE1NzEzOVIQCOv71vGyMxgBKgNWQTYwAfAB6_vW8bIz',
    'AMCV_90241DD164F13A460A495C3A%40AdobeOrg': 'MCMID|77650964991736395601936459931167157139',
    '_gcl_au': '1.1.1814002692.1766006833',
    'bm_mi': '4DCA0326F0C11B68B040D8FB7D105130~YAAQXdMTAorhwiibAQAAVb41Lh6J2KYQaaCy1u6vV6eLMEY1zhZzWL0ObLCB1dAhAZi5APn2Y4OF2hRkuT1qvcuS+ij9bL0s7pPlTzYcA0DGLeVBXW5vawlWRfMEdKzbT7BRKgbx35NDTk+/CML/AVmsLAtY9VpokQjjm4B3adLDvxoZZdmLECVCM8N1PFQDQXiOec1YBYsWbqJFusp2X+7OzD5A3dvKYGkO+eHMDjsPCp2qJE84Ckgs1Hg2Zgehl9FdqMJE4SKrWO6DLFOYMcpN/3phunLrswXjcnRdRPCdcDX8VCiPAlNkALgCPHF+j7zEX9Ep96Jd21WeI0xe6IyrsOOtLvQ=~1',
    'ak_bmsc': '47AE84A58CCD2B1D008EE28AD6094989~000000000000000000000000000000~YAAQXdMTApLhwiibAQAAX781Lh4usqr9aj3cmlgo5MUanzkDAk4xBP2GtKg0XIb6HP3kGSKREVpO4pc+DNkAudet0ynGzaRrb/QzrW8Nm7G3mfLncDWrRW+1hFUf60h187R3VB/SnJI+tHzIms0DpHFDW/xJxbQgSknhHjhPv9dKHjWnOtssxzkzSWFX0/RZ7zZq3VIGDblPISDacYeSSlvVkYk3aY9bMn5ssvJpLThCosZRw1WAhyXX8qfmDBPxqIvX1bwSAOk2IL1N1weBocpIxlCKbolrQGxUn7xbFCK9tQapUdMM60RMidZ6ku4q2nO0i3S9mAGhhQnlz7YAoG3pAQ2zs+pgiIB4hSDUoQzUQEGpMHgKuXgLXudqnjbqZWmJLQjVOO9G3744we/T7j/xV85hGoiWTbrVOHOyryz4+go2faI/pUU+kf3ICq3vBmg6kxkbv/rv',
    '_fbp': 'fb.1.1766006833255.450416808219104123',
    '_ga': 'GA1.1.1100176473.1766006834',
    '_clck': '1esqu4a%5E2%5Eg1x%5E0%5E2177',
    'IsNewUser': 'False',
    'arrowcache': 'a=EMPTY&cu=en-US&is=USD&ne=False',
    '_abck': '550C92C716698B04DBB5B413D96509D3~0~YAAQXdMTAuThwiibAQAAgOg1Lg+JJYc3yddKPgrQaVR4YHhBM62n+GmbJlDL6JNSxPyE7bR9Bgk+s+9lIctTgMC6IH8ZT1rfSSZva+hA7RO5iAXikB+yumSyZ11eIy4L9N8BiGreT2iXj7pgU27X6hWO3AfFYoD21CbuApjCIbsU3r3c5P6l8LdMLVLvIXHQLym6+HsFexR++EV3FtRmIIkYmPFcv3LeKMXHsThGLjqjuytBFysJFkd8qSwnagJkTYtwtsCwFnN0FxQ3VsY7QWH4HAQBrJ/iDZEhc7als4xf+/N3RB1BpeTa4cXT2HsbfWQt1E/ulGumagw/R6ZdjREgyVzs5FYf0dadtBmwI3WUdRHo4U9wDVv4LTqrFfTD26JJNvSFupy2Dy0fXSr8Dd8d02LGnScO6kGtQ6A4WNjQObpHMgaN3Q+PFnoutLtS/X53gPE1nkmiJsq30VebzX8sAbrI+lfTSqh9MVSGMtIFPkD9DXjQ8IlYYamnluymMtFwk5EWmyNgT/FTSIKS/7NoDgtxsFv2Zjw8yxxii0bs2Eb6GSi5xv8SoBgxsb7pmFF/gfC2Xnu5xLXRfgPRPcYCQmH9UK1scotiA56J8/0/EFw0x3SmDF0pRhrp2Qid5CCL3b8UcQ==~-1~-1~-1~AAQAAAAE%2f%2f%2f%2f%2f3vvyPl4GVyPCWsOOWgT4a5A5bkU0IcJIkBovFZAUpVpnEThAXZy3uH33FNs3jXr48LxlHqqBdPeYqVvmoBxdWLPfLlBEXP0LYGU~-1',
    'bm_so': '19185CC954ED0D7D98B269DEAA7CD0F073F5A9AB0FFC337FA05CE7689D9BA6F5~YAAQXdMTAgXiwiibAQAAQSk2LgbZdJ2h59ZR9Qg5p8Av0LNNDj4S8CiF3ERGrmaASUsV4cSY5vEA5V6ptLi9IUOmo0a4ReB1a7ChrdF6azkQwHdD283ZT4OfVOUTu2C1mlv61vo0Ze6Icf7Hppk9elkGoVA+PR1HAJ9rXPAMh+E984RRrYp4Dtr3xnOwPy+CfEO3RbZbbe66aK96wWcUW5Zpq4mZ82xiMDTdXwFM3DEBFd7BJGA3JMvs/EvrJhR0Bl9nH5OlzaKBrmF5F5nIx33/feyaNhYFNzbwbIONJ3H2V5sxp78ywkIBhcUWec6xMQmjmY3A3M83F+efQ0jeuTuYVlldr6W2VQ+lcJJuXuUp2BZ7g/i+YYGiLms12WL8fAX3sDAn6KfQVtKXR24x9LB8SinaOuqmaZWXY9q4QUdF2rSdhWHVC2duHl2yk2yaMh4VWdbepw9NB8LOn5w=',
    'wcs_bt': 's_116daf35dfcd:1766006863',
    '_br_uid_2': 'uid%3D4030322615220%3Av%3D13.0%3Ats%3D1766006832006%3Ahc%3D5',
    '_rdt_uuid': '1766006832777.ca729a6b-1c53-4467-83de-6e04e067becc',
    '_clsk': 'whz0rg%5E1766006865283%5E6%5E0%5Ee.clarity.ms%2Fcollect',
    'bm_lso': '19185CC954ED0D7D98B269DEAA7CD0F073F5A9AB0FFC337FA05CE7689D9BA6F5~YAAQXdMTAgXiwiibAQAAQSk2LgbZdJ2h59ZR9Qg5p8Av0LNNDj4S8CiF3ERGrmaASUsV4cSY5vEA5V6ptLi9IUOmo0a4ReB1a7ChrdF6azkQwHdD283ZT4OfVOUTu2C1mlv61vo0Ze6Icf7Hppk9elkGoVA+PR1HAJ9rXPAMh+E984RRrYp4Dtr3xnOwPy+CfEO3RbZbbe66aK96wWcUW5Zpq4mZ82xiMDTdXwFM3DEBFd7BJGA3JMvs/EvrJhR0Bl9nH5OlzaKBrmF5F5nIx33/feyaNhYFNzbwbIONJ3H2V5sxp78ywkIBhcUWec6xMQmjmY3A3M83F+efQ0jeuTuYVlldr6W2VQ+lcJJuXuUp2BZ7g/i+YYGiLms12WL8fAX3sDAn6KfQVtKXR24x9LB8SinaOuqmaZWXY9q4QUdF2rSdhWHVC2duHl2yk2yaMh4VWdbepw9NB8LOn5w=~1766006865985',
    '_rdt_pn': ':200~d2850825181bc93623197aba93979ab1419c538321d7e9578a058f5c27d47fdf|200~1125bc07b735488d98a3849fc001c01e4fb0df600c049a3aa82ae120d479956e|175~e55173dea29ed4448a98ea45a924afe1102448e8d7232154eeee35f3505f19d5|175~0a54640b48c0c35547f5fbc6805d4b8bc1d2d36002c79a632dce5cfaf6031125|150~08783e581fc0ede1d29c82453e314d9d2473e063c264ae69fea6e6291242bce0',
    'bm_s': 'YAAQXdMTAjziwiibAQAA9lY2LgTBXC2Lie+OINspOpMSCgzUT6jUHGAiPTqG2nRzIEEmBYGUxVDb71KzU50RnS++pe0wFVTfmOK7Qd1Ej6jdxHrpAcwzZ4bdPSkNQKw4WNyfjnKyZNQ8FYUURgJUnJKmxnAH/LmRZxIRGS8erVnXXmZjFZKk+iScGySJZwl4NG766Wc3L+Kz+O1JvW9tRfoxiLU3Y0cbPDuOiidbyqTS5xW65XL6Cft2P6kH9prte1iPQ8tAZfHafzW1Y9Xspd1rebv4NF3B0Ytd6UuTaFanHLhQaQmfdxGyuiwo4xoTgTd3oJf+EG5lwMHeQoD/Vt6c4FU8QaHevyf50dVTBecrAZSktG+x9E8+8jxCRg6ovL9x/JXKTZnxS1NrML0bG5v0KPA3Qy06vE4pjW/iNu/vSwuWGrGmzt+2hoczEkl7WuYqytLS4G8US+lWfezs/qDQxoAje0YnttS+vcXo2V1pqK0CioAhf96uMfd3QBiKK1OmqsK27WXpBbhz7M04FzNem7D4bHo08AwmFQrdWPHOXskEI9aKCL5yjj6AxuiWZMESKQ==',
    'bm_sz': 'A506ED4F933A6FED097E50C57E4370C3~YAAQXdMTAj7iwiibAQAA9lY2Lh510ww4AkYyiTvP3kW8ce22umTYtOrVx/0q2gRjiLyLhbdPGQkhfLUZeiNct+bhGoOLSXOKy38EA6h+yM1r4oxlMBRaY5J9pgQkmVijoBq/6yKxejpQtvsiyTzR0sMG3d7pzowFTtk0hsUDB2opVkKgoqstoie/bLS6ivE+q0mlLKirn8xb06iAQNbs7mcopr56lYnNTu7j1alwsKLCEMS/r+QE75tG0hqooC50jGzjOvug/JiHhe4djuFJXV83r5oL/m9aVhIbCf32OLfjdaA8UifY+NLQon8BUY2dWUv+X4+J/yelv22HkqXV0sbS1xR/xrxOqzmRwNOa4+1cS84AQgpbpf/HmwFMclMEGiYBo7qlfAnAzn+YeRwi+7on18F76/t70aR5RJrQhBObaJiWCEDAAQ==~4469045~3227953',
    '_ga_0K4ZF41NME': 'GS2.1.s1766006833$o1$g1$t1766006871$j22$l0$h0',
    'RT': '"z=1&dm=arrow.com&si=fb924e2a-327f-4493-b210-a4e0835cf3d1&ss=mjaivbby&sl=5&tt=ecv&bcn=%2F%2F17de4c1d.akstat.io%2F&obo=1"',
    'bm_sv': 'AB509B809B9916C0CA060DCB3E01E198~YAAQXdMTAkPiwiibAQAACVo2Lh6pQ+yi8284IQnnPvn26iwCzzKV+sN7oyAh/zHCoDTvbm1Y0BxZ3EI1XOgHBFGBhlvO3RuMzLUZm2rTd92sJGWuuip5VqswTnVCVV5opOeCHfs3Fm4OTRZCroBC3pbrHD4b+CwLb/YesR2M5b+kWHwphzc09+GxBhvtFY59ZcdEHkHjbfOVL1LzUv3YPcwLLRUfNc6cJKkvKxdtJuxrYr5SkdS5Y6N/hGEnFg3H~1',
}

headers = {
    'accept': 'application/json, text/plain, */*',
    'accept-language': 'es-419,es;q=0.9,en;q=0.8',
    'content-type': 'application/json',
    'origin': 'https://www.arrow.com',
    'priority': 'u=1, i',
    'referer': 'https://www.arrow.com/en/categories/connectors-accessories/backshells',
    'sec-ch-ua': '"Chromium";v="142", "Google Chrome";v="142", "Not_A Brand";v="99"',
    'sec-ch-ua-arch': '"arm"',
    'sec-ch-ua-bitness': '"64"',
    'sec-ch-ua-full-version-list': '"Chromium";v="142.0.7444.177", "Google Chrome";v="142.0.7444.177", "Not_A Brand";v="99.0.0.0"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-model': '""',
    'sec-ch-ua-platform': '"macOS"',
    'sec-ch-ua-platform-version': '"15.6.1"',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-origin',
    'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36',
    # 'cookie': 'shell#lang=en; ASP.NET_SessionId=4i0lofdoraq12ikvixxfpjnh; arrowcurrency=isocode=USD&culture=en-US; website#lang=en; AKA_A2=A; bm_ss=ab8e18ef4e; RedirectFromLogin=0; sa-user-id=s%253A0-c6666d79-0ed3-516c-747c-59e5af994c80.3%252B%252BfyUgoam4oac6m%252B5Er3GYZwNCClm9O1e%252FtMnN7xiI; sa-user-id-v2=s%253AxmZteQ7TUWx0fFnlr5lMgMh3OMc.qlfXN1wSgqyrvREfcm9RCMOs5DZaswvNUJWbPSBNsYU; sa-user-id-v3=s%253AAQAKIOOFHzJGRErkMLxpaJr6aoQyirbufkZUf0ia052okM-xEAMYAyCs-YfBBjABOgRvCwCpQgQ2gEkZ.7ma9dn7RLV9t3wWi%252FVfz1xWXiZbpRY39qBHypPXl%252Bd0; _fwb=181dyhElRbMGA5ADTPVo21V.1766006832397; kndctr_90241DD164F13A460A495C3A_AdobeOrg_cluster=va6; kndctr_90241DD164F13A460A495C3A_AdobeOrg_identity=CiY3NzY1MDk2NDk5MTczNjM5NTYwMTkzNjQ1OTkzMTE2NzE1NzEzOVIQCOv71vGyMxgBKgNWQTYwAfAB6_vW8bIz; AMCV_90241DD164F13A460A495C3A%40AdobeOrg=MCMID|77650964991736395601936459931167157139; _gcl_au=1.1.1814002692.1766006833; bm_mi=4DCA0326F0C11B68B040D8FB7D105130~YAAQXdMTAorhwiibAQAAVb41Lh6J2KYQaaCy1u6vV6eLMEY1zhZzWL0ObLCB1dAhAZi5APn2Y4OF2hRkuT1qvcuS+ij9bL0s7pPlTzYcA0DGLeVBXW5vawlWRfMEdKzbT7BRKgbx35NDTk+/CML/AVmsLAtY9VpokQjjm4B3adLDvxoZZdmLECVCM8N1PFQDQXiOec1YBYsWbqJFusp2X+7OzD5A3dvKYGkO+eHMDjsPCp2qJE84Ckgs1Hg2Zgehl9FdqMJE4SKrWO6DLFOYMcpN/3phunLrswXjcnRdRPCdcDX8VCiPAlNkALgCPHF+j7zEX9Ep96Jd21WeI0xe6IyrsOOtLvQ=~1; ak_bmsc=47AE84A58CCD2B1D008EE28AD6094989~000000000000000000000000000000~YAAQXdMTApLhwiibAQAAX781Lh4usqr9aj3cmlgo5MUanzkDAk4xBP2GtKg0XIb6HP3kGSKREVpO4pc+DNkAudet0ynGzaRrb/QzrW8Nm7G3mfLncDWrRW+1hFUf60h187R3VB/SnJI+tHzIms0DpHFDW/xJxbQgSknhHjhPv9dKHjWnOtssxzkzSWFX0/RZ7zZq3VIGDblPISDacYeSSlvVkYk3aY9bMn5ssvJpLThCosZRw1WAhyXX8qfmDBPxqIvX1bwSAOk2IL1N1weBocpIxlCKbolrQGxUn7xbFCK9tQapUdMM60RMidZ6ku4q2nO0i3S9mAGhhQnlz7YAoG3pAQ2zs+pgiIB4hSDUoQzUQEGpMHgKuXgLXudqnjbqZWmJLQjVOO9G3744we/T7j/xV85hGoiWTbrVOHOyryz4+go2faI/pUU+kf3ICq3vBmg6kxkbv/rv; _fbp=fb.1.1766006833255.450416808219104123; _ga=GA1.1.1100176473.1766006834; _clck=1esqu4a%5E2%5Eg1x%5E0%5E2177; IsNewUser=False; arrowcache=a=EMPTY&cu=en-US&is=USD&ne=False; _abck=550C92C716698B04DBB5B413D96509D3~0~YAAQXdMTAuThwiibAQAAgOg1Lg+JJYc3yddKPgrQaVR4YHhBM62n+GmbJlDL6JNSxPyE7bR9Bgk+s+9lIctTgMC6IH8ZT1rfSSZva+hA7RO5iAXikB+yumSyZ11eIy4L9N8BiGreT2iXj7pgU27X6hWO3AfFYoD21CbuApjCIbsU3r3c5P6l8LdMLVLvIXHQLym6+HsFexR++EV3FtRmIIkYmPFcv3LeKMXHsThGLjqjuytBFysJFkd8qSwnagJkTYtwtsCwFnN0FxQ3VsY7QWH4HAQBrJ/iDZEhc7als4xf+/N3RB1BpeTa4cXT2HsbfWQt1E/ulGumagw/R6ZdjREgyVzs5FYf0dadtBmwI3WUdRHo4U9wDVv4LTqrFfTD26JJNvSFupy2Dy0fXSr8Dd8d02LGnScO6kGtQ6A4WNjQObpHMgaN3Q+PFnoutLtS/X53gPE1nkmiJsq30VebzX8sAbrI+lfTSqh9MVSGMtIFPkD9DXjQ8IlYYamnluymMtFwk5EWmyNgT/FTSIKS/7NoDgtxsFv2Zjw8yxxii0bs2Eb6GSi5xv8SoBgxsb7pmFF/gfC2Xnu5xLXRfgPRPcYCQmH9UK1scotiA56J8/0/EFw0x3SmDF0pRhrp2Qid5CCL3b8UcQ==~-1~-1~-1~AAQAAAAE%2f%2f%2f%2f%2f3vvyPl4GVyPCWsOOWgT4a5A5bkU0IcJIkBovFZAUpVpnEThAXZy3uH33FNs3jXr48LxlHqqBdPeYqVvmoBxdWLPfLlBEXP0LYGU~-1; bm_so=19185CC954ED0D7D98B269DEAA7CD0F073F5A9AB0FFC337FA05CE7689D9BA6F5~YAAQXdMTAgXiwiibAQAAQSk2LgbZdJ2h59ZR9Qg5p8Av0LNNDj4S8CiF3ERGrmaASUsV4cSY5vEA5V6ptLi9IUOmo0a4ReB1a7ChrdF6azkQwHdD283ZT4OfVOUTu2C1mlv61vo0Ze6Icf7Hppk9elkGoVA+PR1HAJ9rXPAMh+E984RRrYp4Dtr3xnOwPy+CfEO3RbZbbe66aK96wWcUW5Zpq4mZ82xiMDTdXwFM3DEBFd7BJGA3JMvs/EvrJhR0Bl9nH5OlzaKBrmF5F5nIx33/feyaNhYFNzbwbIONJ3H2V5sxp78ywkIBhcUWec6xMQmjmY3A3M83F+efQ0jeuTuYVlldr6W2VQ+lcJJuXuUp2BZ7g/i+YYGiLms12WL8fAX3sDAn6KfQVtKXR24x9LB8SinaOuqmaZWXY9q4QUdF2rSdhWHVC2duHl2yk2yaMh4VWdbepw9NB8LOn5w=; wcs_bt=s_116daf35dfcd:1766006863; _br_uid_2=uid%3D4030322615220%3Av%3D13.0%3Ats%3D1766006832006%3Ahc%3D5; _rdt_uuid=1766006832777.ca729a6b-1c53-4467-83de-6e04e067becc; _clsk=whz0rg%5E1766006865283%5E6%5E0%5Ee.clarity.ms%2Fcollect; bm_lso=19185CC954ED0D7D98B269DEAA7CD0F073F5A9AB0FFC337FA05CE7689D9BA6F5~YAAQXdMTAgXiwiibAQAAQSk2LgbZdJ2h59ZR9Qg5p8Av0LNNDj4S8CiF3ERGrmaASUsV4cSY5vEA5V6ptLi9IUOmo0a4ReB1a7ChrdF6azkQwHdD283ZT4OfVOUTu2C1mlv61vo0Ze6Icf7Hppk9elkGoVA+PR1HAJ9rXPAMh+E984RRrYp4Dtr3xnOwPy+CfEO3RbZbbe66aK96wWcUW5Zpq4mZ82xiMDTdXwFM3DEBFd7BJGA3JMvs/EvrJhR0Bl9nH5OlzaKBrmF5F5nIx33/feyaNhYFNzbwbIONJ3H2V5sxp78ywkIBhcUWec6xMQmjmY3A3M83F+efQ0jeuTuYVlldr6W2VQ+lcJJuXuUp2BZ7g/i+YYGiLms12WL8fAX3sDAn6KfQVtKXR24x9LB8SinaOuqmaZWXY9q4QUdF2rSdhWHVC2duHl2yk2yaMh4VWdbepw9NB8LOn5w=~1766006865985; _rdt_pn=:200~d2850825181bc93623197aba93979ab1419c538321d7e9578a058f5c27d47fdf|200~1125bc07b735488d98a3849fc001c01e4fb0df600c049a3aa82ae120d479956e|175~e55173dea29ed4448a98ea45a924afe1102448e8d7232154eeee35f3505f19d5|175~0a54640b48c0c35547f5fbc6805d4b8bc1d2d36002c79a632dce5cfaf6031125|150~08783e581fc0ede1d29c82453e314d9d2473e063c264ae69fea6e6291242bce0; bm_s=YAAQXdMTAjziwiibAQAA9lY2LgTBXC2Lie+OINspOpMSCgzUT6jUHGAiPTqG2nRzIEEmBYGUxVDb71KzU50RnS++pe0wFVTfmOK7Qd1Ej6jdxHrpAcwzZ4bdPSkNQKw4WNyfjnKyZNQ8FYUURgJUnJKmxnAH/LmRZxIRGS8erVnXXmZjFZKk+iScGySJZwl4NG766Wc3L+Kz+O1JvW9tRfoxiLU3Y0cbPDuOiidbyqTS5xW65XL6Cft2P6kH9prte1iPQ8tAZfHafzW1Y9Xspd1rebv4NF3B0Ytd6UuTaFanHLhQaQmfdxGyuiwo4xoTgTd3oJf+EG5lwMHeQoD/Vt6c4FU8QaHevyf50dVTBecrAZSktG+x9E8+8jxCRg6ovL9x/JXKTZnxS1NrML0bG5v0KPA3Qy06vE4pjW/iNu/vSwuWGrGmzt+2hoczEkl7WuYqytLS4G8US+lWfezs/qDQxoAje0YnttS+vcXo2V1pqK0CioAhf96uMfd3QBiKK1OmqsK27WXpBbhz7M04FzNem7D4bHo08AwmFQrdWPHOXskEI9aKCL5yjj6AxuiWZMESKQ==; bm_sz=A506ED4F933A6FED097E50C57E4370C3~YAAQXdMTAj7iwiibAQAA9lY2Lh510ww4AkYyiTvP3kW8ce22umTYtOrVx/0q2gRjiLyLhbdPGQkhfLUZeiNct+bhGoOLSXOKy38EA6h+yM1r4oxlMBRaY5J9pgQkmVijoBq/6yKxejpQtvsiyTzR0sMG3d7pzowFTtk0hsUDB2opVkKgoqstoie/bLS6ivE+q0mlLKirn8xb06iAQNbs7mcopr56lYnNTu7j1alwsKLCEMS/r+QE75tG0hqooC50jGzjOvug/JiHhe4djuFJXV83r5oL/m9aVhIbCf32OLfjdaA8UifY+NLQon8BUY2dWUv+X4+J/yelv22HkqXV0sbS1xR/xrxOqzmRwNOa4+1cS84AQgpbpf/HmwFMclMEGiYBo7qlfAnAzn+YeRwi+7on18F76/t70aR5RJrQhBObaJiWCEDAAQ==~4469045~3227953; _ga_0K4ZF41NME=GS2.1.s1766006833$o1$g1$t1766006871$j22$l0$h0; RT="z=1&dm=arrow.com&si=fb924e2a-327f-4493-b210-a4e0835cf3d1&ss=mjaivbby&sl=5&tt=ecv&bcn=%2F%2F17de4c1d.akstat.io%2F&obo=1"; bm_sv=AB509B809B9916C0CA060DCB3E01E198~YAAQXdMTAkPiwiibAQAACVo2Lh6pQ+yi8284IQnnPvn26iwCzzKV+sN7oyAh/zHCoDTvbm1Y0BxZ3EI1XOgHBFGBhlvO3RuMzLUZm2rTd92sJGWuuip5VqswTnVCVV5opOeCHfs3Fm4OTRZCroBC3pbrHD4b+CwLb/YesR2M5b+kWHwphzc09+GxBhvtFY59ZcdEHkHjbfOVL1LzUv3YPcwLLRUfNc6cJKkvKxdtJuxrYr5SkdS5Y6N/hGEnFg3H~1',
}

json_data = {
    'productDetails': [
        '41530515|Assmann WSW components, Inc|ACOV-SUB-15NB4|EAR99|null',
        '41243567|HARTING Technology Group|19365161421|EAR99|null',
        '41530526|Assmann WSW components, Inc|ACOV-SUB-25MB28|EAR99|null',
        '1585857|Amphenol Communications Solutions|10070163-01LF|EAR99|null',
        '41243561|HARTING Technology Group|19365061540|EAR99|null',
        '41530589|Assmann WSW components, Inc|ACOV-SUB-37NB21|EAR99|null',
        '41530501|Assmann WSW components, Inc|ACOV-SUB-15MB6|EAR99|null',
        '50322106|TE Connectivity|T1920060129-000|EAR99|null',
        '27570497|ITT Cannon|192990-1520|EAR99|Top Searched',
        '41530447|Assmann WSW components, Inc|ACOV-SUB-09MB34|EAR99|null',
        '41530455|Assmann WSW components, Inc|ACOV-SUB-09MB42|EAR99|null',
        '21988301|PHOENIX CONTACT|1411070|EAR99|null',
        '41530581|Assmann WSW components, Inc|ACOV-SUB-37MB43|EAR99|null',
        '41530540|Assmann WSW components, Inc|ACOV-SUB-25MB41|EAR99|null',
        '14503615|HARTING Technology Group|9300160731|EAR99|null',
        '41530510|Assmann WSW components, Inc|ACOV-SUB-15NB18|EAR99|null',
        '41530594|Assmann WSW components, Inc|ACOV-SUB-50MB41|EAR99|null',
        '55841532|Amphenol|ATMBS-011-0605|EAR99|null',
        '2384737|Amphenol Communications Solutions|8655PHRA1501LF|EAR99|null',
        '42151034|PHOENIX CONTACT|1415790|EAR99|null',
        '41530556|Assmann WSW components, Inc|ACOV-SUB-25NB23|EAR99|null',
        '42151015|PHOENIX CONTACT|1415765|EAR99|null',
        '55668578|HARTING Technology Group|19440240527|EAR99|null',
        '41530578|Assmann WSW components, Inc|ACOV-SUB-37MB40|EAR99|null',
        '34191933|PHOENIX CONTACT|1407639|EAR99|null',
    ],
}



from aux import get_proxy_dc
response = requests.post(
    'https://www.arrow.com/api/pricing/getgroupedbuyingoptions',
    # cookies=cookies,
    headers=headers,
    json=json_data,
    proxies=get_proxy_dc()
)


response
# Note: json_data will not be serialized by requests
# exactly as it was in the original request.
#data = '{"productDetails":["41530515|Assmann WSW components, Inc|ACOV-SUB-15NB4|EAR99|null","41243567|HARTING Technology Group|19365161421|EAR99|null","41530526|Assmann WSW components, Inc|ACOV-SUB-25MB28|EAR99|null","1585857|Amphenol Communications Solutions|10070163-01LF|EAR99|null","41243561|HARTING Technology Group|19365061540|EAR99|null","41530589|Assmann WSW components, Inc|ACOV-SUB-37NB21|EAR99|null","41530501|Assmann WSW components, Inc|ACOV-SUB-15MB6|EAR99|null","50322106|TE Connectivity|T1920060129-000|EAR99|null","27570497|ITT Cannon|192990-1520|EAR99|Top Searched","41530447|Assmann WSW components, Inc|ACOV-SUB-09MB34|EAR99|null","41530455|Assmann WSW components, Inc|ACOV-SUB-09MB42|EAR99|null","21988301|PHOENIX CONTACT|1411070|EAR99|null","41530581|Assmann WSW components, Inc|ACOV-SUB-37MB43|EAR99|null","41530540|Assmann WSW components, Inc|ACOV-SUB-25MB41|EAR99|null","14503615|HARTING Technology Group|9300160731|EAR99|null","41530510|Assmann WSW components, Inc|ACOV-SUB-15NB18|EAR99|null","41530594|Assmann WSW components, Inc|ACOV-SUB-50MB41|EAR99|null","55841532|Amphenol|ATMBS-011-0605|EAR99|null","2384737|Amphenol Communications Solutions|8655PHRA1501LF|EAR99|null","42151034|PHOENIX CONTACT|1415790|EAR99|null","41530556|Assmann WSW components, Inc|ACOV-SUB-25NB23|EAR99|null","42151015|PHOENIX CONTACT|1415765|EAR99|null","55668578|HARTING Technology Group|19440240527|EAR99|null","41530578|Assmann WSW components, Inc|ACOV-SUB-37MB40|EAR99|null","34191933|PHOENIX CONTACT|1407639|EAR99|null"]}'
#response = requests.post('https://www.arrow.com/api/pricing/getgroupedbuyingoptions', cookies=cookies, headers=headers, data=data)

#%%

import requests

cookies = {
    'shell#lang': 'en',
    'ASP.NET_SessionId': '4i0lofdoraq12ikvixxfpjnh',
    'arrowcurrency': 'isocode=USD&culture=en-US',
    'website#lang': 'en',
    'AKA_A2': 'A',
    'bm_ss': 'ab8e18ef4e',
    'RedirectFromLogin': '0',
    'sa-user-id': 's%253A0-c6666d79-0ed3-516c-747c-59e5af994c80.3%252B%252BfyUgoam4oac6m%252B5Er3GYZwNCClm9O1e%252FtMnN7xiI',
    'sa-user-id-v2': 's%253AxmZteQ7TUWx0fFnlr5lMgMh3OMc.qlfXN1wSgqyrvREfcm9RCMOs5DZaswvNUJWbPSBNsYU',
    'sa-user-id-v3': 's%253AAQAKIOOFHzJGRErkMLxpaJr6aoQyirbufkZUf0ia052okM-xEAMYAyCs-YfBBjABOgRvCwCpQgQ2gEkZ.7ma9dn7RLV9t3wWi%252FVfz1xWXiZbpRY39qBHypPXl%252Bd0',
    '_fwb': '181dyhElRbMGA5ADTPVo21V.1766006832397',
    'kndctr_90241DD164F13A460A495C3A_AdobeOrg_cluster': 'va6',
    'kndctr_90241DD164F13A460A495C3A_AdobeOrg_identity': 'CiY3NzY1MDk2NDk5MTczNjM5NTYwMTkzNjQ1OTkzMTE2NzE1NzEzOVIQCOv71vGyMxgBKgNWQTYwAfAB6_vW8bIz',
    'AMCV_90241DD164F13A460A495C3A%40AdobeOrg': 'MCMID|77650964991736395601936459931167157139',
    '_gcl_au': '1.1.1814002692.1766006833',
    'bm_mi': '4DCA0326F0C11B68B040D8FB7D105130~YAAQXdMTAorhwiibAQAAVb41Lh6J2KYQaaCy1u6vV6eLMEY1zhZzWL0ObLCB1dAhAZi5APn2Y4OF2hRkuT1qvcuS+ij9bL0s7pPlTzYcA0DGLeVBXW5vawlWRfMEdKzbT7BRKgbx35NDTk+/CML/AVmsLAtY9VpokQjjm4B3adLDvxoZZdmLECVCM8N1PFQDQXiOec1YBYsWbqJFusp2X+7OzD5A3dvKYGkO+eHMDjsPCp2qJE84Ckgs1Hg2Zgehl9FdqMJE4SKrWO6DLFOYMcpN/3phunLrswXjcnRdRPCdcDX8VCiPAlNkALgCPHF+j7zEX9Ep96Jd21WeI0xe6IyrsOOtLvQ=~1',
    'ak_bmsc': '47AE84A58CCD2B1D008EE28AD6094989~000000000000000000000000000000~YAAQXdMTApLhwiibAQAAX781Lh4usqr9aj3cmlgo5MUanzkDAk4xBP2GtKg0XIb6HP3kGSKREVpO4pc+DNkAudet0ynGzaRrb/QzrW8Nm7G3mfLncDWrRW+1hFUf60h187R3VB/SnJI+tHzIms0DpHFDW/xJxbQgSknhHjhPv9dKHjWnOtssxzkzSWFX0/RZ7zZq3VIGDblPISDacYeSSlvVkYk3aY9bMn5ssvJpLThCosZRw1WAhyXX8qfmDBPxqIvX1bwSAOk2IL1N1weBocpIxlCKbolrQGxUn7xbFCK9tQapUdMM60RMidZ6ku4q2nO0i3S9mAGhhQnlz7YAoG3pAQ2zs+pgiIB4hSDUoQzUQEGpMHgKuXgLXudqnjbqZWmJLQjVOO9G3744we/T7j/xV85hGoiWTbrVOHOyryz4+go2faI/pUU+kf3ICq3vBmg6kxkbv/rv',
    '_fbp': 'fb.1.1766006833255.450416808219104123',
    '_ga': 'GA1.1.1100176473.1766006834',
    '_clck': '1esqu4a%5E2%5Eg1x%5E0%5E2177',
    'IsNewUser': 'False',
    'arrowcache': 'a=EMPTY&cu=en-US&is=USD&ne=False',
    'bm_sz': 'A506ED4F933A6FED097E50C57E4370C3~YAAQXdMTAnbiwiibAQAAfIc2Lh53Tqyv1kZE9WRnnloSyrmsu38NdOiUJAMeZuEEJD625n0CIJjcphgBA5/5OjZkmfRctnNP67LROl2icAnxiOBaTqAB/3Ad26b6eP6rtd6MIZc/hfglnw5C9Zl0XzzXi+um5EQ41g8ejpLAX/WqH3J3ptJDtjP62ZrIo/E6N+ALS0h3U60/+WQicDF11eC5RXs31OVzIpmRLiG6FKjwRMfw8tA1+lQ2RHgtX85LR9l5sFVb1x3S51e12u2X7FWdEiCHchZ+ibpkmSrs/n/apaE19Bz1GZehO+gDW7E98zSMpplAuSBKdT6uRnnA2ek/hEdjUmLbec/DNw/VEOF3VRR2C7pKHOK2t2Es7x5eSaQssmMEBonNrqZXRPoueBYy2lGWzGzZpcoF0XvWSqo0/AKPvR51QiPMKvJ8ItDEDWU=~4469045~3227953',
    '_abck': '550C92C716698B04DBB5B413D96509D3~0~YAAQXdMTAofiwiibAQAArI02Lg+J4EXe1yb003MAUFlbDSbuN9FR0nkI+LUOF6K5T0vX2zkCEDq1h1DkTR5QnR2Ra1mbo5LRvsQSPE6IM9D8o/Z3klk4FPsDO7sBjnhvt+foO0V4q81SVa9BTxlaQlSLlA/oHOMNXvk42LO7CIpDeD3KXlgGCQG/SFBe2Cq8/JVzTXxfhXj9gFrZ4KOimApTQY7lHt1JDfnaIutzzsrrXHkkUxPVZExyNJaoBwaS2bO9dRqLTkNaARyEjQAFRprcSszK8A1Nw+Dgk9bo+uy+4yXbA+q56JzO7Me7WEep38x2gtUlD5SsZbtvlIUhMnD+dPQYUZ6Gq1vFuDnapj2EgDiq963hGqxh8TkCn+EzAb0yQ4CRNB4V1ebPDr2xxULChGfN5AiL2TfQE6pSR/YNTHLTbXd2JptQ63zV7/cUQkktWQhHHkSSXtGrPMGTO9fkky9tb0p35L4+g3ELppLsfYDFcG40OpVGhCyv7cGuFfHByzlAarskR6kZg5aXun3nQo8COpzdUUi/iaLt6zD1/u2IPJ4GTEO/RUma6Icl7sG4euPzNKvo/jiybbYIEr96YhocoyL5DtyPhkQ4BlX76gn8S9TZaH9UsaHBTZSzBrh8MuoAcOOLrZipV8q2af3V4TW3MUNNz5tYHXAhUGkc6dEwS40HQsjpL6yLiVq2Ht9eFn7Od8zh4nNtJ+Ax5nrOmBtF5bPH4mkPIMON+qGUQLSaK7TVAbLxeGbnW61KM8fPfCh4TR7OX0x0eO/xgMF2hNKExFL/jbjwNLMKbtOW9eKs3hhbKh8CdHawrznwFNdDG6Zqoy/1S0S2iLRy1F7zIA==~-1~-1~-1~AAQAAAAE%2f%2f%2f%2f%2f62TkqZtM0oQSg2ZhGF3ghMkblUg09zGlcVSPrld9v7n5jI3qfdqQ99XETsTr21C8pEyfPuxaKBgkdiBPf6VUS3cwaFuBs%2f5AwEg~-1',
    'bm_lso': 'E51F592BAE13AED829D56C7213399328A41DD50C945AA53FDE29DB70F1DF4E4B~YAAQXdMTAnTiwiibAQAAfIc2LgZQV+Jv38bP5uqMI9En7xdOFPIL20eMtOOWeRF/IDFChMhNqPfTH+oQwgpwk+j4MhnhyollnWKb7u02rtYKHiBaIb2DTdd0f0K2o8pMbNH8IPeHSlfkMSCJScWv4F/am7oX2Q2bGdLIOHaKyYnXKCDg9K62QK1qjDGscGyL3T8iZnD/c+TeytcSgqNBpiM5/pu5cHMLny4xDwnBvwA6G9/LerFVAtC49GhgJocwer+xwII/mY6T/LEc3QaQFdfqh/j6QbffsuB9vPJ4c1h0ocNfNFM+rZVbOAJ/8NwubLpYU9BIt9ZDgxrUZ+Ubzm1hDF19aj5fCdzwvBG0xA6wVaiB3qOUkCtdWJ+/hSOZbEK268YGFzjtXvZ/NZ+vzqEEBtWk8fTm19lQhLAhWOyZBYyUnzQCbNLzapajHfgAMiV7BpVk0f8os5cbIOs=~1766006886031',
    '_br_uid_2': 'uid%3D4030322615220%3Av%3D13.0%3Ats%3D1766006832006%3Ahc%3D7',
    'wcs_bt': 's_116daf35dfcd:1766006886',
    '_rdt_uuid': '1766006832777.ca729a6b-1c53-4467-83de-6e04e067becc',
    '_clsk': 'whz0rg%5E1766006887336%5E8%5E0%5Ee.clarity.ms%2Fcollect',
    'headerTopBarDismissed': 'Wed%2C%2017%20Dec%202025%2021%3A28%3A09%20GMT',
    '_ga_0K4ZF41NME': 'GS2.1.s1766006833$o1$g1$t1766006894$j60$l0$h0',
    '_rdt_pn': ':200~b722efcbacdde2363e9eda55c66fda86cccc00eb03c97639e8f7f1ea5baf2a15|200~2558e9eb1313edbce05bd3795dd16e1c9477bd1e74226017b74dba9254a97379|200~d2850825181bc93623197aba93979ab1419c538321d7e9578a058f5c27d47fdf|200~1125bc07b735488d98a3849fc001c01e4fb0df600c049a3aa82ae120d479956e|175~e55173dea29ed4448a98ea45a924afe1102448e8d7232154eeee35f3505f19d5',
    'bm_s': 'YAAQXdMTAonpwiibAQAAhEM+LgRKRe0cigioWvpWbKkYZGd2jQo9Kl9DqNWJS6q4IR1frq1NimUFqf5jye5DWx7wIzKP6+i9jrJaDNyxIkaTQuBDAbYKt/8bCM2RwdOHjqfVLUBg5klnS9mz/m0N7YJlUicYT1zfAjR2sF8xyFdUfCDfOmYsyEet1E0bg+A2yIQxWiVl2c+SUxtjIoqKBYWf1zBChloPM+toDFVa6z+FFXra7hPjUn5LiyRPE7Z9D2+Ej62WcyGx2VA1J3gfhjgdOwVMet+Ux9DCGAf7q4vFluUnYkURGi5lLh811ljmSGzVRDyV1/Q3p4vnGTVVwoW34uPKUHb07x9HyaPQbjSVaOFX7P/WWtBWvNBiz9/z6ioP4BMwDKlLUFUsDoDX/uW5KIFWxSKkIrHXSnfGCE2ngcUdrXoxSTdiyBoJAsvhlrBCczVHd7JRf7VfJijZj1yedlCY+MFVtNq9dMlyUR2c0B7YzMYiSVnP9ttvF7TXUhOP465S8WFsCLNLXEu/je389iS0ovWNchGsRp14bv37N7LJjtqLDwVHYcFfaYMNnR4QrQ==',
    'bm_so': '1496CC934A7F74E6555FA0FF4912F3DC8417CA44EBAC6BE50DACC3A553E7B13C~YAAQXdMTAorpwiibAQAAhEM+LgYqVswPxvnSDxyWoKjuoct4f0r5W5R0qom594XCP/UCDbACwl7RYEtW5IqH8LZC8kQelCRY3MvBZtevXGk9nDAyTNmS/yOao6KPPX/OskN1yj8BAzV2E0ru2B6rTI/v29T3DVTjdea3neiTTaVQQzUmT7tTbcjfXOMZ81C8uyPc6uYJEw2V/nYj/Azao/Vkrika6LZyrQD1kyoQNB611OrtYIQODe/EKNFa35Xgmzc4zjIGAssGPrzVyXbxFeN6lDCImtOTtayUuzRDGN7VHzesHoA0GVer7ypkFxeLkZhzmgE8y/0zW3tzx+Emyixt8rMOwkygT2XAMdk2Ugd+navtG0NxhFGG0RYlp3YbTwBs1KsWOEVnsXoyLh+H17Au9/1n6n3N4SR4slGgKSA5jS0Ybw0RsCOgK22xNnGW4Nkaiao/kqc74gocnpA=',
    'bm_sv': 'AB509B809B9916C0CA060DCB3E01E198~YAAQXdMTAovpwiibAQAAhEM+Lh6kwpscFIQzss3SzZ1d2W5a5S1bkbRbUwOTIoGig8gj/hKFUtEjqG6m7SGV3j3fBUJibdRUaZMr93ib58MHQKcvxAsT+WVGCUqrhg4Bu4B+OGxb91rqy5EzYQtBXbsiJOt3X08I9uld6o0h62F9kE+MUachapDlG3q1FzZQiPUkxjim7mNiLSAOHMbJscavApSNhK6d5KxYbcQBlEO66xP6WpWNM3tmcTGsJ6/d~1',
    'RT': '"z=1&dm=arrow.com&si=fb924e2a-327f-4493-b210-a4e0835cf3d1&ss=mjaivbby&sl=7&tt=jmk&bcn=%2F%2F17de4c1d.akstat.io%2F&obo=1&nu=143rxpmr&cl=c0mz"',
}

headers = {
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'accept-language': 'es-419,es;q=0.9,en;q=0.8',
    'priority': 'u=0, i',
    'referer': 'https://www.arrow.com/en/categories/connectors-accessories/backshells',
    'sec-ch-ua': '"Chromium";v="142", "Google Chrome";v="142", "Not_A Brand";v="99"',
    'sec-ch-ua-arch': '"arm"',
    'sec-ch-ua-bitness': '"64"',
    'sec-ch-ua-full-version-list': '"Chromium";v="142.0.7444.177", "Google Chrome";v="142.0.7444.177", "Not_A Brand";v="99.0.0.0"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-model': '""',
    'sec-ch-ua-platform': '"macOS"',
    'sec-ch-ua-platform-version': '"15.6.1"',
    'sec-fetch-dest': 'document',
    'sec-fetch-mode': 'navigate',
    'sec-fetch-site': 'same-origin',
    'sec-fetch-user': '?1',
    'upgrade-insecure-requests': '1',
    'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36',
    # 'cookie': 'shell#lang=en; ASP.NET_SessionId=4i0lofdoraq12ikvixxfpjnh; arrowcurrency=isocode=USD&culture=en-US; website#lang=en; AKA_A2=A; bm_ss=ab8e18ef4e; RedirectFromLogin=0; sa-user-id=s%253A0-c6666d79-0ed3-516c-747c-59e5af994c80.3%252B%252BfyUgoam4oac6m%252B5Er3GYZwNCClm9O1e%252FtMnN7xiI; sa-user-id-v2=s%253AxmZteQ7TUWx0fFnlr5lMgMh3OMc.qlfXN1wSgqyrvREfcm9RCMOs5DZaswvNUJWbPSBNsYU; sa-user-id-v3=s%253AAQAKIOOFHzJGRErkMLxpaJr6aoQyirbufkZUf0ia052okM-xEAMYAyCs-YfBBjABOgRvCwCpQgQ2gEkZ.7ma9dn7RLV9t3wWi%252FVfz1xWXiZbpRY39qBHypPXl%252Bd0; _fwb=181dyhElRbMGA5ADTPVo21V.1766006832397; kndctr_90241DD164F13A460A495C3A_AdobeOrg_cluster=va6; kndctr_90241DD164F13A460A495C3A_AdobeOrg_identity=CiY3NzY1MDk2NDk5MTczNjM5NTYwMTkzNjQ1OTkzMTE2NzE1NzEzOVIQCOv71vGyMxgBKgNWQTYwAfAB6_vW8bIz; AMCV_90241DD164F13A460A495C3A%40AdobeOrg=MCMID|77650964991736395601936459931167157139; _gcl_au=1.1.1814002692.1766006833; bm_mi=4DCA0326F0C11B68B040D8FB7D105130~YAAQXdMTAorhwiibAQAAVb41Lh6J2KYQaaCy1u6vV6eLMEY1zhZzWL0ObLCB1dAhAZi5APn2Y4OF2hRkuT1qvcuS+ij9bL0s7pPlTzYcA0DGLeVBXW5vawlWRfMEdKzbT7BRKgbx35NDTk+/CML/AVmsLAtY9VpokQjjm4B3adLDvxoZZdmLECVCM8N1PFQDQXiOec1YBYsWbqJFusp2X+7OzD5A3dvKYGkO+eHMDjsPCp2qJE84Ckgs1Hg2Zgehl9FdqMJE4SKrWO6DLFOYMcpN/3phunLrswXjcnRdRPCdcDX8VCiPAlNkALgCPHF+j7zEX9Ep96Jd21WeI0xe6IyrsOOtLvQ=~1; ak_bmsc=47AE84A58CCD2B1D008EE28AD6094989~000000000000000000000000000000~YAAQXdMTApLhwiibAQAAX781Lh4usqr9aj3cmlgo5MUanzkDAk4xBP2GtKg0XIb6HP3kGSKREVpO4pc+DNkAudet0ynGzaRrb/QzrW8Nm7G3mfLncDWrRW+1hFUf60h187R3VB/SnJI+tHzIms0DpHFDW/xJxbQgSknhHjhPv9dKHjWnOtssxzkzSWFX0/RZ7zZq3VIGDblPISDacYeSSlvVkYk3aY9bMn5ssvJpLThCosZRw1WAhyXX8qfmDBPxqIvX1bwSAOk2IL1N1weBocpIxlCKbolrQGxUn7xbFCK9tQapUdMM60RMidZ6ku4q2nO0i3S9mAGhhQnlz7YAoG3pAQ2zs+pgiIB4hSDUoQzUQEGpMHgKuXgLXudqnjbqZWmJLQjVOO9G3744we/T7j/xV85hGoiWTbrVOHOyryz4+go2faI/pUU+kf3ICq3vBmg6kxkbv/rv; _fbp=fb.1.1766006833255.450416808219104123; _ga=GA1.1.1100176473.1766006834; _clck=1esqu4a%5E2%5Eg1x%5E0%5E2177; IsNewUser=False; arrowcache=a=EMPTY&cu=en-US&is=USD&ne=False; bm_sz=A506ED4F933A6FED097E50C57E4370C3~YAAQXdMTAnbiwiibAQAAfIc2Lh53Tqyv1kZE9WRnnloSyrmsu38NdOiUJAMeZuEEJD625n0CIJjcphgBA5/5OjZkmfRctnNP67LROl2icAnxiOBaTqAB/3Ad26b6eP6rtd6MIZc/hfglnw5C9Zl0XzzXi+um5EQ41g8ejpLAX/WqH3J3ptJDtjP62ZrIo/E6N+ALS0h3U60/+WQicDF11eC5RXs31OVzIpmRLiG6FKjwRMfw8tA1+lQ2RHgtX85LR9l5sFVb1x3S51e12u2X7FWdEiCHchZ+ibpkmSrs/n/apaE19Bz1GZehO+gDW7E98zSMpplAuSBKdT6uRnnA2ek/hEdjUmLbec/DNw/VEOF3VRR2C7pKHOK2t2Es7x5eSaQssmMEBonNrqZXRPoueBYy2lGWzGzZpcoF0XvWSqo0/AKPvR51QiPMKvJ8ItDEDWU=~4469045~3227953; _abck=550C92C716698B04DBB5B413D96509D3~0~YAAQXdMTAofiwiibAQAArI02Lg+J4EXe1yb003MAUFlbDSbuN9FR0nkI+LUOF6K5T0vX2zkCEDq1h1DkTR5QnR2Ra1mbo5LRvsQSPE6IM9D8o/Z3klk4FPsDO7sBjnhvt+foO0V4q81SVa9BTxlaQlSLlA/oHOMNXvk42LO7CIpDeD3KXlgGCQG/SFBe2Cq8/JVzTXxfhXj9gFrZ4KOimApTQY7lHt1JDfnaIutzzsrrXHkkUxPVZExyNJaoBwaS2bO9dRqLTkNaARyEjQAFRprcSszK8A1Nw+Dgk9bo+uy+4yXbA+q56JzO7Me7WEep38x2gtUlD5SsZbtvlIUhMnD+dPQYUZ6Gq1vFuDnapj2EgDiq963hGqxh8TkCn+EzAb0yQ4CRNB4V1ebPDr2xxULChGfN5AiL2TfQE6pSR/YNTHLTbXd2JptQ63zV7/cUQkktWQhHHkSSXtGrPMGTO9fkky9tb0p35L4+g3ELppLsfYDFcG40OpVGhCyv7cGuFfHByzlAarskR6kZg5aXun3nQo8COpzdUUi/iaLt6zD1/u2IPJ4GTEO/RUma6Icl7sG4euPzNKvo/jiybbYIEr96YhocoyL5DtyPhkQ4BlX76gn8S9TZaH9UsaHBTZSzBrh8MuoAcOOLrZipV8q2af3V4TW3MUNNz5tYHXAhUGkc6dEwS40HQsjpL6yLiVq2Ht9eFn7Od8zh4nNtJ+Ax5nrOmBtF5bPH4mkPIMON+qGUQLSaK7TVAbLxeGbnW61KM8fPfCh4TR7OX0x0eO/xgMF2hNKExFL/jbjwNLMKbtOW9eKs3hhbKh8CdHawrznwFNdDG6Zqoy/1S0S2iLRy1F7zIA==~-1~-1~-1~AAQAAAAE%2f%2f%2f%2f%2f62TkqZtM0oQSg2ZhGF3ghMkblUg09zGlcVSPrld9v7n5jI3qfdqQ99XETsTr21C8pEyfPuxaKBgkdiBPf6VUS3cwaFuBs%2f5AwEg~-1; bm_lso=E51F592BAE13AED829D56C7213399328A41DD50C945AA53FDE29DB70F1DF4E4B~YAAQXdMTAnTiwiibAQAAfIc2LgZQV+Jv38bP5uqMI9En7xdOFPIL20eMtOOWeRF/IDFChMhNqPfTH+oQwgpwk+j4MhnhyollnWKb7u02rtYKHiBaIb2DTdd0f0K2o8pMbNH8IPeHSlfkMSCJScWv4F/am7oX2Q2bGdLIOHaKyYnXKCDg9K62QK1qjDGscGyL3T8iZnD/c+TeytcSgqNBpiM5/pu5cHMLny4xDwnBvwA6G9/LerFVAtC49GhgJocwer+xwII/mY6T/LEc3QaQFdfqh/j6QbffsuB9vPJ4c1h0ocNfNFM+rZVbOAJ/8NwubLpYU9BIt9ZDgxrUZ+Ubzm1hDF19aj5fCdzwvBG0xA6wVaiB3qOUkCtdWJ+/hSOZbEK268YGFzjtXvZ/NZ+vzqEEBtWk8fTm19lQhLAhWOyZBYyUnzQCbNLzapajHfgAMiV7BpVk0f8os5cbIOs=~1766006886031; _br_uid_2=uid%3D4030322615220%3Av%3D13.0%3Ats%3D1766006832006%3Ahc%3D7; wcs_bt=s_116daf35dfcd:1766006886; _rdt_uuid=1766006832777.ca729a6b-1c53-4467-83de-6e04e067becc; _clsk=whz0rg%5E1766006887336%5E8%5E0%5Ee.clarity.ms%2Fcollect; headerTopBarDismissed=Wed%2C%2017%20Dec%202025%2021%3A28%3A09%20GMT; _ga_0K4ZF41NME=GS2.1.s1766006833$o1$g1$t1766006894$j60$l0$h0; _rdt_pn=:200~b722efcbacdde2363e9eda55c66fda86cccc00eb03c97639e8f7f1ea5baf2a15|200~2558e9eb1313edbce05bd3795dd16e1c9477bd1e74226017b74dba9254a97379|200~d2850825181bc93623197aba93979ab1419c538321d7e9578a058f5c27d47fdf|200~1125bc07b735488d98a3849fc001c01e4fb0df600c049a3aa82ae120d479956e|175~e55173dea29ed4448a98ea45a924afe1102448e8d7232154eeee35f3505f19d5; bm_s=YAAQXdMTAonpwiibAQAAhEM+LgRKRe0cigioWvpWbKkYZGd2jQo9Kl9DqNWJS6q4IR1frq1NimUFqf5jye5DWx7wIzKP6+i9jrJaDNyxIkaTQuBDAbYKt/8bCM2RwdOHjqfVLUBg5klnS9mz/m0N7YJlUicYT1zfAjR2sF8xyFdUfCDfOmYsyEet1E0bg+A2yIQxWiVl2c+SUxtjIoqKBYWf1zBChloPM+toDFVa6z+FFXra7hPjUn5LiyRPE7Z9D2+Ej62WcyGx2VA1J3gfhjgdOwVMet+Ux9DCGAf7q4vFluUnYkURGi5lLh811ljmSGzVRDyV1/Q3p4vnGTVVwoW34uPKUHb07x9HyaPQbjSVaOFX7P/WWtBWvNBiz9/z6ioP4BMwDKlLUFUsDoDX/uW5KIFWxSKkIrHXSnfGCE2ngcUdrXoxSTdiyBoJAsvhlrBCczVHd7JRf7VfJijZj1yedlCY+MFVtNq9dMlyUR2c0B7YzMYiSVnP9ttvF7TXUhOP465S8WFsCLNLXEu/je389iS0ovWNchGsRp14bv37N7LJjtqLDwVHYcFfaYMNnR4QrQ==; bm_so=1496CC934A7F74E6555FA0FF4912F3DC8417CA44EBAC6BE50DACC3A553E7B13C~YAAQXdMTAorpwiibAQAAhEM+LgYqVswPxvnSDxyWoKjuoct4f0r5W5R0qom594XCP/UCDbACwl7RYEtW5IqH8LZC8kQelCRY3MvBZtevXGk9nDAyTNmS/yOao6KPPX/OskN1yj8BAzV2E0ru2B6rTI/v29T3DVTjdea3neiTTaVQQzUmT7tTbcjfXOMZ81C8uyPc6uYJEw2V/nYj/Azao/Vkrika6LZyrQD1kyoQNB611OrtYIQODe/EKNFa35Xgmzc4zjIGAssGPrzVyXbxFeN6lDCImtOTtayUuzRDGN7VHzesHoA0GVer7ypkFxeLkZhzmgE8y/0zW3tzx+Emyixt8rMOwkygT2XAMdk2Ugd+navtG0NxhFGG0RYlp3YbTwBs1KsWOEVnsXoyLh+H17Au9/1n6n3N4SR4slGgKSA5jS0Ybw0RsCOgK22xNnGW4Nkaiao/kqc74gocnpA=; bm_sv=AB509B809B9916C0CA060DCB3E01E198~YAAQXdMTAovpwiibAQAAhEM+Lh6kwpscFIQzss3SzZ1d2W5a5S1bkbRbUwOTIoGig8gj/hKFUtEjqG6m7SGV3j3fBUJibdRUaZMr93ib58MHQKcvxAsT+WVGCUqrhg4Bu4B+OGxb91rqy5EzYQtBXbsiJOt3X08I9uld6o0h62F9kE+MUachapDlG3q1FzZQiPUkxjim7mNiLSAOHMbJscavApSNhK6d5KxYbcQBlEO66xP6WpWNM3tmcTGsJ6/d~1; RT="z=1&dm=arrow.com&si=fb924e2a-327f-4493-b210-a4e0835cf3d1&ss=mjaivbby&sl=7&tt=jmk&bcn=%2F%2F17de4c1d.akstat.io%2F&obo=1&nu=143rxpmr&cl=c0mz"',
}
from aux import get_proxy_dc
response = requests.get('https://www.arrow.com/en/products/19365061540/harting',
                        # cookies=cookies,
                        proxies=get_proxy_dc(),
                        headers=headers)

response.text.find('8536.90.40.00')
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