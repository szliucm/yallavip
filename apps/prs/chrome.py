from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
import time

from lxml import etree



def get_ali_list(url):
    '''
    url = 'https://www.1688.com/'
    print("url is ", url)
    '''
    chrome_options = Options()
    chrome_options.add_argument('--headless')  # 16年之后，chrome给出的解决办法，抢了PhantomJS饭碗
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--no-sandbox')  # root用户不加这条会无法运行
    chrome_options.add_argument('blink-settings=imagesEnabled=false')

    c_service = Service('/usr/bin/chromedriver')
    c_service.command_line_args()
    c_service.start()

    browser = webdriver.Chrome(options=chrome_options)
    wait = WebDriverWait(browser, 60)

    print("准备打开页面")
    browser.get(url=url)
    print("页面打开了")
    try:
        button=browser.find_element_by_class_name('identity-cancel')
        button.click()
    except:
        pass



    # 定位搜索框
    #input=browser.find_element_by_id('alisearch-keywords')

    #input = browser.find_element_by_class_name('sm-widget-input')
    #input.send_keys(keywords)
    # 定位搜索按钮
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

    try:
        button_deal=browser.find_elements_by_css_selector('.sm-widget-sort.fd-clr.s-widget-sortfilt li')[1]
        button_deal.click()
    except:
        pass


    html = browser.page_source
    with open('ali.txt', 'w') as f:
        f.write(html)

    try:
        print("向下滚屏")
        browser.execute_script('window.scrollTo(0, document.body.scrollHeight)')
        time.sleep(3)
        print("向下滚屏")
        browser.execute_script('window.scrollTo(0, document.body.scrollHeight)')
        time.sleep(3)
        print("向下滚屏")
        browser.execute_script('window.scrollTo(0, document.body.scrollHeight)')
        time.sleep(3)
        print("向下滚屏")
        browser.execute_script('window.scrollTo(0, document.body.scrollHeight)')
        time.sleep(3)

        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR,'#offer60')))
    except :
        print('*'*30,'超时加载','*'*30,'\n\n\n')

    print("获取产品数据")
    #print(type(browser.page_source),browser.page_source)
    #return
    html = browser.page_source
    browser.quit()
    c_service.stop()
    return  ali_list(html)
    '''
    if page>1:
        for page in range(2,page+1):
            get_more_page(key,page)
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

        price_div = vendor.xpath('.//span[@class="sm-offer-priceNum sw-dpl-offer-priceNum"]')
        price = price_div.attrib.get('title')

        print("type  offer_id",type(offer_id), offer_id,price)
    return  vendor_list