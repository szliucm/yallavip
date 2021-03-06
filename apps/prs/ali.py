import json,time,requests,random
#import pymysql,re
from prettytable import PrettyTable
from bs4 import BeautifulSoup
from multiprocessing import Process
import  re
import requests
from requests.exceptions import ProxyError, ConnectTimeout, SSLError, ReadTimeout, ConnectionError
from lxml import etree
from django.utils import timezone as dt







# 请求头
'''
def header(host, offer_id):
    if '1688' in host:
        cookie = open('cookie.txt', 'r').readlines()[1].replace('\n', '').replace(' ', '')
        referer = 'https://detail.1688.com/offer/{}.html'.format(offer_id)
    else:
        cookie = open('cookie.txt', 'r').readlines()[0].replace('\n', '').replace(' ', '')
        referer = 'https://item.taobao.com/item.htm?id={}'.format(offer_id)
    headers = {'Host': host,
               'Connection': 'keep-alive',
               'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.181 Safari/537.36',
               'Referer': referer,
               'Accept-Encoding': 'gzip, deflate, br',
               'Accept-Language': 'zh-CN,zh;q=0.9',
               'Cookie': cookie}
    return headers
'''
def header():
    agents = ['Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; Trident/5.0;',
              'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.6; rv,2.0.1) Gecko/20100101 Firefox/4.0.1',
              'Opera/9.80 (Macintosh; Intel Mac OS X 10.6.8; U; en) Presto/2.8.131 Version/11.11',
              'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_7_0) AppleWebKit/535.11 (KHTML, like Gecko) Chrome/17.0.963.56 Safari/535.11',
              'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; 360SE)']


    cookie = open('cookie.txt', 'r').readlines()[0].replace('\n', '').replace(' ', '')

    headers = {
               'Connection': 'keep-alive',
               'User-Agent': random.choice(agents),
               'Referer': 'https://s.1688.com/selloffer/offer_search.htm?priceStart=5.0&descendOrder=true&sortType=va_rmdarkgmv30rt&uniqfield=userid&keywords=%C5%AE%D0%AC&earseDirect=false&priceEnd=25.0&filt=y&netType=1%2C11&n=y&filt=y',
               'Accept-Encoding': 'gzip, deflate, br',
               'Accept-Language': 'zh-CN,zh;q=0.9',

               'Cookie': cookie
    }
    return headers

from .models import Proxy, Lightin_SPU,Lightin_SKU

def new_proxies():
    #return  {'http':'49.70.223.4:3217'}

    url = "http://webapi.http.zhimacangku.com/getip?num=1&type=1&pro=&city=0&yys=0&port=11&pack=36732&ts=0&ys=0&cs=0&lb=5&sb=0&pb=4&mr=1&regions="
    r = requests.session()
    res = r.get(url, headers=header(), allow_redirects=False)

    ips = res.text.split('\t')

    for ip in ips:
        if len(ip)>4:
            Proxy.objects.update_or_create(
                ip = ip,
                defaults ={
                    "active": True,

                }
    )

    #print("res is", res, res.text)

    #return {'http': "119.101.116.13:9999"}
    return

def get_proxies_xici():
    from bs4 import BeautifulSoup
    import urllib
    import requests
    import socket
    import traceback
    import sys
    import lxml
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.99 Safari/537.36'
    }

    proxies = []
    for i in range(1, 66):
        try:
            url = 'http://www.xicidaili.com/nn/' + str(i)
            # url = 'http://www.xicidaili.com/nn/66'
            req = requests.get(url, headers=headers)
            soup = BeautifulSoup(req.text, 'lxml')
            print(soup)
            print(i)
            ips = soup.findAll('tr')
            for x in range(1, len(ips)):
                ip = ips[x]
                tds = ip.findAll("td")
                ip_temp = tds[1].contents[0] + ":" + tds[2].contents[0]
                proxy = Proxy(
                    ip = ip_temp,
                    active= True
                )
                print(proxy)
                proxies.append(proxy)
        except:
            continue
        Proxy.objects.bulk_create(proxies)
    return proxies



def get_proxies():


    while(1):
        proxies = Proxy.objects.filter(active =True).values_list('ip', flat=True)

        if proxies.count()>0:
            return   random.choice(proxies)
        else:
            new_proxies()
            continue





# 发出请求
def request(url,data=None):

    r = requests.session()
    getted = False
    while(not getted):
        try:
            proxy = get_proxies()
            proxies = {'http': proxy}
            res = r.get(url, data=data, proxies=proxies,verify=False ,headers=header(), allow_redirects=False) #
            getted = True
        except (ProxyError, ConnectTimeout, SSLError, ReadTimeout, ConnectionError):
            print("代理错误")

            continue

    return res

#用代理访问1688，测试代理是否可用
def get_ali_page(offer_id):
    import time
    import traceback
    from requests.packages import urllib3
    urllib3.disable_warnings()
    r = requests.session()
    n = 0
    url = ('https://detail.1688.com/offer/{}.html'.format(offer_id))
    while ( n < 20):
        try:

            #proxy = get_proxies()
            #proxies = {'https': proxy}
            #print("当前使用的代理是",proxies)
            #proxies= None

            res = r.get(url,    headers=header(), allow_redirects=False)#,proxies=proxies,verify=False,)
            if res.status_code == 200:
                print(res, res.status_code)
                return  res.content
            else:

                print(res, res.status_code, res.headers['Location'])
                #Proxy.objects.filter(ip=proxy).update(active=False)
                '''
                n += 1
                time.sleep(1)
                continue
                '''
                return None

        except Exception as e:  #(ProxyError, ConnectTimeout, SSLError, ReadTimeout, ConnectionError):
            print("代理错误")
            '''
            print('str(Exception):\t', str(Exception))
            print("str(e)", str(e))
            print("repr(e)", repr(e))
            print("traceback.print_exc()", traceback.print_exc())
            print("traceback.format_exc()", traceback.format_exc())
            Proxy.objects.filter(ip=proxy).update(active=False)
            time.sleep(1)
            n += 1
            continue
            '''



    return  None


from .fanyi import  baidu_translate
def fanyi(data):
    if data.isdigit():
        return data
    else:
        return baidu_translate(data,"zh","en")#.replace("['","").replace("']","")

    #return requests.post('https://fanyi.baidu.com/transapi', data={"query": data, 'from': 'zh', 'to': 'en'}).json()['data'][0]['dst']

def fanyi_en(data):
    return baidu_translate(data,"en","zh")
    #return requests.post('https://fanyi.baidu.com/transapi', data={"query": data, 'from': 'en', 'to': 'zh'}).json()['data'][0]['dst']

def get_cate_url(keywords):

    from urllib import parse
    values = {'keywords': keywords.encode("gb2312")}
    data = parse.urlencode(values)
    url = 'https://s.1688.com/selloffer/offer_search.htm?priceStart=5.0&descendOrder=true&sortType=va_rmdarkgmv30rt&uniqfield=userid&earseDirect=false&priceEnd=25.0&filt=y&netType=1,11&n=y&filt=y#sm-filtbar'+"&"+data
    return  url

    '''
    import  urllib
    data = urllib.quote(keywords)
    url = 'https://s.1688.com/selloffer/offer_search.htm?priceStart=5.0&descendOrder=true&sortType=va_rmdarkgmv30rt&uniqfield=userid&earseDirect=false&priceEnd=25.0&filt=y&netType=1,11&n=y&filt=y#sm-filtbar'+'&keywords='+data
    return  url
    
    html = request(url,data).content

    #debug用
    with open('ali.txt', 'wb') as f:
        f.write(html)

    f = open("ali.txt", "rb")

    html = f.read()

    htmlEmt = etree.HTML(html)

    # 价格带分布
    priceRegions = htmlEmt.xpath('//div[@ctype="priceRegion"]')
    print("priceRegions *****************", etree.tostring(priceRegions))

    for priceRegion in priceRegions:
        priceRegion_content = json.loads(priceRegion)
        print(priceRegion_content)
    '''




def ali_list(html):
    '''
    import http.client

    http.client.HTTPConnection.debuglevel = 1


    cookie = open('cookie.txt', 'r').readlines()[1].replace('\n', '').replace(' ', '')
    header = {'authority': 's.1688.com',
              'scheme':'https',
              'referer': 'https://www.1688.com/',
              'upgrade-insecure-requests': '1',
              'Connection': 'keep-alive',
              'Cache-Control': 'max-age=0',
              'Upgrade-Insecure-Requests': '1',
              'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.132 Safari/537.36',
              'Accept': '*/*',
              'Accept-Encoding': 'gzip, deflate, br',
              'Accept-Language': 'zh-CN,zh;q=0.9',
              'Cookie': cookie,
              }

    url = "https://s.1688.com/selloffer/offer_search.htm?keywords=%C5%AE%D0%AC&n=y&netType=1%2C11"
    #html_ori = request(url).content

    r = requests.session()
    response = r.get(url, headers=header)
    html_ori = response.content
    #print(html_ori)
    #return
    with open('ali.list', 'wb') as f:

       f.write(html_ori)


    f = open("ali.list", "rb")

    html = f.read()

    '''

    htmlEmt = etree.HTML(html)
    # 取产品id
    '''
    result = etree.tostring(htmlEmt)
    # utf-8 格式输出
    print(result.decode("utf-8"))
    '''
    #vendor_no = htmlEmt.xpath('//*/@offerid')
    #print("vendor_no is ", vendor_no)

    vendors = htmlEmt.xpath('//div[@class="sm-offer "]/ul/li')
    vendor_list = []
    for vendor in vendors:
        #print("type  vendor",type(vendor), etree.tostring(vendor))
        offer_id = vendor.attrib.get('offerid')
        vendor_list.append(offer_id)
        print("type  offer_id",type(offer_id), offer_id)
    return  vendor_list

