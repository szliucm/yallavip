# Create your tasks here
from __future__ import absolute_import, unicode_literals
import numpy as np, re
from celery import shared_task,task
from django.db.models import Q,Count
import requests
import json
import random
from django.utils import timezone as datetime
from django.utils import timezone as dt



from .models import *
from shop.models import  Shop, ShopifyProduct, ShopifyVariant, ShopifyImage, ShopifyOptions
from shop.models import ProductCategoryMypage
from fb.models import MyPage, MyAlbum
from .shop_action import sync_shop
from orders.models import Order, OrderDetail,OrderDetail_lightin


my_app_id = "562741177444068"
my_app_secret = "e6df363351fb5ce4b7f0080adad08a4d"
my_access_token = "EAAHZCz2P7ZAuQBABHO6LywLswkIwvScVqBP2eF5CrUt4wErhesp8fJUQVqRli9MxspKRYYA4JVihu7s5TL3LfyA0ZACBaKZAfZCMoFDx7Tc57DLWj38uwTopJH4aeDpLdYoEF4JVXHf5Ei06p7soWmpih8BBzadiPUAEM8Fw4DuW5q8ZAkSc07PrAX4pGZA4zbSU70ZCqLZAMTQZDZD"

DEBUG = False

if DEBUG:
    warehouse_code = "TW02"
    shipping_method =  "L002-KSA-TEST",
    appToken = "85413bb8f6a270e1ff4558af80f2bef5"
    appKey = "9dca0be4c02bed9e37c1c4189bc1f41b"
else:
    warehouse_code = "W07"
    shipping_method =  "FETCHR_SAUDI_DOM"
    appToken = "909fa3df3b98c26a9221774fe5545afd"
    appKey = "b716b7eb938e9a46ad836e20de0f8b07"

def get_token(target_page,token=None):


    url = "https://graph.facebook.com/v3.2/{}?fields=access_token".format(target_page)
    param = dict()
    if token is None:
        param["access_token"] = my_access_token
    else:
        param["access_token"] = token

    r = requests.get(url, param)

    data = json.loads(r.text)

    # print("request response is ", data["access_token"])
    return data["access_token"]



#更新ali产品数据，把vendor和产品信息连接起来
@shared_task
def update_myproductali():
    dest_shop = "yallasale-com"
    sync_shop(dest_shop)
    products = MyProductAli.objects.filter()

    for ali_product in products:

        #从链接获取供应商编号
        url = ali_product.url
        vendor_no = url.partition(".html")[0].rpartition("/")[2]
        print("url %s vendor_no %s" % (url, vendor_no))

        #用供应商编号获取产品信息
        product =  ShopifyProduct.objects.filter(vendor__exact = vendor_no,shop_name=dest_shop ).first()
        print("product", product)
        print("vendor", vendor_no)

        #在爆款管理中创建记录，并连接爆款记录和ali产品记录
        if product:
            obj, created= MyProductShopify.objects.update_or_create(
                            vendor_no=vendor_no,
                defaults={
                    "product_no" : product.product_no,
                    "handle":product.handle,
            }

            )

            MyProductAli.objects.filter(pk=ali_product.pk).update(

                vendor_no=vendor_no,
                posted_mainshop = True,
                handle=product.handle,
                product_no =  product.product_no,


            )


    return True

#从沙特站发布产品到主站
@shared_task
def post_to_mainshop():
    from .shop_action import post_new_product

    dest_shop = "yallasale-com"
    ori_shop = "yallavip-saudi"

    #先分别同步源站和目标站的数据
    sync_shop(ori_shop)
    sync_shop(dest_shop)

    product_init = ShopifyProduct.objects.filter(Q(handle__startswith='a'),shop_name=dest_shop).order_by('-product_no').first()
    print("主店最新的产品是 %s handle 是%s  供应商是 %s" % (product_init, product_init.handle, product_init.vendor))
    handle_i = product_init.handle

    handle_i = int(handle_i[1:5])
    print("handle_i %s"%(handle_i))


    latest_ori_product =  ShopifyProduct.objects.filter(shop_name=ori_shop, vendor=product_init.vendor).order_by('-product_no').first()
    print("沙特站最后更新的产品是 %s 供应商是 %s,product_no is %d "%(latest_ori_product, latest_ori_product.vendor , latest_ori_product.product_no))

    ori_products = ShopifyProduct.objects.filter(shop_name=ori_shop, product_no__gt = latest_ori_product.product_no).order_by('product_no')

    total_to_update = len(ori_products)
    print("沙特站最新的还有 %d 需要发布" % (total_to_update))

    # 初始化SDK
    #shop_obj = Shop.objects.get(shop_name=dest_shop)
    #shop_url = "https://%s:%s@%s.myshopify.com" % (shop_obj.apikey, shop_obj.password, shop_obj.shop_name)


    for ori_product in ori_products:
        handle_i = handle_i + 1
        handle_new = "A" + str(handle_i).zfill(4)

        #####################
        new_product = post_new_product(dest_shop, ori_product, handle_new)
        ####################

        total_to_update = total_to_update - 1
        print("沙特站最新的还有 %d 需要发布" % (total_to_update))



    #上传完后整体更新目标站数据
    sync_shop(dest_shop)

#把拒签且未上架的产品发布到主站
@shared_task
def rejected_package():

    from logistic.models import  Package

    from .shop_action import create_package_sku

    dest_shop = "yallasale-com"
    discount = 0.9
    min_product_no = 999999999999999

    packages = Package.objects.filter(deal="REFUSED",resell_status="NONE" )
    n=0

    for package in packages:
        order = Order.objects.filter(logistic_no=package.logistic_no).first()
        print("order",  order)
        if not order:
            print("cannot find the order",package.logistic_no )
            continue

        product_no,sku_created = create_package_sku(dest_shop, order, discount)



        if sku_created:
            if product_no < min_product_no:
                min_product_no = product_no



            Package.objects.filter(pk=package.pk).update(resell_status="LISTING")

        n =n+1
        if n>10:
            break
        else:
            print("******", n)

    # 上传完后整体更新目标站数据
    sync_shop(dest_shop, min_product_no)


    return  True

#对过账，已退仓的上架二次销售
#把拒签且未上架的产品发布到主站
@shared_task
def returned_package():

    from logistic.models import  Package

    from .shop_action import create_package_sku

    dest_shop = "yallasale-com"
    discount = 0.9
    min_product_no = 999999999999999

    packages = Package.objects.filter(yallavip_package_status = 'RETURNED', resell_status = "NONE" )
    print("packages is ", packages)

    for package in packages:
        order = Order.objects.filter(logistic_no=package.logistic_no).first()
        print("order",  order)
        if not order:
            print("cannot find the order",package.logistic_no )
            continue

        product_no,sku_created = create_package_sku(dest_shop, order, discount)
        print(order,"created", product_no)


        if sku_created:
            if product_no < min_product_no:
                min_product_no = product_no



            Package.objects.filter(pk=package.pk).update(resell_status="LISTING")
        '''
        n =n+1
        if n>10:
            break
        else:
            print("******", n)
        '''

    # 上传完后整体更新目标站数据
    sync_shop(dest_shop, min_product_no)


    return  True

#生成海外仓包裹的视频
@shared_task
def package_video():
    from .video import  get_order_video
    packages = MyProductPackage.objects.all()
    n = 0
    for package in packages:
        order = Order.objects.get(order_no = package.product_no)
        get_order_video(order)
        n=n+1
        if n >5:
            break

#生成海外仓包裹的视频,使用Facebook的接口，上传图片直接生成slideshow
@shared_task
def package_slideshow():
    from .video import  get_order_slideshow

    #package = MyProductPackage.objects.all().order_by("order_no").first()
    packages = MyProductPackage.objects.all()
    print("packages", packages)
    package = packages.first()
    order = Order.objects.filter(order_no = package.order_no).first()
    get_order_slideshow(order)

#同步海外仓包裹的状态，已经发布到主站的信息，更新到prs里
@shared_task
def package_sync():
    from .shop_action import sycn_package

    sycn_package()
    return

