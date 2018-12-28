import shenjian

user_key = "2aaa34471b-NjVhNDllMj"
user_secret = "kyYWFhMzQ0NzFiNj-63e08890b765a49"
appID = 3166948

service = shenjian.Service(user_key,user_secret)

#创建爬虫类shenjian.Crawler
crawler = shenjian.Crawler(user_key,user_secret,appID)
#用2个节点启动爬虫
result = crawler.start(1)
#停止爬虫
result = crawler.stop()
#获取爬虫状态
result = crawler.get_status()

result = crawler.config_custom(params)