#获取1688产品信息
def get_ali_product_info(offer_id,cate_code):
    from .models import AliProduct

    print("开始抓取1688产品信息 ", offer_id)

    product = AliProduct()
    product.offer_id = offer_id
    product.cate_code = cate_code

    res = get_ali_page(offer_id)
    if res is None:
        return "获取页面失败", False

    htmlEmt = etree.HTML(res)

    # 标题
    title_ori = htmlEmt.xpath('//h1[@class="d-title"]/text()')
    if title_ori:

        print(type(title_ori), title_ori)
        title_ori = title_ori[0]
        title = fanyi(title_ori)

    else:
        print("title is empty",offer_id)
        return "title is empty",False

    # 取主图
    #imgs_list = []
    images_list = []
    image_no = 0

    divs = htmlEmt.xpath('//ul[@class="nav nav-tabs fd-clr"]/li/@data-imgs')
    # image_no = 0
    for div in divs:
        # print("type  div", type(div), div)
        imgs = json.loads(div)
        if imgs:
            '''
            image = {
                "src": imgs["original"],
                "image_no": image_no
            }
            imgs_list.append(image)
            
            image_no += 1
            '''
            images_list.append(imgs["original"])


    option_list = []
    option_zh_list = []

    # 取leading
    option1_list = []
    option1_zh_list = []
    img_dict = {}
    div_leadings = htmlEmt.xpath('//div[@class="obj-leading"]')
    # 有两种情况，有leading 和没有leading
    if not div_leadings:
        leading = False
    else:
        leading = True

        div_leading = div_leadings[0]
        option1 = div_leading.find('.//div[@class="obj-header"]/span').text

        option1_content = div_leading.xpath('.//div[@class="obj-content"]/ul/li/div')
        # print("option1_content *****************", etree.tostring(option1_content))
        for div in option1_content:
            # print("div *****************", etree.tostring(div))

            data_name_div = div.attrib.get('data-unit-config')
            if data_name_div:
                data_name = json.loads(data_name_div)
                option1_name_zh = data_name["name"]
                option1_name_en = fanyi(option1_name_zh)
                #print("option1_name is ", option1_name_zh, option1_name_en)
            else:
                continue

            if option1_name_en in option_list:
                option1_name_en = option1_name_en + "_" + str(len(option_list))
            option1_list.append(option1_name_en)
            option1_zh_list.append(option1_name_zh)

            data_imgs = div.attrib.get('data-imgs')
            if data_imgs:
                data_imgs = json.loads(data_imgs)
                option1_img = data_imgs["original"]
                #print("image is ", option1_img)

                # 规格图片如果不在主图里，也插进列表
                if option1_img not in images_list:
                    images_list.append(option1_img)
                    '''
                    image = {
                        "src": option1_img,
                        "image_no": image_no
                    }
                    imgs_list.append(image)
                    option_image_no = image_no
                    image_no += 1
                else:
                    option_image_no = images_list.index(option1_img)
                '''
                # 规格-图片地址 字典
                img_dict[option1_name_en] = images_list.index(option1_img)


            else:
                option1_img = None
                print("no data image")



        option = {
            "name": fanyi(option1),
            "values": option1_list
        }
        # 插入规格
        option_list.append(option)
        #print("option1 \n", option_list)

        ################插入中文版，便于理解
        option_zh = {
            "name": option1,
            "values": option1_zh_list
        }
        # 插入规格
        option_zh_list.append(option_zh)
        #print("option1 \n", option_list)

    # 取sku
    option2_list = []
    option2_zh_list = []
    price_dict = {}

    div_sku = htmlEmt.xpath('//div[@class="obj-sku"]')
    if div_sku :
        print(div_sku,"\n\n")
        div_sku = div_sku[0]


        option2 = div_sku.find('.//div[@class="obj-header"]/span').text

        option2_content = div_sku.xpath('.//tr')
        # print("option2_content *****************", etree.tostring(option2_content))
        for div in option2_content:
            #print("type  div", type(div), etree.tostring(div))
            # 有两种情况，一种是名字含图片(not leading )，一种是不含图片的(有leading)
            option2_img = None
            if leading:
                option2_name = div.find('.//td[@class="name"]/span').text
                option2_img = None
            else:
                option2_name = div.find('.//td[@class="name"]/span').attrib.get('title')


                option2_imgs = div.find('.//td[@class="name"]/span').attrib.get('data-imgs')
                if option2_imgs:
                    data_imgs = json.loads(option2_imgs)
                    option2_img = data_imgs["original"]
                    #print("image is ", option2_img)

                    # 规格图片如果不在主图里，也插进列表
                    if option2_img not in images_list:
                        images_list.append(option2_img)
                        '''
                        image = {
                            "src": option2_img,
                            "image_no": image_no
                        }
                        imgs_list.append(image)
                        image_no += 1
                        '''

            #不管有没有leading，都有名字要处理，但是只有无leading的，才有规格图片字典
            if option2_name:
                if option2_name.isdigit():
                    option2_name_en = option2_name
                else:
                    option2_name_en = fanyi(option2_name)
            else:
                print("没有规格")
                continue

            #print("###############", option2_name_en, option2_list)
            if option2_name_en in option2_list:
                option2_name_en = option2_name_en + "_" + str(len(option2_list))

            option2_list.append(option2_name_en)
            option2_zh_list.append(option2_name)

            # 规格-图片地址 字典
            if option2_img is not None:
                img_dict[option2_name_en] = images_list.index(option2_img)

            price = div.find('.//td[@class="price"]/span/em').text
            count = div.find('.//td[@class="count"]/span/em[1]').text

            if not count or int(count) == 0:
                print("没有库存", offer_id)
                continue


            price_dict[option2_name_en] = price

        option = {
            "name": fanyi(option2),
            "values": option2_list
        }

        # 插入规格
        option_list.append(option)
        #print("option_list \n", option_list)

        #######中文版
        option_zh = {
            "name": option2,
            "values": option2_zh_list
        }

        # 插入规格
        option_zh_list.append(option_zh)
        #print("option_list \n", option_zh_list)
    else:
        print("obj-sku is empty")
        #return "obj-sku is empty", False


    #找到最大价格
    maxprice = 0
    for price in price_dict.values():
        if float(price)>maxprice:
            maxprice = float(price)

    AliProduct.objects.update_or_create(
        offer_id= offer_id,
        defaults={
            'title' : title,
            'cate_code': cate_code,
            'images': json.dumps(images_list),
            'options': json.dumps(option_list),
            'options_zh': json.dumps(option_zh_list),
            'image_dict': json.dumps(img_dict),
            'price_dict': json.dumps(price_dict),
            "maxprice":maxprice,
            'price_rate' : random.uniform(3, 4),
            "created" : True,
            "created_error": "",
            "created_time": dt.now()

        }
    )
    return "", True






