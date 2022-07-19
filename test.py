#!/usr/bin/env/ python
# -*- coding: utf-8 -*-
"""
@Time    : 2022/6/30 11:39
@Author  : 余半盏
@Email   : 2466857975@@qq.com
@File    : test.py
@Software: PyCharm
"""
import pycurl
from requests import Session
from requests_curl import CURLAdapter
# headers = [
#     'accept: image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8',
#     'accept-language: zh-CN,zh;q=0.9',
#     'accept-encoding: gzip, deflate, br'
#     'cache-control: no-cache',
#     'sec-ch-ua: " Not A;Brand";v="99", "Chromium";v="101", "Google Chrome";v="101"',
#     'sec-ch-ua-mobile: ?0',
#     'sec-ch-ua-platform: "macOS"',
#     'user-agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.4951.64 Safari/537.36'
# ]
# curl = pycurl.Curl()
# curl.setopt(pycurl.VERBOSE, 1)
# curl.setopt(
#     curl.SSL_CIPHER_LIST,
#     'TLS_AES_128_GCM_SHA256,TLS_AES_256_GCM_SHA384,TLS_CHACHA20_POLY1305_SHA256,ECDHE-ECDSA-AES128-GCM-SHA256,ECDHE-RSA-AES128-GCM-SHA256,ECDHE-ECDSA-AES256-GCM-SHA384,ECDHE-RSA-AES256-GCM-SHA384,ECDHE-ECDSA-CHACHA20-POLY1305,ECDHE-RSA-CHACHA20-POLY1305,ECDHE-RSA-AES128-SHA,ECDHE-RSA-AES256-SHA,AES128-GCM-SHA256,AES256-GCM-SHA384,AES128-SHA,AES256-SHA'
# )
# curl.setopt(curl.HTTP_VERSION, curl.CURL_HTTP_VERSION_2_0)
# curl.setopt(curl.SSLVERSION, curl.SSLVERSION_TLSv1_2)
# curl.setopt(curl.SSL_ENABLE_NPN, 0)
# curl.setopt(curl.SSL_ENABLE_ALPS, 1)
# # curl.setopt(curl.SSL_FALSESTART, 0)
# curl.setopt(curl.SSL_CERT_COMPRESSION, "brotli")
# curl.setopt(pycurl.HTTP2_PSEUDO_HEADERS_ORDER, "masp")
# curl.setopt(pycurl.HTTPHEADER, headers)
# curl.setopt(curl.PROXY, 'http://127.0.0.1:7890')
# url = 'https://tls.peet.ws/api/all'
# curl.setopt(pycurl.URL, url)
# curl.perform()
# curl.close()
if __name__ == '__main__':
    print(pycurl.version)
    user_agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.4951.64 Safari/537.36'
    headers = {
        'pragma': 'no-cache',
        'cache-control': 'no-cache',
        'sec-ch-ua': '" Not A;Brand";v="99", "Chromium";v="101", "Google Chrome";v="101"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"macOS"',
        'upgrade-insecure-requests': '1',
        'user-agent': user_agent,
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
        'sec-fetch-site': 'none',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-user': '?1',
        'sec-fetch-dest': 'document',
        'accept-language': 'zh-CN,zh;q=0.9',
    }
    client = Session()
    # proxies = {"https":"http://user:pwd@host:port"}
    proxies = {"https": "https://127.0.0.1:7890"}
    client.mount('https://', CURLAdapter())
    client.headers = {}  # 滞空原始headers，以此保证headers顺序
    info = client.get('https://tls.peet.ws/api/all', headers=headers).text
    print(info)