#扫描feed，匹配到产品
@shared_task
def feed_sync_product():
    from .fb_action import sycn_feed_product

    sycn_feed_product()
    return

@shared_task
def ad_sync_product():
    from .fb_action import sycn_ad_product

    sycn_ad_product()
    return

@shared_task
def post_ali_mainshop():
    from .shop_action import post_ali

    post_ali()
    return


############################
#从沙特站发布产品到主站
############################
@shared_task
def post_saudi_mainshop():
    from .shop_action import post_saudi

    post_saudi()

    return

############################
#
#随机选有动销的产品动图到活跃的page
#
############################
'''
@shared_task
def product_feed():
    from .fb_action import post_product_feed

    post_product_feed()

    return

'''


#####################################
#########把创意发到feed
######################################
@shared_task
def creative_feed():
    from .fb_action import post_creative_feed

    post_creative_feed()
    return

#####################################################################
######把shopify产品库中的还未添加到fb产品库的产品按page对应的品类找出来并添加
#######准备工作，每次从1688上新到shopify后调用一次即可
######################################################################
@shared_task
def product_shopify_to_fb():


    #找出所有活跃的page
    pages = MyPage.objects.filter(active=True)
    n = 0
    for page in pages:
        #遍历page对应的品类
        print("page is ",page)
        cates = ProductCategoryMypage.objects.filter(mypage__pk = page.pk)
        for cate in cates:
            cate_code = cate.productcategory.code
            album_name = cate.album_name
            print(cate_code)
            #根据品类找未添加到fb产品库的产品

            #products_to_add = ShopifyProduct.objects.filter(category_code = cate_code,
            #                                                handle__startswith='a',myfb_product__isnull= True ,)

             #SELECT * FROM shop_shopifyproduct  A WHERE  category_code = "WOMEN_Bags_Handbags" and handle like 'a%' and id  NOT  IN  ( SELECT  B.myproduct_id FROM prs_myfbproduct B where mypage_id=14) order by created_at desc

            handle_like = 'a%'
            products_to_add = ShopifyProduct.objects.raw('SELECT * FROM shop_shopifyproduct  A WHERE '
                                                         'category_code = %s and handle like %s '  
                                                         'and id  NOT  IN  ( SELECT  B.myproduct_id FROM prs_myfbproduct B where mypage_id=%s) order by published_at ',[cate_code,handle_like,page.pk])

            #products_to_add = ShopifyProduct.objects.filter(category_code = cate_code)
            print("products_to_add", products_to_add)
            #print("products_to_add query", products_to_add.query)

            myfbproduct_list = []
            for product_to_add in products_to_add:
                n += 1
                print("     %d is %s"%(n,product_to_add))

                myfbproduct = MyFbProduct(
                    myproduct= ShopifyProduct.objects.get(pk=product_to_add.pk ),
                    mypage=MyPage.objects.get(pk=page.pk ),
                    obj_type="PHOTO",
                    cate_code=cate_code,
                    album_name=album_name,

                )
                myfbproduct_list.append(myfbproduct)

            MyFbProduct.objects.bulk_create(myfbproduct_list)




#发布产品到Facebook的album
@shared_task
def sync_album_fbproduct():
    from fb.models import MyPhoto


    #选择所有可用的page
    mypages = MyPage.objects.filter(active=True)
    print(mypages)
    for mypage in mypages:

        print("当前处理主页", mypage, mypage.pk)
        fbproducts = MyFbProduct.objects.filter(mypage__pk = mypage.pk,published=False)
        for fbproduct in fbproducts:
            photos = MyPhoto.objects.filter(page_no=mypage.page_no,name__icontains=fbproduct.myproduct.handle)
            print("处理 %s   %d  ", fbproduct.myproduct.handle,photos.count() )
            if photos.count() >0:
                photo = photos.first()
                MyFbProduct.objects.filter(mypage__pk=mypage.pk, myproduct__pk = fbproduct.myproduct.pk).update(
                                published=True,
                                fb_id = photo.photo_no,
                                publish_error=photos.count(),
                                published_time=photo.created_time,
                )

################################################
##########
################################################
# 根据链接列表抓取1688数据
@shared_task
def get_ali_list():
    from .ali import get_ali_product_info
    aliproducts = MyProductAli.objects.filter(posted_mainshop=False, active=True)
    print("一共有%d 个1688链接待处理"%(aliproducts.count()))

    for aliproduct in aliproducts:
        offer_id = aliproduct.url.partition(".html")[0].rpartition("/")[2]
        cate_code = aliproduct.myproductcate.code
        message,status=get_ali_product_info(offer_id, cate_code)
        if status:
            MyProductAli.objects.filter(pk=aliproduct.pk).update(posted_mainshop=True)
        else:
            MyProductAli.objects.filter(pk=aliproduct.pk).update(post_error=message)


#1.根据类目关键词抓取1688产品列表(offerid,cate_code)
@shared_task
def ali_cate_get_list():
    from .chrome import get_ali_list
    from .ali import get_cate_url
    from shop.models import ProductCategory
    cates = ProductCategory.objects.filter(~Q(keywords=""),keywords__isnull=False )

    print("beging to scan  cate")
    for cate in cates:

        url = get_cate_url(cate.keywords)

        print("url is ", url)
        if url is None or len(url) < 10:
            continue
        vendor_list = get_ali_list(url)

        for vendor_no in vendor_list:
            AliProduct.objects.update_or_create(
                offer_id=vendor_no,
                defaults={
                    "cate_code": cate.code
                }
            )
    return

#################################
# 2.0 神箭手版抓1688产品详情
################################
#根据1688产品列表抓取产品详细信息（标题，规格，图片，价格）
@shared_task
def ali_list_get_info_shenjian():
    import shenjian

    user_key = "2aaa34471b-NjVhNDllMj"
    user_secret = "kyYWFhMzQ0NzFiNj-63e08890b765a49"
    appID = 3166948

    #service = shenjian.Service(user_key, user_secret)

    # 创建爬虫类shenjian.Crawler
    crawler = shenjian.Crawler(user_key, user_secret, appID)

    # 获取爬虫状态
    result = crawler.get_status()
    if result.get("code") == 0:
        status = result["data"]["status"]
    else:
        status = "error"
        reason = result["reason"]

    if status == "stopped":
        print("爬虫已停止, 准备开始新一轮爬取")
        #先抓供应商提供的产品列表


        aliproducts = AliProduct_vendor.objects.filter(got=False)[:100]
        url_list = []

        if  aliproducts.exists():
            #url_list = aliproducts.values_list('ali_url', flat=True)

            for aliproduct in aliproducts:
                url_list.append(aliproduct.ali_url)
                AliProduct_vendor.objects.filter(pk=aliproduct.pk).update(got=True)

        else:
            print("供应商提供的产品列表没有需要爬取的了")


            #抓类目生成的列表
            aliproducts = AliProduct.objects.filter(created = False, started=False)[:100]

            #print("一共有%d 个1688产品信息待抓取"%(aliproducts.count()))
            url_list = []
            for aliproduct in aliproducts:
                url_list.append("https://detail.1688.com/offer/%s.html"%(aliproduct.offer_id))
                AliProduct.objects.filter(pk=aliproduct.pk).update(started=True)



        params= {}

        #params["crawlType"] = 3
        params["productUrl[]"] = url_list
        #params["crawlDetail"] = False

        # 创建爬虫类shenjian.Crawler
        crawler = shenjian.Crawler(user_key, user_secret, appID)
        try:
            print("自定义设置")
            result = crawler.config_custom(params)
        except Exception as e:
            print("自定义设置出错",str(e))
            return  False


        print("爬虫自定义设置结果", result)

        result = crawler.start()
        print("爬虫启动", result)
    else:
        print("爬取中，等待")

    return  True

