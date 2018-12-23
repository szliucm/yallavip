# coding: utf8
'''
    @Author: LCY
    @Contact: lchuanyong@126.com
    @blog: http://http://blog.csdn.net/lcyong_
    @Date: 2018-01-15
    @Time: 19:19
    说明： appid和secretKey为百度翻译文档中自带的，需要切换为自己的
           python2和python3部分库名称更改对应如下：
           httplib      ---->    http.client
           md5          ---->    hashlib.md5
           urllib.quote ---->    urllib.parse.quote
    官方链接：
           http://api.fanyi.baidu.com/api/trans/product/index

'''

import http.client
import hashlib
import json
import urllib
import random


def baidu_translate(content,fromLang ='zh',toLang='en'):
    appid = '20181223000251503'
    secretKey = 's6Kv6Lq3zyqz2YzqXMlC'
    httpClient = None
    myurl = '/api/trans/vip/translate'
    q = str(content)
    #fromLang = 'zh'  # 源语言
    #toLang = 'en'  # 翻译后的语言
    salt = random.randint(32768, 65536)
    sign = appid + q + str(salt) + secretKey
    sign = hashlib.md5(sign.encode()).hexdigest()
    myurl = myurl + '?appid=' + appid + '&q=' + urllib.parse.quote(
        q) + '&from=' + fromLang + '&to=' + toLang + '&salt=' + str(
        salt) + '&sign=' + sign

    try:
        httpClient = http.client.HTTPConnection('api.fanyi.baidu.com')
        httpClient.request('GET', myurl)
        # response是HTTPResponse对象
        response = httpClient.getresponse()
        jsonResponse = response.read().decode("utf-8")  # 获得返回的结果，结果为json格式
        js = json.loads(jsonResponse)  # 将json格式的结果转换字典结构
        dst = str(js["trans_result"][0]["dst"])  # 取得翻译后的文本结果
        print(dst)  # 打印结果
        return  dst
    except Exception as e:
        print(e)
        return None
    finally:
        if httpClient:
            httpClient.close()


if __name__ == '__main__':
    while True:
        print("请输入要翻译的内容,如果退出输入q")
        content = input()
        if (content == 'q'):
            break
        baidu_translate(content)
