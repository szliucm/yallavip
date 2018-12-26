from selenium import webdriver
import time
chromedriver = "C:/chrome/chromedriver"

#chrome_options = Options()
#chrome_options.add_argument('--headless')  # 16年之后，chrome给出的解决办法，抢了PhantomJS饭碗
#chrome_options.add_argument('--disable-gpu')
#chrome_options.add_argument('--disable-dev-shm-usage')
#chrome_options.add_argument('--no-sandbox')  # root用户不加这条会无法运行
#chrome_options.add_argument('blink-settings=imagesEnabled=false')

chromeOptions = webdriver.ChromeOptions()
chromeOptions.add_argument("--proxy-server=http://66.42.110.94:8888")
url= 'https://www.baidu.com'
driver = webdriver.Chrome(chromedriver,chrome_options = chromeOptions)
driver.get(url)
time.sleep(60)