def get_ali_product(offer_id,max_id,tags):

    from shop.models import Shop, ShopifyProduct
    from prs.shop_action import post_product_main, post_product_variant, insert_product

    product = ShopifyProduct()
    dest_shop = "yallasale-com"
    shop_obj = Shop.objects.get(shop_name=dest_shop)

    shop_url = "https://%s:%s@%s.myshopify.com" % (shop_obj.apikey, shop_obj.password, shop_obj.shop_name)


    html = request('https://detail.1688.com/offer/{}.html'.format(offer_id)).content
    
    with open('ali.txt', 'wb') as f:
        f.write(html)


    f = open("ali.txt", "rb")

    html = f.read()

    htmlEmt = etree.HTML(html)

    # 标题
    title_ori = htmlEmt.xpath('//h1[@class="d-title"]/text()')

    if title_ori:
        product.title = fanyi(title_ori)
    else:
        print("tile ###############")
        result = etree.tostring(htmlEmt)
        # utf-8 格式输出
        print(result.decode("utf-8"))
        print(type(title_ori),title_ori )
        print("title is empty", offer_id)
        return False


    #取主图
    imgs_list=[]
    image_no=0

    divs = htmlEmt.xpath('//ul[@class="nav nav-tabs fd-clr"]/li/@data-imgs')
    #image_no = 0
    for div in divs:
        #print("type  div", type(div), div)
        imgs = json.loads(div)
        if imgs:

            image = {
                "src": imgs["original"],
                "image_no": image_no
            }
            imgs_list.append(image)
            image_no += 1





    product.body_html= product.title
    product.vendor = offer_id
    product.product_type = 'auto'
    product.tags = tags

    option_list =[]

    # 取option1
    option1_list = []
    img_dict ={}
    div_leadings = htmlEmt.xpath('//div[@class="obj-leading"]')
    #有两种情况，有leading 和没有leading
    if not div_leadings:
        leading = False
    else:
        leading = True


        div_leading = div_leadings[0]
        option1_name = div_leading.find('.//div[@class="obj-header"]/span').text
        option1_content = div_leading.xpath('.//div[@class="obj-content"]/ul/li/div')
        #print("option1_content *****************", etree.tostring(option1_content))
        for div in option1_content:
            #print("div *****************", etree.tostring(div))


            data_name_div = div.attrib.get('data-unit-config')
            if data_name_div:
                data_name = json.loads(data_name_div)
                option1_name_zh = data_name["name"]
                option1_name_en =  fanyi(option1_name_zh)
                print("option1_name is ", option1_name_zh, option1_name_en)
            else:
                continue

            data_imgs = div.attrib.get('data-imgs')
            if data_imgs:
                data_imgs = json.loads(data_imgs)
                option1_img = data_imgs["original"]
                print("image is ", option1_img)

                #规格图片如果不在主图里，也插进列表
                if option1_img not in imgs_list:
                    image = {
                        "src": option1_img,
                        "image_no": image_no
                    }
                    imgs_list.append(image)
                    image_no += 1


                #规格-图片地址 字典
                img_dict[option1_name_en] = option1_img
            else:
                option1_img = None
                print("no data image")

            option1_list.append(option1_name_en)

        option = {
            "name": fanyi(option1_name),
            "values": option1_list
        }
        # 插入规格
        option_list.append(option)
        print("option1 \n", option_list)

    # 取option2
    option2_list = []
    price_dict = {}

    div_sku = htmlEmt.xpath('//div[@class="obj-sku"]')[0]
    option2_name = div_sku.find('.//div[@class="obj-header"]/span').text
    option2_name_en = fanyi(option2_name)
    option2_content = div_sku.xpath('.//tr')
    #print("option2_content *****************", etree.tostring(option2_content))
    for div in option2_content:
        #print("type  div", type(div), etree.tostring(div))
        #有两种情况，一种是名字含图片(not leading )，一种是不含图片的(有leading)
        option2_img = None
        if leading:
            option2_name = div.find('.//td[@class="name"]/span').text

        else:
            option2_name = div.find('.//td[@class="name"]/span').attrib.get('title')
            option2_imgs = div.find('.//td[@class="name"]/span').attrib.get('data-imgs')
            if option2_imgs:
                data_imgs = json.loads(option2_imgs)
                option2_img = data_imgs["original"]
                print("image is ", option2_img)

                #规格图片如果不在主图里，也插进列表
                if option2_img not in imgs_list:
                    image = {
                        "src": option2_img,
                        "image_no": image_no
                    }
                    imgs_list.append(image)
                    image_no += 1

        if option2_name:
            if option2_name_en.isdigit():
                option2_name_en = option2_name
            else:
                option2_name_en = fanyi(option2_name)
        else:
            continue
    
        # 规格-图片地址 字典
        if option2_img:
            img_dict[option2_name_en] = option2_img


        price = div.find('.//td[@class="price"]/span/em').text
        count = div.find('.//td[@class="count"]/span/em[1]').text

        if not count or int(count) == 0:
            continue



        option2_list.append(option2_name_en)
        price_dict[option2_name_en] = price


    option = {
        "name": option2_name_en,
        "values": option2_list
    }

    # 插入规格
    option_list.append(option)
    print("option_list \n", option_list)


    ################################
    ##############################
    ############可以发布主产品了
    #############################
    handle_new = 'a' + str(max_id)
    print("发布产品", shop_url,handle_new,imgs_list)
    new_product = post_product_main(shop_url, handle_new, product, imgs_list)
    if new_product:
        products = []
        products.append(new_product)
        # 插入到系统数据库
        insert_product(shop_obj.shop_name, products)

        # 修改handle最大值
        Shop.objects.filter(shop_name=shop_obj.shop_name).update(max_id=max_id)

        print("产品主体发布成功！！！！")
        print(type(new_product),  new_product.get("id"))

    else:

        print("产品主体发布失败！！！！")
        return False

    #################################
    # 新创建的主图信息，创建变体需要
    #################################
    image_dict = {}
    new_images = new_product["images"]
    print("new_images", new_images)
    for k in range(len(new_images)):
        new_image_no = new_images[k]["id"]

        old_image_src = imgs_list[k]["src"]

        #原图片对应shopify的id
        image_dict[old_image_src] = new_image_no
        # print("old image %s new image %s"%(old_image_no, new_image_no ))


    ###################################
    # 创建变体
    ###################################
    old_image_no = 0
    position = 0
    variants_list = []
    if leading:
        for option1 in option1_list:
            for option2 in option2_list:
                # 根据规格-图片地址 字典 找到图片地址
                #根据图片地址找到shopify 的图片id
                print("option1", option1)

                option1_img = img_dict.get(option1)
                print("img_dict",img_dict)
                print("image_dict", image_dict)

                print("option1_img", option1_img)



                new_image_no = image_dict.get(option1_img)


                sku = handle_new
                option1 = option1
                option2 = option2
                option3 = None

                if option1:
                    sku = sku + "-" + option1.replace("&", '').replace('-', '').replace('.', '').replace(' ', '')
                    if option2:
                        sku = sku + "_" + option2.replace("&", '').replace('-', '').replace('.', '').replace(' ', '')
                        if option3:
                            sku = sku + "_" + option3.replace("&", '').replace('-', '').replace('.', '').replace(' ',
                                                                                                                 '')

                variant_item = {
                    "option1": option1,
                    "option2": option2,
                    "option3": option3,
                    "price": int(float(price_dict[option2]) * 2.8),
                    "compare_at_price": int(float(price_dict[option2]) * 2.8 * random.uniform(2, 3)),
                    "sku": sku,
                    "position": position,
                    "image_id": new_image_no,
                    "grams": 0,
                    "title": sku,
                    "taxable": "true",
                    "inventory_management": "shopify",
                    "fulfillment_service": "manual",
                    "inventory_policy": "continue",

                    "inventory_quantity": 10000,
                    "requires_shipping": "true",
                    "weight": 0.5,
                    "weight_unit": "kg",

                }
                # print("variant_item", variant_item)
                variants_list.append(variant_item)
                position += 1
            old_image_no += 1
    else:
        for option2 in option2_list:
            # 根据规格-图片地址 字典 找到图片地址
            # 根据图片地址找到shopify 的图片id
            print("option2", option2)

            option2_img = img_dict.get(option2)
            print("img_dict", img_dict)
            print("image_dict", image_dict)

            print("option1_img", option2_img)

            new_image_no = image_dict.get(option2_img)

            sku = handle_new
            option1 = option2
            option2 = None
            option3 = None

            if option1:
                sku = sku + "-" + option1.replace("&", '').replace('-', '').replace('.', '').replace(' ', '')
                if option2:
                    sku = sku + "_" + option2.replace("&", '').replace('-', '').replace('.', '').replace(' ', '')
                    if option3:
                        sku = sku + "_" + option3.replace("&", '').replace('-', '').replace('.', '').replace(' ',
                                                                                                             '')

            variant_item = {
                "option1": option1,
                "option2": option2,
                "option3": option3,
                "price": int(float(price_dict[option2]) * 2.8),
                "compare_at_price": int(float(price_dict[option2]) * 2.8 * random.uniform(2, 3)),
                "sku": sku,
                "position": position,
                "image_id": new_image_no,
                "grams": 0,
                "title": sku,
                "taxable": "true",
                "inventory_management": "shopify",
                "fulfillment_service": "manual",
                "inventory_policy": "continue",

                "inventory_quantity": 10000,
                "requires_shipping": "true",
                "weight": 0.5,
                "weight_unit": "kg",

            }
            # print("variant_item", variant_item)
            variants_list.append(variant_item)
            position += 1
        old_image_no += 1

    posted = post_product_variant(shop_url, new_product.get("id"), variants_list, option_list)


    return


