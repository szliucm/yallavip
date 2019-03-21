# Create your tasks here
from __future__ import absolute_import, unicode_literals

import json
import numpy as np
import random
import re
import requests
from celery import shared_task, task
from django.db.models import Q, Count
from django.utils import timezone as datetime
from django.utils import timezone as dt
from fb.models import MyPage, MyAlbum
from logistic.tasks import my_custom_sql
from orders.models import Order, OrderDetail, OrderDetail_lightin
from shop.models import ProductCategoryMypage
from shop.models import Shop, ShopifyProduct, ShopifyVariant, ShopifyImage, ShopifyOptions

from .models import *
from .shop_action import sync_shop

my_app_id = "562741177444068"
my_app_secret = "e6df363351fb5ce4b7f0080adad08a4d"
my_access_token = "EAAHZCz2P7ZAuQBABHO6LywLswkIwvScVqBP2eF5CrUt4wErhesp8fJUQVqRli9MxspKRYYA4JVihu7s5TL3LfyA0ZACBaKZAfZCMoFDx7Tc57DLWj38uwTopJH4aeDpLdYoEF4JVXHf5Ei06p7soWmpih8BBzadiPUAEM8Fw4DuW5q8ZAkSc07PrAX4pGZA4zbSU70ZCqLZAMTQZDZD"

DEBUG = False

if DEBUG:
    warehouse_code = "TW02"
    shipping_method = "L002-KSA-TEST",
    appToken = "85413bb8f6a270e1ff4558af80f2bef5"
    appKey = "9dca0be4c02bed9e37c1c4189bc1f41b"
else:
    warehouse_code = "W07"
    shipping_method = "FETCHR_SAUDI_DOM"
    appToken = "909fa3df3b98c26a9221774fe5545afd"
    appKey = "b716b7eb938e9a46ad836e20de0f8b07"

    tms_appToken = "883b3289a5e3b55ceaddb2093834c13a"
    tms_appKey = "883b3289a5e3b55ceaddb2093834c13a574fda321ae620e2aa43c2117abb7553"


def get_token(target_page, token=None):
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


# 更新ali产品数据，把vendor和产品信息连接起来
@shared_task
def update_myproductali():
    dest_shop = "yallasale-com"
    sync_shop(dest_shop)
    products = MyProductAli.objects.filter()

    for ali_product in products:

        # 从链接获取供应商编号
        url = ali_product.url
        vendor_no = url.partition(".html")[0].rpartition("/")[2]
        print("url %s vendor_no %s" % (url, vendor_no))

        # 用供应商编号获取产品信息
        product = ShopifyProduct.objects.filter(vendor__exact=vendor_no, shop_name=dest_shop).first()
        print("product", product)
        print("vendor", vendor_no)

        # 在爆款管理中创建记录，并连接爆款记录和ali产品记录
        if product:
            obj, created = MyProductShopify.objects.update_or_create(
                vendor_no=vendor_no,
                defaults={
                    "product_no": product.product_no,
                    "handle": product.handle,
                }

            )

            MyProductAli.objects.filter(pk=ali_product.pk).update(

                vendor_no=vendor_no,
                posted_mainshop=True,
                handle=product.handle,
                product_no=product.product_no,

            )

    return True


# 从沙特站发布产品到主站
@shared_task
def post_to_mainshop():
    from .shop_action import post_new_product

    dest_shop = "yallasale-com"
    ori_shop = "yallavip-saudi"

    # 先分别同步源站和目标站的数据
    sync_shop(ori_shop)
    sync_shop(dest_shop)

    product_init = ShopifyProduct.objects.filter(Q(handle__startswith='a'), shop_name=dest_shop).order_by(
        '-product_no').first()
    print("主店最新的产品是 %s handle 是%s  供应商是 %s" % (product_init, product_init.handle, product_init.vendor))
    handle_i = product_init.handle

    handle_i = int(handle_i[1:5])
    print("handle_i %s" % (handle_i))

    latest_ori_product = ShopifyProduct.objects.filter(shop_name=ori_shop, vendor=product_init.vendor).order_by(
        '-product_no').first()
    print("沙特站最后更新的产品是 %s 供应商是 %s,product_no is %d " % (
        latest_ori_product, latest_ori_product.vendor, latest_ori_product.product_no))

    ori_products = ShopifyProduct.objects.filter(shop_name=ori_shop,
                                                 product_no__gt=latest_ori_product.product_no).order_by('product_no')

    total_to_update = len(ori_products)
    print("沙特站最新的还有 %d 需要发布" % (total_to_update))

    # 初始化SDK
    # shop_obj = Shop.objects.get(shop_name=dest_shop)
    # shop_url = "https://%s:%s@%s.myshopify.com" % (shop_obj.apikey, shop_obj.password, shop_obj.shop_name)

    for ori_product in ori_products:
        handle_i = handle_i + 1
        handle_new = "A" + str(handle_i).zfill(4)

        #####################
        new_product = post_new_product(dest_shop, ori_product, handle_new)
        ####################

        total_to_update = total_to_update - 1
        print("沙特站最新的还有 %d 需要发布" % (total_to_update))

    # 上传完后整体更新目标站数据
    sync_shop(dest_shop)


# 把拒签且未上架的产品发布到主站
@shared_task
def rejected_package():
    from logistic.models import Package

    from .shop_action import create_package_sku

    dest_shop = "yallasale-com"
    discount = 0.9
    min_product_no = 999999999999999

    packages = Package.objects.filter(deal="REFUSED", resell_status="NONE")
    n = 0

    for package in packages:
        order = Order.objects.filter(logistic_no=package.logistic_no).first()
        print("order", order)
        if not order:
            print("cannot find the order", package.logistic_no)
            continue

        product_no, sku_created = create_package_sku(dest_shop, order, discount)

        if sku_created:
            if product_no < min_product_no:
                min_product_no = product_no

            Package.objects.filter(pk=package.pk).update(resell_status="LISTING")

        n = n + 1
        if n > 10:
            break
        else:
            print("******", n)

    # 上传完后整体更新目标站数据
    sync_shop(dest_shop, min_product_no)

    return True


# 对过账，已退仓的上架二次销售
# 把拒签且未上架的产品发布到主站
@shared_task
def returned_package():
    from logistic.models import Package

    from .shop_action import create_package_sku

    dest_shop = "yallasale-com"
    discount = 0.9
    min_product_no = 999999999999999

    packages = Package.objects.filter(yallavip_package_status='RETURNED', resell_status="NONE")
    print("packages is ", packages)

    for package in packages:
        order = Order.objects.filter(logistic_no=package.logistic_no).first()
        print("order", order)
        if not order:
            print("cannot find the order", package.logistic_no)
            continue

        product_no, sku_created = create_package_sku(dest_shop, order, discount)
        print(order, "created", product_no)

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

    return True


# 生成海外仓包裹的视频
@shared_task
def package_video():
    from .video import get_order_video
    packages = MyProductPackage.objects.all()
    n = 0
    for package in packages:
        order = Order.objects.get(order_no=package.product_no)
        get_order_video(order)
        n = n + 1
        if n > 5:
            break


# 生成海外仓包裹的视频,使用Facebook的接口，上传图片直接生成slideshow
@shared_task
def package_slideshow():
    from .video import get_order_slideshow

    # package = MyProductPackage.objects.all().order_by("order_no").first()
    packages = MyProductPackage.objects.all()
    print("packages", packages)
    package = packages.first()
    order = Order.objects.filter(order_no=package.order_no).first()
    get_order_slideshow(order)


# 同步海外仓包裹的状态，已经发布到主站的信息，更新到prs里
@shared_task
def package_sync():
    from .shop_action import sycn_package

    sycn_package()
    return


# 扫描feed，匹配到产品
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
# 从沙特站发布产品到主站
############################
@shared_task
def post_saudi_mainshop():
    from .shop_action import post_saudi

    post_saudi()

    return


############################
#
# 随机选有动销的产品动图到活跃的page
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
    # 找出所有活跃的page
    pages = MyPage.objects.filter(active=True)
    n = 0
    for page in pages:
        # 遍历page对应的品类
        print("page is ", page)
        cates = ProductCategoryMypage.objects.filter(mypage__pk=page.pk)
        for cate in cates:
            cate_code = cate.productcategory.code
            album_name = cate.album_name
            print(cate_code)
            # 根据品类找未添加到fb产品库的产品

            # products_to_add = ShopifyProduct.objects.filter(category_code = cate_code,
            #                                                handle__startswith='a',myfb_product__isnull= True ,)

            # SELECT * FROM shop_shopifyproduct  A WHERE  category_code = "WOMEN_Bags_Handbags" and handle like 'a%' and id  NOT  IN  ( SELECT  B.myproduct_id FROM prs_myfbproduct B where mypage_id=14) order by created_at desc

            handle_like = 'a%'
            products_to_add = ShopifyProduct.objects.raw('SELECT * FROM shop_shopifyproduct  A WHERE '
                                                         'category_code = %s and handle like %s '
                                                         'and id  NOT  IN  ( SELECT  B.myproduct_id FROM prs_myfbproduct B where mypage_id=%s) order by published_at ',
                                                         [cate_code, handle_like, page.pk])

            # products_to_add = ShopifyProduct.objects.filter(category_code = cate_code)
            print("products_to_add", products_to_add)
            # print("products_to_add query", products_to_add.query)

            myfbproduct_list = []
            for product_to_add in products_to_add:
                n += 1
                print("     %d is %s" % (n, product_to_add))

                myfbproduct = MyFbProduct(
                    myproduct=ShopifyProduct.objects.get(pk=product_to_add.pk),
                    mypage=MyPage.objects.get(pk=page.pk),
                    obj_type="PHOTO",
                    cate_code=cate_code,
                    album_name=album_name,

                )
                myfbproduct_list.append(myfbproduct)

            MyFbProduct.objects.bulk_create(myfbproduct_list)