#根据1688产品列表抓取产品详细信息（标题，规格，图片，价格）
@shared_task
def ali_url_get_info_shenjian():
    import shenjian

    user_key = "2aaa34471b-NjVhNDllMj"
    user_secret = "kyYWFhMzQ0NzFiNj-63e08890b765a49"
    appID = 3166948

    #service = shenjian.Service(user_key, user_secret)

    # 创建爬虫类shenjian.Crawler
    crawler = shenjian.Crawler(user_key, user_secret, appID)

    # 获取爬虫状态
    result = crawler.get_status()
    if result.get("code") == 0:
        status = result["data"]["status"]
    else:
        status = "error"
        reason = result["reason"]

    if status == "stopped":
        print("爬虫已停止, 准备开始新一轮爬取")
        ali_urls = AliProduct_vendor.objects.filter(got = False).values_list('ali_url', flat=True)[:100]
        if not ali_urls.exists():
            print("没有需要爬取的了")
            return False

        #print("一共有%d 个1688产品信息待抓取"%(aliproducts.count()))

        params= {}

        #params["crawlType"] = 3
        params["productUrl[]"] = ali_urls
        #params["crawlDetail"] = False

        # 创建爬虫类shenjian.Crawler
        crawler = shenjian.Crawler(user_key, user_secret, appID)
        try:
            print("自定义设置")
            result = crawler.config_custom(params)
        except Exception as e:
            print("自定义设置出错",str(e))
            return  False


        print("爬虫自定义设置结果", result)

        result = crawler.start()
        print("爬虫启动", result)
    else:
        print("爬取中，等待")

    return  True



#2,根据1688产品列表抓取产品详细信息（标题，规格，图片，价格）
@shared_task
def ali_list_get_info():


    aliproducts = AliProduct.objects.filter(created=False)[:10]
    print("一共有%d 个1688产品信息待抓取"%(aliproducts.count()))

    for aliproduct in aliproducts:
        offer_id = aliproduct.offer_id
        cate_code = aliproduct.cate_code
        #get_aliproduct.apply_async((aliproduct.pk, offer_id,cate_code),queue="ali")
        get_aliproduct(aliproduct.pk, offer_id, cate_code)

@task
def get_aliproduct(pk, offer_id,cate_code):
    from .ali import get_ali_product_info
    import time

    time.sleep(random.uniform(30,60))
    message, status = get_ali_product_info(offer_id, cate_code)
    if status is False:
        AliProduct.objects.filter(pk=pk).update(created_error=message)




#3,将1688产品详细信息发布到shopfiy店铺
@shared_task
def post_ali_shopify():


    dest_shop = "yallasale-com"
    # ori_shop = "yallavip-saudi"

    # sync_shop(ori_shop)
    sync_shop(dest_shop)

    aliproducts = AliProduct.objects.filter(created = True, published=False,stopped=False)
    print("一共有%d 个1688产品信息待发布" % (aliproducts.count()))
    for aliproduct in aliproducts:
        post_to_shopify.delay(aliproduct.pk)

#3,将1688产品详细信息发布到shopfiy店铺
@shared_task
def post_ali_shopify_shenjian():


    dest_shop = "yallasale-com"
    # ori_shop = "yallavip-saudi"

    # sync_shop(ori_shop)
    sync_shop(dest_shop)

    aliproducts = AliProduct.objects.filter(created = True, published=False)
    print("一共有%d 个1688产品信息待发布" % (aliproducts.count()))
    for aliproduct in aliproducts:
        post_to_shopify_shenjian.delay(aliproduct.pk)

@task
def post_to_shopify_shenjian(aliproduct_pk ):
    from .ali import create_body_shenjian, create_variant_shenjian
    from django.utils import timezone as datetime
    dest_shop = "yallasale-com"

    aliproduct = AliProduct.objects.get(pk=aliproduct_pk)

    vendor_no = aliproduct.offer_id
    print("vendor_no", vendor_no)

    dest_products = ShopifyProduct.objects.filter(shop_name=dest_shop, vendor=vendor_no)

    if dest_products:
        print("这个产品已经发布过了！！！！", vendor_no)
        #把以前的删了重新发布
        shop_obj = Shop.objects.get(shop_name=dest_shop)
        # 初始化SDK
        shop_url = "https://%s:%s@%s.myshopify.com" % (shop_obj.apikey, shop_obj.password, shop_obj.shop_name)
        for product in dest_products:
            # delete a product

            product_no = product.product_no
            if product_no is None:
                continue
            else:
                url = shop_url + "/admin/products/%s.json" % (product_no)

                headers = {
                    "Content-Type": "application/json",
                    "charset": "utf-8",

                }

                r = requests.delete(url, headers=headers)
                print("response is ", r)
            # 删除本地数据库记录
            ShopifyProduct.objects.filter(pk=product.pk).delete()
            ShopifyVariant.objects.filter(product_no=product_no).delete()
            ShopifyImage.objects.filter(product_no=product_no).delete()
            ShopifyOptions.objects.filter(product_no=product_no).delete()

    #shop_obj = Shop.objects.get(shop_name=dest_shop)
    #max_id = shop_obj.max_id + 1

    shopifyproduct = create_body_shenjian(aliproduct )
    if shopifyproduct is not None:
        posted = create_variant_shenjian(aliproduct, shopifyproduct)
        if posted is not None:
            print("创建新产品成功")
            AliProduct.objects.filter(pk=aliproduct.pk).update(published=True, handle=posted.get("handle"),
                                                               title = posted.get("title"),

                                                               product_no=posted.get("product_no"),
                                                               published_time=datetime.now())
        else:
            print("创建新产品变体失败")
            AliProduct.objects.filter(pk=aliproduct.pk).update(publish_error="创建新产品变体失败",
                                                               published_time=datetime.now())
            return

    else:
        print("创建新产品失败")
        AliProduct.objects.filter(pk=aliproduct.pk).update(publish_error="创建新产品失败", published_time=datetime.now())
        return


@task
def post_to_shopify(aliproduct_pk ):
    from .ali import create_body, create_variant
    from django.utils import timezone as datetime
    dest_shop = "yallasale-com"

    aliproduct = AliProduct.objects.get(pk=aliproduct_pk)

    vendor_no = aliproduct.offer_id
    print("vendor_no", vendor_no)

    dest_product = ShopifyProduct.objects.filter(shop_name=dest_shop, vendor=vendor_no).first()

    if dest_product:
        print("这个产品已经发布过了！！！！", vendor_no)
        AliProduct.objects.filter(pk=aliproduct.pk).update(published=True, handle=dest_product.handle,
                                                           product_no=dest_product.product_no,
                                                           published_time=datetime.now())

        return
    #shop_obj = Shop.objects.get(shop_name=dest_shop)
    #max_id = shop_obj.max_id + 1

    shopifyproduct = create_body(aliproduct )
    if shopifyproduct is not None:
        posted = create_variant(aliproduct, shopifyproduct)
        if posted is not None:
            print("创建新产品成功")
            AliProduct.objects.filter(pk=aliproduct.pk).update(published=True, handle=posted.get("handle"),
                                                               product_no=posted.get("product_no"),
                                                               published_time=datetime.now())
        else:
            print("创建新产品变体失败")
            AliProduct.objects.filter(pk=aliproduct.pk).update(publish_error="创建新产品变体失败",
                                                               published_time=datetime.now())
            return

    else:
        print("创建新产品失败")
        AliProduct.objects.filter(pk=aliproduct.pk).update(publish_error="创建新产品失败", published_time=datetime.now())
        return