# 1688offer
def list_ali_product(offer_id,  max_id, shop_obj):
    from shop.models import Shop, ShopifyProduct
    from prs.shop_action import post_product_main, post_product_variant,insert_product

    dest_shop = "yallasale-com"
    shop_obj = Shop.objects.get(shop_name=dest_shop)

    shop_url = "https://%s:%s@%s.myshopify.com" % (shop_obj.apikey, shop_obj.password, shop_obj.shop_name)
    product = ShopifyProduct()

    html = request('https://detail.1688.com/offer/{}.html'.format(offer_id)).content
    #with open('ali.txt', 'wb') as f:
     #   f.write(html)


    #f = open("ali.txt", "rb")

    #html = f.read()

    htmlEmt = etree.HTML(html)

    #取主图
    imgs_list=[]

    divs = htmlEmt.xpath('//ul[@class="nav nav-tabs fd-clr"]/li/@data-imgs')
    image_no = 0
    for div in divs:
        #print("type  div", type(div), div)
        imgs = json.loads(div)
        image = {
            "src": imgs["original"],
            "image_no": image_no
        }
        imgs_list.append(image)
        image_no += 1

    # 标题
    title_ori = htmlEmt.xpath('//h1[@class="d-title"]/text()')
    if title_ori:
        product.title = fanyi(title_ori)
    else:
        print(" title is empty",offer_id)
        return False


    product.body_html= product.title
    product.vendor = offer_id
    product.product_type = 'auto'
    #

    ##############################
    ############可以发布主产品了
    #############################
    handle_new = 'a' + str(max_id)
    new_product = post_product_main(shop_url, handle_new, product, imgs_list)
    if new_product:
        products = []
        products.append(new_product)
        # 插入到系统数据库
        insert_product(shop_obj.shop_name, products)

        # 修改handle最大值
        Shop.objects.filter(shop_name=shop_obj.shop_name).update(max_id=max_id)

        print("产品发布成功！！！！"  )
        print(type(new_product),new_product.get("id"))

    else:

        print("产品发布失败！！！！")
        return  False

    # 新创建的主图信息
    image_dict = {}
    for k_img in range(len(new_product["images"])):
        image_row = new_product["images"][k_img]
        new_image_no = image_row["id"]
        # new_image_list.append(image_no)
        old_image_src = imgs_list[k_img]["src"]

        image_dict[old_image_src] = new_image_no
        # print("old image %s new image %s"%(old_image_no, new_image_no ))


    option_list =[]

    # 取颜色
    option1_list = []

    print("颜色")
    divs = htmlEmt.xpath('//ul[@class="list-leading"]/li/div')
    for div in divs:
        #print("type  div",type(div), etree.tostring(div))
        color_images_div = div.attrib.get('data-imgs')
        if color_images_div:
            color_images = json.loads(color_images_div)
            print("color_images is ", color_images["original"])
        else:
            print("no color image")

        color_name_div =  div.attrib.get('data-unit-config')
        color_name = json.loads(color_name_div)
        print("color_name is ", color_name["name"],fanyi(color_name["name"]))

        option1_list.append(fanyi(color_name["name"]))


    option = {
        "name": "color",
        "values": option1_list
    }
    #插入规格
    option_list.append(option)


    #取尺码
    option2_list = []
    price_dict = {}
    print("尺码")
    divs = htmlEmt.xpath('//*[@class="table-sku"]/tr')
    for div in divs:
        #print("type  div", type(div), div)
        option2 = div.find('.//td[@class="name"]/span').text
        price = div.find('.//td[@class="price"]/span/em').text

        print("option2 price ", option2, price)
        price_dict[option2] = price

        option2_list.append(option2)

    option = {
        "name": "size",
        "values": option2_list
    }
    # 插入规格
    option_list.append(option)

    #创建变体
    old_image_no = 0
    position = 0
    variants_list = []
    for option1 in option1_list:
        for option2 in option2_list:
            new_image_no = image_dict.get(old_image_no)
            sku = handle_new
            option1 = option1
            option2 = option2
            option3 = None

            if option1:
                sku = sku + "-" + option1.replace("&", '').replace('-', '').replace('.', '').replace(' ', '')
                if option2:
                    sku = sku + "_" + option2.replace("&", '').replace('-', '').replace('.', '').replace(' ', '')
                    if option3:
                        sku = sku + "_" + option3.replace("&", '').replace('-', '').replace('.', '').replace(' ', '')

            variant_item = {
                "option1": option1,
                "option2": option2,
                "option3": option3,
                "price": int(float(price_dict[option2]) * 2.8),
                "compare_at_price": int(float( price_dict[option2]) * 2.8 * random.uniform(2, 3)),
                "sku": sku,
                "position": position ,
                "image_id": new_image_no,
                "grams": 0,
                "title": sku,
                "taxable": "true",
                "inventory_management": "shopify",
                "fulfillment_service": "manual",
                "inventory_policy": "continue",

                "inventory_quantity": 10000,
                "requires_shipping": "true",
                "weight": 0.5,
                "weight_unit": "kg",

            }
            # print("variant_item", variant_item)
            variants_list.append(variant_item)
            position += 1
        old_image_no += 1

    posted = post_product_variant(shop_url,new_product.get("id"), variants_list, option_list)


    #f.close()

    return posted






# 淘宝offer
def taobao(offer_id):
    # 销量及价格
    sale = request('https://detailskip.taobao.com/service/getData/1/p1/item/detail/sib.htm?itemId={}'
                   '&modules=dynStock,qrcode,viewer,price,duty,xmpPromotion,delivery,activity,fqg,zjys,'
                   'amountRestriction,couponActivity,soldQuantity,originalPrice,tradeContract'.format(offer_id))
    sale = eval(sale.text.encode('utf-8').decode('unicode_escape').replace('true', '-1').replace('false', '-2').replace('null', '-3').replace('\n',''))
    old_price = sale['data']['price']
    price = sale['data']['promotion']['promoData']['def'][0]['price']
    confirmGoodsCount = sale['data']['soldQuantity']['confirmGoodsCount']  # 交易成功笔数
    soldTotalCount = sale['data']['soldQuantity']['soldTotalCount']  # 总数量
    sku_count = len(sale['data']['promotion']['promoData'])-1
    # 收藏数
    fav = \
    request('https://count.taobao.com/counter3?callback=jsonp&sign=2&keys=ICCP_1_{}'.format(offer_id)).text.split(':')[
        1].split('}')[0]
    # 评论详情
    comment = eval(request('https://rate.taobao.com/detailCommon.htm?auctionNumId={}'.format(offer_id)).text.replace('(', '').replace(')', '').replace('true', '-1').replace('false', '-2'))
    normal = comment['data']['count']['normal']
    total = comment['data']['count']['total']
    bad = comment['data']['count']['bad']
    tryRepotr = comment['data']['count']['tryReport']
    goodFull = comment['data']['count']['goodFull']
    additional = comment['data']['count']['additional']
    pic = comment['data']['count']['pic']
    channel = '淘宝'
    # shop信息
    r = request('https://item.taobao.com/item.htm?id={}'.format(offer_id))

    soup = BeautifulSoup(r.text, 'html.parser')
    title = soup.select('title')[0].text[:-4]
    sellerNick = r.text.split('sellerNick       : \'')[1].split('\'')[0]
    sellerId = r.text.split('sellerId         : \'')[1].split('\'')[0]
    # 数据展示
    table = PrettyTable(['卖家名','offer_id','收藏数','原价格','活动价格','规格数','成交数','总数','评价数','中评','好评','差评','试用','照片评价','追加评论','时间'])
    table.add_row([sellerNick,offer_id,fav,old_price, price, sku_count, confirmGoodsCount, soldTotalCount,total, normal,goodFull,bad,tryRepotr,pic,additional,str(dt.now())[:19]])
    print(table)
    # 数据存储
    classify = 'other_details(sellername, sellerid, 渠道,offer_id, title, fav, oldprice, saleprice, speCount, 成交数, 总数, 评价数, 中评, 好评, 差评, 试用, pic, additional, now_time)'
    values = (sellerNick,sellerId,channel, offer_id,title,fav,old_price, price, sku_count, confirmGoodsCount, soldTotalCount,total, normal,goodFull,bad,tryRepotr,pic,additional,str(dt.now())[:19])
    append(connectdb('taobao_offer'),classify, values)


# 天猫offer
def tianmao(offer_id):
    # 销量及价格
    sale = request('https://detailskip.taobao.com/service/getData/1/p1/item/detail/sib.htm?itemId={}'
                   '&modules=dynStock,qrcode,viewer,price,duty,xmpPromotion,delivery,activity,fqg,zjys,'
                   'amountRestriction,couponActivity,soldQuantity,originalPrice,tradeContract'.format(offer_id))
    sale = eval(
        sale.text.encode('utf-8').decode('unicode_escape').replace('true', '-1').replace('false', '-2').replace('null',
                                                                                                           '-3').replace(
            '\n', ''))
    old_price = sale['data']['price']
    price = sale['data']['promotion']['promoData']['def'][0]['price']
    confirmGoodsCount = sale['data']['soldQuantity']['confirmGoodsCount']  # 交易成功笔数
    soldTotalCount = sale['data']['soldQuantity']['soldTotalCount']  # 总数量
    sku_count = len(sale['data']['promotion']['promoData']) - 1
    # 收藏数
    fav = \
    request('https://count.taobao.com/counter3?callback=jsonp&sign=2&keys=ICCP_1_{}'.format(offer_id)).text.split(':')[
        1].split('}')[0]
    # shop信息
    r = request('https://detail.tmall.com/item.htm?id={}'.format(offer_id))
    soup = BeautifulSoup(r.text, 'html.parser')
    if 'tmall.com' in soup.select('title')[0].text:
        title = soup.select('title')[0].text[:-12]
        sellerNick = soup.select('a.slogo-shopname strong')[0].text
        sellerId = r.text.split('sellerId:\"')[1].split('\"')[0]
        channel = '天猫'
    else:
        r = request('https://detail.tmall.hk/hk/item.htm?id={}'.format(offer_id))
        soup = BeautifulSoup(r.text, 'html.parser')
        title = soup.select('title')[0].text[:-13]
        sellerNick = soup.select('a.slogo-shopname strong')[0].text
        sellerId = r.text.split('sellerId:\"')[1].split('\"')[0]
        channel = '天猫国际'
    # 评论详情
    comment = eval(request('https://rate.taobao.com/detailCommon.htm?auctionNumId={}'.format(offer_id)).text.replace('(', '').replace(')', '').replace('true', '-1').replace('false', '-2'))
    comment2 = eval(request('https://rate.tmall.com/list_detail_rate.htm?itemId={}&sellerId={}&order=3&content=0&callback=jsonp'
                            .format(offer_id, sellerId)).text.split('jsonp(')[1].replace(')', '').replace('true', '-1').replace('false', '-2'))
    normal = comment['data']['count']['normal']
    total = comment2['rateDetail']['rateCount']['total']
    bad = comment['data']['count']['bad']
    tryRepotr = comment['data']['count']['tryReport']
    goodFull = comment['data']['count']['goodFull']
    additional = comment2['rateDetail']['rateCount']['used']
    pic = comment2['rateDetail']['rateCount']['picNum']
    # 数据展示
    table = PrettyTable(['卖家名','offer_id','收藏数','原价格','活动价格','规格数','成交数','总数','评价数','中评','好评','差评','试用','照片评价','追加评论','时间'])
    table.add_row([sellerNick,offer_id,fav,old_price, price, sku_count, confirmGoodsCount, soldTotalCount,total, normal,goodFull,bad,tryRepotr,pic,additional,str(dt.now())[:19]])
    print(table)
    # 数据存储
    classify = 'other_details(sellername, sellerid, 渠道,offer_id, title, fav, oldprice, saleprice, speCount, 成交数, 总数, 评价数, 中评, 好评, 差评, 试用, pic, additional, now_time)'
    values = (sellerNick,sellerId,channel, offer_id,title,fav,old_price, price, sku_count, confirmGoodsCount, soldTotalCount,total, normal,goodFull,bad,tryRepotr,pic,additional,str(dt.now())[:19])
    append(connectdb('taobao_offer'),classify, values)


