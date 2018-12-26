# coding=utf-8
# encoding=utf8
from bs4 import BeautifulSoup
import urllib
import requests
import socket
import traceback
import sys
import lxml
from .models import Proxy

# User_Agent = 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.99 Safari/537.36'
# header = {}
# header['User-Agent'] = User_Agent
headers = {
    'User-Agent':  'Opera/9.80 (Macintosh; Intel Mac OS X 10.6.8; U; en) Presto/2.8.131 Version/11.11',
}

#获取所有代理IP地址

def getProxyIp():

    for i in range(1, 10):
        proxies = []
        try:
            print("pages", i)
            url = 'http://www.xicidaili.com/nn/' + str(i)
            # url = 'http://www.xicidaili.com/nn/66'

            req = requests.get(url, headers = headers)
            print(req)
            soup = BeautifulSoup(req.text ,'lxml')
            #print(soup)

            ips = soup.findAll('tr')
            print(len(ips))
            for x in range(1, len(ips)):
                ip = ips[x]
                tds = ip.findAll("td")
                ip_temp = tds[1].contents[0] + ":" + tds[2].contents[0]

                proxy = Proxy(
                    ip=ip_temp,
                    active=True
                )
                #print(proxy)
                proxies.append(proxy)
        except Exception as e:  # (ProxyError, ConnectTimeout, SSLError, ReadTimeout, ConnectionError):

            print(url)
            print("str(e)", str(e))
            continue

        Proxy.objects.bulk_create(proxies)

    return