###########################################################
######4.0  每个page 根据自己的品类，从1688新品中随机挑选30个产品，放入待发相册的数据库，供人工排查
######
###########################################################
@shared_task
def prepare_newproduct_album():
    # 找出所有活跃的page
    pages = MyPage.objects.filter(active=True)
    for page in pages:
        #遍历page对应的品类
        print("page is ",page)
        cates = ProductCategoryMypage.objects.filter(mypage__pk = page.pk)
        for cate in cates:
            cate_code = cate.productcategory.code
            album_name = cate.album_name
            album_no = cate.album_no

            # 根据品类找已经上架到shopify 但还未添加到fb接触点（新）的产品
            products_to_add = AliProduct.objects.raw('SELECT * FROM prs_aliproduct  A WHERE '
                                                         'cate_code = %s and published = TRUE  '  
                                                         'and id  NOT  IN  ( SELECT  B.myaliproduct_id FROM prs_myfbproduct B where mypage_id=%s and B.myaliproduct_id is not NULL) ',[cate_code,page.pk], )
            #order by rand() limit 30
            print("products_to_add", page, cate_code, len(products_to_add))

            myfbproduct_list = []
            for product_to_add in products_to_add:
                #n += 1
                #print("     %d is %s" % (n, product_to_add))

                myfbproduct = MyFbProduct(
                    myaliproduct=AliProduct.objects.get(pk=product_to_add.pk),
                    #myproduct=ShopifyProduct.objects.filter(vendor=product_to_add.offer_id).first(),
                    mypage=MyPage.objects.get(pk=page.pk),
                    obj_type="PHOTO",
                    cate_code = cate_code,
                    album_name = album_name,
                    album_no=album_no,



                )
#                print(myfbproduct, AliProduct.objects.get(pk=product_to_add.pk),MyPage.objects.get(pk=page.pk),cate_code,album_name, )
                myfbproduct_list.append(myfbproduct)


            print(myfbproduct_list)
            MyFbProduct.objects.bulk_create(myfbproduct_list)


#4,1 将shopify产品发布到相册
#发布产品到Facebook的album
@shared_task
def post_newproduct_album():

    #选择所有可用的page
    mypages = MyPage.objects.filter(active=True)
    print(mypages)
    for mypage in mypages:
        post_newproduct_album_page(mypage)


    return

def post_newproduct_album_page(mypage):



    print("当前处理主页", mypage, mypage.pk)

    albums = MyFbProduct.objects.filter(mypage__pk=mypage.pk, published=False, myaliproduct__handle__startswith='b') \
        .values_list('album_name').annotate(product_count=Count('id')).order_by('-product_count')

    print("当前主页待处理产品相册", albums)

    album_list = []
    for album in albums:

        if album[1] > 0 and len(album[0]) > 3:
            album_list.append(album[0])

        else:
            print("相册为空或者没有产品要发布了")
            continue

    print("当前主页可处理产品相册", album_list)

    if len(album_list) == 0:
        print("没有相册需要处理了")
        return

    album_name = random.choice(album_list)
    print("这次要处理的相册", album_name)

    post_newproduct_album_page_album(mypage, album_name)


def post_newproduct_album_page_album(mypage, album_name):
    from .fb_action import   post_photo_to_album
    from fb.models import MyAlbum

    products = MyFbProduct.objects.filter(mypage__pk=mypage.pk, published=False, album_name=album_name,
                                          myaliproduct__handle__startswith='b').order_by("-id")
    print("###############这次需要发的产品", products.count(),products )
    if products is None or products.count() == 0:
        print("没有产品可发布了")
        return

    # 发到指定相册

    n = 0
    for product in products:
        myproduct = product.myaliproduct
        album_no = MyAlbum.objects.get(page_no=mypage.page_no,name= album_name).album_no

        error, posted = post_photo_to_album(mypage, album_no, myproduct)

        if posted is not None:
            MyFbProduct.objects.filter(mypage__pk=mypage.pk, myaliproduct__pk=product.myaliproduct.pk).update(

                fb_id=posted,
                published=True,
                published_time=datetime.now()
            )
            print("发布新产品到相册成功 page_pk %s  product_pk %s   photo_id   %s" % (mypage.pk, myproduct.pk, posted))
            # print("created is ", created)
            # print("obj is ", obj)
            n += 1
            if n > 5:
                break
        else:
            print("发布新产品到相册失败 page_pk %s  album %s product_pk %s   error   %s" % (mypage.pk, album_name,myproduct.pk, error))
            MyFbProduct.objects.filter(mypage__pk=mypage.pk, myaliproduct__pk=product.myaliproduct.pk).update(
                myproduct=myproduct,
                published=False,
                publish_error=error[:90],
                published_time=datetime.now()
            )
#####################################################################
#4,0 把shopify产品库中的还未添加到fb产品库的产品按page对应的品类找出来并添加
#######准备工作，每次从1688上新到shopify后调用一次即可
######################################################################
@shared_task
def product_shopify_to_fb():


    #找出所有活跃的page
    pages = MyPage.objects.filter(active=True)
    n = 0
    for page in pages:
        #遍历page对应的品类
        print("page is ",page)
        cates = ProductCategoryMypage.objects.filter(mypage__pk = page.pk)
        for cate in cates:
            cate_code = cate.productcategory.code
            album_name = cate.album_name
            print(cate_code)
            #根据品类找未添加到fb产品库的产品

            #products_to_add = ShopifyProduct.objects.filter(category_code = cate_code,
            #                                                handle__startswith='a',myfb_product__isnull= True ,)

             #SELECT * FROM shop_shopifyproduct  A WHERE  category_code = "WOMEN_Bags_Handbags" and handle like 'a%' and id  NOT  IN  ( SELECT  B.myproduct_id FROM prs_myfbproduct B where mypage_id=14) order by created_at desc

            handle_like = 'b%'
            products_to_add = ShopifyProduct.objects.raw('SELECT * FROM shop_shopifyproduct  A WHERE '
                                                         'category_code = %s and handle like %s '  
                                                         'and id  NOT  IN  ( SELECT  B.myproduct_id FROM prs_myfbproduct B where mypage_id=%s) order by published_at ',[cate_code,handle_like,page.pk])

            #products_to_add = ShopifyProduct.objects.filter(category_code = cate_code)
            print("products_to_add", products_to_add)
            #print("products_to_add query", products_to_add.query)

            myfbproduct_list = []
            for product_to_add in products_to_add:
                n += 1
                print("     %d is %s"%(n,product_to_add))

                myfbproduct = MyFbProduct(
                    myproduct= ShopifyProduct.objects.get(pk=product_to_add.pk ),
                    mypage=MyPage.objects.get(pk=page.pk ),
                    obj_type="PHOTO",
                    cate_code=cate_code,
                    album_name=album_name,

                )
                myfbproduct_list.append(myfbproduct)

            MyFbProduct.objects.bulk_create(myfbproduct_list)

#4,1 将shopify产品发布到相册
#发布产品到Facebook的album
@shared_task
def post_to_album():
    from .fb_action import   post_photo_to_album
    from fb.models import MyAlbum





    #选择所有可用的page
    mypages = MyPage.objects.filter(active=True)
    print(mypages)
    for mypage in mypages:

        print("当前处理主页", mypage, mypage.pk)

        # 主页已有的相册
        album_dict = {}
        albums = MyAlbum.objects.filter(page_no=mypage.page_no,active=True)

        for album in albums:
            album_dict[album.name] = album.album_no


        #print("当前主页已有相册", album_dict)

        albums = MyFbProduct.objects.filter(mypage__pk=mypage.pk, published=False) \
            .values_list('album_name').annotate(product_count=Count('id')).order_by('-product_count')

        print("当前主页待处理产品相册", albums)


        album_list =[]
        for album in albums:
            if album[1]>0 :
                if len(album[0])>3:
                    album_list.append(album[0])
            else:
                break

        print("当前主页可处理产品相册", album_list)

        if len(album_list) == 0:
            print("没有相册需要处理了")
            continue


        album_name = random.choice(album_list)
        print("这次要处理的相册", album_name)
        # 是否已经建了相册

        target_album_no = album_dict.get(album_name)



        if not target_album_no :
            print("此相册还没有创建，请新建一个")
            continue
        print("target_album %s" % (album_list))



        # 发到指定相册
        products =MyFbProduct.objects.filter(mypage__pk=mypage.pk, published=False, album_name =album_name,myproduct__handle__startswith='b').order_by("-id")
        n = 0
        for product in products:
            posted = post_photo_to_album(mypage, target_album_no, product.myproduct)


            if posted:
                MyFbProduct.objects.filter(mypage__pk=mypage.pk ,myproduct__pk=product.myproduct.pk).update(
                    fb_id = posted,
                    published = True,
                    published_time = datetime.now()
                )
                print("更新page_类目记录 page_pk %s  product_pk %s   photo_id   %s" % (mypage.pk, product.myproduct.pk, posted))
                #print("created is ", created)
                #print("obj is ", obj)
                n += 1
                if n>5:
                    break
            else:
                MyFbProduct.objects.filter(mypage__pk=mypage.pk ,myproduct__pk=product.myproduct.pk).update(
                    published=False,
                    publish_error="发布失败",
                    published_time=datetime.now()
                )

    return