# 聚划算


# 数据集合
def collect(offer_id):
    r = request('https://item.taobao.com/item.htm?id={}'.format(offer_id))
    soup = BeautifulSoup(r.text, 'html.parser')
    if '淘宝' in soup.select('title')[0].text:
        taobao(offer_id)
    else:
        tianmao(offer_id)


if __name__ == '__main__':
    # while True:
    #     now = str(datetime.datetime.now())[11:19]
    #     if now[3:] == '17:30':
    #         offer_id = ['574502330964','521240946180','531163568440','553933356519','548808206714','562316697901','571717334695']
    #         # offer_id = ['574502330964','521240946180','531163568440']
    #         for a in offer_id:
    #             p = Process(target=ali,args=(a,))
    #             p.start()
    #             p.join()
    #             time.sleep(random.uniform(30, 100))

    while True:
        now = str(datetime.datetime.now())[11:19]
        if now[3:] == '04:40':
            offer_id = ['575430961024','575067441525']
            for item in offer_id:
                p = Process(target=collect, args=(item,))
                p.start()
                time.sleep(1)
                p.join()





from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By


import time
'''
chrome_options = Options()
chrome_options.add_argument('--headless')  # 16年之后，chrome给出的解决办法，抢了PhantomJS饭碗
chrome_options.add_argument('--disable-gpu')
chrome_options.add_argument('--no-sandbox')  # root用户不加这条会无法运行

browser = webdriver.Chrome(options=chrome_options)
wait=WebDriverWait(browser,15)
'''
def crawle(key,page):
    url='https://www.1688.com/'
    browser.get(url=url)
    try:
        button=browser.find_element_by_class_name('identity-cancel')
        button.click()
    except:
        pass

    input=browser.find_element_by_id('alisearch-keywords')
    input.send_keys(key)

    sea_button=browser.find_element_by_id('alisearch-submit')
    sea_button.click()
    try:
        button_1=browser.find_element_by_class_name('s-overlay-close-l')
        button_1.click()
    except:
        pass
    try:
        button_deal=browser.find_elements_by_css_selector('.sm-widget-sort.fd-clr.s-widget-sortfilt li')[1]
        button_deal.click()
    except:
        pass

    try:
        browser.execute_script('window.scrollTo(0, document.body.scrollHeight)')
        time.sleep(3)
        browser.execute_script('window.scrollTo(0, document.body.scrollHeight)')
        time.sleep(3)
        browser.execute_script('window.scrollTo(0, document.body.scrollHeight)')
        time.sleep(3)
        browser.execute_script('window.scrollTo(0, document.body.scrollHeight)')
        time.sleep(3)

        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR,'#offer60')))
    except :
        print('*'*30,'超时加载','*'*30,'\n\n\n')

    n=1
    for item in get_products():
        print("item is ", item, n)
        n+=1
        #save_to_mongo(item,key)

    print('一共%d条数据' % n)

    if page>1:
        for page in range(2,page+1):
            get_more_page(key,page)

def get_ali_list(url ,data=None):
    chrome_options = Options()
    chrome_options.add_argument('--headless')  # 16年之后，chrome给出的解决办法，抢了PhantomJS饭碗
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--no-sandbox')  # root用户不加这条会无法运行

    browser = webdriver.Chrome(options=chrome_options)
    wait = WebDriverWait(browser, 15)

    print("url is ", url)

    browser.get(url=url, data=data)
    print("页面打开了")
    try:
        button=browser.find_element_by_class_name('identity-cancel')
        button.click()
    except:
        pass

    #input=browser.find_element_by_id('alisearch-keywords')
    #input.send_keys(key)

    #sea_button=browser.find_element_by_id('alisearch-submit')
    #sea_button.click()
    print("关掉可能弹出的页面")
    try:
        button_1=browser.find_element_by_class_name('s-overlay-close-l')
        button_1.click()
    except:
        pass
    try:
        button_deal=browser.find_elements_by_css_selector('.sm-widget-sort.fd-clr.s-widget-sortfilt li')[1]
        button_deal.click()
    except:
        pass
    print("向下滚屏")
    try:
        browser.execute_script('window.scrollTo(0, document.body.scrollHeight)')
        time.sleep(3)
        browser.execute_script('window.scrollTo(0, document.body.scrollHeight)')
        time.sleep(3)
        browser.execute_script('window.scrollTo(0, document.body.scrollHeight)')
        time.sleep(3)
        browser.execute_script('window.scrollTo(0, document.body.scrollHeight)')
        time.sleep(3)

        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR,'#offer60')))
    except :
        print('*'*30,'超时加载','*'*30,'\n\n\n')

    print("获取产品数据")
    print(type(browser.page_source),browser.page_source)
    return
    #return  ali_list(browser.page_source)
    '''
    if page>1:
        for page in range(2,page+1):
            get_more_page(key,page)
    '''

def get_more_page(key,page):
    page_input=browser.find_element_by_class_name('fui-paging-input')
    page_input.clear()
    page_input.send_keys(page)
    button=browser.find_element_by_class_name('fui-paging-btn')
    button.click()
    time.sleep(3)
    browser.execute_script('window.scrollTo(0, document.body.scrollHeight)')
    try:
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR,'#offer60')))
    except :
        print('*'*30,'超时加载','*'*30,'\n\n\n')
    for item in get_products():
        print("item is ", item)
        #save_to_mongo(item,key)


def get_products():
    html=browser.page_source

    return ali_list(html)

    items=doc('.sm-offer .fd-clr .sm-offer-item').items()
    index=0
    for item in items:
        index+=1
        print('*'*50)
        title=item.find('.s-widget-offershopwindowtitle').text().split('\n')
        title=' '.join(title)
        price_a=item.find('.s-widget-offershopwindowprice').text().split('\n')
        price=''.join(price_a[:2])
        deal=''.join(price_a[2:])
        #产品网址
        text=item.find('.s-widget-offershopwindowtitle')
        soup=BeautifulSoup(str(text),'lxml')
        a=soup.select('.s-widget-offershopwindowtitle a')[0]
        url=a['href']
        print(title)
        print(price)
        print(deal)
        print(url)
        yield{
        'title':title,
        'deal':deal,
        'price':price,
        'url':url}

    print(' (●ˇ∀ˇ●) '*5)
    print('一共%d条数据'%index)