# 发布产品到Facebook的album
@shared_task
def sync_album_fbproduct():
    from fb.models import MyPhoto

    # 选择所有可用的page
    mypages = MyPage.objects.filter(active=True)
    print(mypages)
    for mypage in mypages:

        print("当前处理主页", mypage, mypage.pk)
        fbproducts = MyFbProduct.objects.filter(mypage__pk=mypage.pk, published=False)
        for fbproduct in fbproducts:
            photos = MyPhoto.objects.filter(page_no=mypage.page_no, name__icontains=fbproduct.myproduct.handle)
            print("处理 %s   %d  ", fbproduct.myproduct.handle, photos.count())
            if photos.count() > 0:
                photo = photos.first()
                MyFbProduct.objects.filter(mypage__pk=mypage.pk, myproduct__pk=fbproduct.myproduct.pk).update(
                    published=True,
                    fb_id=photo.photo_no,
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
    print("一共有%d 个1688链接待处理" % (aliproducts.count()))

    for aliproduct in aliproducts:
        offer_id = aliproduct.url.partition(".html")[0].rpartition("/")[2]
        cate_code = aliproduct.myproductcate.code
        message, status = get_ali_product_info(offer_id, cate_code)
        if status:
            MyProductAli.objects.filter(pk=aliproduct.pk).update(posted_mainshop=True)
        else:
            MyProductAli.objects.filter(pk=aliproduct.pk).update(post_error=message)


# 1.根据类目关键词抓取1688产品列表(offerid,cate_code)
@shared_task
def ali_cate_get_list():
    from .chrome import get_ali_list
    from .ali import get_cate_url
    from shop.models import ProductCategory
    cates = ProductCategory.objects.filter(~Q(keywords=""), keywords__isnull=False)

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
# 根据1688产品列表抓取产品详细信息（标题，规格，图片，价格）
@shared_task
def ali_list_get_info_shenjian():
    import shenjian

    user_key = "2aaa34471b-NjVhNDllMj"
    user_secret = "kyYWFhMzQ0NzFiNj-63e08890b765a49"
    appID = 3166948

    # service = shenjian.Service(user_key, user_secret)

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
        # 先抓供应商提供的产品列表

        aliproducts = AliProduct_vendor.objects.filter(got=False)[:100]
        url_list = []

        if aliproducts.exists():
            # url_list = aliproducts.values_list('ali_url', flat=True)

            for aliproduct in aliproducts:
                url_list.append(aliproduct.ali_url)
                AliProduct_vendor.objects.filter(pk=aliproduct.pk).update(got=True)

        else:
            print("供应商提供的产品列表没有需要爬取的了")

            # 抓类目生成的列表
            aliproducts = AliProduct.objects.filter(created=False, started=False)[:100]

            # print("一共有%d 个1688产品信息待抓取"%(aliproducts.count()))
            url_list = []
            for aliproduct in aliproducts:
                url_list.append("https://detail.1688.com/offer/%s.html" % (aliproduct.offer_id))
                AliProduct.objects.filter(pk=aliproduct.pk).update(started=True)

        params = {}

        # params["crawlType"] = 3
        params["productUrl[]"] = url_list
        # params["crawlDetail"] = False

        # 创建爬虫类shenjian.Crawler
        crawler = shenjian.Crawler(user_key, user_secret, appID)
        try:
            print("自定义设置")
            result = crawler.config_custom(params)
        except Exception as e:
            print("自定义设置出错", str(e))
            return False

        print("爬虫自定义设置结果", result)

        result = crawler.start()
        print("爬虫启动", result)
    else:
        print("爬取中，等待")

    return True


# 根据1688产品列表抓取产品详细信息（标题，规格，图片，价格）
@shared_task
def ali_url_get_info_shenjian():
    import shenjian

    user_key = "2aaa34471b-NjVhNDllMj"
    user_secret = "kyYWFhMzQ0NzFiNj-63e08890b765a49"
    appID = 3166948

    # service = shenjian.Service(user_key, user_secret)

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
        ali_urls = AliProduct_vendor.objects.filter(got=False).values_list('ali_url', flat=True)[:100]
        if not ali_urls.exists():
            print("没有需要爬取的了")
            return False

        # print("一共有%d 个1688产品信息待抓取"%(aliproducts.count()))

        params = {}

        # params["crawlType"] = 3
        params["productUrl[]"] = ali_urls
        # params["crawlDetail"] = False

        # 创建爬虫类shenjian.Crawler
        crawler = shenjian.Crawler(user_key, user_secret, appID)
        try:
            print("自定义设置")
            result = crawler.config_custom(params)
        except Exception as e:
            print("自定义设置出错", str(e))
            return False

        print("爬虫自定义设置结果", result)

        result = crawler.start()
        print("爬虫启动", result)
    else:
        print("爬取中，等待")

    return True


# 2,根据1688产品列表抓取产品详细信息（标题，规格，图片，价格）
@shared_task
def ali_list_get_info():
    aliproducts = AliProduct.objects.filter(created=False)[:10]
    print("一共有%d 个1688产品信息待抓取" % (aliproducts.count()))

    for aliproduct in aliproducts:
        offer_id = aliproduct.offer_id
        cate_code = aliproduct.cate_code
        # get_aliproduct.apply_async((aliproduct.pk, offer_id,cate_code),queue="ali")
        get_aliproduct(aliproduct.pk, offer_id, cate_code)


@task
def get_aliproduct(pk, offer_id, cate_code):
    from .ali import get_ali_product_info
    import time

    time.sleep(random.uniform(30, 60))
    message, status = get_ali_product_info(offer_id, cate_code)
    if status is False:
        AliProduct.objects.filter(pk=pk).update(created_error=message)


# 3,将1688产品详细信息发布到shopfiy店铺
@shared_task
def post_ali_shopify():
    dest_shop = "yallasale-com"
    # ori_shop = "yallavip-saudi"

    # sync_shop(ori_shop)
    sync_shop(dest_shop)

    aliproducts = AliProduct.objects.filter(created=True, published=False, stopped=False)
    print("一共有%d 个1688产品信息待发布" % (aliproducts.count()))
    for aliproduct in aliproducts:
        post_to_shopify.delay(aliproduct.pk)


# 3,将1688产品详细信息发布到shopfiy店铺
@shared_task
def post_ali_shopify_shenjian():
    dest_shop = "yallasale-com"
    # ori_shop = "yallavip-saudi"

    # sync_shop(ori_shop)
    sync_shop(dest_shop)

    aliproducts = AliProduct.objects.filter(created=True, published=False)
    print("一共有%d 个1688产品信息待发布" % (aliproducts.count()))
    for aliproduct in aliproducts:
        post_to_shopify_shenjian.delay(aliproduct.pk)


@task
def post_to_shopify_shenjian(aliproduct_pk):
    from .ali import create_body_shenjian, create_variant_shenjian
    from django.utils import timezone as datetime
    dest_shop = "yallasale-com"

    aliproduct = AliProduct.objects.get(pk=aliproduct_pk)

    vendor_no = aliproduct.offer_id
    print("vendor_no", vendor_no)

    dest_products = ShopifyProduct.objects.filter(shop_name=dest_shop, vendor=vendor_no)

    if dest_products:
        print("这个产品已经发布过了！！！！", vendor_no)
        # 把以前的删了重新发布
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

    # shop_obj = Shop.objects.get(shop_name=dest_shop)
    # max_id = shop_obj.max_id + 1

    shopifyproduct = create_body_shenjian(aliproduct)
    if shopifyproduct is not None:
        posted = create_variant_shenjian(aliproduct, shopifyproduct)
        if posted is not None:
            print("创建新产品成功")
            AliProduct.objects.filter(pk=aliproduct.pk).update(published=True, handle=posted.get("handle"),
                                                               title=posted.get("title"),

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
def post_to_shopify(aliproduct_pk):
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
    # shop_obj = Shop.objects.get(shop_name=dest_shop)
    # max_id = shop_obj.max_id + 1

    shopifyproduct = create_body(aliproduct)
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
        # 遍历page对应的品类
        print("page is ", page)
        cates = ProductCategoryMypage.objects.filter(mypage__pk=page.pk)
        for cate in cates:
            cate_code = cate.productcategory.code
            album_name = cate.album_name
            album_no = cate.album_no

            # 根据品类找已经上架到shopify 但还未添加到fb接触点（新）的产品
            products_to_add = AliProduct.objects.raw('SELECT * FROM prs_aliproduct  A WHERE '
                                                     'cate_code = %s and published = TRUE  '
                                                     'and id  NOT  IN  ( SELECT  B.myaliproduct_id FROM prs_myfbproduct B where mypage_id=%s and B.myaliproduct_id is not NULL) ',
                                                     [cate_code, page.pk], )
            # order by rand() limit 30
            print("products_to_add", page, cate_code, len(products_to_add))

            myfbproduct_list = []
            for product_to_add in products_to_add:
                # n += 1
                # print("     %d is %s" % (n, product_to_add))

                myfbproduct = MyFbProduct(
                    myaliproduct=AliProduct.objects.get(pk=product_to_add.pk),
                    # myproduct=ShopifyProduct.objects.filter(vendor=product_to_add.offer_id).first(),
                    mypage=MyPage.objects.get(pk=page.pk),
                    obj_type="PHOTO",
                    cate_code=cate_code,
                    album_name=album_name,
                    album_no=album_no,

                )
                #                print(myfbproduct, AliProduct.objects.get(pk=product_to_add.pk),MyPage.objects.get(pk=page.pk),cate_code,album_name, )
                myfbproduct_list.append(myfbproduct)

            print(myfbproduct_list)
            MyFbProduct.objects.bulk_create(myfbproduct_list)


# 4,1 将shopify产品发布到相册
# 发布产品到Facebook的album
@shared_task
def post_newproduct_album():
    # 选择所有可用的page
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
    from .fb_action import post_photo_to_album
    from fb.models import MyAlbum

    products = MyFbProduct.objects.filter(mypage__pk=mypage.pk, published=False, album_name=album_name,
                                          myaliproduct__handle__startswith='b').order_by("-id")
    print("###############这次需要发的产品", products.count(), products)
    if products is None or products.count() == 0:
        print("没有产品可发布了")
        return

    # 发到指定相册

    n = 0
    for product in products:
        myproduct = product.myaliproduct
        album_no = MyAlbum.objects.get(page_no=mypage.page_no, name=album_name).album_no

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
            print("发布新产品到相册失败 page_pk %s  album %s product_pk %s   error   %s" % (
                mypage.pk, album_name, myproduct.pk, error))
            MyFbProduct.objects.filter(mypage__pk=mypage.pk, myaliproduct__pk=product.myaliproduct.pk).update(
                myproduct=myproduct,
                published=False,
                publish_error=error[:90],
                published_time=datetime.now()
            )


#####################################################################
# 4,0 把shopify产品库中的还未添加到fb产品库的产品按page对应的品类找出来并添加
#######准备工作，每次从1688上新到shopify后调用一次即可
######################################################################
@shared_task
def product_shopify_to_fb():
    # 找出所有活跃的page
    pages = MyPage.objects.filter(active=True)
    n = 0
    for page in pages:
        # 遍历page对应的品类
        print("page is ", page)
        cates = ProductCategoryMypage.objects.filter(mypage__pk=page.pk)
        for cate in cates:
            cate_code = cate.productcategory.code
            album_name = cate.album_name
            print(cate_code)
            # 根据品类找未添加到fb产品库的产品

            # products_to_add = ShopifyProduct.objects.filter(category_code = cate_code,
            #                                                handle__startswith='a',myfb_product__isnull= True ,)

            # SELECT * FROM shop_shopifyproduct  A WHERE  category_code = "WOMEN_Bags_Handbags" and handle like 'a%' and id  NOT  IN  ( SELECT  B.myproduct_id FROM prs_myfbproduct B where mypage_id=14) order by created_at desc

            handle_like = 'b%'
            products_to_add = ShopifyProduct.objects.raw('SELECT * FROM shop_shopifyproduct  A WHERE '
                                                         'category_code = %s and handle like %s '
                                                         'and id  NOT  IN  ( SELECT  B.myproduct_id FROM prs_myfbproduct B where mypage_id=%s) order by published_at ',
                                                         [cate_code, handle_like, page.pk])

            # products_to_add = ShopifyProduct.objects.filter(category_code = cate_code)
            print("products_to_add", products_to_add)
            # print("products_to_add query", products_to_add.query)

            myfbproduct_list = []
            for product_to_add in products_to_add:
                n += 1
                print("     %d is %s" % (n, product_to_add))

                myfbproduct = MyFbProduct(
                    myproduct=ShopifyProduct.objects.get(pk=product_to_add.pk),
                    mypage=MyPage.objects.get(pk=page.pk),
                    obj_type="PHOTO",
                    cate_code=cate_code,
                    album_name=album_name,

                )
                myfbproduct_list.append(myfbproduct)

            MyFbProduct.objects.bulk_create(myfbproduct_list)


# 4,1 将shopify产品发布到相册
# 发布产品到Facebook的album
@shared_task
def post_to_album():
    from .fb_action import post_photo_to_album
    from fb.models import MyAlbum

    # 选择所有可用的page
    mypages = MyPage.objects.filter(active=True)
    print(mypages)
    for mypage in mypages:

        print("当前处理主页", mypage, mypage.pk)

        # 主页已有的相册
        album_dict = {}
        albums = MyAlbum.objects.filter(page_no=mypage.page_no, active=True)

        for album in albums:
            album_dict[album.name] = album.album_no

        # print("当前主页已有相册", album_dict)

        albums = MyFbProduct.objects.filter(mypage__pk=mypage.pk, published=False) \
            .values_list('album_name').annotate(product_count=Count('id')).order_by('-product_count')

        print("当前主页待处理产品相册", albums)

        album_list = []
        for album in albums:
            if album[1] > 0:
                if len(album[0]) > 3:
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

        if not target_album_no:
            print("此相册还没有创建，请新建一个")
            continue
        print("target_album %s" % (album_list))

        # 发到指定相册
        products = MyFbProduct.objects.filter(mypage__pk=mypage.pk, published=False, album_name=album_name,
                                              myproduct__handle__startswith='b').order_by("-id")
        n = 0
        for product in products:
            posted = post_photo_to_album(mypage, target_album_no, product.myproduct)

            if posted:
                MyFbProduct.objects.filter(mypage__pk=mypage.pk, myproduct__pk=product.myproduct.pk).update(
                    fb_id=posted,
                    published=True,
                    published_time=datetime.now()
                )
                print("更新page_类目记录 page_pk %s  product_pk %s   photo_id   %s" % (
                    mypage.pk, product.myproduct.pk, posted))
                # print("created is ", created)
                # print("obj is ", obj)
                n += 1
                if n > 5:
                    break
            else:
                MyFbProduct.objects.filter(mypage__pk=mypage.pk, myproduct__pk=product.myproduct.pk).update(
                    published=False,
                    publish_error="发布失败",
                    published_time=datetime.now()
                )

    return


# 5,爆款生成动图发布到feed
############################
#
# 随机选有动销的产品动图到活跃的page
#
############################
@shared_task
def product_feed():
    from .fb_action import post_album_feed

    post_album_feed()
    # post_product_feed()

    return


# 6,创意发布到feed
#####################################
#########把创意发到feed
######################################
@shared_task
def creative_feed():
    from .fb_action import post_creative_feed

    post_creative_feed()
    return


# 7,


##########海外仓包裹从fb下架
### 1  找到已销售的包裹
### 2  从Facebook照片里找到对应的photo id， 删除
### 3, 从Facebook feed里找到对应的帖子 id， 删除

def unlisting_overseas_package():
    from fb.models import MyPhoto

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

            myphotos = MyPhoto.objects.filter(name__icontains=sku_name, page_no=mypage.page_no)

            print("myphotos %s" % (myphotos), myphotos.count())
            if myphotos is None or myphotos.count() == 0:
                continue

            FacebookAdsApi.init(access_token=get_token(mypage.page_no))
            n = 1
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
                    print("%s response is %s" % (n, response))
                    n += 1
                except:
                    continue

            # 修改数据库记录
            myphotos.update(listing_status=False)

            ShopifyVariant.objects.filter(sku=sku).update(supply_status="STOP", listing_status=False)

            Order.objects.filter(pk=order_detail.order.pk).update(resell_status='SELLING')


def unlisting_overseas_package_new():
    from fb.models import MyPhoto

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

            myphotos = MyPhoto.objects.filter(name__icontains=sku_name, page_no=mypage.page_no)

            print("myphotos %s" % (myphotos), myphotos.count())
            if myphotos is None or myphotos.count() == 0:
                continue

            FacebookAdsApi.init(access_token=get_token(mypage.page_no))
            n = 1
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
                    print("%s response is %s" % (n, response))
                    n += 1
                except:
                    continue

            # 修改数据库记录
            myphotos.update(listing_status=False)

            ShopifyVariant.objects.filter(sku=sku).update(supply_status="STOP", listing_status=False)
            Order.objects.filter(pk=order_detail.order.pk).update(resell_status='SELLING')


def sync_aliproduct_shopify():
    from django.utils import timezone as datetime

    aliproducts = AliProduct.objects.filter(created=True)
    print("一共有%d 个1688产品信息待同步" % (aliproducts.count()))

    for aliproduct in aliproducts:
        dest_products = ShopifyProduct.objects.filter(vendor=aliproduct.offer_id)

        if dest_products.exists():

            print("这个产品已经发布过了！！！！", aliproduct.offer_id, dest_products)
            AliProduct.objects.filter(pk=aliproduct.pk).update(published=True, published_time=datetime.now(),
                                                               publish_error="")
        else:
            print("还没有发布过 ######", aliproduct.offer_id)
            AliProduct.objects.filter(pk=aliproduct.pk).update(published=False, published_time=None,
                                                               publish_error="")


def complete_aliproduct_shopify():
    from django.utils import timezone as datetime

    # aliproducts = AliProduct.objects.filter(created=True,published=True,handle="")
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

    # 抓取隐藏的属性图片
    # lightinproducts = Lightin_SPU.objects.filter(~(Q(attr_image_dict="{}")|Q(attr_image_dict="")),got=False,got_error="无" , sellable__gt=0)

    # 抓取没有属性图片字典
    lightinproducts = Lightin_SPU.objects.filter(~(Q(attr_image_dict="{}") | Q(attr_image_dict="")),
                                                 spu_sku__skuattr__contains="Color", sellable__gt=0)

    n = lightinproducts.count()
    print("一共有%d 个lightin链接待处理" % (n))

    for lightinproduct in lightinproducts:
        print("还有%d 个lightin链接待处理" % (n))
        message, status = get_lightin_product_info(lightinproduct.SPU, lightinproduct.link)
        if status:
            print("成功！")
        else:
            print("失败！！！", message)
            # 更新产品记录
            Lightin_SPU.objects.update_or_create(
                SPU=lightinproduct.SPU,
                defaults={
                    "got_error": message,
                    "got_time": dt.now()

                }
            )
        n -= 1


# 3,将产品详细信息发布到shopfiy店铺
@shared_task
def post_lightin_shopify():
    dest_shop = "yallasale-com"
    # ori_shop = "yallavip-saudi"

    # sync_shop(ori_shop)
    sync_shop(dest_shop)

    lightinproducts = Lightin_SPU.objects.filter(got=True, published=False, publish_error="无")
    print("一共有%d 个lightin产品信息待发布" % (lightinproducts.count()))
    n = 0
    for lightinproduct in lightinproducts:
        # post_to_shopify_lightin.delay(lightinproduct.pk)
        post_to_shopify_lightin(lightinproduct.pk)
        '''
        n += 1
        if n>10:
            break
        '''


def post_to_shopify_lightin(lightinproduct_pk):
    from .ali import create_body_lightin, create_variant_lightin
    from django.utils import timezone as datetime
    dest_shop = "yallasale-com"

    lightin_spu = Lightin_SPU.objects.get(pk=lightinproduct_pk)

    vendor_no = lightin_spu.SPU
    print("vendor_no", vendor_no)

    dest_products = ShopifyProduct.objects.filter(shop_name=dest_shop, vendor=vendor_no)

    if dest_products:
        print("这个产品已经发布过了！！！！", vendor_no)
        # 把以前的删了重新发布
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

    # shop_obj = Shop.objects.get(shop_name=dest_shop)
    # max_id = shop_obj.max_id + 1

    shopifyproduct = create_body_lightin(lightin_spu)
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


# 更新产品标题，把货号加在后面，便于客服下单
# 把5Sar一下的产品，标题里加个[freegift]

@shared_task
def update_lightin_shopify_title():
    dest_shop = "yallasale-com"
    shop_obj = Shop.objects.get(shop_name=dest_shop)
    # 初始化SDK
    shop_url = "https://%s:%s@%s.myshopify.com" % (shop_obj.apikey, shop_obj.password, shop_obj.shop_name)

    # 为了加货号
    # lightinproducts = Lightin_SPU.objects.filter(got = True, published=True, updated=False)

    # 找出5sar以下的产品
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
def update_shopify_title_lightin(lightin_spu, shop_url):
    from .ali import create_body_lightin, create_variant_lightin
    from django.utils import timezone as datetime

    # 标题里加货号
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
    if r.status_code == 200:
        Lightin_SPU.objects.filter(pk=lightin_spu.pk).update(updated=True, title=title)
    else:
        print(r.text)


@shared_task
def prepare_lightin_album():
    from django.db import connection, transaction
    cursor = connection.cursor()

    # 找出所有活跃的page
    pages = MyPage.objects.filter(active=True)
    for page in pages:
        # 遍历page对应的相册
        print("page is ", page)
        albums = MyAlbum.objects.filter(Q(cates__isnull=False) | Q(prices__isnull=False) | Q(attrs__isnull=False),
                                        mypage__pk=page.pk, )
        print("albums is ", albums)
        for album in albums:
            is_sku = False
            print("album is ", album)

            # 拼接相册的筛选产品的条件
            q_cate = Q()
            q_cate.connector = 'AND'
            if album.cates:
                if album.cates == "Combo":
                    is_sku = True
                    q_cate.children.append(('comboed', True))
                    q_cate.children.append(('o_sellable__gt', 0))
                else:
                    for cate in album.cates.split(","):
                        q_cate.children.append(('breadcrumb__contains', cate))

            q_price = Q()
            q_price.connector = 'AND'
            if album.prices:
                prices = album.prices.split(",")
                if is_sku:
                    q_price.children.append(('sku_price__gt', prices[0]))
                    q_price.children.append(('sku_price__lte', prices[1]))
                else:
                    q_price.children.append(('shopify_price__gt', prices[0]))
                    q_price.children.append(('shopify_price__lte', prices[1]))

            q_attr = Q()
            q_attr.connector = 'OR'
            if album.attrs:
                for attr in album.attrs.split(","):
                    q_attr.children.append(('spu_sku__skuattr__contains', attr))

            con = Q()
            con.add(q_cate, 'AND')
            con.add(q_price, 'AND')
            con.add(q_attr, 'AND')

            # 根据品类找已经上架到shopify 但还未添加到相册的产品

            print(con)
            product_list = []

            if is_sku:
                skus_to_add = Lightin_SKU.objects.filter(con, listed=True, locked=True, imaged=True).exclude(id__in=
                LightinAlbum.objects.filter(
                    myalbum__pk=album.pk,
                    lightin_sku__isnull=False).values_list(
                    'lightin_sku__id',
                    flat=True)).distinct()

                for sku_to_add in skus_to_add:

                    name = "[" + sku_to_add.SKU + "]"
                    items = sku_to_add.combo_item.all().values_list("lightin_sku__SKU", flat=True)
                    for item in items:
                        name = name + "\n" + item
                    name = name + "\n\nPrice:  " + str(sku_to_add.sku_price) + "SAR"

                    product = LightinAlbum(
                        lightin_sku=Lightin_SKU.objects.get(pk=sku_to_add.pk),
                        myalbum=MyAlbum.objects.get(pk=album.pk),
                        name=name

                    )
                    product_list.append(product)

            else:
                products_to_add = Lightin_SPU.objects.filter(con, published=True).exclude(id__in=
                LightinAlbum.objects.filter(
                    myalbum__pk=album.pk,
                    lightin_spu__isnull=False).values_list(
                    'lightin_spu__id',
                    flat=True)).distinct()

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
    # 批次号
    batch_no = LightinAlbum.objects.all().aggregate(Max('batch_no')).get("batch_no__max") + 1

    # 分相册随机选产品

    lightinalbums_all = LightinAlbum.objects.filter(published=False, publish_error="无", material=False,
                                                    material_error="无", batch_no=0)

    albums_list = lightinalbums_all.distinct().values_list('myalbum', flat=True)
    print("albums_list is ", albums_list)

    for album in albums_list:
        lightinalbums = lightinalbums_all.filter(myalbum__pk=album).order_by('?')[:9]
        print(lightinalbums)

        for lightinalbum in lightinalbums:
            spu = lightinalbum.lightin_spu
            sku = lightinalbum.lightin_sku

            if sku:
                LightinAlbum.objects.filter(pk=lightinalbum.pk).update(
                    image_marked=sku.image_marked,
                    batch_no=batch_no,
                    material=True
                )

            elif spu:

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

                if len(options) > 0:
                    name = name + "\n\nSkus:  "

                for option in options:
                    name = name + "\n\n   " + option

                # 价格
                price1 = int(spu.shopify_price)
                price2 = int(price1 * random.uniform(5, 6))
                # 为了减少促销的麻烦，文案里不写价格了
                # name = name + "\n\nPrice:  " + str(price1) + "SAR"

                # 准备图片
                # 先取第一张，以后考虑根据实际有库存的sku的图片（待优化）
                if spu.images_dict:
                    image = json.loads(spu.images_dict).values()
                    if image and len(image) > 0:
                        a = "/"
                        image_split = list(image)[0].split(a)

                        image_split[4] = '800x800'
                        image = a.join(image_split)

                    # 打水印
                    # logo， page促销标
                    # 如果有相册促销标，就打相册促销标，否则打价格标签

                    image_marked, image_marked_url = lightin_mark_image(image, spu.handle, str(price1), str(price2),
                                                                        lightinalbum)
                    if not image_marked:
                        error = "打水印失败"

                else:
                    print(album, spu.SPU, "没有图片")
                    error = "没有图片"

                if error == "":
                    LightinAlbum.objects.filter(pk=lightinalbum.pk).update(
                        name=name,
                        image_marked=image_marked_url,
                        batch_no=batch_no,
                        material=True
                    )
                else:
                    LightinAlbum.objects.filter(pk=lightinalbum.pk).update(
                        material_error=error
                    )


@shared_task
def sync_lightin_album(album_name=None):
    from django.db.models import Min

    # 之前只考虑一次统一发一个批次，但因为各个相册建立的时间不同，批次差异很大，所以必须按相册找到当前需要发的批次
    if album_name:
        lightinalbums_all = LightinAlbum.objects.filter(
            Q(lightin_spu__sellable__gt=0) | Q(lightin_sku__o_sellable__gt=0),
            published=False, publish_error="无",
            material=True, myalbum__name__contains=album_name)
    else:
        lightinalbums_all = LightinAlbum.objects.filter(
            Q(lightin_spu__sellable__gt=0) | Q(lightin_sku__o_sellable__gt=0),
            published=False, publish_error="无", material=True)

    batch_nos = lightinalbums_all.values_list('myalbum').annotate(Min('batch_no'))
    print("有%s个相册待更新" % (batch_nos.count()))
    for batch_no in batch_nos:
        lightinalbums = lightinalbums_all.filter(myalbum__pk=batch_no[0], batch_no=batch_no[1])
        print("相册%s 批次 %s 有%s 个图片待发" % (batch_no[0], batch_no[1], lightinalbums.count()))
        sync_lightin_album_batch(lightinalbums)

        # 把比当前批次号小 20 的批次的图片 还在发布状态的从Facebook删除

        delete_outdate_lightin_album(batch_no)


# 把图片发到Facebook相册
def sync_lightin_album_batch(lightinalbums):
    from .fb_action import post_lightin_album

    for lightinalbum in lightinalbums:
        error, posted = post_lightin_album(lightinalbum)

        # 更新Facebook图片数据库记录

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


# 把比当前批次号，且还在发布状态的从Facebook删除
def delete_outdate_lightin_album(batch_no):
    # 按批次号找出子集
    if batch_no[1] > 20:
        lightinalbums_outdate = LightinAlbum.objects.filter(published=True, myalbum__pk=batch_no[0],
                                                            batch_no=batch_no[1] - 20, )

        # 删除子集
        delete_out_lightin_album(lightinalbums_outdate)


# 把所有sku都没有库存，spu还在发布状态的从Facebook删除
@shared_task
def delete_outstock_lightin_album():
    # 更新还在发布中的spu的库存
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

    '''
    # 先初始化spu的库存
    mysql = "UPDATE prs_lightin_spu INNER JOIN (SELECT SPU, sum(o_sellable) as quantity FROM prs_lightin_sku GROUP BY SPU ) b ON prs_lightin_spu.SPU = b.SPU) SET prs_lightin_spu.sellable = b.quantity"
    my_custom_sql(mysql)
    '''

    # 每天更新一次所有在发布的图片，每分钟更新一次订单sku对应的图片
    lightinalbums_all = LightinAlbum.objects.filter(Q(lightin_spu__sellable__lte=0) | Q(lightin_sku__o_sellable__lte=0),
                                                    published=True).values_list("myalbum__page_no", "fb_id").order_by(
        "myalbum__page_no")
    print("一共有%s 个图片待删除" % (lightinalbums_all.count()))

    lightinalbums_out = {}

    for lightinalbum in lightinalbums_all:
        page_no = lightinalbum[0]
        fb_id = lightinalbum[1]
        photo_list = lightinalbums_out.get(page_no)
        if not photo_list:
            photo_list = []

        if fb_id not in photo_list:
            photo_list.append(fb_id)

        lightinalbums_out[page_no] = photo_list

    # 删除子集

    delete_out_lightin_album(lightinalbums_out)
    if not all:
        Order.objects.filter(updated=True).update(updated=False)

    delete_missed_photo()
    delete_oversea_photo()


# 删除lightin_album 的某个特定子集
def delete_out_lightin_album(lightinalbums_out):
    from facebook_business.api import FacebookAdsApi

    # 选择所有可用的page

    for page_no in lightinalbums_out:
        FacebookAdsApi.init(access_token=get_token(page_no))

        photo_nos = lightinalbums_out[page_no]
        print("page %s 待删除数量 %s  " % (page_no, len(photo_nos)))
        if photo_nos is None or len(photo_nos) == 0:
            continue

        delete_photos(photo_nos)


# 删除重复发布且已下架的图片

def delete_missed_photo():
    from facebook_business.api import FacebookAdsApi
    from fb.models import MyPhoto

    # 找出已下架商品的handle
    handles = Lightin_SPU.objects.filter(sellable__lte=0).values_list("handle", flat=True).distinct()

    photo_miss = {}
    # 在fb的图片里找handle的图片
    for handle in handles:
        myphotos = MyPhoto.objects.filter(name__contains=handle, active=True)
        photos = myphotos.values_list("page_no", "photo_no").distinct()
        for photo in photos:
            page_no = photo[0]
            fb_id = photo[1]
            photo_list = photo_miss.get(page_no)
            if not photo_list:
                photo_list = []

            if fb_id not in photo_list:
                photo_list.append(fb_id)

            photo_miss[page_no] = photo_list

        myphotos.delete()

    # 选择所有可用的page
    for page_no in photo_miss:
        FacebookAdsApi.init(access_token=get_token(page_no))

        photo_nos = photo_miss[page_no]
        print("page %s 待删除数量 %s  " % (page_no, len(photo_nos)))
        if photo_nos is None or len(photo_nos) == 0:
            continue

        delete_photos(photo_nos)


# 删除那些找不到库存的图片
# 找到所有的可疑图片，查找对应的库存

def delete_lost_photo(what):
    from facebook_business.api import FacebookAdsApi
    from fb.models import MyPhoto
    from django.db.models import Sum
    import re

    # 在fb的图片里找含what(579815 \ l00 \ c00 之类的，某种特征字符)的图片
    myphotos = MyPhoto.objects.filter(name__contains=what, active=True)

    photo_miss = {}
    photos = myphotos.values_list("page_no", "photo_no", "name").distinct()
    for photo in photos:
        page_no = photo[0]
        fb_id = photo[1]
        name = photo[2]
        pos = name.find(what)
        a = name[pos:pos + 12]
        b = re.findall("\d+", a)
        sku = "-".join(b)

        SKU = Lightin_SKU.objects.filter(SKU=sku)
        # 如果找不到或者可售库存小于0，就删除
        if not SKU or SKU.aggregate(nums=Sum('o_sellable')).get("nums") <= 0:
            photo_list = photo_miss.get(page_no)
            if not photo_list:
                photo_list = []
            if fb_id not in photo_list:
                photo_list.append(fb_id)

            photo_miss[page_no] = photo_list

    # 选择所有可用的page
    for page_no in photo_miss:
        FacebookAdsApi.init(access_token=get_token(page_no))

        photo_nos = photo_miss[page_no]
        print("page %s 待删除数量 %s  " % (page_no, len(photo_nos)))
        if photo_nos is None or len(photo_nos) == 0:
            continue

        delete_photos(photo_nos)


# 删除缺货的组合商品
# 组合库存减为0， 自动释放组合占用库存
# 删除图片
# shopify的库存减为0 (还没实现)
def delete_combo_photo():
    from facebook_business.api import FacebookAdsApi
    from fb.models import MyPhoto

    # 找出缺货的组合商品
    combo_SKUs = ComboItem.objects.filter(lightin_sku__o_sellable__lt=0).values_list("combo__SKU", flat=True).distinct()

    photo_miss = {}
    # 在fb的图片里找combo_SKU的图片
    for combo_SKU in combo_SKUs:
        myphotos = MyPhoto.objects.filter(name__contains=combo_SKU, active=True)
        print("当前处理组合 ", combo_SKU, myphotos.count())
        photos = myphotos.values_list("page_no", "photo_no").distinct()
        for photo in photos:
            page_no = photo[0]
            fb_id = photo[1]
            photo_list = photo_miss.get(page_no)
            if not photo_list:
                photo_list = []

            if fb_id not in photo_list:
                photo_list.append(fb_id)

            photo_miss[page_no] = photo_list

        myphotos.delete()

    # 选择所有可用的page
    for page_no in photo_miss:
        FacebookAdsApi.init(access_token=get_token(page_no))

        photo_nos = photo_miss[page_no]
        print("page %s 待删除数量 %s  " % (page_no, len(photo_nos)))
        if photo_nos is None or len(photo_nos) == 0:
            continue

        delete_photos(photo_nos)


# 删除无货的海外仓包裹
def delete_oversea_photo():
    from facebook_business.api import FacebookAdsApi
    from fb.models import MyPhoto

    # 找出已下架商品的handle
    handles = Lightin_SKU.objects.filter(o_sellable__lte=0, SKU__startswith="579815").values_list("SKU",
                                                                                                  flat=True).distinct()

    photo_miss = {}
    # 在fb的图片里找handle的图片
    for handle in handles:
        myphotos = MyPhoto.objects.filter(name__contains=handle)
        print("当前处理包裹 ", handle, myphotos.count())
        photos = myphotos.values_list("page_no", "photo_no").distinct()
        for photo in photos:
            page_no = photo[0]
            fb_id = photo[1]
            photo_list = photo_miss.get(page_no)
            if not photo_list:
                photo_list = []

            if fb_id not in photo_list:
                photo_list.append(fb_id)

            photo_miss[page_no] = photo_list

        myphotos.delete()

    # 选择所有可用的page
    for page_no in photo_miss:
        FacebookAdsApi.init(access_token=get_token(page_no))

        photo_nos = photo_miss[page_no]
        print("page %s 待删除数量 %s  " % (page_no, len(photo_nos)))
        if photo_nos is None or len(photo_nos) == 0:
            continue

        delete_photos(photo_nos)


def delete_photos(photo_nos):
    from facebook_business.adobjects.photo import Photo

    for photo_no in photo_nos:

        fields = [
        ]
        params = {

        }
        error = ""
        try:

            response = Photo(photo_no).api_delete(
                fields=fields,
                params=params,
            )

            # response = "delete photo_no "+ photo_no
        except Exception as e:
            print("删除图片出错", photo_no, e)
            error = "删除图片出错"
            # continue
        # 更新lightinalbum的发布记录
        # print("facebook 返回结果",response)
        LightinAlbum.objects.filter(fb_id=photo_no).update(

            published=False,
            deleted=True,
            delete_error=error,
            deleted_time=dt.now()

        )
        print("删除相册图片 LightinAlbum %s" % (photo_no))


@shared_task
def mapping_orders_lightin():
    from django.db.models import Sum
    from prs.models import Lightin_barcode

    # orders = Order.objects.raw(  'SELECT * FROM orders_order  A WHERE financial_status = "paid" and  inventory_status <> "库存锁定"')
    # orders = Order.objects.filter(financial_status = "paid", fulfillment_status__isnull=True,status = "open").order_by("verify__sms_status")
    orders = Order.objects.filter(financial_status="paid",
                                  fulfillment_status__isnull=True,
                                  status="open",
                                  verify__verify_status="SUCCESS",
                                  verify__sms_status="CHECKED",
                                  wms_status="")

    print("一共有 %s 个订单待处理", orders.count())

    # 处理每个订单
    for order in orders:
        mapping_order_lightin(order)


def mapping_order_lightin(order):
    # 先把自己可能占用的库存释放
    OrderDetail_lightin.objects.filter(order=order).delete()

    inventory_list = []
    error = ""

    orderdetails = order.order_orderdetail.all()
    print("当前处理订单 ", order)

    # 每个订单项
    for orderdetail in orderdetails:
        # sku = orderdetail.sku
        sku_list = ["13531030880298", "price gap", "COD link", "price gap 2", ]
        if orderdetail.sku in sku_list:
            continue

        try:
            SKU = Lightin_SKU.objects.get(SKU=orderdetail.sku)
        except:
            print(orderdetail.sku)
            error = "找不到sku"
            break

        price = orderdetail.price
        quantity = int(float(orderdetail.product_quantity))
        print("sku %s , 需求量 %s 价格 %s" % (SKU, quantity, price))

        # 组合商品需要进一步拆分成item，然后映射
        # 非组合商品， item = sku
        if SKU.comboed:
            items = SKU.combo_item.values_list("SKU", flat=True)
        else:
            items = [SKU]

        for item in items:
            item_inventory_list, error = get_barcodes(item, quantity, price)
            if error == "":
                inventory_list += item_inventory_list
            else:
                break

    if error == "":
        print("映射成功", inventory_list)
        # 插入到OrderDetail_lightin
        orderdetail_lightin_list = []

        for inventory in inventory_list:
            orderdetail_lightin = OrderDetail_lightin(
                order=order,
                SKU=inventory[0],
                barcode=inventory[1],
                quantity=inventory[2],
                price=inventory[3],
            )
            orderdetail_lightin_list.append(orderdetail_lightin)

        OrderDetail_lightin.objects.bulk_create(orderdetail_lightin_list)
    else:
        print("映射不成功", error)

    return error


def get_barcodes(sku, quantity, price):
    inventory_list = []
    lightin_barcodes = Lightin_barcode.objects.filter(SKU=sku)

    if lightin_barcodes is None:
        print("找不到映射，也就意味着无法管理库存！")
        # 需要标识为异常订单
        error = "找不到SKU"
        return None, error

    # 每个可能的条码
    for lightin_barcode in lightin_barcodes:
        print("处理每个可能的条码")
        if quantity == 0:
            # 已经凑齐了sku所需的数量
            break
        if lightin_barcode.sellable <= 0:
            continue

        if quantity > lightin_barcode.sellable:
            # 条码的库存数量比订单项所需的少
            quantity -= lightin_barcode.sellable
            occupied = lightin_barcode.sellable
        else:
            occupied = quantity
            quantity = 0

        print("        条码 %s , 条码可售库存 %s 占用 %s" % (lightin_barcode, lightin_barcode.sellable, occupied))

        inventory_list.append([sku, lightin_barcode, occupied, price])

    # 需求没有被满足，标识订单缺货
    print("quantity", quantity)
    if quantity > 0:
        error = sku.SKU + " 缺货"
        return None, error
    else:
        return inventory_list, ""


@shared_task
def fulfill_orders_lightin():
    orders = Order.objects.filter(financial_status="paid",
                                  fulfillment_status__isnull=True,
                                  status="open",
                                  verify__verify_status="SUCCESS",
                                  verify__sms_status="CHECKED",
                                  wms_status__in=["", "F"])
    print("共有%s个订单待发货" % (orders.count()))
    order_list = []
    for order in orders:
        if order.stock in ["充足", "紧张"]:
            error = mapping_order_lightin(order)
            if error == "":
                result = fulfill_order_lightin(order)
                if result:
                    # 发货成功的列表
                    order_list.append(order)

    # 提交仓库准备发货成功的，要更新本地库存
    update_barcode_stock(order_list, "W")


def update_stock(order_list, action):
    # SKU 库存
    update_sku_stock(order_list, action)
    # barco 库存
    update_barcode_stock(order_list, action)


def update_sku_stock(order_list, action):
    from django.db.models import Sum
    # OrderDetail.objects.filter(order__in=order_list).values_list("sku").
    return True


def update_barcode_stock(order_list, action):
    from django.db.models import Sum
    barcode_quantity = {}
    barcode_list = []

    order_barcodes = OrderDetail_lightin.objects.filter(order__in=order_list,
                                                        ).values_list('barcode').annotate(Sum('quantity'))

    for order_barcode in order_barcodes:
        barcode_quantity[order_barcode[0]] = order_barcode[1]
        if order_barcode[0] not in barcode_list:
            barcode_list.append(order_barcode[0])

    print("有%s个sku需要更新" % (len(barcode_quantity)))

    for barcode in barcode_quantity:
        try:
            lightin_barcode = Lightin_barcode.objects.get(pk=barcode)
            if action == 'W':
                lightin_barcode.o_reserved += barcode_quantity[barcode]
                lightin_barcode.o_sellable -= barcode_quantity[barcode]
            elif action == 'D':
                lightin_barcode.o_reserved -= barcode_quantity[barcode]
                lightin_barcode.o_quantity -= barcode_quantity[barcode]

            lightin_barcode.save()

            print(lightin_barcode, lightin_barcode.o_reserved)

        except Exception as e:
            print("更新出错", barcode, e)

    return True


def fulfill_order_lightin(order):
    from suds.client import Client
    from xml.sax.saxutils import escape

    service = "createOrder"
    items = []

    for order_item in order.order_orderdetail_lightin.all():
        # print(order_item)

        item = {
            "product_sku": order_item.barcode.barcode,
            # "product_name_en":title,
            "product_declared_value": order_item.price,
            "quantity": order_item.quantity,
        }
        items.append(item)

    param = {
        "platform": "B2C",
        "allocated_auto": "1",
        "warehouse_code": warehouse_code,
        "shipping_method": shipping_method,
        "reference_no": order.order_no,
        # "order_desc":"\u8ba2\u5355\u63cf\u8ff0",
        "country_code": "SA",
        "province": order.receiver_city,
        "city": order.receiver_city,
        "address1": order.receiver_addr1,
        "address2": order.receiver_addr2,
        "address3": "",
        "zipcode": "123456",
        "doorplate": "doorplate",
        "company": "company",
        "name": order.receiver_name,
        "phone": order.receiver_phone,
        "cell_phone": "",
        "email": "na@yallavip.com",
        "order_cod_price": order.order_amount,
        "order_cod_currency": "SAR",
        "order_age_limit": "2",
        "is_signature": "0",
        "is_insurance": "0",
        "insurance_value": "0",
        "verify": "1",
        "items": items,
        # "tracking_no":"123",
        # "label":{
        #    "file_type":"png",
        #    "file_data":"hVJPjUP4+yHjvKErt5PuFfvRhd..."
        # }
    }

    result = yunwms(service, param)
    print(result)
    if result.get("ask") == "Success":
        # 发货成功，更新订单状态
        Order.objects.filter(pk=order.pk).update(
            wms_status=result.get("order_status"),
            logistic_no=result.get("tracking_no"),
            fulfill_error="",
        )
        return True
    else:
        Order.objects.filter(pk=order.pk).update(
            wms_status="F",
            fulfill_error=result.get("message"),

        )
        return False


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


# 把wms已发货的订单同步回来

# 修改本地的barcode的库存数量
# 已发货的barcode，不占用库存

@shared_task
def sync_Shipped_order_lightin(days=1):
    import datetime
    from django.db.models import F

    today = datetime.date.today()
    start_time = str(today - datetime.timedelta(days=days))

    page = 1

    while 1:

        param = {
            "pageSize": "100",
            "page": page,
            "order_code": "",
            # "order_status": "D",
            "order_code_arr": [],
            "create_date_from": start_time,
            "create_date_to": "",
            "modify_date_from": "",
            "modify_date_to": ""
        }

        service = "getOrderList"

        result = yunwms(service, param)

        # print(result)
        if result.get("ask") == "Success":

            for data in result.get("data"):
                order_no = data.get("reference_no")
                if not order_no:
                    print("没有订单号", data)
                    continue
                print("当前处理订单 ", order_no, data.get("order_status"), data.get("tracking_no"))

                order = Order.objects.get(order_no=order_no)
                if order:
                    send_time = None
                    if order.wms_status == "W" and data.get("order_status") == "D":
                        # wms状态从待发货变成已发货，就修改本地 barcode 库存

                        items = OrderDetail_lightin.objects.filter(order=order)
                        # 更新本地barcode库存
                        for item in items:
                            barcode = Lightin_barcode.objects.get(barcode=item.barcode)
                            barcode.o_reserved = F("o_reserved") - item.quantity
                            barcode.o_quantity = F("o_quantity") - item.quantity
                            barcode.save()
                        print ("更新本地barcode库存")

                        send_time = data.get("date_shipping")
                    elif data.get("order_status") == "W":
                        pass

                    # 更新本地的订单状态
                    Order.objects.update_or_create(
                        order_no=order_no,
                        defaults={
                            "wms_status": data.get("order_status"),
                            "logistic_type": data.get("shipping_method"),
                            "logistic_no": data.get("tracking_no"),
                            "send_time": send_time,
                            "weight": data.get("order_weight"),
                        },
                    )
                    print ("更新本地的订单状态")

        if result.get("nextPage") == "false":
            break
        else:
            page += 1;


# 若wms已发货，shopify还未发货，则同步shopify发货
@shared_task
def sync_Shipped_order_shopify():
    from prs.shop_action import fulfill_order_shopify
    from django.db.models import F

    orders = Order.objects.filter(status="open", wms_status__in=["W"], logistic_no__isnull=False,
                                  order_id__isnull=False)

    n = orders.count()
    for order in orders:

        # 更新shopify的发货状态

        print("shopify 发货 ", order.order_no, order.order_id, order.logistic_no)

        print("还有 %s 待发货" % (n))
        n -= 1
        data = fulfill_order_shopify(order.order_id, order.logistic_no)

        if data.get("errors"):
            fulfillment_status = data.get("errors")

        else:
            # shopify发货成功

            if not order.fulfillment_status == '':
                # wms状态从未发货变成已发货，就修改本地 sku 库存，否则订单关闭，自动计算的占用库存会出错
                items = OrderDetail.objects.filter(order=order)

                # 更新本地sku库存
                for item in items:
                    lightin_skus = Lightin_SKU.objects.filter(SKU=item.sku)
                    if lightin_skus:

                        lightin_sku = lightin_skus.first()
                        lightin_sku.o_quantity = F("o_quantity") - item.product_quantity
                        lightin_sku.o_reserved = F("o_reserved") - item.product_quantity

                        lightin_sku.save()

                        # 如果是组合商品，还要调整对应的item的库存
                        if lightin_sku.comboed:
                            for combo_item in lightin_sku.combo_item.values_list("SKU", flat=True):
                                combo_lightin_sku = Lightin_SKU.objects.get(SKU=combo_item)
                                combo_lightin_sku.o_quantity = F("o_quantity") - item.product_quantity
                                combo_lightin_sku.o_reserved = F("o_reserved") - item.product_quantity

                                combo_lightin_sku.save()

                    print ("更新本地sku库存", order.order_no, item.sku)

            fulfillment_status = "fulfilled"

        # 更新本地的订单状态
        print(order, order.order_no)
        Order.objects.update_or_create(
            order_no=order.order_no,
            defaults={
                "fulfillment_status": fulfillment_status,

            },
        )


def get_wms_product():
    page = 1
    pages = 0

    while 1:
        print("一共 %s页 正在处理第 %s 页" % (pages, page))

        param = {
            "pageSize": "100",
            "page": page,
            "product_sku": "",
            "product_sku_arr": [],
            "start_time": "2018-02-08 10:00:00",
            # "end_time":"",
        }

        service = "getProductList"

        result = yunwms(service, param)

        # print(result)
        if result.get("ask") == "Success":
            for data in result.get("data"):
                Lightin_barcode.objects.update_or_create(
                    barcode=data.get("product_sku"),
                    defaults={
                        "product_status": data.get("product_status"),
                        "product_title": data.get("product_title"),
                        "product_weight": data.get("product_weight"),

                    },
                )
            if pages == 0:
                pages = int(int(result.get("count")) / 100)
        else:
            print("获取wms库存出错", result.get("message"))
            break

        if result.get("nextPage") == "false":
            break
        else:
            page += 1;


def get_wms_quantity(barcode=""):
    page = 1

    pages = 0

    while 1:
        print("一共 %s页 正在处理第 %s 页" % (pages, page))

        param = {
            "pageSize": "100",
            "page": page,
            "product_sku": barcode,
            "product_sku_arr": [],
            "warehouse_code": warehouse_code,
            "warehouse_code_arr": []
        }

        service = "getProductInventory"

        result = yunwms(service, param)

        # print(result)
        if result.get("ask") == "Success":
            for data in result.get("data"):
                Lightin_barcode.objects.update_or_create(
                    barcode=data.get("product_sku"),
                    defaults={
                        "warehouse_code": data.get("warehouse_code"),
                        "y_onway": data.get("y_onway"),
                        "y_pending": data.get("y_pending"),
                        "y_sellable": data.get("sellable"),
                        "y_unsellable": data.get("y_unsellable"),
                        "y_reserved": data.get("reserved"),
                        "y_shipped": data.get("shipped"),
                        "updated_time": dt.now()
                        # "quantity":  int(data.get("sellable")) + int(data.get("reserved"))

                    },
                )
            if pages == 0:
                pages = int(int(result.get("count")) / 100)
        else:
            print("获取wms库存出错", result.get("message"))
            break

        if result.get("nextPage") == "false":
            break
        else:
            page += 1;


def get_shopify_quantity():
    "GET /admin/inventory_levels.json?inventory_item_ids=808950810,39072856&location_ids=905684977,487838322"

    page = 1

    while 1:
        print("正在处理第 %s 页" % (page))

        param = {
            "pageSize": "100",
            "page": page,
            "product_sku": "",
            "product_sku_arr": [],
            "warehouse_code": warehouse_code,
            "warehouse_code_arr": []
        }

        service = "getProductInventory"

        result = yunwms(service, param)

        # print(result)
        if result.get("ask") == "Success":
            for data in result.get("data"):
                Lightin_barcode.objects.update_or_create(
                    barcode=data.get("product_sku"),
                    defaults={
                        "y_sellable": data.get("sellable"),
                        "y_reserved": data.get("reserved"),
                        "y_shipped": data.get("shipped")
                        # "quantity":  int(data.get("sellable")) + int(data.get("reserved"))

                    },

                )
        if result.get("nextPage") == "false":
            break
        else:
            page += 1;


def getShippingMethod():
    param = {
        "warehouseCode": warehouse_code,
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
    return result


def getTrack(logistic_list):
    param = {
        "codes": logistic_list,
    }

    service = "getCargoTrack"

    result = yuntms(service, param)

    return result


def yuntms(service, param):
    from suds.client import Client
    from xml.sax.saxutils import escape

    url = "http://toms.cititrans.com/default/svc/wsdl"
    client = Client(url)

    response = client.service.callService(appToken=tms_appToken,
                                          appKey=tms_appKey,
                                          service=service,
                                          paramsJson=json.dumps(param)
                                          )
    result = json.loads(escape(response))
    return result


@shared_task
def cal_reserved(overtime=24):
    from django.db.models import Sum
    from orders.models import OrderDetail
    from shop.models import DraftItem

    # 先清空所有的库存占用
    Lightin_SKU.objects.update(o_reserved=0)

    # 计算库存占用
    sku_quantity = {}
    sku_list = []
    # 计算组合商品
    combo_skus = ComboItem.objects.filter(combo__locked=True).values_list('SKU').annotate(Sum('combo__o_quantity'))

    for combo_sku in combo_skus:
        # 每个sku占用的库存，等于它对应的combo的库存

        sku_quantity[combo_sku[0]] = sku_quantity.get(combo_sku[0], 0) + combo_sku[1]
        if combo_sku[0] not in sku_list:
            sku_list.append(combo_sku[0])

    print("组合商品 有%s个sku需要更新" % (len(sku_quantity)))

    # 计算订单
    order_skus = OrderDetail.objects.filter(order__status="open",
                                            # order__order_time__gt =  dt.now() - dt.timedelta(hours=overtime),
                                            ).values_list('sku').annotate(Sum('product_quantity'))
    for order_sku in order_skus:
        print(order_sku)
        sku_quantity[order_sku[0]] = sku_quantity.get(order_sku[0], 0) + order_sku[1]
        if order_sku[0] not in sku_list:
            sku_list.append(order_sku[0])

    print("加上开放的订单 有%s个sku需要更新" % (len(sku_quantity)))

    # 计算草稿
    draft_skus = DraftItem.objects.filter(draft__status="open",
                                          draft__created_at__gt=dt.now() - dt.timedelta(hours=overtime),
                                          ).values_list('sku').annotate(Sum('quantity'))

    for draft_sku in draft_skus:
        if sku_quantity.get(draft_sku[0]):
            sku_quantity[draft_sku[0]] += draft_sku[1]
        else:
            sku_quantity[draft_sku[0]] = draft_sku[1]
        if draft_sku[0] not in sku_list:
            sku_list.append(draft_sku[0])

    n = len(sku_quantity)
    print("加上24小时内的草稿 有%s个sku需要更新" % (n))

    # 更新库存占用
    lightin_skus = Lightin_SKU.objects.filter(SKU__in=sku_list).distinct()
    for lightin_sku in lightin_skus:
        try:

            lightin_sku.o_reserved = sku_quantity[lightin_sku.SKU]
            # lightin_sku.o_sellable = lightin_sku.o_quantity - sku_quantity[sku]
            lightin_sku.save()

            # print(lightin_sku, lightin_sku.o_reserved, lightin_sku.o_sellable)

        except Exception as e:
            print("更新出错", sku, e)

    '''
    for sku in sku_quantity:
        try:
            lightin_sku = Lightin_SKU.objects.get(SKU = sku)
            lightin_sku.o_reserved = sku_quantity[sku]
            #lightin_sku.o_sellable = lightin_sku.o_quantity - sku_quantity[sku]
            lightin_sku.save()

            #print(lightin_sku, lightin_sku.o_reserved, lightin_sku.o_sellable)

        except Exception as e:
            print("更新出错",sku, e)

        n-=1
        print("还有%s个待更新"%(n))
    '''

    # 更新所有的可售库存
    mysql = "update prs_lightin_sku set o_sellable = o_quantity - o_reserved"

    my_custom_sql(mysql)

    # 更新对应的spu的可售库存
    print(sku_list)
    lightin_spus = Lightin_SPU.objects.filter(spu_sku__SKU__in=sku_list).distinct()
    print("有%s个spu需要更新" % (lightin_spus.count()))
    for lightin_spu in lightin_spus:
        lightin_spu.sellable = Lightin_SKU.objects.filter(lightin_spu__pk=lightin_spu.pk).aggregate(
            nums=Sum('o_sellable')).get("nums")
        lightin_spu.save()


@shared_task
def cal_reserved_skus(skus, overtime=24):
    from django.db.models import Sum
    from orders.models import OrderDetail
    from shop.models import DraftItem

    # 先清空所有的库存占用
    Lightin_SKU.objects.filter(SKU__in=skus).update(o_reserved=0)

    # 计算库存占用
    sku_quantity = {}
    sku_list = []
    # 计算组合商品
    combo_skus = ComboItem.objects.filter(combo__locked=True, lightin_sku__SKU__in=skus).values_list('SKU').annotate(
        Sum('combo__o_quantity'))

    for combo_sku in combo_skus:
        # 每个sku占用的库存，等于它对应的combo的库存

        sku_quantity[combo_sku[0]] = sku_quantity.get(combo_sku[0], 0) + combo_sku[1]
        if combo_sku[0] not in sku_list:
            sku_list.append(combo_sku[0])

    print("组合商品 有%s个sku需要更新" % (len(sku_quantity)))

    # 计算订单
    order_skus = OrderDetail.objects.filter(order__status="open", sku__in=skus,
                                            # order__order_time__gt =  dt.now() - dt.timedelta(hours=overtime),
                                            ).values_list('sku').annotate(Sum('product_quantity'))
    for order_sku in order_skus:
        print(order_sku)
        sku_quantity[order_sku[0]] = sku_quantity.get(order_sku[0], 0) + order_sku[1]
        if order_sku[0] not in sku_list:
            sku_list.append(order_sku[0])

    print("加上开放的订单 有%s个sku需要更新" % (len(sku_quantity)))

    # 计算草稿
    draft_skus = DraftItem.objects.filter(draft__status="open", sku__in=skus,
                                          draft__created_at__gt=dt.now() - dt.timedelta(hours=overtime),
                                          ).values_list('sku').annotate(Sum('quantity'))

    for draft_sku in draft_skus:
        if sku_quantity.get(draft_sku[0]):
            sku_quantity[draft_sku[0]] += draft_sku[1]
        else:
            sku_quantity[draft_sku[0]] = draft_sku[1]
        if draft_sku[0] not in sku_list:
            sku_list.append(draft_sku[0])

    n = len(sku_quantity)
    print("加上24小时内的草稿 有%s个sku需要更新" % (n))

    # 更新库存占用
    for sku in sku_quantity:
        try:
            lightin_sku = Lightin_SKU.objects.get(SKU=sku)
            lightin_sku.o_reserved = sku_quantity[sku]
            # lightin_sku.o_sellable = lightin_sku.o_quantity - sku_quantity[sku]
            lightin_sku.save()

            # print(lightin_sku, lightin_sku.o_reserved, lightin_sku.o_sellable)

        except Exception as e:
            print("更新出错", sku, e)

        n -= 1
        print("还有%s个待更新" % (n))

    # 更新所有的可售库存
    mysql = "update prs_lightin_sku set o_sellable = o_quantity - o_reserved"

    my_custom_sql(mysql)

    # 更新对应的spu的可售库存
    print(sku_list)
    lightin_spus = Lightin_SPU.objects.filter(spu_sku__SKU__in=sku_list).distinct()
    print("有%s个spu需要更新" % (lightin_spus.count()))
    for lightin_spu in lightin_spus:
        lightin_spu.sellable = Lightin_SKU.objects.filter(lightin_spu__pk=lightin_spu.pk).aggregate(
            nums=Sum('o_sellable')).get("nums")
        lightin_spu.save()


@shared_task
def cal_reserved_barcode(overtime=24):
    from django.db.models import Sum
    from orders.models import OrderDetail_lightin

    barcode_quantity = {}
    barcode_list = []
    # 计算待发货
    # W状态的就是待发货的
    order_barcodes = OrderDetail_lightin.objects.filter(order__wms_status="W",
                                                        ).values_list('barcode').annotate(Sum('quantity'))
    for order_barcode in order_barcodes:
        barcode_quantity[order_barcode[0]] = order_barcode[1]
        if order_barcode[0] not in barcode_list:
            barcode_list.append(order_barcode[0])

    print("有%s个lightin_barcode需要更新" % (len(barcode_quantity)))

    for barcode in barcode_quantity:
        try:
            lightin_barcode = Lightin_barcode.objects.get(barcode=barcode)
            lightin_barcode.o_reserved = barcode_quantity[barcode]
            lightin_barcode.o_sellable = lightin_barcode.o_quantity - barcode_quantity[barcode]

            # lightin_barcode.save()

            print(lightin_barcode, lightin_barcode.o_quantity, lightin_barcode.o_reserved, lightin_barcode.o_sellable)

        except Exception as e:
            print("更新出错", barcode, e)


def cal_barcode(wms_status):
    from django.db.models import Sum
    from orders.models import OrderDetail_lightin

    barcode_quantity = {}
    barcode_list = []

    Lightin_barcode.objects.update(o_reserved=0)

    order_barcodes = OrderDetail_lightin.objects.filter(order__wms_status=wms_status,
                                                        # order__status = 'open',
                                                        ).values_list('barcode__barcode').annotate(Sum('quantity'))
    for order_barcode in order_barcodes:
        barcode_quantity[order_barcode[0]] = order_barcode[1]
        if order_barcode[0] not in barcode_list:
            barcode_list.append(order_barcode[0])

    print("有%s个sku需要更新" % (len(barcode_quantity)))

    for barcode in barcode_quantity:
        try:
            lightin_barcode = Lightin_barcode.objects.get(barcode=barcode)
            if wms_status == "W":
                lightin_barcode.o_reserved = barcode_quantity[barcode]
                lightin_barcode.o_sellable = lightin_barcode.o_quantity - barcode_quantity[barcode]
            elif wms_status == "D":
                lightin_barcode.o_shipped = barcode_quantity[barcode]
            # lightin_sku.o_sellable = lightin_sku.o_quantity - sku_quantity[sku]
            lightin_barcode.save()

            print(lightin_barcode, wms_status, barcode_quantity[barcode])

        except Exception as e:
            print("更新出错", barcode, e)


@shared_task
def sync_shopify(minutes=10):
    from shop.tasks import get_orders, update_orders, get_drafts, update_drafts
    get_orders(minutes=minutes)
    update_orders()

    get_drafts(minutes=minutes)
    update_drafts()

    cal_reserved(overtime=24)

    delete_outstock_lightin_album()


@shared_task
def get_wms_orders(days=1):
    import datetime
    from django.db.models import F

    today = datetime.date.today()
    start_time = str(today - datetime.timedelta(days=days))

    page = 1

    while 1:

        param = {
            "pageSize": "100",
            "page": page,
            "order_code": "",
            # "order_status": "D",
            "order_code_arr": [],
            "create_date_from": start_time,
            "create_date_to": "",
            "modify_date_from": "",
            "modify_date_to": ""
        }

        service = "getOrderList"

        result = yunwms(service, param)

        # print(result)
        if result.get("ask") == "Success":
            order_id_list = []
            oriorders_list = []
            for row in result.get("data"):
                order_id_list.append(row["order_code"])
                oriorder = WmsOriOrder(
                    order_id=row["order_code"],
                    order_no=row["reference_no"],
                    tracking_no=row["tracking_no"],
                    created_at=row["date_create"],
                    status=row["order_status"],
                    order_json=json.dumps(row),
                    updated=True,
                )
                oriorders_list.append(oriorder)

                # 删除所有可能重复的订单信息
            WmsOriOrder.objects.filter(order_id__in=order_id_list).delete()

            WmsOriOrder.objects.bulk_create(oriorders_list)
        else:
            print("出错了！", result.get("message"))
            break

        if result.get("nextPage") == "false":
            break
        else:
            page += 1;


def update_shopify_variant():
    from shop.models import ShopifyVariant

    dest_shop = "yallasale-com"
    shop_obj = Shop.objects.get(shop_name=dest_shop)

    shop_url = "https://%s:%s@%s.myshopify.com" % (shop_obj.apikey, shop_obj.password, shop_obj.shop_name)

    variants = ShopifyVariant.objects.filter(inventory_policy="continue").distinct().values_list("variant_no",
                                                                                                 flat=True)
    for variant_id in variants:

        params = {
            "variant": {
                "id": variant_id,
                "inventory_policy": "deny",
                "inventory_management": "shopify"
            }
        }
        headers = {
            "Content-Type": "application/json",
            "charset": "utf-8",

        }
        # 初始化SDK
        url = shop_url + "/admin/variants/%s.json" % (variant_id)

        print("开始修改变体", variant_id)
        # print(url, json.dumps(params))

        r = requests.put(url, headers=headers, data=json.dumps(params))
        if r.text is None:
            print(r)
            return None

        ShopifyVariant.objects.filter(variant_no=variant_id).update(
            inventory_policy="deny",
            inventory_management="shopify"
        )


# 把有货，还未上架的包裹上架
@shared_task
def list_package():
    from logistic.models import Package

    from .shop_action import create_package_sku

    dest_shop = "yallasale-com"
    discount = 0.9
    min_product_no = 999999999999999

    lightin_skus = Lightin_SKU.objects.filter(SKU__startswith='579815', o_sellable__gt=0, listed=False)
    print("packages is ", lightin_skus)

    for lightin_sku in lightin_skus:
        order = Order.objects.filter(order_no=lightin_sku.SKU).first()
        print("order", order)
        if not order:
            print("cannot find the order", lightin_sku.SKU)
            continue

        product_no, sku_created = create_package_sku(dest_shop, order, discount)
        print(order, "created", product_no)

        if sku_created:
            if product_no < min_product_no:
                min_product_no = product_no

            Lightin_SKU.objects.filter(pk=lightin_sku.pk).update(listed=True)
        '''
        n =n+1
        if n>10:
            break
        else:
            print("******", n)
        '''

    # 上传完后整体更新目标站数据
    sync_shop(dest_shop, min_product_no)

    return True


def lock_combo():
    # 先同步shopify，更新库存占用
    sync_shopify()

    combos = Combo.objects.filter(comboed=True, locked=False)

    for combo in combos:
        # 先判断所有的项目是否都有库存，否则返回失败
        items = combo.combo_item.all()
        target_count = items.count()
        real_items = items.filter(lightin_sku__o_sellable__gt=0)
        real_count = real_items.count()
        print (combo, target_count, real_count)
        if real_count < target_count:
            combo.combo_error = "sku 缺货"
            combo.o_quantity = 0
            combo.o_sellable = 0

            combo.save()

        else:
            combo.o_quantity = 1
            combo.o_sellable = 1
            combo.locked = True
            combo.save()

    # 更新库存占用
    cal_reserved()

    return


def init_combos(num):
    sku = Lightin_SKU.objects.filter(comboed=True).last()
    sku_prefix = sku.SKU[0]
    sku_no = int(sku.SKU[1:])

    # 先更新一遍库存
    cal_reserved()

    for n in range(1, num):
        init_combo(sku_prefix + str(sku_no + n).zfill(4))


def gen_package(main_cate, main_cate_nums, sub_cate, sub_cate_nums, sub_cate_price):
    # 随机取main_cate_nums个大件
    skus_all = Lightin_SKU.objects.filter(o_sellable__gt=0, lightin_spu__breadcrumb__icontains=main_cate)
    skus = random.sample(list(skus_all), main_cate_nums)

    # 随机取sub_cate_nums个价格不高于sub_cate_price的小件
    skus_all = Lightin_SKU.objects.filter(o_sellable__gt=0, lightin_spu__breadcrumb__icontains=sub_cate,
                                          vendor_supply_price__lt=sub_cate_price)
    pieces = random.randint(sub_cate_nums[0], sub_cate_nums[1])
    skus_all_list = list(skus_all)
    skus.extend(random.sample(skus_all_list, min(len(skus_all_list), pieces)))

    return skus


# 组合一个combo
# sku是combo的sku号，skus是combo的items
def make_combo(sku, skus):
    combo = Combo.objects.create(
        SKU=sku,
        comboed=True
    )

    comboitem_list = []
    price = 0
    for row in skus:
        # print("row is ",row)
        comboitem = ComboItem(
            combo=combo,
            lightin_sku=row,
            SKU=row.SKU
        )
        price += row.vendor_supply_price
        comboitem_list.append(comboitem)
    ComboItem.objects.bulk_create(comboitem_list)

    combo.sku_price = int(price * 6.5)
    combo.o_quantity = 1
    combo.o_sellable = 1
    combo.locked = True
    combo.save()

    # 更新库存以便锁定
    cal_reserved_skus(skus)


def init_combo(sku):
    # 随机生成包裹类型
    combo_types = [
        {
            "main_cate": '"Women\'s Tops & Sets"',
            "main_cate_nums": 2,
            "sub_cates": '"Women\'s Tops & Sets"',
            "sub_cate_nums": [3, 4],
            "sub_cate_price": 3.6
        },
        {
            "main_cate": '"Bags"',
            "main_cate_nums": 2,
            "sub_cates": '"Jewelry & Watches"',
            "sub_cate_nums": [3, 6],
            "sub_cate_price": 2
        },
    ]

    combo_type = random.choice(combo_types)

    skus = gen_package(combo_type["main_cate"], combo_type["main_cate_nums"], combo_type["sub_cates"],
                       combo_type["sub_cate_nums"], combo_type["sub_cate_price"])

    make_combo(sku, skus)

    '''
    #随机取大件
    skus_all = Lightin_SKU.objects.filter(o_sellable__gt=0,lightin_spu__breadcrumb__icontains= combo_type["main_cate"] )
    skus = random.sample(list(skus_all),combo_type["main_cate_nums"])

    # 随机取小件
    skus_all = Lightin_SKU.objects.filter(o_sellable__gt=0, lightin_spu__breadcrumb__icontains=combo_type["sub_cates"], vendor_supply_price__lt=combo_type["sub_cate_price"])
    pieces = random.randint(combo_type["sub_cate_nums"][0],combo_type["sub_cate_nums"][1])
    skus_all_list = list(skus_all)
    skus.extend(random.sample(skus_all_list,min(len(skus_all_list),pieces)))
  
    combo = Combo.objects.create(
        SKU=sku,
        comboed = True
        )

    comboitem_list=[]
    price = 0
    for row in skus:
        # print("row is ",row)
        comboitem = ComboItem(
            combo=combo,
            lightin_sku=row,
            SKU=row.SKU
        )
        price += row.vendor_supply_price
        comboitem_list.append(comboitem)
    ComboItem.objects.bulk_create(comboitem_list)

    combo.sku_price =  int(price*6.5)
    combo.o_quantity = 1
    combo.o_sellable = 1
    combo.locked = True
    combo.save()


    #更新库存以便锁定
    cal_reserved_skus(skus)
    '''
    return


def create_combo():
    from .shop_action import create_package_sku
    dest_shop = "yallasale-com"
    min_product_no = 999999999999999

    combos = Combo.objects.filter(comboed=True, locked=True, listed=False)
    for combo in combos:
        product_no, sku_created = create_combo_sku(dest_shop, combo)

        if sku_created:
            if product_no < min_product_no:
                min_product_no = product_no

            # Combo.objects.filter(pk=combo.pk).update(listed=True)
            combo.listed = True
            combo.combo_error = ""

        else:
            combo.combo_error = "创建shopfiy失败 "

        combo.save()

    # 上传完后整体更新目标站数据
    sync_shop(dest_shop, min_product_no)


# 创建组合商品sku，每100个组合商品sku建一个product
def create_combo_sku(dest_shop, combo):
    # 初始化SDK
    shop_obj = Shop.objects.get(shop_name=dest_shop)

    shop_url = "https://%s:%s@%s.myshopify.com" % (shop_obj.apikey, shop_obj.password, shop_obj.shop_name)

    # url = shop_url + "/admin/products.json"

    # 每100个组合商品sku创建一个组合商品，组合商品sku作为变体存放。，否则创建新的
    # 以数据库中最大的组合商品的sku号为基准创建handle和sku

    handle_new = combo.SKU[:-2]
    # 创建变体
    variants_list = []

    sku = combo.SKU
    print("handle_new  sku", handle_new, sku)

    variant_item = {

        "price": combo.sku_price,
        "compare_at_price": combo.sku_price * 2.5,
        "sku": sku,
        "option1": sku,

        "title": sku,
        "taxable": "true",
        "inventory_management": "shopify",
        "fulfillment_service": "manual",
        "inventory_policy": "deny",

        "inventory_quantity": 1,
        "requires_shipping": "true",
        "weight": combo.weight,
        "weight_unit": "g",

    }
    # print("variant_item", variant_item)
    variants_list.append(variant_item)

    # 所以先检测商品是否存在
    url = shop_url + "/admin/products.json"
    params = {
        "handle": handle_new,
        # "page": 1,
        # "limit": 100,
        # "since_id": max_product_no,
        "fields": "id,handle, variants",
    }

    response = requests.get(url, params)
    # print("url %s, params %s , response %s" % (url, json.dumps(params), response))

    data = json.loads(response.text)
    # print("check ori_product data is ", data)

    headers = {
        "Content-Type": "application/json",
        "charset": "utf-8",

    }

    ori_products = data.get("products")

    # print("ori_products", ori_products, len(ori_products))

    if len(ori_products) == 0:
        print("product does not exist yet")
        # 创建新商品
        url = shop_url + "/admin/products.json"

        params = {
            "product": {
                "handle": handle_new,
                "title": "Overseas Package " + handle_new,
                "variants": variants_list,
            }
        }

        response = requests.post(url, headers=headers, data=json.dumps(params))
        data = json.loads(response.text)
        new_product = data.get("product")
        if new_product is None:
            # 创建新产品失败
            print("data is ", data)
            return None, False




    elif len(ori_products) == 1:

        ori_product = ori_products[0]
        if ori_product is None:
            # 获取原有产品失败
            print("data is ", data)
            return None, False
        else:
            print("product exist", ori_product["handle"])
            # 获取原有产品信息
            for k in range(len(ori_product["variants"])):
                variant_row = ori_product["variants"][k]
                # print("variant_row is ", variant_row)
                variant_item = {

                    "id": variant_row.get("id"),

                }

                variants_list.append(variant_item)

            # 更新原有商品
            # PUT /admin/products/#{product_id}.json
            url = shop_url + "/admin/products/%s.json" % (ori_product.get("id"))

            params = {
                "product": {
                    "id": ori_product.get("id"),
                    # "title": "Overseas Package " + handle_new,
                    "variants": variants_list,
                }
            }

            response = requests.put(url, headers=headers, data=json.dumps(params))
            data = json.loads(response.text)
            new_product = data.get("product")
            if new_product is None:
                # 更新原有产品变体失败
                print("fail to update variant")
                print("data is ", data)
                return None, False

    else:
        print("unknow error")
        return None, False

    print("new product is ", new_product.get("id"))

    return (new_product.get("id"), True)


# 拼接组合商品图片
def combo_images():
    for combo in Combo.objects.filter(comboed=True, imaged=False):
        print ("当前处理 combo ", combo)
        combo_image(combo)


def combo_image(combo):
    from shop.photo_mark import clipResizeImg_new, get_remote_image
    import os
    from django.conf import settings
    domain = "http://admin.yallavip.com"
    FONT = os.path.join(settings.BASE_DIR, "static/font/ARIAL.TTF")

    try:
        from PIL import Image, ImageDraw, ImageFont, ImageEnhance

    except ImportError:
        import Image, ImageDraw, ImageFont, ImageEnhance

    price_dict = {}
    image_dict = {}

    items = combo.combo_item.all()

    for item in items:
        print (item, item.SKU)
        sku = item.lightin_sku

        # 如果sku有属性图片则用属性图片，否则用spu图片
        image = None
        if sku.image:
            image = sku.image
            print("sku 图片")
        else:

            spu = sku.lightin_spu
            # images = json.loads(Lightin_SPU.objects.get(spu_sku__SKU= item.SKU).images)
            if spu.images_dict:
                image = json.loads(spu.images_dict).values()
                if image and len(image) > 0:
                    a = "/"
                    image_split = list(image)[0].split(a)

                    image_split[4] = '800x800'
                    image = a.join(image_split)
                    print("spu 图片", spu, image)

        im = get_remote_image(image)
        if not im:
            combo.image_marked = "image打不开"
            combo.save()
            return

        image_dict[item.SKU] = im
        price_dict[item.SKU] = sku.vendor_supply_price

    price_dict_sorted = sorted(price_dict.items(), key=lambda item: item[1], reverse=True)
    # print(image_split, price_dict_sorted, price_dict)

    if not items.count() == len(image_dict):
        combo.image_marked = "图片和items数量不一致"
        combo.save()
        return

    # 把所有的项目按价格排序，价格高的在前面
    # 按价格高低放图，价格高的放在大的位置
    ims = []
    for item_sorted in price_dict_sorted:
        sku = item_sorted[0]
        im = image_dict[sku]
        ims.append(im)

    # 开始拼图

    item_count = items.count()
    if item_count == 4:
        # 四张图
        # 先做个900x1000的画布
        layer = Image.new("RGB", (900, 1000), "red")

        layer.paste(clipResizeImg_new(ims[0], 450, 450), (0, 0))
        layer.paste(clipResizeImg_new(ims[1], 450, 450), (0, 450))
        layer.paste(clipResizeImg_new(ims[2], 450, 450), (450, 0))
        layer.paste(clipResizeImg_new(ims[3], 450, 450), (450, 450))

    elif item_count == 5:
        # 五张图
        # 先做个900x1000的画布
        layer = Image.new("RGB", (900, 1180), "red")
        layer.paste(clipResizeImg_new(ims[0], 540, 540), (0, 0))
        layer.paste(clipResizeImg_new(ims[1], 540, 540), (0, 540))
        layer.paste(clipResizeImg_new(ims[2], 360, 360), (540, 0))
        layer.paste(clipResizeImg_new(ims[3], 360, 360), (540, 360))
        layer.paste(clipResizeImg_new(ims[4], 360, 360), (540, 720))

    elif item_count == 6:
        # 六张图
        # 先做个900x900的画布
        layer = Image.new("RGB", (900, 1000), "red")

        layer.paste(clipResizeImg_new(ims[0], 600, 600), (0, 0))
        layer.paste(clipResizeImg_new(ims[1], 300, 300), (0, 600))
        layer.paste(clipResizeImg_new(ims[2], 300, 300), (300, 600))
        layer.paste(clipResizeImg_new(ims[3], 300, 300), (600, 0))
        layer.paste(clipResizeImg_new(ims[4], 300, 300), (600, 300))
        layer.paste(clipResizeImg_new(ims[5], 300, 300), (600, 600))
    elif item_count == 7:
        # 先做个900x130的画布
        layer = Image.new("RGB", (900, 1300), "red")
        layer.paste(clipResizeImg_new(ims[0], 450, 450), (0, 0))
        layer.paste(clipResizeImg_new(ims[1], 450, 450), (450, 0))
        layer.paste(clipResizeImg_new(ims[2], 450, 450), (0, 450))
        layer.paste(clipResizeImg_new(ims[3], 450, 450), (450, 450))
        layer.paste(clipResizeImg_new(ims[4], 300, 300), (0, 900))
        layer.paste(clipResizeImg_new(ims[5], 300, 300), (300, 900))
        layer.paste(clipResizeImg_new(ims[6], 300, 300), (600, 900))
    elif item_count == 8:
        # 先做个900x1150的画布
        layer = Image.new("RGB", (900, 1150), "red")
        layer.paste(clipResizeImg_new(ims[0], 450, 450), (0, 0))
        layer.paste(clipResizeImg_new(ims[1], 450, 450), (450, 0))
        layer.paste(clipResizeImg_new(ims[2], 300, 300), (0, 450))
        layer.paste(clipResizeImg_new(ims[3], 300, 300), (0, 750))
        layer.paste(clipResizeImg_new(ims[4], 300, 300), (300, 450))
        layer.paste(clipResizeImg_new(ims[5], 300, 300), (300, 750))
        layer.paste(clipResizeImg_new(ims[6], 300, 300), (600, 450))
        layer.paste(clipResizeImg_new(ims[7], 300, 300), (600, 750))
    elif item_count == 9:
        # 先做个900x1000的画布
        layer = Image.new("RGB", (900, 1000), "red")
        layer.paste(clipResizeImg_new(ims[0], 300, 300), (0, 0))
        layer.paste(clipResizeImg_new(ims[1], 300, 300), (0, 300))
        layer.paste(clipResizeImg_new(ims[2], 300, 300), (0, 600))
        layer.paste(clipResizeImg_new(ims[3], 300, 300), (300, 0))
        layer.paste(clipResizeImg_new(ims[4], 300, 300), (300, 300))
        layer.paste(clipResizeImg_new(ims[5], 300, 300), (300, 600))
        layer.paste(clipResizeImg_new(ims[6], 300, 300), (600, 0))
        layer.paste(clipResizeImg_new(ims[7], 300, 300), (600, 300))
        layer.paste(clipResizeImg_new(ims[8], 300, 300), (600, 600))
    elif item_count == 10:
        # 先做个900x130的画布
        layer = Image.new("RGB", (900, 925), "red")
        layer.paste(clipResizeImg_new(ims[0], 300, 300), (0, 0))
        layer.paste(clipResizeImg_new(ims[1], 300, 300), (0, 300))
        layer.paste(clipResizeImg_new(ims[2], 300, 300), (300, 0))
        layer.paste(clipResizeImg_new(ims[3], 300, 300), (300, 300))
        layer.paste(clipResizeImg_new(ims[4], 300, 300), (600, 0))
        layer.paste(clipResizeImg_new(ims[5], 300, 300), (600, 300))
        layer.paste(clipResizeImg_new(ims[6], 225, 225), (0, 600))
        layer.paste(clipResizeImg_new(ims[7], 225, 225), (225, 600))
        layer.paste(clipResizeImg_new(ims[8], 225, 225), (450, 600))
        layer.paste(clipResizeImg_new(ims[9], 225, 225), (675, 600))
    else:
        layer = None

    print(price_dict, price_dict_sorted)

    '''
    #发布的时候根据在那个page，选择不同的logo， 左上角打水印
    logo = Image.open(logo)
    lw, lh = logo.size
    

    layer.paste(clipResizeImg_new(logo, lw * 50/lh , 50), (600, 900))
    '''
    # 左下角写货号，free delivery
    # 右下角写 几件 原价，售价
    if layer:
        font = ImageFont.truetype(FONT, 35)
        draw1 = ImageDraw.Draw(layer)
        # 简单打货号
        lw, lh = layer.size

        x = 0
        y = lh - 100
        # 写货号
        draw1.rectangle((x + 20, y + 5, x + 180, y + 45), fill='yellow')
        draw1.text((x + 30, y + 10), combo.SKU, font=font,
                   fill="black")  # 设置文字位置/内容/颜色/字体
        # 写包邮
        promote = "Free Deliver"
        draw1.rectangle((x + 20, y + 55, x + 250, y + 95), fill='yellow')
        draw1.text((x + 30, y + 60), promote, font=font,
                   fill=(0, 0, 0))  # 设置文字位置/内容/颜色/字体
        # 写件数 和 售价
        font = ImageFont.truetype(FONT, 50)
        draw1.text((x + 450, y + 25), "%s pcs" % (item_count), font=font,
                   fill="white")  # 设置文字位置/内容/颜色/字体

        draw1.rectangle((x + 600, y + 20, x + 800, y + 80), fill='white')
        draw1.text((x + 610, y + 25), "%s sar" % (combo.sku_price), font=font, fill="red")  # 设置文字位置/内容/颜色/字体

        out = layer.convert('RGB')
        # out.show()
        image_filename = combo.SKU + '.jpg'

        destination = os.path.join(settings.MEDIA_ROOT, "combo/", image_filename)

        out.save(destination, 'JPEG', quality=95)
        # out.save('target%s.jpg'%(combo.SKU), 'JPEG')

        destination_url = domain + os.path.join(settings.MEDIA_URL, "combo/", image_filename)
        print("destination_url", destination_url)

        combo.image_marked = destination_url
        combo.imaged = True

    else:
        combo.image_marked = "items数量问题"

    combo.save()
    '''
    for

        if (n == 0):
            ims.append(clipResizeImg_new(im, 600, 900))
            im_main = im

    '''

    '''
    while n < 4:
        try:
            im = Image.open('./ori/' + str(row[0]) + '_' + str(m) + '.jpg')  # image 对象
        except:
            m = m + 1
            if m > 20:
                # im = Image.new("RGB", (300, 300), "white")
                break
            else:
                continue

        if (n == 0):
            ims.append(clipResizeImg_new(im, 600, 900))
            im_main = im
        else:
            ims.append(clipResizeImg_new(im, 299, 299))
        n = n + 1
        m = m + 1

    layer = Image.new("RGB", (900, 900), "white")

    layer.paste(ims[0], (0, 0))
    # layer.paste("blue", (0,0,900,900))
    # out = Image.composite(layer, im1, layer)
    for index in range(len(ims)):
        layer.paste(ims[index], (601, 300 * (index - 1)))

    out = Image.composite(layer, im2, layer)

    out = layer.convert('RGB')
    # out.show()
    out.save('target.jpg', 'JPEG')

    
    '''


def skus_image():
    lightin_skus = Lightin_SKU.objects.filter(
        ~(Q(lightin_spu__attr_image_dict__isnull=True) | Q(lightin_spu__attr_image_dict="") |
          Q(lightin_spu__images_dict__isnull=True) | Q(lightin_spu__images_dict="")),
        comboed=False, imaged=False)
    for lightin_sku in lightin_skus:
        print ("开始处理 ", lightin_sku)
        sku_image(lightin_sku)


def sku_image(lightin_sku):
    attr = lightin_sku.skuattr
    spu = lightin_sku.lightin_spu

    attr_image_dict = json.loads(spu.attr_image_dict)
    images_dict = json.loads(spu.images_dict)
    image_key = None
    print ("对应spu属性 ", spu, attr_image_dict, images_dict, attr)
    # 遍历字典项，找到可能的属性图片，可能为空
    for attr_key in attr_image_dict:
        print(attr_key)
        if attr.find(attr_key) >= 0:
            image_key = attr_image_dict.get(attr_key)
            print("匹配成功")
            break

    print(image_key, images_dict.get(image_key))

    lightin_sku.image = images_dict.get(image_key)
    lightin_sku.imaged = True
    lightin_sku.save()
    print("保存成功")


@shared_task
def post_combo_feed():
    from shop.photo_mark import fill_image, get_remote_image
    import os
    from django.conf import settings
    domain = "http://admin.yallavip.com"
    FONT = os.path.join(settings.BASE_DIR, "static/font/ARIAL.TTF")

    try:
        from PIL import Image, ImageDraw, ImageFont, ImageEnhance

    except ImportError:
        import Image, ImageDraw, ImageFont, ImageEnhance

    from .video import fb_slideshow

    page_nos = MyPage.objects.filter(active=True, is_published=True).values_list('page_no', flat=True)
    # page_nos = ["281101289261739"]   #for debug
    for page_no in page_nos:

        combo = Combo.objects.filter(comboed=True, listed=True, imaged=True, o_sellable__gt=0).order_by('?')[:1].first()
        items = combo.combo_item.all()
        if items.count() > 6:
            continue

        print("准备在page %s 上发组合商品 %s 的动图" % (page_no, combo))
        dest_images = []
        # 首张图要变成1:1,以便和后面的图一样大小
        im = get_remote_image(combo.image_marked)

        new_im = fill_image(im)

        # out.show()
        image_filename = combo.SKU + '_slide.jpg'

        destination = os.path.join(settings.MEDIA_ROOT, "combo/", image_filename)

        new_im.save(destination, 'JPEG', quality=95)
        # out.save('target%s.jpg'%(combo.SKU), 'JPEG')

        destination_url = domain + os.path.join(settings.MEDIA_URL, "combo/", image_filename)

        dest_images.append(destination_url)

        # 两次要用到拼图：制作组合图和制作动图，可以考虑一次搞定，把images列表数据存起来即可

        for item in items:
            print (item, item.SKU)
            sku = item.lightin_sku

            # 如果sku有属性图片则用属性图片，否则用spu图片
            image = None
            if sku.image:
                image = sku.image
                print("sku 图片")
            else:

                spu = sku.lightin_spu
                # images = json.loads(Lightin_SPU.objects.get(spu_sku__SKU= item.SKU).images)
                if spu.images_dict:
                    image = json.loads(spu.images_dict).values()
                    if image and len(image) > 0:
                        a = "/"
                        image_split = list(image)[0].split(a)

                        image_split[4] = '800x800'
                        image = a.join(image_split)
                        print("spu 图片", spu, image)

            im = get_remote_image(image)
            if not im:
                break

            dest_images.append(image)

        if len(dest_images) == items.count() + 1:
            post_id = fb_slideshow(list(dest_images), page_no)

            print("postid ", post_id)
        else:
            combo.combo_error = "为page %s组合动图时image数量少了" % (page_no)
            combo.save()
            continue


# 更新相册对应的主页外键
# update fb_myalbum a , fb_mypage p set a.mypage_id = p.id where p.page_no = a.page_no
'''
from django.db import connection, transaction

    sql = "UPDATE prs_lightin_spu SET  quantity =(SELECT sum(k.quantity) FROM prs_lightin_sku k WHERE k.SPU = prs_lightin_spu.SPU and prs_lightin_spu.published = true)"

    cursor = connection.cursor()
    cursor.execute(sql)
    transaction.commit()
'''