#5,爆款生成动图发布到feed
############################
#
#随机选有动销的产品动图到活跃的page
#
############################
@shared_task
def product_feed():
    from .fb_action import post_album_feed

    post_album_feed()
    #post_product_feed()

    return


#6,创意发布到feed
#####################################
#########把创意发到feed
######################################
@shared_task
def creative_feed():
    from .fb_action import post_creative_feed

    post_creative_feed()
    return
#7,


##########海外仓包裹从fb下架
### 1  找到已销售的包裹
### 2  从Facebook照片里找到对应的photo id， 删除
### 3, 从Facebook feed里找到对应的帖子 id， 删除

def unlisting_overseas_package():
    from fb.models import  MyPhoto

    from facebook_business.api import FacebookAdsApi
    from facebook_business.adobjects.photo import Photo


    # 订单状态已付款， 订单明细sku名字中含overseas的订单找出来

    order_details = OrderDetail.objects.filter(~Q(order__order_status="已退款"), sku__istartswith="overseas")
    print("####### 已销售海外仓包裹总数", order_details.count())
    n = 0
    for order_detail in order_details:
        sku = order_detail.sku
        # 删除Facebook上的图片

        sku_name = sku.partition("-")[2]

        print("sku is %s, sku_name is %s" % (sku, sku_name))

        # 选择所有可用的page
        mypages = MyPage.objects.filter(active=True)
        print(mypages)
        for mypage in mypages:



            myphotos = MyPhoto.objects.filter(name__icontains=sku_name, page_no=mypage.page_no )

            print("myphotos %s" % (myphotos), myphotos.count())
            if myphotos is None or myphotos.count() == 0:
                continue

            FacebookAdsApi.init(access_token=get_token(mypage.page_no))
            n=1
            for myphoto in myphotos:

                fields = [
                ]
                params = {

                }
                try:
                    response = Photo(myphoto.photo_no).api_delete(
                        fields=fields,
                        params=params,
                    )
                    print("%s response is %s" %(n, response))
                    n +=1
                except:
                    continue



            # 修改数据库记录
            myphotos.update(listing_status=False)

            ShopifyVariant.objects.filter(sku=sku).update(supply_status="STOP", listing_status=False)

            Order.objects.filter(pk = order_detail.order.pk).update(resell_status = 'SELLING')


def unlisting_overseas_package_new():
    from fb.models import  MyPhoto

    from facebook_business.api import FacebookAdsApi
    from facebook_business.adobjects.photo import Photo


    # 订单状态已付款， 订单明细sku名字中含overseas的订单找出来

    order_details = OrderDetail.objects.filter(~Q(order__order_status="已退款"), sku__istartswith="579815")
    print("####### 已销售海外仓包裹总数", order_details.count())
    n = 0
    for order_detail in order_details:
        sku = order_detail.sku
        # 删除Facebook上的图片

        sku_name = sku

        print("sku is %s, sku_name is %s" % (sku, sku_name))

        # 选择所有可用的page
        mypages = MyPage.objects.filter(active=True)
        print(mypages)
        for mypage in mypages:



            myphotos = MyPhoto.objects.filter(name__icontains=sku_name, page_no=mypage.page_no )

            print("myphotos %s" % (myphotos), myphotos.count())
            if myphotos is None or myphotos.count() == 0:
                continue

            FacebookAdsApi.init(access_token=get_token(mypage.page_no))
            n=1
            for myphoto in myphotos:

                fields = [
                ]
                params = {

                }
                try:
                    response = Photo(myphoto.photo_no).api_delete(
                        fields=fields,
                        params=params,
                    )
                    print("%s response is %s" %(n, response))
                    n +=1
                except:
                    continue



            # 修改数据库记录
            myphotos.update(listing_status=False)

            ShopifyVariant.objects.filter(sku=sku).update(supply_status="STOP", listing_status=False)
            Order.objects.filter(pk = order_detail.order.pk).update(resell_status = 'SELLING')


def sync_aliproduct_shopify():
    from django.utils import timezone as datetime

    aliproducts = AliProduct.objects.filter(created=True)
    print("一共有%d 个1688产品信息待同步" % (aliproducts.count()))

    for aliproduct in aliproducts:
        dest_products = ShopifyProduct.objects.filter(vendor=aliproduct.offer_id)

        if dest_products.exists():

            print("这个产品已经发布过了！！！！", aliproduct.offer_id, dest_products)
            AliProduct.objects.filter(pk=aliproduct.pk).update(published=True, published_time= datetime.now(),publish_error="")
        else:
            print("还没有发布过 ######", aliproduct.offer_id)
            AliProduct.objects.filter(pk=aliproduct.pk).update(published=False, published_time=None,
                                                               publish_error="")

def complete_aliproduct_shopify():
    from django.utils import timezone as datetime

    #aliproducts = AliProduct.objects.filter(created=True,published=True,handle="")
    aliproducts = AliProduct.objects.filter(created=True, handle="")
    print("一共有%d 个1688产品信息待补充" % (aliproducts.count()))

    for aliproduct in aliproducts:
        handle_new = 'b' + str(aliproduct.pk).zfill(5)
        AliProduct.objects.filter(pk=aliproduct.pk).update(handle=handle_new)



# 抓取lightin页面数据
@shared_task
def get_lightin():
    from .ali import get_lightin_product_info
    from django.utils import timezone as dt

    lightinproducts = Lightin_SPU.objects.filter(got=False,got_error="无" )
    print("一共有%d 个lightin链接待处理"%(lightinproducts.count()))



    for lightinproduct in lightinproducts:

        message,status=get_lightin_product_info(lightinproduct.SPU, lightinproduct.link)
        if status:
            print("成功！")
        else:
            print("失败！！！", message)
            # 更新产品记录
            Lightin_SPU.objects.update_or_create(
                SPU=lightinproduct.SPU,
                defaults={
                    "got_error":message,
                    "got_time": dt.now()

                }
            )


#3,将1688产品详细信息发布到shopfiy店铺
@shared_task
def post_lightin_shopify():


    dest_shop = "yallasale-com"
    # ori_shop = "yallavip-saudi"

    # sync_shop(ori_shop)
    sync_shop(dest_shop)

    lightinproducts = Lightin_SPU.objects.filter(got = True, published=False,publish_error="无")
    print("一共有%d 个lightin产品信息待发布" % (lightinproducts.count()))
    n = 0
    for lightinproduct in lightinproducts:
        #post_to_shopify_lightin.delay(lightinproduct.pk)
        post_to_shopify_lightin(lightinproduct.pk)
        '''
        n += 1
        if n>10:
            break
        '''