def create_variant(aliproduct, shopifyproduct):
    from prs.shop_action import post_product_variant,update_or_create_product
    from shop.models import Shop, ShopifyProduct
    #################################
    # 新创建的主图信息，创建变体需要
    #################################

    shopify_images = shopifyproduct.get("images")


    #print("aliproduct", aliproduct)
    #print("shopifyproduct", shopifyproduct)
    #print("shopify_images", shopify_images)

    ###################################
    # 创建变体
    ###################################
    option_list = json.loads(aliproduct.options)
    ali_image_dict = json.loads(aliproduct.image_dict)
    ali_price_dict = json.loads(aliproduct.price_dict)
    position = 0
    variants_list = []
    price_rate = aliproduct.price_rate
    price_compare_rate = random.uniform(2, 4)
    if len(option_list)==2 :

        for option1 in option_list[0].get("values"):
            for option2 in option_list[1].get("values"):
                # 根据规格-图片地址 字典 找到ali_image_no
                #根据ali_iamge_no 找到shopify image_no
                ali_image_no = ali_image_dict.get(option1,None)
                if ali_image_no is None:
                    shopify_image_no = None
                else:
                    #print("option image_no", option1, ali_image_no)
                    if ali_image_no < len(shopify_images):
                        shopify_image_no = shopify_images[ali_image_no].get("id")
                    else:
                        shopify_image_no = None


                sku = shopifyproduct.get("handle")
                #option1 = option1
                #option2 = option2
                option3 = None

                if option1:
                    sku = sku + "-" + option1.replace("&", '').replace('-', '').replace('.', '').replace(' ', '')
                    if option2:
                        sku = sku + "_" + option2.replace("&", '').replace('-', '').replace('.', '').replace(' ', '')
                        if option3:
                            sku = sku + "_" + option3.replace("&", '').replace('-', '').replace('.', '').replace(' ',
                                                                                                                 '')

                price = float(ali_price_dict.get(option2,0)) * price_rate
                if price == 0:
                    print("没有价格")
                    continue

                variant_item = {
                    "option1": option1,
                    "option2": option2,
                    "option3": option3,
                    "price": int(price),
                    "compare_at_price": int(price* price_compare_rate),
                    "sku": sku,
                    "position": position,
                    "image_id": shopify_image_no,
                    "grams": 0,
                    "title": sku,
                    "taxable": "true",
                    "inventory_management": "shopify",
                    "fulfillment_service": "manual",
                    "inventory_policy": "continue",

                    "inventory_quantity": 10000,
                    "requires_shipping": "true",
                    "weight": 0.5,
                    "weight_unit": "kg",

                }
                # print("variant_item", variant_item)
                variants_list.append(variant_item)
                position += 1

    elif len(option_list)==1:
        for option1 in option_list[0].get("values"):
            # 根据规格-图片地址 字典 找到ali_image_no
            # 根据ali_iamge_no 找到shopify image_no
            ali_image_no = ali_image_dict.get(option1)
            if ali_image_no is None:
                shopify_image_no = None
            else:
                #print("option image_no", option1, ali_image_no)
                if ali_image_no < len(shopify_images) :
                    shopify_image_no = shopify_images[ali_image_no].get("id")
                else:
                    shopify_image_no = None

            sku = sku = shopifyproduct.get("handle")
            #option1 = option1
            option2 = None
            option3 = None
            price = float(ali_price_dict.get(option1,0)) * price_rate
            if price == 0:
                print("没有价格")
                continue

            if option1:
                sku = sku + "-" + option1.replace("&", '').replace('-', '').replace('.', '').replace(' ', '')
                if option2:
                    sku = sku + "_" + option2.replace("&", '').replace('-', '').replace('.', '').replace(' ', '')
                    if option3:
                        sku = sku + "_" + option3.replace("&", '').replace('-', '').replace('.', '').replace(' ',
                                                                                                             '')

            variant_item = {
                "option1": option1,
                "option2": option2,
                "option3": option3,
                "price": int(price),
                "compare_at_price": int(price * price_compare_rate),
                "sku": sku,
                "position": position,
                "image_id": shopify_image_no,
                "grams": 0,
                "title": sku,
                "taxable": "true",
                "inventory_management": "shopify",
                "fulfillment_service": "manual",
                "inventory_policy": "continue",

                "inventory_quantity": 10000,
                "requires_shipping": "true",
                "weight": 0.5,
                "weight_unit": "kg",

            }
            # print("variant_item", variant_item)
            variants_list.append(variant_item)
            position += 1

    dest_shop = "yallasale-com"
    shop_obj = Shop.objects.get(shop_name=dest_shop)

    shop_url = "https://%s:%s@%s.myshopify.com" % (shop_obj.apikey, shop_obj.password, shop_obj.shop_name)
    new_product = post_product_variant(shop_url, shopifyproduct.get("id"), variants_list, option_list)
    if new_product:
        products = []
        products.append(new_product)
        # 插入到系统数据库
        #insert_product(shop_obj.shop_name, products)
        update_or_create_product(shop_obj.shop_name, products)


        print("产品变体发布成功！！！！")
        print(type(new_product),  new_product.get("id"))
        return new_product

    else:

        print("产品变体发布失败！！！！")
        return None


def create_body(aliproduct):
 ################################
    ##############################
    ############可以发布主产品了
    #############################
    from shop.models import Shop, ShopifyProduct
    from prs.shop_action import post_product_main,   update_or_create_product



    dest_shop = "yallasale-com"
    shop_obj = Shop.objects.get(shop_name=dest_shop)

    shop_url = "https://%s:%s@%s.myshopify.com" % (shop_obj.apikey, shop_obj.password, shop_obj.shop_name)

    handle_new = 'b' + str(aliproduct.pk).zfill(4)

    shopify_images = []
    #image_no = 0

    for image in json.loads(aliproduct.images):
        image = {
            "src": image,
            #"image_no": image_no
        }
        shopify_images.append(image)
        #image_no += 1


    params = {
        "product": {
            "handle": handle_new,
            "title": aliproduct.title,
            "body_html": aliproduct.title,
            "vendor": aliproduct.offer_id,
            "product_type": "auto",
            "tags": aliproduct.cate_code.replace("_", ","),
            "images": shopify_images,
            # "variants": variants_list,
            #"options": json.loads(aliproduct.options),
        }
    }
    headers = {
        "Content-Type": "application/json",
        "charset": "utf-8",

    }
    # 初始化SDK
    # shop_obj = Shop.objects.get(shop_name=shop_name)


    url = shop_url + "/admin/products.json"


    print("开始创建主体")
    print(url, json.dumps(params))



    r = requests.post(url, headers=headers, data=json.dumps(params))
    if r.text is None:
        return None
    try:
        data = json.loads(r.text)
        print("创建的新产品",r, data)
    except:
        print("创建产品主体失败")
        print(url, json.dumps(params))
        print(r)
        print(r.text)
        return None
    # print("r is ", r)
    # print("r.text is ", r.text)

    # data = demjson.decode(r.text)
    new_product = data.get("product")

    if new_product:
        products = []
        products.append(new_product)
        # 插入到系统数据库
        #insert_product(shop_obj.shop_name, products)
        update_or_create_product(shop_obj.shop_name, products)
        # 修改handle最大值
        #Shop.objects.filter(shop_name=shop_obj.shop_name).update(max_id=max_id)

        print("产品主体发布成功！！！！")
        #print(type(new_product),  new_product)
        return new_product

    else:

        print("产品主体发布失败！！！！")
        print(data)
        return None

#从神箭手的数据生成ali图片列表
def get_image_list(aliproduct):
    image_list = []
    #先取主图
    for image in json.loads(aliproduct.images):
        image_list.append(image)

    #再取规格图
    for sku in json.loads(aliproduct.sku_info):
        try:
            values = sku.get("values")
            if values is None:
                continue
            for value in values:
                sku_image = value.get("image")
                if  sku_image is not None and sku_image not in image_list:
                        image_list.append(sku_image)
        except:
            continue

    #生成shopify图
    shopify_images = []
    for image in image_list:
        image = {
            "src": image,
            #"image_no": image_no
        }
        shopify_images.append(image)
        #image_no += 1
    return  shopify_images

#这一版是从神箭手转化数据
#即使自己抓，也可以转化成神箭手的格式，后话了
##################################################
def create_body_shenjian(aliproduct):
 ################################
    ##############################
    ############可以发布主产品了
    #############################
    from shop.models import Shop, ShopifyProduct
    from prs.shop_action import post_product_main,   update_or_create_product
    from .models import AliProduct

    dest_shop = "yallasale-com"
    shop_obj = Shop.objects.get(shop_name=dest_shop)

    shop_url = "https://%s:%s@%s.myshopify.com" % (shop_obj.apikey, shop_obj.password, shop_obj.shop_name)

    handle_new = 'b' + str(aliproduct.pk).zfill(5)
    title = fanyi(aliproduct.title_zh)

    #image_no = 0


    shopify_images = get_image_list(aliproduct)

    params = {
        "product": {
            "handle": handle_new,
            "title": title,
            "body_html": title,
            "vendor": aliproduct.offer_id,
            "product_type": "auto",
            "tags": aliproduct.cate_code.replace("_", ","),
            "images": shopify_images,
            # "variants": variants_list,
            #"options": json.loads(aliproduct.options),
        }
    }
    headers = {
        "Content-Type": "application/json",
        "charset": "utf-8",

    }
    # 初始化SDK
    # shop_obj = Shop.objects.get(shop_name=shop_name)


    url = shop_url + "/admin/products.json"


    print("开始创建主体")
    print(url, json.dumps(params))



    r = requests.post(url, headers=headers, data=json.dumps(params))
    if r.text is None:
        return None
    try:
        data = json.loads(r.text)
        print("创建的新产品",r, data)
    except:
        print("创建产品主体失败")
        print(url, json.dumps(params))
        print(r)
        print(r.text)
        return None
    # print("r is ", r)
    # print("r.text is ", r.text)

    # data = demjson.decode(r.text)
    new_product = data.get("product")

    if new_product:
        products = []
        products.append(new_product)
        # 插入到系统数据库
        #insert_product(shop_obj.shop_name, products)
        update_or_create_product(shop_obj.shop_name, products)
        # 修改handle最大值
        #Shop.objects.filter(shop_name=shop_obj.shop_name).update(max_id=max_id)
        #AliProduct.objects.filter(pk=aliproduct.pk).update(title=title,handle = handle_new,publish_error="产品主体发布成功" )
        print("产品主体发布成功！！！！")

        #print(type(new_product),  new_product)
        return new_product

    else:

        print("产品主体发布失败！！！！")
        print(data)
        return None


