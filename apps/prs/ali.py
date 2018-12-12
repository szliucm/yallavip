import json,time,datetime,requests,random
#import pymysql,re
from prettytable import PrettyTable
from bs4 import BeautifulSoup
from multiprocessing import Process
import  re
import requests
from lxml import etree




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

    cookie = open('cookie.txt', 'r').readlines()[1].replace('\n', '').replace(' ', '')

    headers = {
               'Connection': 'keep-alive',
               'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.181 Safari/537.36',

               'Accept-Encoding': 'gzip, deflate, br',
               'Accept-Language': 'zh-CN,zh;q=0.9',
               'Cookie': cookie}
    return headers



# 发出请求
def request(url):
    r = requests.session()
    r = r.get(url, headers=header(), allow_redirects=False)
    return r

def fanyi(data):
    return requests.post('https://fanyi.baidu.com/transapi', data={"query": data, 'from': 'zh', 'to': 'en'}).json()['data'][0]['dst']

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



    for vendor in vendors:
        #print("type  vendor",type(vendor), etree.tostring(vendor))
        offer_id = vendor.attrib.get('offerid')
        print("type  offer_id",type(offer_id), offer_id)

# 1688offer
def list_ali_product(offer_id,  max_id, shop_obj):
    from shop.models import Shop, ShopifyProduct
    from prs.shop_action import post_product_main, post_product_variant,insert_product

    #dest_shop = "yallasale-com"
    #shop_obj = Shop.objects.get(shop_name=dest_shop)

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
        print("type  div", type(div), div)
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
        print("title is empty")
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

        print("产品发布成功！！！！" )

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

    posted = post_product_variant(shop_url, new_product.get("product_no"), variants_list, option_list)


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
    table.add_row([sellerNick,offer_id,fav,old_price, price, sku_count, confirmGoodsCount, soldTotalCount,total, normal,goodFull,bad,tryRepotr,pic,additional,str(datetime.datetime.now())[:19]])
    print(table)
    # 数据存储
    classify = 'other_details(sellername, sellerid, 渠道,offer_id, title, fav, oldprice, saleprice, speCount, 成交数, 总数, 评价数, 中评, 好评, 差评, 试用, pic, additional, now_time)'
    values = (sellerNick,sellerId,channel, offer_id,title,fav,old_price, price, sku_count, confirmGoodsCount, soldTotalCount,total, normal,goodFull,bad,tryRepotr,pic,additional,str(datetime.datetime.now())[:19])
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
    table.add_row([sellerNick,offer_id,fav,old_price, price, sku_count, confirmGoodsCount, soldTotalCount,total, normal,goodFull,bad,tryRepotr,pic,additional,str(datetime.datetime.now())[:19]])
    print(table)
    # 数据存储
    classify = 'other_details(sellername, sellerid, 渠道,offer_id, title, fav, oldprice, saleprice, speCount, 成交数, 总数, 评价数, 中评, 好评, 差评, 试用, pic, additional, now_time)'
    values = (sellerNick,sellerId,channel, offer_id,title,fav,old_price, price, sku_count, confirmGoodsCount, soldTotalCount,total, normal,goodFull,bad,tryRepotr,pic,additional,str(datetime.datetime.now())[:19])
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
chrome_options = Options()
chrome_options.add_argument('--headless')  # 16年之后，chrome给出的解决办法，抢了PhantomJS饭碗
chrome_options.add_argument('--disable-gpu')
chrome_options.add_argument('--no-sandbox')  # root用户不加这条会无法运行

browser = webdriver.Chrome(options=chrome_options)
wait=WebDriverWait(browser,15)

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

    ali_list(html)
    return
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