@task
def post_to_shopify_lightin(lightinproduct_pk ):
    from .ali import create_body_lightin, create_variant_lightin
    from django.utils import timezone as datetime
    dest_shop = "yallasale-com"

    lightin_spu = Lightin_SPU.objects.get(pk=lightinproduct_pk)

    vendor_no = lightin_spu.SPU
    print("vendor_no", vendor_no)

    dest_products = ShopifyProduct.objects.filter(shop_name=dest_shop, vendor=vendor_no)

    if dest_products:
        print("这个产品已经发布过了！！！！", vendor_no)
        #把以前的删了重新发布
        shop_obj = Shop.objects.get(shop_name=dest_shop)
        # 初始化SDK
        shop_url = "https://%s:%s@%s.myshopify.com" % (shop_obj.apikey, shop_obj.password, shop_obj.shop_name)
        for product in dest_products:
            # delete a product

            product_no = product.product_no
            if product_no is None:
                continue
            else:
                url = shop_url + "/admin/products/%s.json" % (product_no)

                headers = {
                    "Content-Type": "application/json",
                    "charset": "utf-8",

                }

                r = requests.delete(url, headers=headers)
                print("response is ", r)
            # 删除本地数据库记录
            ShopifyProduct.objects.filter(pk=product.pk).delete()
            ShopifyVariant.objects.filter(product_no=product_no).delete()
            ShopifyImage.objects.filter(product_no=product_no).delete()
            ShopifyOptions.objects.filter(product_no=product_no).delete()

    #shop_obj = Shop.objects.get(shop_name=dest_shop)
    #max_id = shop_obj.max_id + 1

    shopifyproduct = create_body_lightin(lightin_spu )
    if shopifyproduct is not None:
        posted = create_variant_lightin(lightin_spu)
        if posted is not None:
            print("创建新产品成功")
            Lightin_SPU.objects.filter(pk=lightin_spu.pk).update(published=True, handle=posted.get("handle"),
                                                               product_no=posted.get("id"),
                                                               published_time=datetime.now())
        else:
            print("创建新产品变体失败")
            Lightin_SPU.objects.filter(pk=lightin_spu.pk).update(publish_error="创建新产品变体失败",
                                                               published_time=datetime.now())
            return

    else:
        print("创建新产品失败")
        Lightin_SPU.objects.filter(pk=lightin_spu.pk).update(publish_error="创建新产品失败", published_time=datetime.now())
        return


#更新产品标题，把货号加在后面，便于客服下单
#把5Sar一下的产品，标题里加个[freegift]

@shared_task
def update_lightin_shopify_title():

    dest_shop = "yallasale-com"
    shop_obj = Shop.objects.get(shop_name=dest_shop)
    # 初始化SDK
    shop_url = "https://%s:%s@%s.myshopify.com" % (shop_obj.apikey, shop_obj.password, shop_obj.shop_name)

    #为了加货号
    #lightinproducts = Lightin_SPU.objects.filter(got = True, published=True, updated=False)

    #找出5sar以下的产品
    lightinproducts = Lightin_SPU.objects.filter(published=True, vendor_supply_price__lt=1)

    print("一共有%d 个lightin产品信息待更新标题" % (lightinproducts.count()))
    n = 0
    for lightinproduct in lightinproducts:

        update_shopify_title_lightin(lightinproduct, shop_url)
        '''
        n += 1
        if n>2:
            break
        '''

@shared_task
def update_shopify_title_lightin(lightin_spu, shop_url ):
    from .ali import create_body_lightin, create_variant_lightin
    from django.utils import timezone as datetime


    #标题里加货号
    # title = lightin_spu.title + " [" + lightin_spu.handle + "]"
    title = lightin_spu.en_name + " [" + lightin_spu.handle + "]" + " [freegift]"
    print("title is ", title)

    params = {
        "product": {

            "title": title,

        }
    }
    headers = {
        "Content-Type": "application/json",
        "charset": "utf-8",

    }
    url = shop_url + "/admin/products/%s.json" % (lightin_spu.product_no)

    r = requests.put(url, headers=headers, data=json.dumps(params))
    print("r  ", r)
    if r.status_code  == 200:
        Lightin_SPU.objects.filter(pk=lightin_spu.pk).update(updated=True,title=title)
    else:
        print(r.text)




@shared_task
def prepare_lightin_album():
    from django.db import connection, transaction
    cursor = connection.cursor()
    # 找出所有活跃的page
    pages = MyPage.objects.filter(active=True)
    for page in pages:
        #遍历page对应的相册
        print("page is ",page)
        albums = MyAlbum.objects.filter(Q(cates__isnull=False)|Q(prices__isnull=False)|Q(attrs__isnull=False), mypage__pk = page.pk, )
        print("albums is ", albums)
        for album in albums:
            print("album is ", album)

            #拼接相册的筛选产品的条件
            q_cate = Q()
            q_cate.connector = 'OR'
            if album.cates:
                for cate in album.cates.split(","):
                    q_cate.children.append(('breadcrumb__contains', cate))


            q_price = Q()
            q_price.connector = 'AND'
            if album.prices:
                prices = album.prices.split(",")
                q_price.children.append(('shopify_price__gt',prices[0]))
                q_price.children.append(('shopify_price__lte', prices[1]))

            q_attr = Q()
            q_attr.connector = 'OR'
            if album.attrs:
                for attr in album.attrs.split(","):
                    q_attr.children.append(('spu_sku__skuattr__contains',attr))

            con = Q()
            con.add(q_cate, 'AND')
            con.add(q_price, 'AND')
            con.add(q_attr, 'AND')




            # 根据品类找已经上架到shopify 但还未添加到相册的产品

            print(con)
            products_to_add = Lightin_SPU.objects.filter(con,published=True).exclude(id__in =
                                                                   LightinAlbum.objects.filter(myalbum__pk = album.pk, lightin_spu__isnull=False ).values_list('lightin_spu__id',flat=True)  ).distinct()



            product_list = []
            for product_to_add in products_to_add:
                product = LightinAlbum(
                    lightin_spu=Lightin_SPU.objects.get(pk=product_to_add.pk),
                    myalbum=MyAlbum.objects.get(pk=album.pk),

                )
                product_list.append(product)


            print(product_list)
            LightinAlbum.objects.bulk_create(product_list)



@shared_task
def prepare_lightin_album_material():
    from django.db.models import Max
    from shop.photo_mark import lightin_mark_image
    #批次号
    batch_no = LightinAlbum.objects.all().aggregate(Max('batch_no')).get("batch_no__max") + 1

    #分相册随机选产品

    lightinalbums_all = LightinAlbum.objects.filter(published= False,publish_error="无",material=False,material_error ="无", batch_no=0 )

    albums_list  = lightinalbums_all.distinct().values_list('myalbum', flat=True)
    print("albums_list is ", albums_list)

    for album in albums_list:
        lightinalbums = lightinalbums_all.filter(myalbum__pk=album).order_by('?')[:9]
        print(lightinalbums)

        for lightinalbum in lightinalbums:
            spu = lightinalbum.lightin_spu
            error = ""
            # 准备文字
            # 标题
            title = spu.title
            # 货号
            name = title + "  [" + spu.handle + "]"
            # 规格
            lightin_skus = Lightin_SKU.objects.filter(SPU=spu.SPU)
            options = []
            for sku in lightin_skus:
                option = sku.skuattr
                if option not in options:
                    options.append(option)

            if len(options)>0:
                name = name + "\n\nSkus:  "

            for option in options:
                name = name + "\n\n   " + option


            #价格
            price1 = int(spu.shopify_price)
            price2 = int(price1 * random.uniform(5, 6))
            #为了减少促销的麻烦，文案里不写价格了
            #name = name + "\n\nPrice:  " + str(price1) + "SAR"

            # 准备图片
            #先取第一张，以后考虑根据实际有库存的sku的图片（待优化）
            if spu.images_dict:
                image = json.loads(spu.images_dict).values()
                if image and len(image)>0:
                    a = "/"
                    image_split = list(image)[0].split(a)

                    image_split[4] = '800x800'
                    image = a.join(image_split)

                # 打水印
                # logo， page促销标
                # 如果有相册促销标，就打相册促销标，否则打价格标签

                image_marked, iamge_marked_url = lightin_mark_image(image, spu.handle, str(price1), str(price2),
                                                                    lightinalbum)
                if not image_marked:
                    error = "打水印失败"

            else:
                print(album, spu.SPU, "没有图片")
                error = "没有图片"

            if error == "":
                LightinAlbum.objects.filter(pk = lightinalbum.pk ).update(
                        name=name,
                        image_marked=iamge_marked_url,
                        batch_no=batch_no,
                        material = True
                    )
            else:
                LightinAlbum.objects.filter(pk=lightinalbum.pk).update(
                    material_error =  error
                )