def create_variant_shenjian(aliproduct, shopifyproduct):
    from prs.shop_action import post_product_variant,update_or_create_product
    from shop.models import Shop, ShopifyProduct
    #################################
    # 新创建的主图信息，创建变体需要
    #################################

    shopify_images = shopifyproduct.get("images")


    #print("aliproduct", aliproduct)
    #print("shopifyproduct", shopifyproduct)
    #print("shopify_images", shopify_images)

    ###################################
    # 创建变体
    ###################################
    shopify_images = shopifyproduct.get("images")

    ali_image_list =[]
    shopify_option_list = []
    ali_image_dict = {}
    for sku in json.loads(aliproduct.sku_info):

        try:
            values = sku.get("values")

            if values is None:
                continue
        except:
            continue


        option_list = []
        for value in values:
            print("5 ###########", value)
            desc_zh = value.get("desc")

            if desc_zh is not None:
                desc = fanyi(desc_zh)
                if desc in option_list:
                    desc = desc + "_" + str(len(option_list))
                option_list.append(desc)
            else:
                continue

            sku_image = value.get("image")

            if sku_image is not None:
                # 规格图片如果不在主图里，也插进列表
                if sku_image not in ali_image_list:
                    ali_image_list.append(sku_image)

                # 规格-图片地址 字典
                ali_image_dict[desc] = ali_image_list.index(sku_image)

        shopify_option ={
            "name" : fanyi(sku.get("label")),
            "values": option_list
        }
        shopify_option_list.append(shopify_option)
    print("1 ############",ali_image_dict,  "\n\n1.1 ##########",ali_image_list)

    price_rate = aliproduct.price_rate
    if price_rate == 0:
        price_rate = 3
    price_compare_rate = random.uniform(2, 4)



    variants_list =[]
    position = 0

    for sku_detail in json.loads(aliproduct.sku_detail):
        print("2 ###############", sku_detail)
        try:
            stock= sku_detail.get("stock")
        except:
            continue
        if stock == 0:
            print("库存为0")
            continue

        try:
            sku= sku_detail.get("sku")
        except:
            continue

        if sku.find(">") >0:
            option1 = fanyi(sku.partition(">")[0])
            option2 = fanyi(sku.partition(">")[2])
            option3 = None
        else:
            option1 = fanyi(sku)
            option2 = None
            option3 = None



        ali_image_no = ali_image_dict.get(option1, None)
        if ali_image_no is None:
            shopify_image_no = None
        else:
            if ali_image_no < len(shopify_images):
                shopify_image_no = shopify_images[ali_image_no].get("id")
            else:
                shopify_image_no = None
        print(ali_image_dict)
        print("3 ##############", option1, option2, ali_image_no, shopify_image_no)


        if sku_detail.get("price") is None:
            price_range = aliproduct.price_range
            if price_range.find("-")>=0:
                print ("here", price_range)
                price = float(price_range.partition("-")[0]) * price_rate
            else:

                price = float(price_range )* price_rate

        else:
            price = float(sku_detail.get("price") )* price_rate

        variant_sku = shopifyproduct.get("handle")
        if option1:
            variant_sku = variant_sku + "-" + option1.replace("&", '').replace('-', '').replace('.', '').replace(' ', '')
            if option2:
                variant_sku = variant_sku + "_" + option2.replace("&", '').replace('-', '').replace('.', '').replace(' ', '')
                if option3:
                    variant_sku = variant_sku + "_" + option3.replace("&", '').replace('-', '').replace('.', '').replace(' ',
                                                                                                                         '')

        variant_item = {
            "option1": option1,
            "option2": option2,
            "option3": option3,
            "price": int(price),
            "compare_at_price": int(price * price_compare_rate),
            "sku": variant_sku,
            "position": position,
            "image_id": shopify_image_no,
            "grams": 0,
            "title": variant_sku,
            "taxable": "true",
            "inventory_management": "shopify",
            "fulfillment_service": "manual",
            "inventory_policy": "continue",

            "inventory_quantity": 10000,
            "requires_shipping": "true",
            "weight": 0.5,
            "weight_unit": "kg",

        }
        print("variant_item", variant_item)
        variants_list.append(variant_item)
        position += 1


    dest_shop = "yallasale-com"
    shop_obj = Shop.objects.get(shop_name=dest_shop)

    shop_url = "https://%s:%s@%s.myshopify.com" % (shop_obj.apikey, shop_obj.password, shop_obj.shop_name)
    new_product = post_product_variant(shop_url, shopifyproduct.get("id"), variants_list, shopify_option_list)
    if new_product:
        products = []
        products.append(new_product)
        # 插入到系统数据库
        #insert_product(shop_obj.shop_name, products)
        update_or_create_product(shop_obj.shop_name, products)


        print("产品变体发布成功！！！！")
        print(type(new_product),  new_product.get("id"))
        return new_product

    else:

        print("产品变体发布失败！！！！")
        return None






#获取页面
def get_lingtin_page(url):
    import time
    import traceback
    from requests.packages import urllib3
    urllib3.disable_warnings()
    r = requests.session()
    n = 0

    #url = ('https://www.lightinthebox.com/p/_p6636997.html')
    #url = (
     #   'https://www.lightinthebox.com/en/p/men-s-athletic-shoes-comfort-pu-tulle-spring-fall-outdoor-athletic-running-lace-up-flat-heel-black-red-gray-dark-blue-under-1in_p5885959.html')
    while ( n < 20):
        try:

            #proxy = get_proxies()
            #proxies = {'https': proxy}
            #print("当前使用的代理是",proxies)
            #proxies= None

            res = r.get(url,    headers=header(), allow_redirects=True)#,proxies=proxies,verify=False,)
            if res.status_code == 200:
                print(res, res.status_code)
                return  res.content

            else:

                print(res, res.status_code, res.headers['Location'])
                #Proxy.objects.filter(ip=proxy).update(active=False)
                '''
                n += 1
                time.sleep(1)
                continue
                '''
                return None

        except Exception as e:  #(ProxyError, ConnectTimeout, SSLError, ReadTimeout, ConnectionError):
            print("代理错误")
            '''
            print('str(Exception):\t', str(Exception))
            print("str(e)", str(e))
            print("repr(e)", repr(e))
            print("traceback.print_exc()", traceback.print_exc())
            print("traceback.format_exc()", traceback.format_exc())
            Proxy.objects.filter(ip=proxy).update(active=False)
            time.sleep(1)
            n += 1
            continue
            '''



    return  None


# 解析页面，获取产品信息
def get_lightin_product_info(SPU, url):
    from .models import AliProduct

    print("开始抓取lightin产品信息 ", url)



    res = get_lingtin_page(url)
    if res is None:
        return "获取页面失败", False

    # debug用
    '''
    with open('funmart.txt', 'wb') as f:
        f.write(res)


    f = open("lightin.txt", "rb")

    res = f.read()
    '''

    htmlEmt = etree.HTML(res)

    #print(htmlEmt)
    #result = etree.tostring(htmlEmt)
    #print(result.decode('utf-8'))



    # 标题

    title_ori = htmlEmt.xpath('//div[@class="widget prod-info-title"]/h1')
    if title_ori:
        title = title_ori[0].text
        item_id = title_ori[0].xpath('.//span[@class="item-id"]')


    else:
        #print("title is empty", offer_id)
        print("title is empty",url)
        return "title is empty", False

    #取面包屑
    breadcrumb_divs = htmlEmt.xpath('//ul[contains(@class,"breadcrumb")]/li')
    breadcrumb_list = []
    for row in breadcrumb_divs:
        #print(etree.tostring(row))
        breadcrumb = row.xpath('.//a/text()')
        if breadcrumb:
            breadcrumb_list.append( " ".join(breadcrumb[0].split()))



    # 取销售价
    currency_div = htmlEmt.xpath('//dl[contains(@class,"prod-i-c-s")]/dt/a/text()')



    price_div = htmlEmt.xpath('//strong[contains(@class,"sale-price")]')



    if price_div:

        price = price_div[0].text.split()
        sale_price = price[0].replace("$","").replace(",","")

    else:
        print("price is empty",url)
        return "price is empty", False


    # 取主图

    images_list = []
    images_dict = {}
    divs = htmlEmt.xpath('//div[@class="viewport"]')
    if divs:
        img_div = divs[0].xpath('.//div/div')
        if not img_div:
            img_div = divs[0].xpath('.//ul/li')

        for row in img_div:
            image_id = row.attrib.get("id").split("_")[1]
            img = row.xpath('.//img')[0].attrib.get('data-normal')
            images_dict[image_id] = img
            if img not in images_list:
                images_list.append(img)

        #src = row.attrib.get('src')
        #attribute_id = row.attrib.get('attribute_id')

    #取隐藏的sku图
    divs = htmlEmt.xpath('//div[@class="image-sku-list hide"]')
    if divs:

        img_div = divs[0].xpath('.//li')
        print("隐藏的sku图", img_div)

        for row in img_div:
            image_id = row.attrib.get("id").split("_")[1]
            img = row.xpath('.//img')[0].attrib.get('data-normal')
            images_dict[image_id] = img
            if img not in images_list:
                images_list.append(img)


        # src = row.attrib.get('src')
        # attribute_id = row.attrib.get('attribute_id')



    # 取sku属性-图对应记录
    divs = htmlEmt.xpath('//li[contains(@class,"attr-v-show-img")]')
    attr_image_dict = {}
    if divs:
        sku_divs = divs[0].xpath('.//div/span')
        for sku_div in sku_divs:
            image_id = sku_div.attrib.get("image-id")
            attr_string = sku_div.xpath('string()')
            if attr_string:
                attr = attr_string.split()[0]
                attr_image_dict[attr] = image_id
    else:
        #另一种方式去属性-图对应记录
        divs = htmlEmt.xpath('//li[contains(@class,"attr-v-show")]')
        print("另一种属性 ",divs)
        if divs:
            sku_divs = divs[0].xpath('.//div/span')
            print("属性值", sku_divs)
            for sku_div in sku_divs:
                image_id = sku_div.attrib.get("image-id")
                attr = sku_div.attrib.get("data-content")
                attr_image_dict[attr] = image_id



    #更新产品记录
    Lightin_SPU.objects.update_or_create(
        SPU=SPU,
        defaults={
            'title': title,
            'images': json.dumps(images_list),
            'images_dict': json.dumps(images_dict),
            'attr_image_dict': json.dumps(attr_image_dict),
            'breadcrumb': json.dumps(breadcrumb_list),
            'currency': currency_div[0],
            "sale_price": sale_price,

            "got": True,
            "got_time": dt.now()

        }
    )
    return "", True

# 解析页面，获取产品信息
def get_tomtop_product_info(SPU, url):
    from .models import AliProduct

    print("开始抓取tomtop产品信息 ", url)



    res = get_lingtin_page(url)
    if res is None:
        return "获取页面失败", False

    # debug用
    '''
    with open('tomtop.txt', 'wb') as f:
        f.write(res)


    f = open("lightin.txt", "rb")

    res = f.read()
    '''

    htmlEmt = etree.HTML(res)

    #print(htmlEmt)
    #result = etree.tostring(htmlEmt)
    #print(result.decode('utf-8'))

    return  htmlEmt

    # 标题

    title_ori = htmlEmt.xpath('//div[contains(@class,"prod-info-title")]/h1')
    if title_ori:
        title = title_ori[0].text
        item_id = title_ori[0].xpath('.//span[@class="item-id"]')


    else:
        #print("title is empty", offer_id)
        print("title is empty",url)
        return "title is empty", False

    #取面包屑
    breadcrumb_divs = htmlEmt.xpath('//ul[contains(@class,"breadcrumb")]/li')
    breadcrumb_list = []
    for row in breadcrumb_divs:
        #print(etree.tostring(row))
        breadcrumb = row.xpath('.//a/text()')
        if breadcrumb:
            breadcrumb_list.append( " ".join(breadcrumb[0].split()))



    # 取销售价
    currency_div = htmlEmt.xpath('//dl[contains(@class,"prod-i-c-s")]/dt/a/text()')



    price_div = htmlEmt.xpath('//strong[contains(@class,"sale-price")]')



    if price_div:

        price = price_div[0].text.split()
        sale_price = price[0].replace("$","").replace(",","")

    else:
        print("price is empty",url)
        return "price is empty", False


    # 取主图

    images_list = []
    images_dict = {}
    divs = htmlEmt.xpath('//div[@class="viewport"]')
    if divs:
        img_div = divs[0].xpath('.//div/div')
        if not img_div:
            img_div = divs[0].xpath('.//ul/li')

        for row in img_div:
            image_id = row.attrib.get("id").split("_")[1]
            img = row.xpath('.//img')[0].attrib.get('data-normal')
            images_dict[image_id] = img
            images_list.append(img)

        #src = row.attrib.get('src')
        #attribute_id = row.attrib.get('attribute_id')


    # 取sku图
    divs = htmlEmt.xpath('//li[contains(@class,"attr-v-show-img")]')
    attr_image_dict = {}
    if divs:
        sku_divs = divs[0].xpath('.//div/span')
        for sku_div in sku_divs:
            image_id = sku_div.attrib.get("image-id")
            attr_string = sku_div.xpath('string()')
            if attr_string:
                attr = attr_string.split()[0]
                attr_image_dict[attr] = image_id


    '''
    #更新产品记录
    Lightin_SPU.objects.update_or_create(
        SPU=SPU,
        defaults={
            'title': title,
            'images': json.dumps(images_list),
            'images_dict': json.dumps(images_dict),
            'attr_image_dict': json.dumps(attr_image_dict),
            'breadcrumb': json.dumps(breadcrumb_list),
            'currency': currency_div[0],
            "sale_price": sale_price,

            "got": True,
            "got_time": dt.now()

        }
    )
    '''

    return "", True


#这一版是从神箭手转化数据
#即使自己抓，也可以转化成神箭手的格式，后话了
##################################################
def create_body_lightin(lightin_spu):
 ################################
    ##############################
    ############可以发布主产品了
    #############################
    from shop.models import Shop, ShopifyProduct
    from prs.shop_action import post_product_main,   update_or_create_product
    from .models import AliProduct

    dest_shop = "yallasale-com"
    shop_obj = Shop.objects.get(shop_name=dest_shop)

    shop_url = "https://%s:%s@%s.myshopify.com" % (shop_obj.apikey, shop_obj.password, shop_obj.shop_name)

    handle_new = 'l' + str(lightin_spu.pk).zfill(6)

    if lightin_spu.title:
        title = lightin_spu.title
    else:
        title = lightin_spu.en_name + " [" + lightin_spu.handle + "]"

    #生成shopify图
    shopify_images = []

    if lightin_spu.images :
        image_list =  json.loads(lightin_spu.images)
        for image in image_list:
            image = {
                "src": image,
                #"image_no": image_no
            }
            shopify_images.append(image)




    params = {
        "product": {
            "handle": handle_new,
            "title": title,
            "body_html": title,
            "vendor": lightin_spu.SPU,
            "product_type": "auto",
            "tags": "%s,%s,%s" %(lightin_spu.cate_1, lightin_spu.cate_2,lightin_spu.cate_3),
            #"images": shopify_images,
            # "variants": variants_list,
            #"options": json.loads(aliproduct.options),
        }
    }
    headers = {
        "Content-Type": "application/json",
        "charset": "utf-8",

    }
    # 初始化SDK
    # shop_obj = Shop.objects.get(shop_name=shop_name)


    url = shop_url + "/admin/products.json"


    print("开始创建主体")
    print(url, json.dumps(params))



    r = requests.post(url, headers=headers, data=json.dumps(params))
    if r.text is None:
        return None
    try:
        data = json.loads(r.text)
        print("创建的新产品",r, data)
    except:
        print("创建产品主体失败")
        print(url, json.dumps(params))
        print(r)
        print(r.text)
        return None
    # print("r is ", r)
    # print("r.text is ", r.text)

    # data = demjson.decode(r.text)
    new_product = data.get("product")

    if new_product:
        products = []
        products.append(new_product)
        # 插入到系统数据库
        #insert_product(shop_obj.shop_name, products)
        update_or_create_product(shop_obj.shop_name, products)
        # 修改handle最大值
        #Shop.objects.filter(shop_name=shop_obj.shop_name).update(max_id=max_id)
        #AliProduct.objects.filter(pk=aliproduct.pk).update(title=title,handle = handle_new,publish_error="产品主体发布成功" )
        print("产品主体发布成功！！！！")

        #print(type(new_product),  new_product)
        return new_product

    else:

        print("产品主体发布失败！！！！")
        print(data)
        return None

def create_variant_lightin(lightin_spu):

    from prs.shop_action import post_product_variant,update_or_create_product
    from shop.models import Shop, ShopifyProduct


    lightin_skus = Lightin_SKU.objects.filter(SPU = lightin_spu.SPU)
    shopifyproduct = ShopifyProduct.objects.get(vendor = lightin_spu.SPU )

    ###################################
    # 创建变体
    ###################################



    shopify_option_list = []
    variants_list =[]
    position = 0

    for sku in lightin_skus:
        print(sku.skuattr)

        option_sets = sku.skuattr.split(";")
        n=1
        option1 = ""
        option2 = ""
        option3 = ""

        for option_set in option_sets:
            if option_set.find("=")>0:
                option_name, option_value = option_set.split("=")

                find_flag = 0
                for row in shopify_option_list:
                    if option_name == row.get("name"):
                        values = row.get("values")
                        if option_value not in values:

                            values.append(option_value)
                        find_flag=1
                        break

                if  find_flag == 0:
                    values = []
                    values.append(option_value)
                    option = {
                        "name" : option_name,
                        "values" : values
                    }
                    shopify_option_list.append(option)

                if n == 1:
                    option1 = option_value
                elif n == 2:
                    option2 = option_value
                elif n == 3:
                    option3 = option_value

                n += 1


        variant_item = {
            "option1": option1,
            "option2": option2,
            "option3": option3,
            "price": int(sku.vendor_supply_price * 5.63),
            "compare_at_price": int(sku.vendor_sale_price * 5.63 ),
            "sku": sku.SKU,
            "barcode": sku.barcode,
            "position": position,

            "grams": sku.weight,

            "taxable": "true",
            "inventory_management": "shopify",
            "fulfillment_service": "manual",
            "inventory_policy": "continue",

            "inventory_quantity": sku.quantity,
            "requires_shipping": "true",
            "weight": sku.weight,
            "weight_unit": "kg",

        }
        print("variant_item", variant_item)
        variants_list.append(variant_item)
        position += 1


    dest_shop = "yallasale-com"
    shop_obj = Shop.objects.get(shop_name=dest_shop)

    shop_url = "https://%s:%s@%s.myshopify.com" % (shop_obj.apikey, shop_obj.password, shop_obj.shop_name)
    new_product = post_product_variant(shop_url, shopifyproduct.product_no, variants_list, shopify_option_list)
    if new_product:
        products = []
        products.append(new_product)
        # 插入到系统数据库
        #insert_product(shop_obj.shop_name, products)
        update_or_create_product(shop_obj.shop_name, products)


        print("产品变体发布成功！！！！")
        print(type(new_product),  new_product.get("id"))
        return new_product

    else:

        print("产品变体发布失败！！！！")
        return None


def chrome_get_url(url ,data=None):
    chrome_options = Options()
    chrome_options.add_argument('--headless')  # 16年之后，chrome给出的解决办法，抢了PhantomJS饭碗
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--no-sandbox')  # root用户不加这条会无法运行

    browser = webdriver.Chrome(options=chrome_options)
    wait = WebDriverWait(browser, 15)

    print("url is ", url)

    #browser.get(url=url, data=data)
    browser.get(url=url)
    html=browser.page_source


    with open('funmart.txt', 'w') as f:
        f.write(html)

    #input_third = browser.find_element_by_xpath('//*[@class="price"]')

    #print(input_third)

    print(html)

    browser.close()