@shared_task
def sync_lightin_album():
    from django.db.models import Min
    from .fb_action import post_lightin_album
    #把有未发布的图片的，最小批次号作为当前批次
    batch_no = LightinAlbum.objects.filter(published=False, publish_error="无",material =True).aggregate(Min('batch_no')).get("batch_no__min")

    # 将当前批次下未发布的图片，发布到Facebook
    #分相册 处理
    lightinalbums_all = LightinAlbum.objects.filter(published=False, publish_error="无", material =True,batch_no=batch_no)

    albums_list = lightinalbums_all.distinct().values_list('myalbum', flat=True)

    for album in albums_list:
        lightinalbums = lightinalbums_all.filter(myalbum__pk=album)
        for lightinalbum in lightinalbums:
            error, posted = post_lightin_album(lightinalbum)

            #更新Facebook图片数据库记录

            if posted is not None:
                LightinAlbum.objects.filter(pk=lightinalbum.pk).update(

                    fb_id=posted,
                    published=True,
                    published_time=dt.now()
                )
                print("发布新产品到相册成功 LightinAlbum %s" % (lightinalbum.pk))
            else:
                print(
                    "发布新产品到相册失败 LightinAlbum %s   error   %s" % (lightinalbum.pk, error))
                LightinAlbum.objects.filter(pk=lightinalbum.pk).update(

                    published=False,
                    publish_error=error[:90],
                    published_time=dt.now()
                )
    # 把比当前批次号小 20 的批次的图片 还在发布状态的从Facebook删除
    if batch_no >20:
        delete_outdate_lightin_album(batch_no -20)


#把比当前批次号，且还在发布状态的从Facebook删除
def delete_outdate_lightin_album(batch_no):

    #按批次号找出子集
    lightinalbums_outdate = LightinAlbum.objects.filter(published=True, batch_no=batch_no)

    #删除子集
    delete_out_lightin_album(lightinalbums_outdate)



#把所有sku都没有库存，spu还在发布状态的从Facebook删除
@shared_task
def delete_outstock_lightin_album(all=False):
    #更新还在发布中的spu的库存
    from django.db import connection, transaction
    '''
    sql = "UPDATE prs_lightin_spu SET  quantity =(SELECT sum(k.quantity) FROM prs_lightin_sku k WHERE k.SPU = prs_lightin_spu.SPU and prs_lightin_spu.published = true)"

    cursor = connection.cursor()
    cursor.execute(sql)
    transaction.commit()
    
    
    #选出库存为零，还在发布中的spu
    lightinalbums_outstock = LightinAlbum.objects.filter(
        Q(lightin_spu__quantity__isnull=True)|Q(lightin_spu__quantity=0),
        lightin_spu__published=True)
    print("库存为零的发布中的相册子集",lightinalbums_outstock)
    '''
    #每天更新一次所有在发布的图片，每分钟更新一次订单sku对应的图片
    if all:
        lightinalbums = LightinAlbum.objects.filter(published=True)
    else:
        orderdetails = OrderDetail.objects.filter(~Q(order__wms_status="D"),
                                   order__financial_status="paid",
                                   order__updated=True,
                                   order__status="open")
        lightinalbums = LightinAlbum.objects.filter(published=True,
                                    lightin_spu__spu_sku__SKU__in =
                                        orderdetails.values_list('sku', flat=True))

    lightinalbums_out = {}

    n = lightinalbums.count()

    for lightinalbum in lightinalbums:
        print("一共还有%s 个图片待排查"%(n))
        n -= 1
        #print("%s lightinalbum.lightin_spu.sellable is %s "%(lightinalbum.lightin_spu ,lightinalbum.lightin_spu.sellable))
        if  lightinalbum.lightin_spu.sellable <= 0:
            photo_list = lightinalbums_out.get(lightinalbum.myalbum.page_no)
            if not photo_list :
                photo_list = []
            if lightinalbum.fb_id not in photo_list:
                photo_list.append(lightinalbum.fb_id)

            lightinalbums_out[lightinalbum.myalbum.page_no] = photo_list
            #print("lightinalbum is %s  page no is %s, photo_id is %s "%(lightinalbum, lightinalbum.myalbum.page_no,lightinalbum.fb_id ))

    # 删除子集

    delete_out_lightin_album(lightinalbums_out)
    if not all:
        Order.objects.filter(updated=True).update(updated=False)

#删除lightin_album 的某个特定子集
def delete_out_lightin_album(lightinalbums_out):
    from facebook_business.api import FacebookAdsApi
    from facebook_business.adobjects.photo import Photo

    # 选择所有可用的page

    for page_no in lightinalbums_out:
        FacebookAdsApi.init(access_token=get_token(page_no))

        photo_nos = lightinalbums_out[page_no]
        print("page %s 待删除数量 %s  "%(page_no, len(photo_nos)))
        if photo_nos is None or len(photo_nos) == 0:
            continue

        for photo_no in photo_nos:

            fields = [
            ]
            params = {

            }
            try:
                '''
                response = Photo(photo_no).api_delete(
                    fields=fields,
                    params=params,
                )
                '''
                response = "delete photo_no "+ photo_no
            except:
                continue
            #更新lightinalbum的发布记录
            print("facebook 返回结果",response)
            LightinAlbum.objects.filter(fb_id=photo_no).update(

                    published=False,
                    deleted=True,
                    #delete_error=response,
                    deleted_time=dt.now()

                )
            print("删除相册图片 LightinAlbum %s %s" % (photo_no, response))

@shared_task
def mapping_order_lightin():

    from django.db.models import Sum
    from prs.models import Lightin_barcode


    #orders = Order.objects.raw(  'SELECT * FROM orders_order  A WHERE financial_status = "paid" and  inventory_status <> "库存锁定"')
    orders = Order.objects.filter(financial_status = "paid", fulfillment_status__isnull=True,status = "open").order_by("verify__sms_status")

    print("一共有 %s 个订单待处理", orders.count())

    # 处理每个订单
    for order in orders:
        if order.inventory_status == "库存锁定":
            continue

        #先把自己可能占用的库存释放
        OrderDetail_lightin.objects.filter(order=order).delete()

        inventory_list = []
        error = ""

        orderdetails = order.order_orderdetail.all()
        print("当前处理订单 ", order)

        # 每个订单项
        for orderdetail in orderdetails:
            sku = orderdetail.sku
            price = orderdetail.price
            quantity = int(float(orderdetail.product_quantity))

            lightin_barcodes = Lightin_barcode.objects.filter(SKU=sku)

            if lightin_barcodes is None:
                print("找不到映射，也就意味着无法管理库存！")
                #需要标识为异常订单
                error = "找不到SKU"
                continue



            # 每个可能的条码
            for lightin_barcode in lightin_barcodes:
                if quantity == 0:
                    break
                if lightin_barcode.sellable == 0:
                    continue

                print("sku %s , 需求量 %s , 条码 %s , 条码可售库存 %s"%(sku,  quantity, lightin_barcode, lightin_barcode.sellable  ))
                if quantity > lightin_barcode.sellable:
                    # 条码的库存数量比订单项所需的少
                    quantity -= lightin_barcode.sellable

                    occupied = lightin_barcode.sellable
                else:

                    occupied = quantity
                    quantity = 0

                inventory_list.append([sku, lightin_barcode, occupied, price])

            #需求没有被满足，标识订单缺货
            print("quantity", quantity)
            if quantity > 0:
                error = "缺货"
        print(inventory_list)


        # 插入到OrderDetail_lightin
        orderdetail_lightin_list = []

        for inventory in inventory_list:

            orderdetail_lightin = OrderDetail_lightin(
                order=order,
                SKU=inventory[0],
                barcode=inventory[1],
                quantity=inventory[2],
                price = inventory[3],
            )
            orderdetail_lightin_list.append(orderdetail_lightin)


        OrderDetail_lightin.objects.bulk_create(orderdetail_lightin_list)





@shared_task
def fulfill_order_lightin():
    from suds.client import Client
    from xml.sax.saxutils import escape

    service = "createOrder"

    orders = Order.objects.filter(financial_status="paid" ,
                                  fulfillment_status__isnull = True,
                                  status = "open",

                                  verify__verify_status = "SUCCESS",
                                  verify__sms_status = "CHECKED",
                                  wms_status = "")
    print("共有%s个订单待发货"%(orders.count()))
    for order in orders:
        if not order.inventory_status == "库存锁定" :
            continue

        items = []

        for order_item in order.order_orderdetail_lightin.all():
            #print(order_item)

            item = {
                    "product_sku": order_item.barcode.barcode,
                    #"product_name_en":title,
                    "product_declared_value": order_item.price,
                    "quantity": order_item.quantity,
                }
            items.append(item)


        param = {
            "platform": "B2C",
            "allocated_auto":"1",
            "warehouse_code":warehouse_code,
            "shipping_method":shipping_method,
            "reference_no":order.order_no,
            #"order_desc":"\u8ba2\u5355\u63cf\u8ff0",
            "country_code":"SA",
            "province":order.receiver_city,
            "city":order.receiver_city,
            "address1":order.receiver_addr1,
            "address2":order.receiver_addr2,
            "address3":"",
            "zipcode":"123456",
            "doorplate":"doorplate",
            "company":"company",
            "name":order.receiver_name,
            "phone":order.receiver_phone,
            "cell_phone":"",
            "email": order.buyer_name.replace(" ", "") + "@yallavip.com",
            "order_cod_price":order.order_amount,
            "order_cod_currency":"SAR",
            "order_age_limit":"2",
            "is_signature":"0",
            "is_insurance":"0",
            "insurance_value":"0",
            "verify":"1",
            "items":items,
            #"tracking_no":"123",
            #"label":{
            #    "file_type":"png",
            #    "file_data":"hVJPjUP4+yHjvKErt5PuFfvRhd..."
            #}
        }
        #print(param)
        result = yunwms(service, param)

        print(result)
        if result.get("ask") == "Success":
            #发货成功
            Order.objects.filter(pk = order.pk).update(
                wms_status = result.get("order_status"),
                logistic_no = result.get("tracking_no"),

            )
        else:
            Order.objects.filter(pk=order.pk).update(
                fulfill_error=result.get("message"),


            )





@shared_task
def sync_status_order_lightin():
    param = {
        "pageSize": "100",
        "page": "1",
        "order_code": "",
        "order_status": "",
        "order_code_arr": [],
        "create_date_from": "",
        "create_date_to": "",
        "modify_date_from": "",
        "modify_date_to": ""
    }

    service = "getOrderList"



    result = yunwms(service, param)

    print(result)

#把wms已发货的订单同步回来

#修改本地的barcode的库存数量
#已发货的barcode，不占用库存

@shared_task
def sync_Shipped_order_lightin():
    import  datetime
    from django.db.models import F

    today = datetime.date.today()
    start_time = str(today - datetime.timedelta(days=1))

    page = 1

    while 1:

        param = {
            "pageSize": "100",
            "page": page,
            "order_code": "",
            "order_status": "D",
            "order_code_arr": [],
            "create_date_from": start_time,
            "create_date_to": "",
            "modify_date_from": "",
            "modify_date_to": ""
        }

        service = "getOrderList"

        result = yunwms(service, param)

        #print(result)
        if result.get("ask") == "Success":

            for data in result.get("data"):
                order_no = data.get("reference_no")
                if not order_no :
                    print(data)
                    continue
                print("当前处理订单 ", order_no)

                order = Order.objects.get(order_no=order_no)
                if order:
                    if order.wms_status == "":
                        #更新本地库存
                        items = OrderDetail_lightin.objects.filter(order=order)
                        for item in items:
                            barcode = Lightin_barcode.objects.get(barcode=item.barcode)
                            barcode.quantity = F("quantity") - item.quantity
                            barcode.save()
                        print ("更新本地库存")

                        #更新本地的订单状态
                        Order.objects.update_or_create(
                            order_no = order_no,
                            defaults={
                                "wms_status": data.get("order_status"),
                                "logistic_type":data.get("shipping_method"),
                                "logistic_no": data.get("tracking_no"),
                                "send_time": data.get("date_shipping"),
                                "weight": data.get("order_weight"),
                            },
                        )
                        print ("更新本地的订单状态")

        if result.get("nextPage") == "false":
            break
        else:
            page += 1;

#若wms已发货，shopify还未发货，则同步shopify发货
@shared_task
def sync_Shipped_order_shopify():
    from prs.shop_action import  fulfill_order_shopify

    orders = Order.objects.filter(status = "open", wms_status= "D",logistic_no__isnull=False, fulfillment_status__isnull=True ,order_id__isnull=False)

    n= orders.count()
    for order in orders:

        # 更新shopify的发货状态

        print("shopify 发货 ", order.order_no,order.order_id, order.logistic_no)
        n -= 1
        print("还有 %s 待发货" % (n))

        data = fulfill_order_shopify(order.order_id, order.logistic_no)

        if data.get("errors"):
            fulfillment_status = data.get("errors")

        else:
            fulfillment_status = "fulfilled"


        # 更新本地的订单状态
        Order.objects.update_or_create(
            order_no=order.order_no,
            defaults={
                "fulfillment_status": fulfillment_status,

            },
        )

def get_wms_quantity():
    page = 1

    while 1:
        print("正在处理第 %s 页"%(page))

        param = {
            "pageSize": "100",
            "page": page,
             "product_sku":"",
            "product_sku_arr":[],
            "warehouse_code":warehouse_code,
            "warehouse_code_arr":[]
        }

        service = "getProductInventory"

        result = yunwms(service, param)

        #print(result)
        if result.get("ask") == "Success":
            for data in result.get("data"):
                Lightin_barcode.objects.update_or_create(
                    barcode=data.get("product_sku"),
                    defaults={
                        "y_sellable" : data.get("sellable"),
                        "y_reserved": data.get("reserved"),
                        "y_shipped": data.get("shipped"),
                        "quantity":  int(data.get("sellable")) + int(data.get("reserved"))

                    },


                )
        if result.get("nextPage") == "false":
            break
        else:
            page += 1;

def get_shopify_quantity():

    "GET /admin/inventory_levels.json?inventory_item_ids=808950810,39072856&location_ids=905684977,487838322"

    page = 1

    while 1:
        print("正在处理第 %s 页"%(page))

        param = {
            "pageSize": "100",
            "page": page,
             "product_sku":"",
            "product_sku_arr":[],
            "warehouse_code":warehouse_code,
            "warehouse_code_arr":[]
        }

        service = "getProductInventory"

        result = yunwms(service, param)

        #print(result)
        if result.get("ask") == "Success":
            for data in result.get("data"):
                Lightin_barcode.objects.update_or_create(
                    barcode=data.get("product_sku"),
                    defaults={
                        "y_sellable" : data.get("sellable"),
                        "y_reserved": data.get("reserved"),
                        "y_shipped": data.get("shipped"),
                        "quantity":  int(data.get("sellable")) + int(data.get("reserved"))

                    },


                )
        if result.get("nextPage") == "false":
            break
        else:
            page += 1;



def getShippingMethod():
    param = {
        "warehouseCode":warehouse_code,
    }

    service = "getShippingMethod"

    result = yunwms(service, param)

    print(result)


def yunwms(service, param):
    from suds.client import Client
    from xml.sax.saxutils import escape

    url = "http://cititrans.yunwms.com/default/svc/wsdl"
    client = Client(url)

    response = client.service.callService(appToken=appToken,
                                          appKey=appKey,
                                          service=service,
                                          paramsJson=json.dumps(param)
                                          )
    result = json.loads(escape(response))
    return  result




# 更新相册对应的主页外键
#update fb_myalbum a , fb_mypage p set a.mypage_id = p.id where p.page_no = a.page_no
'''
from django.db import connection, transaction

    sql = "UPDATE prs_lightin_spu SET  quantity =(SELECT sum(k.quantity) FROM prs_lightin_sku k WHERE k.SPU = prs_lightin_spu.SPU and prs_lightin_spu.published = true)"

    cursor = connection.cursor()
    cursor.execute(sql)
    transaction.commit()
'''

