

# Create your tasks here
from __future__ import absolute_import, unicode_literals

import json
import numpy as np
import random
import re
import requests
import time

from celery import shared_task, task
from django.db.models import Q, Count, Max
from django.utils import timezone as datetime
from django.utils import timezone as dt
from fb.models import MyPage, MyAlbum

from orders.models import Order, OrderDetail, OrderDetail_lightin,Verify,Sms

from shop.models import ProductCategoryMypage
from shop.models import Shop, ShopifyProduct, ShopifyVariant, ShopifyImage, ShopifyOptions
from customer.models import  Draft
from commodity.models import  PageRule

from .models import *
from .shop_action import sync_shop
from facebook_business.api import FacebookAdsApi
from facebook_business.adobjects.page import Page

from shop.photo_mark import yallavip_mark_image
from prs.album import get_promote_ads

my_app_id = "562741177444068"
my_app_secret = "e6df363351fb5ce4b7f0080adad08a4d"
#my_access_token = "EAAHZCz2P7ZAuQBABHO6LywLswkIwvScVqBP2eF5CrUt4wErhesp8fJUQVqRli9MxspKRYYA4JVihu7s5TL3LfyA0ZACBaKZAfZCMoFDx7Tc57DLWj38uwTopJH4aeDpLdYoEF4JVXHf5Ei06p7soWmpih8BBzadiPUAEM8Fw4DuW5q8ZAkSc07PrAX4pGZA4zbSU70ZCqLZAMTQZDZD"
#my_access_token = "	EAAcGAyHVbOEBAEtwMPUeTci0x3G6XqlAwIhuQiZBZCVhZBRx88Rki0Lo7WNSxvAw7jAhhRlxsLjARbAZCnDvIoQ68Baj9TJrQC8KvEzyDhRWlnILGxRyc49b02aPInvpI9bcfgRowJfDrIt0kFE01LGD86vLKuLixtB0aTvTHww9SkedBzFZA"
ad_tokens = "EAAHZCz2P7ZAuQBANXASqgDJV7vsZCKn4KoZCNAyEFUzWV4XFlvs3exbtdQJrLrVzkuIqpZCZBjKBwUJEL9lxFJE8zZA6pMtCQqgzWW6J1ldyjTUCztSs4kMybpsHi0lNfk45veF4SGjmXJwurTnskia71yZAQSqL0DxuXLCC3xFXooZC1tpB9AB9G"
DEBUG = False

if DEBUG:
    WAREHOUSE_CODE = "TW02"
    shipping_method = "L002-KSA-TEST",
    appToken = "85413bb8f6a270e1ff4558af80f2bef5"
    appKey = "9dca0be4c02bed9e37c1c4189bc1f41b"
else:
    WAREHOUSE_CODE = "W07"
    #warehouse_code = "W08"
    warehouse_code_arr = ["W07", "W08"]
    shipping_methods = ["ARAMEX_KSA","FETCHR_SAUDI_DOM"]
    #shipping_method = "FETCHR_SAUDI_DOM"
    #shipping_method = "ARAMEX_KSA"
    appToken = "909fa3df3b98c26a9221774fe5545afd"
    appKey = "b716b7eb938e9a46ad836e20de0f8b07"

    tms_appToken = "883b3289a5e3b55ceaddb2093834c13a"
    tms_appKey = "883b3289a5e3b55ceaddb2093834c13a574fda321ae620e2aa43c2117abb7553"


from prs.fb_action import  get_token



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

'''
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
'''

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
            access_token, long_token = get_token(mypage.page_no)
            FacebookAdsApi.init(access_token=access_token)
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

            access_token, long_token = get_token(mypage.page_no)
            FacebookAdsApi.init(access_token=access_token)
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
                if title.find(spu.handle) == -1:
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
        #暂停删老图
        #delete_outdate_lightin_album(batch_no)


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

    #delete_missed_photo()
    delete_oversea_photo()


# 把所有sku都没有库存，spu还在发布状态的从Facebook删除
@shared_task
def delete_lightin_album_cate(cate):
    # 更新还在发布中的spu的库存
    from django.db import connection, transaction



    lightinalbums_all = LightinAlbum.objects.filter(lightin_spu__breadcrumb__contains = "Underwear", published=True).values_list("myalbum__page_no", "fb_id").order_by(
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

    #delete_missed_photo()
    delete_oversea_photo()

# 删除lightin_album 的某个特定子集
def delete_out_lightin_album(lightinalbums_out):


    # 选择所有可用的page

    for page_no in lightinalbums_out:

        #FacebookAdsApi.init(access_token=get_token(page_no))





        photo_nos = lightinalbums_out[page_no]
        print("page %s 待删除数量 %s  " % (page_no, len(photo_nos)))
        if photo_nos is None or len(photo_nos) == 0:
            continue

        delete_photos(page_no,photo_nos)


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
        if myphotos:
            print ("handle %s 缺货 %s"%( handle, myphotos.count()))
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

            myphotos.update(active=False)

    # 选择所有可用的page
    for page_no in photo_miss:


        photo_nos = photo_miss[page_no]
        print("page %s 待删除数量 %s  " % (page_no, len(photo_nos)))
        if photo_nos is None or len(photo_nos) == 0:
            continue

        delete_photos(page_no, photo_nos)


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


        photo_nos = photo_miss[page_no]
        print("page %s 待删除数量 %s  " % (page_no, len(photo_nos)))
        if photo_nos is None or len(photo_nos) == 0:
            continue

        delete_photos(page_no, photo_nos)


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

        myphotos.update(active=False)

    # 选择所有可用的page
    for page_no in photo_miss:


        photo_nos = photo_miss[page_no]
        print("page %s 待删除数量 %s  " % (page_no, len(photo_nos)))
        if photo_nos is None or len(photo_nos) == 0:
            continue

        delete_photos(page_no, photo_nos)


# 删除无货的海外仓包裹
def delete_oversea_photo():
    from facebook_business.api import FacebookAdsApi
    from fb.models import MyPhoto

    # 找出已下架商品的handle
    #handles = Lightin_SKU.objects.filter(o_sellable__lte=0, SKU__startswith="579815").values_list("SKU",
     #                                                                                             flat=True).distinct()

    skus = Lightin_SKU.objects.filter(o_sellable__lte=0, SKU__startswith="579815",published=True).distinct()
    photo_miss = {}
    # 在fb的图片里找handle的图片
    for sku in skus:
        handle = sku.SKU
        myphotos = MyPhoto.objects.filter(name__contains=handle, active = True)
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

        sku.published=False
        sku.save()
        myphotos.update(active=False)


    # 选择所有可用的page
    for page_no in photo_miss:


        photo_nos = photo_miss[page_no]
        print("page %s 待删除数量 %s  " % (page_no, len(photo_nos)))
        if photo_nos is None or len(photo_nos) == 0:
            continue

        delete_photos(page_no, photo_nos)


def delete_posts(page_no, post_ids):
    from facebook_business.adobjects.pagepost import PagePost
    access_token, long_token = get_token(page_no)
    if not access_token:
        error = "获取token失败"
        print(error, page_no)

        return error, None


    FacebookAdsApi.init(access_token=access_token)
    for post_id in post_ids:

        fields = [
        ]
        params = {

        }
        error = ""
        try:

            response = PagePost(post_id).api_delete(
                fields=fields,
                params=params,
            )

        except Exception as e:
            print("删除post出错", post_id, e)
            error = "删除post出错"

        MyFeed.objects.filter(feed_no=post_id).update(

            active=False

        )


def delete_photos(page_no, photo_nos):
    from facebook_business.adobjects.photo import Photo
    access_token, long_token = get_token(page_no)
    if not access_token:
        error = "获取token失败"
        print(error, page_no)

        return error, None

    FacebookAdsApi.init(access_token=access_token)
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
            #print (my_access_token)

            #continue


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
    from django.db.models import F

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

            # 更新barcode占用

            #barcode = inventory[1]
            #barcode.o_reserved = F("o_reserved") + inventory[2]




        OrderDetail_lightin.objects.bulk_create(orderdetail_lightin_list)
    else:
        print("映射不成功", error)

    return error


def get_barcodes(sku, quantity, price):
    inventory_list = []
    lightin_barcodes = Lightin_barcode.objects.filter(SKU=sku).order_by("?")

    print ("get_barcodes",  sku, type(sku))
    if lightin_barcodes is None:
        print("找不到映射，也就意味着无法管理库存！")
        # 需要标识为异常订单
        error = "找不到SKU"
        return None, error

    # 每个可能的条码
    for lightin_barcode in lightin_barcodes:
        print("处理每个可能的条码", lightin_barcode)
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

        lightin_barcode.synced=False
        lightin_barcode.save()

        print("        条码 %s , 条码可售库存 %s 占用 %s" % (lightin_barcode, lightin_barcode.sellable, occupied))

        inventory_list.append([sku, lightin_barcode, occupied, price])

    # 需求没有被满足，标识订单缺货
    print("quantity", quantity)
    if quantity > 0:

        error = str(sku) + "  缺货"
        return None, error
    else:


        return inventory_list, ""


@shared_task
def fulfill_orders_lightin():
    orders = Order.objects.filter(
        Q(fulfillment_status__isnull=True)|Q(fulfillment_status=""),
                                financial_status="paid",

                                  status="open",
                                  verify__verify_status="SUCCESS",
                                  verify__sms_status="CHECKED",
                                  wms_status__in=["", "F"])
    print("共有%s个订单待发货" % (orders.count()))
    order_list = []
    for order in orders:
        #if order.stock in ["充足", "紧张"]:
        #只有所有sku可售库存大于等于零，才发货，避免库存争夺

        if order.stock in ["充足","紧张"]:
            print("准备发货", order)
            error = mapping_order_lightin(order)
            if error == "":
                result = fulfill_order_lightin(order)
                if result:
                    # 发货成功的列表
                    order_list.append(order)
        else:
            print ("库存不足", order.order_no)

    # 提交仓库准备发货成功的，要更新本地库存
    update_barcode_stock(order_list, "W")

    #shopify发货
    sync_Shipped_order_shopify()

    #同步wms库存
    sync_wms_quantity()


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
        warehouse_code = order_item.barcode.warehouse_code
        item = {
            "product_sku": order_item.barcode.barcode,
            # "product_name_en":title,
            "product_declared_value": order_item.price,
            "quantity": order_item.quantity,
        }
        items.append(item)
    #选择物流公司
    shipping_method=  shipping_methods[1]

    param = {
        "platform": "B2C",
        "allocated_auto": "1",
        "warehouse_code": warehouse_code,
        "shipping_method": shipping_method,
        "reference_no": order.order_no,
        # "order_desc":"\u8ba2\u5355\u63cf\u8ff0",
        "country_code": "SA",
        "province": order.receiver_city,
        "city": order.verify.city,
        "address1": order.receiver_addr1,
        "address2": order.receiver_addr2,
        "address3": "",
        "zipcode": "123456",
        "doorplate": "doorplate",
        "company": "company",
        "name": order.receiver_name,
        "phone": order.verify.phone_1,
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
            status = "transit",
            wms_status=result.get("order_status"),
            logistic_no=result.get("tracking_no"),
            fulfill_error="",
        )
        return True
    else:
        Order.objects.filter(pk=order.pk).update(
            wms_status="F",
            fulfill_error=result.get("message")[:499],

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

                try:
                    order = Order.objects.get(order_no=order_no)
                except:
                    print("not found order", order_no)
                    continue
                if order:
                    send_time = None

                    if  data.get("order_status") == "D":
                        send_time = data.get("date_shipping")
                        if order.wms_status == "W" :
                            # wms状态从待发货变成已发货，就修改本地 barcode 库存

                            items = OrderDetail_lightin.objects.filter(order=order)
                            # 更新本地barcode库存
                            for item in items:
                                barcode = Lightin_barcode.objects.get(barcode=item.barcode)

                                if  barcode.o_reserved >= item.quantity:
                                    barcode.o_reserved = F("o_reserved") - item.quantity
                                    barcode.o_quantity = F("o_quantity") - item.quantity
                                    barcode.save()
                                    print ("更新本地barcode库存")
                                else:
                                    print ("保留库存小于应释放库存##############")




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

    orders = Order.objects.filter(~Q(order_no__startswith="yalla"),~Q(fulfillment_status = "fulfilled" ), status="open", wms_status__in=["W"], logistic_no__isnull=False,
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
            error = data.get("errors").get("order")
            if error :
                if error[0].find("already fulfilled") >-1:
                    fulfillment_status = "fulfilled"

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
        '''
        Order.objects.update_or_create(
            order_no=order.order_no,
            defaults={
                "fulfillment_status": fulfillment_status,

            },
        )
        '''
        order.fulfillment_status = fulfillment_status
        order.save()


def get_wms_product():
    page = 1
    #pages = 0
    last_update_time = Lightin_barcode.objects.aggregate(last_update_time=Max("product_modify_time")).get('last_update_time')
    if last_update_time:
        update_start_time = last_update_time.strftime("%Y-%m-%d")
    else:
        update_start_time = "2000-01-01"

    pages ,result = get_wms_product_page(page, update_start_time)


    print("一共 %s页" % pages)
    while page <= pages and result:

        print("正在处理第 %s 页" % page)
        get_wms_product_page.apply_async((page,update_start_time), queue='wms')

        page += 1

@shared_task
def get_wms_product_page(page,update_start_time):
    param = {
        "pageSize": "100",
        "page": page,
        "product_sku": "",
        "product_sku_arr": [],
        #"start_time": "2018-02-08 10:00:00",
        "update_start_time": update_start_time,

    }

    service = "getProductList"

    result = yunwms(service, param)

    # print(result)
    if result.get("ask") == "Success":
        for data in result.get("data"):
            Lightin_barcode.objects.update_or_create(
                barcode=data.get("product_sku"),
                defaults={
                    "reference_no": data.get("reference_no"),


                    "product_status": data.get("product_status"),
                    "product_title": data.get("product_title"),
                    "product_weight": data.get("product_weight"),
                    "product_add_time": data.get("product_add_time"),
                    "product_modify_time": data.get("product_modify_time"),

                },
            )

        pages = int(int(result.get("count")) / 100)
    else:

        print("获取wms产品出错",result.get("message") )
        return  0, False

    if result.get("nextPage") == "false":
        print("No more page")
        return  pages, False
    else:
        return  pages, True



def sync_wms_quantity():
    mysqls = [
        "update prs_lightin_barcode set o_quantity = y_sellable + y_reserved ,o_sellable = y_sellable , o_reserved = y_reserved,synced=True",
        "UPDATE prs_lightin_sku INNER JOIN ( SELECT SKU,sum(o_sellable) as quantity FROM prs_lightin_barcode GROUP BY SKU ) b ON prs_lightin_sku.SKU = b.SKU SET prs_lightin_sku.o_quantity = b.quantity ",
        "update prs_lightin_sku set o_sellable = o_quantity - o_reserved",
        "UPDATE prs_lightin_spu INNER JOIN ( SELECT SPU, sum(o_sellable) as quantity FROM prs_lightin_sku GROUP BY SPU ) b ON prs_lightin_spu.SPU = b.SPU SET prs_lightin_spu.sellable = b.quantity",
    ]

    warehouse_codes = Lightin_barcode.objects.values_list("warehouse_code",flat=True).distinct()
    for warehouse_code in warehouse_codes:
        if warehouse_code:
            barcodes = Lightin_barcode.objects.filter(warehouse_code= warehouse_code,synced=False).values_list("barcode",flat=True)
            if barcodes:
                get_wms_quantity(warehouse_code,list(barcodes))

            for mysql in mysqls:
                print(mysql)
                my_custom_sql(mysql)

def get_wms_quantity(warehouse_code, barcodes=[]):


    page = 1
    pages, result = get_wms_quantity_page(warehouse_code,page, barcodes)

    print("一共 %s页" % pages)

    while page <= pages and result:

        print("正在处理第 %s 页" % page)
        get_wms_quantity_page.apply_async((warehouse_code, page, barcodes), queue='wms')

        page += 1

@shared_task
def get_wms_quantity_page(warehouse_code,page, barcodes):

    param = {
        "pageSize": "100",
        "page": page,
        "product_sku": "",
        "product_sku_arr": barcodes,
        "warehouse_code": warehouse_code,
        "warehouse_code_arr": [],
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
                    "updated_time": dt.now(),
                    'synced': True,
                    # "quantity":  int(data.get("sellable")) + int(data.get("reserved"))

                },
            )

        pages = int(int(result.get("count")) / 100)
        print("page %s got"%page)
    else:
        print("获取wms库存出错", result.get("message"))
        return 0, False


    if result.get("nextPage") == "false":
        print("No more page")
        return  pages, False
    else:
        return  pages, True




def getShippingMethod():
    param = {
        "warehouseCode": WAREHOUSE_CODE,
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
    Lightin_SKU.objects.update(o_reserved=0, o_locked = 0)

    # 计算库存占用

    sku_list = []
    # 计算组合商品， lock库存
    sku_locked_quantity = {}
    '''
    combo_skus = ComboItem.objects.filter(combo__locked=True).values_list('SKU').annotate(Sum('combo__o_quantity'))

    for combo_sku in combo_skus:
        # 每个sku占用的库存，等于它对应的combo的库存

        sku_locked_quantity[combo_sku[0]] = sku_locked_quantity.get(combo_sku[0], 0) + combo_sku[1]
        if combo_sku[0] not in sku_list:
            sku_list.append(combo_sku[0])

    print("组合商品 有%s个sku 锁定库存 需要更新" % (len(sku_locked_quantity)))
    '''
    # 计算订单 reserved库存
    sku_reserved_quantity = {}
    order_skus = OrderDetail.objects.filter(order__status="open",
                                            # order__order_time__gt =  dt.now() - dt.timedelta(hours=overtime),
                                            ).values_list('sku').annotate(Sum('product_quantity'))
    for order_sku in order_skus:
        print(order_sku)
        sku_reserved_quantity[order_sku[0]] = sku_reserved_quantity.get(order_sku[0], 0) + order_sku[1]
        if order_sku[0] not in sku_list:
            sku_list.append(order_sku[0])

    print("开放的订单 有%s个sku需要更新" % (len(sku_reserved_quantity)))

    # 计算草稿
    draft_skus = DraftItem.objects.filter(draft__status="open",
                                          draft__created_at__gt=dt.now() - dt.timedelta(hours=overtime),
                                          ).values_list('sku').annotate(Sum('quantity'))

    for draft_sku in draft_skus:
        sku_reserved_quantity[order_sku[0]] = sku_reserved_quantity.get(draft_sku[0], 0) + draft_sku[1]

        if draft_sku[0] not in sku_list:
            sku_list.append(draft_sku[0])

    #计算自己的草稿
    '''
    y_draft_skus = Draft.objects.filter( customer__update_time__gt = dt.now() - dt.timedelta(hours=overtime),).values_list('lightin_sku__SKU').annotate(Sum('quantity'))
    #draft__status = "open",draft__created_at__gt = dt.now() - dt.timedelta(hours=overtime),
    for y_draft_sku in y_draft_skus:
        sku_reserved_quantity[order_sku[0]] = sku_reserved_quantity.get(y_draft_sku[0], 0) + draft_sku[1]

        if y_draft_sku[0] not in sku_list:
            sku_list.append(y_draft_sku[0])
    '''
    print("加上24小时内的草稿 有%s个sku需要更新" % (len(sku_reserved_quantity)))

    # 更新库存占用
    lightin_skus = Lightin_SKU.objects.filter(SKU__in=sku_list).distinct()
    for lightin_sku in lightin_skus:
        try:
            lightin_sku.o_locked = sku_locked_quantity.get(lightin_sku.SKU,0)
            lightin_sku.o_reserved = sku_reserved_quantity.get(lightin_sku.SKU,0)
            # lightin_sku.o_sellable = lightin_sku.o_quantity - sku_quantity[sku]
            lightin_sku.save()

            # print(lightin_sku, lightin_sku.o_reserved, lightin_sku.o_sellable)

        except Exception as e:
            print("更新出错", lightin_sku, e)



    # 更新所有的可售库存
    mysql = "update prs_lightin_sku set o_sellable = o_quantity - o_locked - o_reserved"

    my_custom_sql(mysql)

    # 更新对应的spu的可售库存
    #print(sku_list)
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
    Lightin_SKU.objects.filter(SKU__in=skus).update(o_reserved=0, o_locked = 0)

    # 计算库存占用

    sku_list = []
    # 计算组合商品
    sku_locked_quantity = {}
    combo_skus = ComboItem.objects.filter(combo__locked=True, lightin_sku__SKU__in=skus).values_list('SKU').annotate(
        Sum('combo__o_quantity'))

    for combo_sku in combo_skus:
        # 每个sku占用的库存，等于它对应的combo的库存

        sku_locked_quantity[combo_sku[0]] = sku_locked_quantity.get(combo_sku[0], 0) + combo_sku[1]
        if combo_sku[0] not in sku_list:
            sku_list.append(combo_sku[0])

    print("组合商品 有%s个sku需要更新" % (len(sku_locked_quantity)))

    # 计算订单
    sku_reserved_quantity = {}
    order_skus = OrderDetail.objects.filter(order__status="open", sku__in=skus,
                                            # order__order_time__gt =  dt.now() - dt.timedelta(hours=overtime),

                                            ).values_list('sku').annotate(Sum('product_quantity'))
    for order_sku in order_skus:
        print(order_sku)
        sku_reserved_quantity[order_sku[0]] = sku_reserved_quantity.get(order_sku[0], 0) + order_sku[1]
        if order_sku[0] not in sku_list:
            sku_list.append(order_sku[0])

    print("加上开放的订单 有%s个sku需要更新" % (len(sku_reserved_quantity)))

    # 计算草稿
    draft_skus = DraftItem.objects.filter(draft__status="open", sku__in=skus,
                                          draft__created_at__gt=dt.now() - dt.timedelta(hours=overtime),
                                          ).values_list('sku').annotate(Sum('quantity'))

    for draft_sku in draft_skus:
        sku_reserved_quantity[draft_sku[0]] = sku_reserved_quantity.get(draft_sku[0], 0) + draft_sku[1]

        if draft_sku[0] not in sku_list:
            sku_list.append(draft_sku[0])
    # 计算自己的草稿
    '''
    y_draft_skus = Draft.objects.filter(sku__in=skus,
        customer__update_time__gt=dt.now() - dt.timedelta(hours=overtime), ).values_list(
        'lightin_sku__SKU').annotate(Sum('quantity'))
    # draft__status = "open",draft__created_at__gt = dt.now() - dt.timedelta(hours=overtime),
    for y_draft_sku in y_draft_skus:
        sku_reserved_quantity[order_sku[0]] = sku_reserved_quantity.get(y_draft_sku[0], 0) + draft_sku[1]

        if y_draft_sku[0] not in sku_list:
            sku_list.append(y_draft_sku[0])
    '''
    print("加上24小时内的草稿 有%s个sku需要更新" % (len(sku_reserved_quantity)))

    # 更新库存占用
    lightin_skus = Lightin_SKU.objects.filter(SKU__in=sku_list).distinct()
    for lightin_sku in lightin_skus:
        try:
            lightin_sku.o_locked = sku_locked_quantity.get(lightin_sku.SKU, 0)
            lightin_sku.o_reserved = sku_reserved_quantity.get(lightin_sku.SKU, 0)
            # lightin_sku.o_sellable = lightin_sku.o_quantity - sku_quantity[sku]
            lightin_sku.save()

            # print(lightin_sku, lightin_sku.o_reserved, lightin_sku.o_sellable)

        except Exception as e:
            print("更新出错", lightin_sku, e)


    # 更新所有的可售库存
    mysql = "update prs_lightin_sku set o_sellable = o_quantity - o_locked - o_reserved"

    my_custom_sql(mysql)

    # 更新对应的spu的可售库存
    #print(sku_list)
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

    #先重置所有的reserved
    Lightin_barcode.objects.update(o_reserved = 0)
    for barcode in barcode_quantity:
        try:
            lightin_barcode = Lightin_barcode.objects.get(pk=barcode)
            lightin_barcode.o_reserved = barcode_quantity[barcode]
            lightin_barcode.o_sellable = lightin_barcode.o_quantity - barcode_quantity[barcode]

            lightin_barcode.save()

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

    adjust_shopify_inventories()

    #elete_outstock_lighin_album()
    auto_smscode()


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
            page += 1

        '''
        //初始化barcode库存
        update prs_lightin_barcode set o_quantity = y_sellable + y_reserved ,o_sellable = y_sellable , o_reserved = y_reserved
        
        //初始化sku库存
        UPDATE prs_lightin_sku
        INNER JOIN (
        SELECT
        SKU,
        sum(o_sellable) as quantity
        FROM
        prs_lightin_barcode
        GROUP BY
        SKU
        ) b ON prs_lightin_sku.SKU = b.SKU
        SET prs_lightin_sku.o_quantity = b.quantity 
        
        update prs_lightin_sku set o_sellable = o_quantity - o_reserved
        
        //初始化spu库存
        UPDATE prs_lightin_spu
        INNER JOIN (
        SELECT
        SPU,
        sum(o_sellable) as quantity
        FROM
        prs_lightin_sku
        GROUP BY
        SPU
        ) b ON prs_lightin_spu.SPU = b.SPU
        SET prs_lightin_spu.sellable = b.quantity
        '''


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

            skus = items.values_list("lightin_sku__SKU",flat=True)
            cal_reserved_skus(list(skus))

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

    print(main_cate, main_cate_nums, sub_cate, sub_cate_nums, sub_cate_price)
    skus = []
    # 随机取main_cate_nums个大件
    skus_all = Lightin_SKU.objects.filter(o_sellable__gt=0, lightin_spu__breadcrumb__icontains=main_cate)
    skus.extend(random.sample(list(skus_all), main_cate_nums))

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
    print(sku, skus)

    combo, created = Combo.objects.update_or_create(SKU=sku,
        defaults={
        'comboed'  :True
        }
    )

    comboitem_list = []
    price = 0
    for row in skus:
        # print("row is ",row)
        print("comboitem ", row.SKU, row.vendor_supply_price)
        comboitem = ComboItem(
            combo=combo,
            lightin_sku=row,
            SKU=row.SKU
        )
        price += row.vendor_supply_price
        comboitem_list.append(comboitem)

    print(comboitem_list)

    ComboItem.objects.filter(combo=combo).delete()
    ComboItem.objects.bulk_create(comboitem_list)


    combo.sku_price = int(price * 6.5)
    combo.o_quantity = 1
    combo.o_sellable = 1
    combo.locked = True
    combo.save()

    print("new combo is ", combo)

    # 更新库存以便锁定
    cal_reserved_skus(skus)


def init_combo(sku):
    # 随机生成包裹类型
    combo_types = [

        {
            "main_cate": '"Bags"',
            "main_cate_nums": 2,
            "sub_cates": '"Jewelry & Watches"',
            "sub_cate_nums": [3, 6],
            "sub_cate_price": 2
        },
    ]
    '''
           {
               "main_cate": '"Women\'s Tops & Sets"',
               "main_cate_nums": 2,
               "sub_cates": '"Women\'s Tops & Sets"',
               "sub_cate_nums": [3, 4],
               "sub_cate_price": 3.6
           },
           '''

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
        promote = "Free Shipping"
        draw1.rectangle((x + 20, y + 55, x + 250, y + 95), fill='yellow')
        draw1.text((x + 30, y + 60), promote, font=font,
                   fill=(0, 0, 0))  # 设置文字位置/内容/颜色/字体
        # 写件数 和 售价
        font = ImageFont.truetype(FONT, 50)
        draw1.text((x + 450, y + 25), "%s sets" % (item_count), font=font,
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

def valid_combo():
    combo_items = ComboItem.objects.filter(lightin_sku__o_sellable__lt=0).values_list("combo").distinct()

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

    #from .video import fb_slideshow

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

#规范电话号码
def valid_phone(x):
    x = str(x)
    x = x.replace(' ', '')
    x = x.replace('o', '')
    x = x.replace('O', '')

    if x.find('966') > -1:
        a = x.find('966') + 3
        x = x[a:]
    x = x.lstrip('0')

    return x

def send_sms(verify_orders_checked):
    from yunpian_python_sdk.model import constant as YC
    from yunpian_python_sdk.ypclient import YunpianClient
    import urllib
    import sys
    from django.utils import timezone as dt

    clnt = YunpianClient('2f22880b34b7dc5c6d93ce21047601f9')

    for verify_order  in verify_orders_checked:

        #检验电话号码
        phone_1 = verify_order.phone_1
        if not len(phone_1) == 9:
            #可能是多号码，也可能是号码不正确，先返回错误，不自动拆分多个电话号码
            error = "电话号码错误"
            verify_order.verify_status='SIMPLE'
            verify_order.verify_comments ="phone to be confirm"
            verify_order.save()
            continue

        #判断是否需要发送验证码
        #还没做



        # 随机生成验证码，避免作弊
        code = "F"+ str(random.randint(0,99999)).zfill(5)
        print(phone_1, code)

        #发送验证码
        param = {YC.MOBILE: "+966"+phone_1,
                 YC.TEXT: '【YallaVIP】Please send  YallaVIP\'s Confirmation code#%s# to us by facebook messanger. We will deliver your order when we get your code.' %(code)}

        urllib.parse.urlencode(param)
        r = clnt.sms().single_send(param)

        #记录本次发送的验证码
        #tobe do
        Sms.objects.create(
            phone="966"+phone_1,
            send_status=r.code(),
            send_time=dt.now(),
            content=code,
            fail_reason=r.msg(),

        )
        # 记录发送状态到数据库
        verify_order.sms_status = "WAIT"
        verify_order.save()


#自动发送验证码
@shared_task
def auto_smscode():
    from yunpian_python_sdk.model import constant as YC
    from yunpian_python_sdk.ypclient import YunpianClient
    import urllib
    import sys
    from django.utils import timezone as dt

    #取需要处理的订单
    #取出还没添加到审核的订单
    orders_tocheck = Order.objects.filter(verify__isnull=True, status="open",
                                  financial_status__in=("paid","pending"))
    # 添加到待审核订单
    for row in orders_tocheck:

        facebook_user_name = ''
        sales = ''
        tmp = re.split(r"\[|\]", str(row.order_comment)[:100])
        if (len(tmp) > 3):
            facebook_user_name = tmp[1]
            sales = tmp[3]
        elif (len(tmp) > 1):
            facebook_user_name = tmp[1]

        v = Verify(
            order=Order.objects.get(id=row.id),
            verify_status="PROCESSING",
            city = row.receiver_city,
            phone_1=valid_phone(row.receiver_phone),
            sms_status="NOSTART",
            start_time=datetime.now(),
            final_time=datetime.now(),
        )

        if row.customer:
            v.facebook_user_name=",".join(list(row.customer.customer_conversation.values_list("name",flat=True)))
            v.sales = row.customer.sales
            v.conversation_link = ",".join(list(row.customer.customer_conversation.values_list("conversation",flat=True)))


        v.save()
        split_conversation_link(v)

    #还没发送验证码的订单
    verify_orders = Verify.objects.filter( sms_status = "NOSTART",order__status="open", order__financial_status="paid",)

    #审单




    #不在派送范围的直接标记问题单
    verify_orders_outrang = verify_orders.filter(city ="None").update(verify_comments ="out of range")


    #验证通过的，这里只考虑了一种情况：城市在派送范围内
    verify_orders_checked = verify_orders.filter(~Q(city ="None"))
    clnt = YunpianClient('2f22880b34b7dc5c6d93ce21047601f9')

    for verify_order  in verify_orders_checked:

        #检验电话号码
        phone_1 = verify_order.phone_1
        if not len(phone_1) == 9:
            #可能是多号码，也可能是号码不正确，先返回错误，不自动拆分多个电话号码
            error = "电话号码错误"
            verify_order.verify_status='SIMPLE'
            verify_order.verify_comments ="phone to be confirm"
            verify_order.save()
            continue

        #判断是否需要发送验证码
        #还没做



        # 随机生成验证码，避免作弊
        code = "F"+ str(random.randint(0,99999)).zfill(5)
        print(phone_1, code)

        #发送验证码
        param = {YC.MOBILE: "+966"+phone_1,
                 YC.TEXT: '【YallaVIP】Please send  YallaVIP\'s Confirmation code#%s# to us by facebook messanger. We will deliver your order when we get your code.' %(code)}

        urllib.parse.urlencode(param)
        r = clnt.sms().single_send(param)

        #记录本次发送的验证码
        #tobe do
        Sms.objects.create(
            phone="966"+phone_1,
            send_status=r.code(),
            send_time=dt.now(),
            content=code,
            fail_reason=r.msg(),

        )
        # 记录发送状态到数据库
        verify_order.sms_status = "WAIT"
        verify_order.save()

    #已发送验证码的订单
    wait_orders = Verify.objects.filter( sms_status = "WAIT",order__status="open", order__financial_status="paid")
    for wait_order in wait_orders:
        if wait_order.sms_code:
            code = re.findall("\d+",  wait_order.sms_code)
        else:
            code = re.findall("\d+",  wait_order.cs_reply)

        if not code:
            continue

        reply_code =  "F" + code[0]
        phone_list = []
        if wait_order.phone_1:
            phone_list.append("966"+wait_order.phone_1)
        if wait_order.phone_2:
            phone_list.append("966"+wait_order.phone_2)
        sms = Sms.objects.filter(phone__in = phone_list, content = reply_code)

        if sms:
            # 记录验证成功状态到数据库
            wait_order.sms_status = "CHECKED"
            wait_order.save()


    return


@shared_task
def fulfill_orders():
    orders = Order.objects.filter(fulfillment_status__isnull=True,
                                  status="open",
                                  verify__verify_status="SUCCESS",
                                  verify__sms_status="CHECKED",
                                  wms_status__in=["", "F"])
    print("共有%s个订单待发货" % (orders.count()))
    order_list = []
    for order in orders:
        #if order.stock in ["充足", "紧张"]:
        #只有所有sku可售库存大于等于零，才发货，避免库存争夺

        if order.stock in ["充足","紧张"]:
            print("准备发货", order)
            error = mapping_order_lightin(order)
            if error == "":
                result = fulfill_order_lightin(order)
                if result:
                    # 发货成功的列表
                    order_list.append(order.pk)


        else:
            print ("库存不足")

    # 提交仓库准备发货成功的，要更新本地库存
    update_barcode_stock(order_list, "W")
    # 清空发货成功的订单对应的草稿
    clean_draft(order_list)

def clean_draft(order_list):

    customer_list = Order.objects.filter(pk__in=order_list).values_list("customer",flat=True)
    Draft.objects.filter(customer__in=customer_list).delete()

    '''
    customer.discount = 0 
    customer.order_amount = 0
    customer.handles = ""
    customer.sales = ""
    customer.save()
    '''

def sync_outstock_photo():
    fb_ids = LightinAlbum.objects.filter(lightin_spu__sellable__lte=0).values_list("fb_id",flat=True)
    myphotos = MyPhoto.objects.filter(photo_no__in=fb_ids,active=True)
    photos = myphotos.values_list("page_no", "photo_no").distinct()

    photo_miss = {}

    for photo in photos:
        page_no = photo[0]
        fb_id = photo[1]
        photo_list = photo_miss.get(page_no)
        if not photo_list:
            photo_list = []

        if fb_id not in photo_list:
            photo_list.append(fb_id)

        photo_miss[page_no] = photo_list

    myphotos.update(active=False)

    # 选择所有可用的page
    for page_no in photo_miss:


        photo_nos = photo_miss[page_no]
        print("page %s 待删除数量 %s  " % (page_no, len(photo_nos)))
        if photo_nos is None or len(photo_nos) == 0:
            continue

        delete_photos(page_no, photo_nos)

def sync_outstock_post():
    spus = Lightin_SPU.objects.filter(sellable__lte=0, active=True)
    feed_dict = {}

    for spu in spus:

        handle = spu.handle
        if not handle:
            print("handle [%s] 为空"%(handle))
            continue

        feeds = MyFeed.objects.filter(message__icontains=handle)
        if feeds:
            print("handle [%s] 有%s个feed待删除"%(handle, feeds.count()))
            feed_nos = feeds.values_list("page_no", "feed_no").distinct()

            for feed_no in feed_nos:
                page_no = feed_no[0]
                feed_id = feed_no[1]
                feed_list = feed_dict.get(page_no)
                if not feed_list:
                    feed_list = []

                if feed_id not in feed_list:
                    feed_list.append(feed_id)

                feed_dict[page_no] = feed_list

            spu.active=False
            spu.save()

    # 选择所有可用的page
    for page_no in feed_dict:


        feed_ids = feed_dict[page_no]
        print("page %s 待删除数量 %s  " % (page_no, len(feed_ids)))
        if feed_ids is None or len(feed_ids) == 0:
            continue

        delete_posts(page_no, feed_ids)
        #print(feed_ids)


#批量上传图片到shpify，并记录图片的id和原始对应的关系，以便以后更新变体图片
'''
Update a product by adding a new product image
PUT /admin/products/#{product_id}.json
{
  "product": {
    "id": 632910392,
    "images": [
      {
        "id": 850703190
      },
      {
        "id": 562641783
      },
      {
        "src": "http://example.com/rails_logo.gif"
      }
    ]
  }
}
'''
def update_shopify_products_images():
    spus = Lightin_SPU.objects.filter(published=True,image_published=False,sellable__gt=0,images_dict__isnull=False)
    for spu in spus:
        info, updated = update_shopify_product_images(spu)
        if updated:
            spu.image_published = True
            spu.images_shopify = json.dumps(info)
        else:
            spu.publish_error = info

        spu.save()



def update_shopify_product_images(spu):
    from shop.models import Shop, ShopifyProduct
    from prs.shop_action import post_product_main, update_or_create_product
    from .models import AliProduct

    dest_shop = "yallasale-com"
    shop_obj = Shop.objects.get(shop_name=dest_shop)

    shop_url = "https://%s:%s@%s.myshopify.com" % (shop_obj.apikey, shop_obj.password, shop_obj.shop_name)

    # image_no = 0

    if spu.images_dict:
        images_dict =json.loads(spu.images_dict)
        shopify_images = []
        for key in images_dict:
            shopify_image ={
                "src": images_dict[key],
                "alt": key,
            }
            shopify_images.append(shopify_image)
    else:
        return "没有图片信息",False



    params = {
        "product": {
            "id": spu.product_no,
            "images": shopify_images,
        }
    }
    headers = {
        "Content-Type": "application/json",
        "charset": "utf-8",

    }
    # 初始化SDK
    url = shop_url + "/admin/products/%s.json"%(spu.product_no)

    print("开始更新产品图片")
    print(url, json.dumps(params))

    r = requests.put(url, headers=headers, data=json.dumps(params))
    if r.text is None:
        return "更新产品图片失败", False
    try:
        data = json.loads(r.text)
        print("更新产品图片", r, data)
    except:
        print("更新产品图片失败")
        print(url, json.dumps(params))
        print(r)
        print(r.text)
        return "更新产品图片失败", False

    new_product = data.get("product")

    if new_product:
        images_shopify = {}
        images = new_product.get("images")
        for image in images:
            images_shopify[image.get("alt")] = image.get("id")
        return images_shopify, True
    else:

        print("更新产品图片失败！！！！")
        print(data)
        return "更新产品图片失败", False

def my_custom_sql(mysql):
    from django.db import connection, transaction
    with connection.cursor() as c:
        c.execute(mysql)
        rows = c.fetchall()

    return  rows

    # Data retrieval operation - no commit required
    #cursor.execute("SELECT foo FROM bar WHERE baz = %s", [self.baz])
    #row = cursor.fetchone()
    #transaction.commit_unless_managed()
    #return


def adjust_shopify_inventories():

    mysql = "select v.sku , v.inventory_item_no , s.o_sellable - v.inventory_quantity, s.o_sellable , v.inventory_quantity " \
            "from shop_shopifyvariant v, prs_lightin_sku s " \
            "where v.sku= s.SKU and v.inventory_quantity <> s.o_sellable"

    rows = my_custom_sql(mysql)


    n = len(rows)

    print("一共有 %s条待更新"%n)
    for row in rows:
        print("正在处理", row[0],row[1], row[2],row[3],row[4])
        info, adjusted = adjust_shopify_inventory(row[1],int(row[2]))
        if adjusted:

            skus = ShopifyVariant.objects.filter(sku=row[0])
            skus.update(inventory_quantity=row[3])
        n -= 1
        print("还有 %s条待更新" % n)
        time.sleep(1)

#把不在lightin_sku 里且库存大于0 的variant的库存都改成0
def zero_shopify_inventories():
    to_zero_products = ShopifyVariant.objects.filter(inventory_quantity__gt=0).exclude(
        sku__in=list(Lightin_SKU.objects.values_list("SKU",flat=True))
    )

    rows = to_zero_products.values_list("sku","inventory_item_no")
    for row in rows:

        info, adjusted = adjust_shopify_inventory(row[1],0)
        if adjusted:

            skus = ShopifyVariant.objects.filter(sku=row[0])
            skus.update(inventory_quantity=0)
        time.sleep(1)

def adjust_shopify_inventory(inventory_item_id,available_adjustment ):
    from shop.models import Shop, ShopifyProduct
    from prs.shop_action import post_product_main, update_or_create_product


    dest_shop = "yallasale-com"
    location_id = "11796512810"
    shop_obj = Shop.objects.get(shop_name=dest_shop)

    shop_url = "https://%s:%s@%s.myshopify.com" % (shop_obj.apikey, shop_obj.password, shop_obj.shop_name)

    # image_no = 0




    params = {
        "location_id": location_id,
        "inventory_item_id": inventory_item_id,
        "available_adjustment": available_adjustment,

    }
    headers = {
        "Content-Type": "application/json",
        "charset": "utf-8",

    }
    # 初始化SDK
    url = shop_url + "/admin/inventory_levels/adjust.json"

    print("开始更新库存")
    print(url, json.dumps(params))

    r = requests.post(url, headers=headers, data=json.dumps(params))
    if r.status_code == 200:
        return "更新库存成功", True
    else:
        print(r.text)
        return "更新库存失败", False

def get_shopify_inventory( ):

    from django.core.paginator import Paginator

    dest_shop = "yallasale-com"
    location_id = "11796512810"
    shop_obj = Shop.objects.get(shop_name=dest_shop)

    shop_url = "https://%s:%s@%s.myshopify.com" % (shop_obj.apikey, shop_obj.password, shop_obj.shop_name)

    params = {
        "location_ids":location_id,

    }

    # 初始化SDK
    url = shop_url + "/admin/inventory_levels.json"

    print("开始获取库存")
    variants = ShopifyVariant.objects.filter(sku__istartswith='s',synced=False).values_list("inventory_item_no",flat=True).order_by("inventory_item_no")
    ids = Paginator(list(variants),50)
    print("total page count", ids.num_pages  )
    for i in ids.page_range:
        print("page ", i)

        params["inventory_item_ids"] = ",".join(ids.page(i).object_list)
        r = requests.get(url,  params)

        if r.status_code == 200:
            data = json.loads(r.text)
            inventory_levels = data.get("inventory_levels")

            for inventory_level in inventory_levels:

                inventory_item_id = inventory_level.get("inventory_item_id")

                if inventory_item_id :
                    try:
                        ShopifyVariant.objects.update_or_create(inventory_item_no = inventory_item_id,
                                                        defaults ={
                                                            "inventory_quantity": inventory_level.get("available",0),
                                                            "synced":True,
                                                        }
                        )
                    except Exception as e:
                        print(inventory_item_id, inventory_level.get("available",0), e)


        else:
            print(r.text)
            return "获取库存失败", False

#更新价格,顺便把库存策略改成无货后不不能下单
def adjust_shopify_prices():
    mysql = "select v.sku , v.variant_no, s.sku_price " \
            "from shop_shopifyvariant v, prs_lightin_sku s " \
            "where v.sku= s.SKU and v.price <> s.sku_price and update_error='' and s.o_sellable>0  order by s.sku_price"

    rows = my_custom_sql(mysql)
    n = len(rows)

    print("一共有 %s条待更新" % n)
    for row in rows:
        print ("更新变体价格： ",row[0],row[2])

        info, adjusted = adjust_shopify_price(row)
        vs = ShopifyVariant.objects.filter(variant_no=row[1])
        if adjusted:
            vs.update(price=row[2],inventory_policy = "deny",update_error="")
        else:
            vs.update(update_error = info)

        n -= 1
        print("还有 %s条待更新" % n)
        time.sleep(1)

#根据库存更新产品可视状态
#所有sku都没有货的，就隐藏
#有库存，但是没有发布到channels 的，就要发布
#def adjust_listing():


def adjust_shopify_price(row):
    from shop.models import Shop, ShopifyProduct
    from prs.shop_action import post_product_main, update_or_create_product
    from .models import AliProduct

    dest_shop = "yallasale-com"
    location_id = "11796512810"
    shop_obj = Shop.objects.get(shop_name=dest_shop)

    shop_url = "https://%s:%s@%s.myshopify.com" % (shop_obj.apikey, shop_obj.password, shop_obj.shop_name)


    params = {
        "variant": {
                "id": row[1],
                "inventory_policy": "deny",
                "price": row[2]
              }
    }
    headers = {
        "Content-Type": "application/json",
        "charset": "utf-8",

    }
    # 初始化SDK
    url = shop_url + "/admin/variants/%s.json"%(row[1])

    print("开始更新变体")
    print(url, json.dumps(params))

    r = requests.put(url, headers=headers, data=json.dumps(params))
    if r.status_code == 200:
        return "更新变体成功", True
    else:
        print("更新变体失败",r,  r.text)
        return "更新变体失败", False

def create_album(page_no , album_name ):
    access_token, long_token = get_token(page_no)
    FacebookAdsApi.init(access_token=access_token)

    fields = ["created_time", "description", "id",
              "name", "count", "updated_time", "link",
              "likes.summary(true)", "comments.summary(true)"
              ]
    params = {
            'name': album_name,
            'location': 'Riyadh Region, Saudi Arabia',
            #'privacy': 'everyone',
            #'place': '111953658894021',
            'message':"Yallavip's most fashion flash sale "+ album_name,

                }
    album = Page(page_no).create_album(
                            fields=fields,
                            params=params,
                        )
    #插入到待返回的相册列表中
    if album:

        #保存到数据库中
        obj, created = MyAlbum.objects.update_or_create(album_no=album["id"],
                                                    defaults={'page_no': page_no,
                                                              'created_time': album["created_time"],
                                                              'updated_time': album["updated_time"],

                                                              'name': album["name"],
                                                              'count': album["count"],
                                                              'like_count': album["likes"]["summary"][
                                                                  "total_count"],
                                                              'comment_count': album["comments"]["summary"][
                                                                  "total_count"],
                                                              'link': album["link"],

                                                              }
                                                    )




    return  obj


@shared_task
#根据page规则，更新page的相册
#将page中失效的相册找出来并删掉
#未创建的则创建之
def update_yallavip_album(page_no=None):
    from django.db import connection, transaction

    # 找出所有活跃的page
    pages = MyPage.objects.filter(active=True)
    if page_no:
        pages = pages.filter(page_no=page_no)

    for page in pages:

        print("page is ", page)
        # 找到那些还没添加对应page的规则


        #相册里有，但page规则里没有的，先标记成无效,等page的相册丰富了，再删除
        rules_to_del = YallavipAlbum.objects.filter(page__pk=page.pk).exclude(
            rule__in=PageRule.objects.get(mypage__pk=page.pk).rules.all().distinct())
        rules_to_del.update(active = False)

        #page规则里有，但相册里没有的，要创建
        rules_to_add = PageRule.objects.get( mypage__pk=page.pk).rules.all().exclude(
            id__in = YallavipAlbum.objects.filter(page__pk=page.pk).values("rule__pk")
        ).distinct()
        # 根据规则创建相册，成功后记录到数据库里

        for rule_to_add in rules_to_add:
            new_album = create_album(page.page_no, rule_to_add.name)
            YallavipAlbum.objects.create(
                page=page,
                rule=rule_to_add,
                album=new_album,
                published=True,
                publish_error="",
                published_time=dt.now(),
                active = True
            )

        #相册里有，page里也有的，把状态更新成active
        rules_have = YallavipAlbum.objects.filter(page__pk=page.pk).filter(
            rule__in=PageRule.objects.get(mypage__pk=page.pk
            ).rules.all().distinct())
        rules_have.update(active=True)

        #print("page %s 待删除 %s  待创建 %s 已有 %s "%(page, rules_to_del,rules_to_add,rules_have))
        print("page %s 待删除 %s  待创建 %s 已有 %s " % (page, rules_to_del.count(), rules_to_add.count(), rules_have.count()))




@shared_task
def prepare_yallavip_photoes(page_no=None):
    from django.db import connection, transaction

    # 找出所有活跃的page
    pages = MyPage.objects.filter(active=True)
    if page_no:
        pages = pages.filter(page_no=page_no)

    for page in pages:
        # 遍历page对应的相册
        print("page is ", page)
        albums = YallavipAlbum.objects.filter(page__pk= page.pk, active=True  )
        print("albums is ", albums)
        for album in albums:
            is_sku = False
            print("album is ", album)
            rule = album.rule

            # 拼接相册的筛选产品的条件
            q_cate = Q()
            q_cate.connector = 'OR'
            if rule.cates:
                if rule.cates == "Combo":
                    is_sku = True
                    q_cate.children.append(('comboed', True))
                    q_cate.children.append(('o_sellable__gt', 0))
                else:
                    for cate in rule.cates.split(","):
                        q_cate.children.append(('breadcrumb__contains', cate))

            q_price = Q()
            q_price.connector = 'AND'
            if rule.prices:
                prices = rule.prices.split(",")
                if is_sku:
                    q_price.children.append(('sku_price__gt', prices[0]))
                    q_price.children.append(('sku_price__lte', prices[1]))
                else:
                    q_price.children.append(('shopify_price__gt', prices[0]))
                    q_price.children.append(('shopify_price__lte', prices[1]))

            q_attr = Q()
            q_attr.connector = 'OR'
            if rule.attrs:
                for attr in rule.attrs.split(","):
                    q_attr.children.append(('spu_sku__skuattr__contains', attr))

            con = Q()
            con.add(q_cate, 'AND')
            con.add(q_price, 'AND')
            con.add(q_attr, 'AND')

            # 根据品类找已经上架到shopify 但还未添加到相册的产品


            product_list = []

            if is_sku:
                skus_to_add = Lightin_SKU.objects.filter(con, listed=True, locked=True, imaged=True,o_sellable__gt=0).\
                    exclude(id__in = LightinAlbum.objects.filter(
                                            yallavip_album__pk=album.pk,
                                            lightin_sku__isnull=False).values_list('lightin_sku__id',flat=True)).distinct()

                for sku_to_add in skus_to_add:

                    name = "[" + sku_to_add.SKU + "]"
                    items = sku_to_add.combo_item.all().values_list("lightin_sku__SKU", flat=True)
                    for item in items:
                        name = name + "\n" + item
                    name = name + "\n\nPrice:  " + str(sku_to_add.sku_price) + "SAR"

                    product = LightinAlbum(
                        lightin_sku=sku_to_add,
                        yallavip_album=album,
                        name=name

                    )
                    product_list.append(product)

            else:
                products_to_add = Lightin_SPU.objects.filter(con, published=True,sellable__gt=0).exclude(id__in=
                                                LightinAlbum.objects.filter(
                                                    yallavip_album__pk=album.pk,
                                                    lightin_spu__isnull=False).values_list(
                                                    'lightin_spu__id',
                                                    flat=True)).distinct()

                for product_to_add in products_to_add:
                    obj, created = LightinAlbum.objects.update_or_create(lightin_spu=product_to_add,
                                                                         yallavip_album=album,
                                                                   defaults={'name': product_to_add.title

                                                                             }
                                                                   )


@shared_task
def prepare_yallavip_album_source(page_no=None):
    from django.db.models import Max



    lightinalbums_all = LightinAlbum.objects.filter(sourced=False,source_error="",yallavip_album__isnull = False )
    if page_no:
        lightinalbums_all = lightinalbums_all.filter(yallavip_album__page__page_no=page_no)




    albums_list = lightinalbums_all.values_list('yallavip_album', flat=True).distinct()
    print("albums_list is ", albums_list)

    for album in albums_list:
        lightinalbums = lightinalbums_all.filter(yallavip_album=album)
        print(lightinalbums)

        for lightinalbum in lightinalbums:
            spu = lightinalbum.lightin_spu
            sku = lightinalbum.lightin_sku


            if sku:

                lightinalbum.source_image=sku.image_marked
                lightinalbum.sourced=True


            elif spu:

                # 准备图片
                # 先取第一张，以后考虑根据实际有库存的sku的图片（待优化）
                if spu.images_dict:
                    image = json.loads(spu.images_dict).values()
                    if image and len(image) > 0:
                        a = "/"
                        image_split = list(image)[0].split(a)

                        image_split[4] = '800x800'

                        lightinalbum.source_image = a.join(image_split)
                        lightinalbum.sourced = True

                else:
                    print(album, spu.SPU, "没有图片")
                    lightinalbum.source_error = "没有图片"

            lightinalbum.save()

'''
@shared_task
def prepare_yallavip_album_material(page_no=None, free_delivery=False):
    from django.db.models import Max

   #每次每个相册处理最多100张图片

    lightinalbums_all = LightinAlbum.objects.filter(published=False, publish_error="无", material=False,
                                                    material_error="无",lightin_spu__sellable__gt=0,
                                                    yallavip_album__isnull = False,yallavip_album__active = True  )
    if page_no:
        lightinalbums_all = lightinalbums_all.filter(yallavip_album__page__page_no=page_no)


    albums_list = lightinalbums_all.values_list('yallavip_album', flat=True).distinct()
    print("albums_list is ", albums_list)

    for album in albums_list:

        lightinalbums = lightinalbums_all.filter(yallavip_album=album).order_by("lightin_spu__sellable")
        print(lightinalbums)

        for lightinalbum in lightinalbums:
            prepare_a_album.apply_async((lightinalbum.pk,free_delivery), queue='fb')
'''


@shared_task
def prepare_a_album(lightinalbum_pk):

    ori_lightinalbum = LightinAlbum.objects.get(pk=lightinalbum_pk)

    spu = ori_lightinalbum.lightin_spu
    spu_pk = spu.pk
    print("正在处理spu", spu_pk)
    #updated = update_promote_price(spu, free_delivery)

    lightinalbum = LightinAlbum.objects.get(pk=lightinalbum_pk)


    spu = lightinalbum.lightin_spu
    sku = lightinalbum.lightin_sku

    print("prepare_a_album ",lightinalbum_pk,  spu)

    if sku:
        LightinAlbum.objects.filter(pk=lightinalbum.pk).update(
            image_marked=sku.image_marked,

            # batch_no=batch_no,
            material=True
        )

    elif spu:
        error = ""
        # 准备文字
        # 标题
        title = spu.title
        # 货号
        if title.find(spu.handle) == -1:
            name = title + "  [" + spu.handle + "]"
        else:
            name = title
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

        if spu.free_shipping:
            price1 = int(spu.free_shipping_price)
        else:
            price1 = int(spu.yallavip_price)

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

            image_marked, image_pure_url, image_marked_url = yallavip_mark_image(image, spu.handle, str(price1), str(price2),
                                                                 lightinalbum.yallavip_album.page, spu.free_shipping)
            if not image_marked:
                error = "打水印失败"

        else:
            print(album, spu.SPU, "没有图片")
            error = "没有图片"

        print("打水印",lightinalbum.pk, error)
        if error == "":
            LightinAlbum.objects.filter(pk=lightinalbum.pk).update(
                name=name,
                image_pure=image_pure_url,
                image_marked=image_marked_url,

                # batch_no=batch_no,
                material=True
            )
        else:
            LightinAlbum.objects.filter(pk=lightinalbum.pk).update(
                material_error=error
            )



def cal_price():
    #spus = Lightin_SPU.objects.filter(sellable__gt=0)
    spus = Lightin_SPU.objects.all()
    for spu in spus:
        #采购价的6倍 和销售价的七折，取较大的作为定价
        # 采购价 6倍 =  vendor_supply_price * 3.76 * 0.3 * 6
        #售价七折 = vendor_sale_price *3.76* 0.7
        price_6 = spu.vendor_supply_price * 6.77
        price_7 = spu.vendor_sale_price *2.63

        if price_6 > price_7:
            price = price_6
        else:
            price = price_7

        if price <=5:
            price = 5
        elif price<=20:
            price = 29
        elif price <= 30:
            price = 39
        elif price <= 40:
            price = 49
        elif price <= 50:
            price = 59
        elif price <= 60:
            price = 69
        else:
            price = int(price/10)*10

        spu.yallavip_price = price
        spu.save()


@shared_task
def sync_yallavip_album(page_no=None):
    from django.db.models import Min

    lightinalbums_all = LightinAlbum.objects.filter(
        Q(lightin_spu__sellable__gt=0) | Q(lightin_sku__o_sellable__gt=0),
        published=False, publish_error="无", material=True, yallavip_album__active=True,yallavip_album__page__active=True)

    if page_no:
        lightinalbums_all = lightinalbums_all.filter(
            yallavip_album__page__page_no=page_no)

    print("有%s个相册待更新" % (lightinalbums_all.count()))

    albums = lightinalbums_all.values_list('yallavip_album', "yallavip_album__cate__sellable_gt","yallavip_album__page__page_no").distinct()

    for album in albums:

        access_token, long_token = get_token(album[2])

        if not access_token:
            error = "获取token失败"
            print (error, page_no)
            continue

        '''
        if album[1]> 0:
            sellable_gt = album[1]
        else:
            sellable_gt = 0
            '''
        sellable_gt = 0

        lightinalbums = lightinalbums_all.filter(yallavip_album=album[0], lightin_spu__sellable__gt=sellable_gt).order_by("lightin_spu__sellable").values_list("pk",flat=True)[:100]
        #sync_yallavip_album_batch.apply_async((lightinalbums,), queue='fb')
        print ("准备发布图片到相册 %s,共%s条"%(album[0],lightinalbums.count()))
        sync_yallavip_album_batch(lightinalbums,access_token)


# 把图片发到Facebook相册
@shared_task
def sync_yallavip_album_batch(lightinalbums,access_token):
    from .fb_action import post_yallavip_album


    for lightinalbum in lightinalbums:
        #error, posted = post_yallavip_album(lightinalbum)
        post_yallavip_album.apply_async((lightinalbum,access_token), queue='album')
        # 更新Facebook图片数据库记录
        '''
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
            break
        '''

#按关键词删除相册中的图片
def delete_target_photo(what):
    from facebook_business.api import FacebookAdsApi
    from fb.models import MyPhoto
    from django.db.models import Sum
    import re

    # 在fb的图片里找含what(579815 \ l00 \ c00 之类的，某种特征字符)的图片
    myphotos = LightinAlbum.objects.filter(name__icontains=what, published=True)

    photo_miss = {}
    photos = myphotos.values_list("yallavip_album__page__page_no", "myalbum__page_no","fb_id").distinct()
    for photo in photos:
        if photo[0]:
            page_no = photo[0]
        elif photo[1]:
            page_no = photo[1]
        else:
            continue
        fb_id = photo[1]



        photo_list = photo_miss.get(page_no)
        if not photo_list:
            photo_list = []
        if fb_id not in photo_list:
            photo_list.append(fb_id)

        photo_miss[page_no] = photo_list

    # 选择所有可用的page
    for page_no in photo_miss:


        photo_nos = photo_miss[page_no]
        print("page %s 待删除数量 %s  " % (page_no, len(photo_nos)))
        if photo_nos is None or len(photo_nos) == 0:
            continue

        delete_photos(page_no, photo_nos)


def delete_lost_photo_0409(what):
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


        photo_list = photo_miss.get(page_no)
        if not photo_list:
            photo_list = []
        if fb_id not in photo_list:
            photo_list.append(fb_id)

        photo_miss[page_no] = photo_list

    # 选择所有可用的page
    for page_no in photo_miss:


        photo_nos = photo_miss[page_no]
        print("page %s 待删除数量 %s  " % (page_no, len(photo_nos)))
        if photo_nos is None or len(photo_nos) == 0:
            continue

        delete_photos(page_no, photo_nos)

def delete_album_photo_cate(what):
    from facebook_business.api import FacebookAdsApi
    from fb.models import MyPhoto
    from django.db.models import Sum
    import re

    #在相册里找某个特定的品类，面包屑里的关键字
    myphotos = LightinAlbum.objects.filter(lightin_spu__breadcrumb__icontains=what, material=True,fb_id__in=
                MyPhoto.objects.filter(active=True).values_list("photo_no",flat=True)  )

    photo_miss = {}
    photos = myphotos.values_list("myalbum__page_no", "yallavip_album__page__page_no", "fb_id").distinct()
    for photo in photos:
        if photo[0]:
            page_no = photo[0]
        elif photo[1]:
            page_no = photo[1]
        else:
            print("no page")
            continue

        fb_id = photo[2]

        photo_list = photo_miss.get(page_no)
        if not photo_list:
            photo_list = []
        if fb_id not in photo_list:
            photo_list.append(fb_id)

        photo_miss[page_no] = photo_list

    # 选择所有可用的page
    for page_no in photo_miss:
        if not page_no:
            print("page_no 为空")
            continue

        photo_nos = photo_miss[page_no]
        print("page %s 待删除数量 %s  " % (page_no, len(photo_nos)))
        if photo_nos is None or len(photo_nos) == 0:
            continue

        delete_photos(page_no, photo_nos)

def get_token_status():
    from facebook_business.api import FacebookAdsApi
    from facebook_business.adobjects.user import User

    tokens = Token.objects.all()


    for token in tokens:
        FacebookAdsApi.init(access_token=token.long_token)
        fields = [
        ]
        params = {
        }
        user = None
        try:
            user = User(token.user_no).api_get(
                fields=fields,
                params=params,
            )
            token.user_name = user.get("name")
            token.active = True
            token.info = ""
        except Exception as e:
            #print(e,json.loads(e))
            print(e)

            token.active = False
            token.page_no = ""
            token.info = e.api_error_message()

        token.save()

def check_ad_sellable():
    ads = YallavipAd.objects.filter(active=True)

    for ad in ads:
        spus = Lightin_SPU.objects.filter(handle__in=ad.spus_name.split(','), sellable__gt=0)
        print(ad.spus_name, spus.count())

# 更新相册对应的主页外键
# update fb_myalbum a , fb_mypage p set a.mypage_id = p.id where p.page_no = a.page_no
'''
from django.db import connection, transaction

    sql = "UPDATE prs_lightin_spu SET  quantity =(SELECT sum(k.quantity) FROM prs_lightin_sku k WHERE k.SPU = prs_lightin_spu.SPU and prs_lightin_spu.published = true)"

    cursor = connection.cursor()
    cursor.execute(sql)
    transaction.commit()
'''

#根据库存，动态调整shopify的发布状态
def change_products_publish_status():

    #将 ligthin_spu 里有库存,但shopify没上架 的上架
    to_publish_products = Lightin_SPU.objects.filter(sellable__gt=0, published=True, shopify_published=False)

    for to_publish_product in to_publish_products:

        info, published = change_product_publish_status(to_publish_product.product_no, published=True)
        if published:
            to_publish_product.shopify_published =True
            to_publish_product.save()



    #将 ligthin_spu 里没库存的但shopify在上架 的下架
    to_unpublish_products = Lightin_SPU.objects.filter(sellable__lte=0, published=True,shopify_published=True)

    for to_unpublish_product in to_unpublish_products:

        info, published = change_product_publish_status(to_unpublish_product.product_no, published=False)
        if published:
            to_unpublish_product.shopify_published = False
            to_unpublish_product.save()


#将在shopify里已经发布 但不在ligthin_spu 里的下架
#这个可能是一次性动作
def unpubulish_shopify():
    to_unpublish_products = ShopifyProduct.objects.filter(published_at__isnull=False).exclude(
        product_no__in=Lightin_SPU.objects.values_list("product_no",flat=True)
    )
    for to_unpublish_product in to_unpublish_products:

        info, published = change_product_publish_status(to_unpublish_product.product_no, published=False)
        if published:
            to_unpublish_product.published_at = None
            to_unpublish_product.save()








def change_product_publish_status(product_no, published):
    from shop.models import Shop, ShopifyProduct
    from prs.shop_action import post_product_main, update_or_create_product
    from .models import AliProduct

    dest_shop = "yallasale-com"
    location_id = "11796512810"
    shop_obj = Shop.objects.get(shop_name=dest_shop)

    shop_url = "https://%s:%s@%s.myshopify.com" % (shop_obj.apikey, shop_obj.password, shop_obj.shop_name)


    params = {
        "product":{
            "id": product_no,
            "published": published,
        }


    }
    headers = {
        "Content-Type": "application/json",
        "charset": "utf-8",

    }
    # 初始化SDK
    url = shop_url + "/admin/products/%s.json"%(product_no)

    print("开始更新发布状态")
    print(url, json.dumps(params))

    r = requests.put(url, headers=headers, data=json.dumps(params))
    if r.status_code == 200:
        products = ShopifyProduct.objects.filter(product_no=product_no)
        if published:
            products.update(published_at=dt.now())
        else:
            products.update(published_at=None)
        return "更新发布状态成功", True
    else:
        print(r.text)
        return "更新发布状态失败", False

#同步myad和yallavipad
def sync_ads():
    ads = MyAd.objects.filter(active=True).values_list("ad_no",flat=True)

    YallavipAd.objects.update(ad_status="",engagement_ad_status="", message_ad_status="")
    YallavipAd.objects.filter(ad_id__in = ads).update(ad_status="active")
    YallavipAd.objects.filter(engagement_ad_id__in=ads).update(engagement_ad_status="active")
    YallavipAd.objects.filter(message_ad_id__in=ads).update(message_ad_status="active")








#根据面包屑更新品类表
#从spu表取出所有distinct面包屑
#遍历所有面包屑
#分解成3级品类
#把品类更新到数据库
def breadcrumb_cates():
    breadcrumbs = Lightin_SPU.objects.values_list("breadcrumb",flat=True).distinct()
    catelist = []

    for breadcrumb in breadcrumbs:
        if not breadcrumb:
            continue

        #tag =  breadcrumb.replace("[","").replace("]","").split(',')
        tag = breadcrumb.split(',')
        cates = json.loads(breadcrumb)
        print(tag)

        if len(tag)>0:
            cate_1 = ("", cates[0].strip() , 1, tag[0].strip())
            if cate_1 not in catelist:
                catelist.append(cate_1)
        if len(tag) > 1:
            cate_2 = (cates[0].strip(), cates[1].strip() , 2, tag[0].strip() + ','+ tag[1].strip())
            if cate_2 not in catelist:
                catelist.append(cate_2)

        if len(tag) > 2:
            cate_3 = (cates[1].strip(), cates[2].strip() , 3, tag[0].strip() + ','+ tag[1].strip()+','+ tag[2].strip())
            if cate_3 not in catelist:
                catelist.append(cate_3)

    for cate in catelist:
        obj, created = MyCategory.objects.update_or_create(
                                                        tags = cate[3],
                                                       defaults={
                                                           'super_name':cate[0],
                                                           'name':cate[1],
                                                           'level': cate[2],
                                                                 }
                                                       )
def clean_breadcrumb():
    spus = Lightin_SPU.objects.all()


    for spu in spus:


        if not spu.breadcrumb:
            continue

        tags = spu.breadcrumb.split(",")
        new_tags = []
        for tag in tags:
            new_tag = tag.strip()
            new_tags.append(new_tag)
        new_tags = ",".join(new_tags)
        print (new_tags)
        spu.breadcrumb = new_tags

        spu.save()




def create_collcetions():
    from prs.shop_action import  create_smart_collection

    cates = MyCategory.objects.filter(active=True, published=False)

    for cate in cates:
        info,created = create_smart_collection(cate.name, cate.tags)
        if created:
            cate.collcetion_no = info
            cate.published = True
        else:
            cate.publishe_error = info[:499]

        cate.save()
'''
def delete_collections():
    from prs.shop_action import  delete_smart_collection
    size_cates = MyCategorySize.objects.filter(active=True, published=True)
    for cate in size_cates:
        info,deleted = delete_smart_collection(cate.collcetion_no)
        if deleted:
            cate.collcetion_no = ""
            cate.published = False

        else:
            cate.publishe_error = info[:499]

        cate.save()
'''

def create_size_collcetions():
    from prs.shop_action import  create_smart_collection

    size_cates = MyCategorySize.objects.filter(active=True, published=False,collcetion_no="")

    for size_cate in size_cates:
        cate = size_cate.cate
        if not cate.name or cate.name=="":
            print (cate, "没有name")
            continue

        name = cate.name + ' / ' + size_cate.size
        tags = cate.tags
        size = size_cate.size

        info,created = create_smart_collection(name, tags,size)

        if created:

            size_cate.collcetion_no = info
            size_cate.published = True
        else:
            size_cate.publish_error = info[:499]

        size_cate.save()


def create_size_abs():


    size_counts =  MyCategorySize.objects.values("size").annotate(count=Count(id)).order_by("-count")

    for size_count in size_counts:
        obj, created = SizeAbs.objects.update_or_create(size=size_count["size"],
                                                       defaults={
                                                           "catesize_count" :  size_count["count"],
                                                                 }
                                                       )

def create_abs_label():


    abs_counts =  SizeAbs.objects.values("size_abs").annotate(count=Count(id)).order_by("-count")

    for abs_count in abs_counts:
        obj, created = SizeAbsLabel.objects.update_or_create(size_abs=abs_count["size_abs"],
                                                       defaults={
                                                           "size_count" :  abs_count["count"],
                                                                 }
                                                       )


#使用之前要先把updated置为False,才能把有错误的挑出来重做

def update_shopify_tags():
    from prs.shop_action import  adjust_shopify_tags
    spus = Lightin_SPU.objects.filter(published=True, sellable__gt=0 ,updated=False).order_by("-sellable","-shopify_price")

    for spu in spus:
        info, updated = adjust_shopify_tags(spu.product_no, spu.breadcrumb)
        if updated:
            spu.updated = True
        else:
            spu.update_error = info[:499]

        spu.save()




def update_variant_title():
    #遍历所有的handle用l开头的variant,

    rows = my_custom_sql(mysql)

    for row in rows:
        print ("更新变体价格： ",row[0],row[2])

        info, adjusted = adjust_shopify_price(row)
        vs = ShopifyVariant.objects.filter(variant_no=row[1])
        if adjusted:
            vs.update(price=row[2],inventory_policy = "deny",update_error="")
        else:
            vs.update(update_error = info)


def adjust_shopify_price(row):
    from shop.models import Shop, ShopifyProduct
    from prs.shop_action import post_product_main, update_or_create_product
    from .models import AliProduct

    dest_shop = "yallasale-com"
    location_id = "11796512810"
    shop_obj = Shop.objects.get(shop_name=dest_shop)

    shop_url = "https://%s:%s@%s.myshopify.com" % (shop_obj.apikey, shop_obj.password, shop_obj.shop_name)


    params = {
        "variant": {
                "id": row[1],
                "inventory_policy": "deny",
                "price": row[2]
              }
    }
    headers = {
        "Content-Type": "application/json",
        "charset": "utf-8",

    }
    # 初始化SDK
    url = shop_url + "/admin/variants/%s.json"%(row[1])

    print("开始更新变体")
    print(url, json.dumps(params))

    r = requests.put(url, headers=headers, data=json.dumps(params))
    if r.status_code == 200:
        return "更新变体成功", True
    else:
        print("更新变体失败",r,  r.text)
        return "更新变体失败", False


def cal_cate_size():
    from django.db.models import Count

    cates = MyCategory.objects.filter(active=True)

    for cate in cates:
        variants = ShopifyVariant.objects.filter(sku__in=
                                                 Lightin_SKU.objects.filter(o_sellable__gt=0,
                                                                            lightin_spu__breadcrumb__contains=cate.tags,
                                                                            skuattr__icontains="size")
                                                 .values_list("SKU", flat=True))
        if variants:
            sizes = variants.values("option2").annotate(sku_quantity = Count(id))
            for size in sizes:
                obj, created = MyCategorySize.objects.update_or_create(cate=cate,
                                                                       size = size.get("option2"),
                                                               defaults={'sku_quantity':size.get("sku_quantity"),

                                                                         }
                                                               )

def test_for_post():
    from facebook_business.adobjects.adaccount import AdAccount
    # 调试用的参数
    adaccount_no = "act_1903121643086425"
    adset_no = "23843327820590510"
    page_id = "546407779047102"
    message = "This is only a test"
    image_url = "https://li2.rightinthebox.com/images/384x500/201703/ebcwqx1488880984387.jpg"


    '''
    access_token, long_token = get_token(page_id)
    print (access_token, long_token, page_id)
    if not long_token:
        return
    '''

    access_token = "EAAcGAyHVbOEBAFBBe5hTsB9vXLrar6suadomIiRFlF6Bbg701tj6ZBQAcvNShNQWnAPjr04vOtgyfZAWMUVoYVoKQykdjw5VGragjAppHB0vxsa5J9Ky5vaLgWMijXWYYZAEAx5Ki4zuZAiz23rZBPhHKBAe7we4tB5dpRUiIlcsFICCLX2ZBHyg6zj2ObpZBjQNAIu5N9MPjRFuhdZCZCpSL"
    adobjects = FacebookAdsApi.init(access_token=access_token, debug=True)


    #创建page photo
    fields = [
    ]
    params = {
        'url': image_url,
        'published': 'false',
    }
    photo_to_be_post = Page(page_id).create_photo(
        fields=fields,
        params=params,
    )
    photo_to_be_post_id = photo_to_be_post.get_id()

    #创建post
    fields = [
            'object_id',
        ]
    
    params = {
        'message': message,
        #'attached_media': [{'media_fbid': photo_to_be_post_id}],
        'attached_media': [{'media_fbid': photo_to_be_post_id}],
        "call_to_action": {"type": "MESSAGE_PAGE",
                            "value": {"app_destination": "MESSENGER"}},
    }
    '''
    #创建Link Page Post with Call to Action
    fields = [
        'object_id',
    ]
    params = {
        "call_to_action": {"type": "MESSAGE_PAGE"},
                           #"value": {"app_destination": "MESSENGER"}},
        # "image_hash": adimagehash,
        "picture": image_url,
        "link": "http://www.yallavip.com",

        "message": message,
        "name": "Yallavip",
        "description": "Online Flash Sale Everyhour",
        "use_flexible_image_aspect_ratio": True,

    }
    '''
    feed_post = Page(page_id).create_feed(
        fields=fields,
        params=params,
    )
    print (feed_post)


    object_story_id = feed_post.get_id()

    #在post的基础上创建广告
    adobjects = FacebookAdsApi.init(access_token=ad_tokens, debug=True)
    #创建creative

    fields = [
    ]
    params = {
        'name': 'Sample Promoted Post',
        'object_story_id': object_story_id,

    }
    adCreativeID = AdAccount(adaccount_no).create_ad_creative(
        fields=fields,
        params=params,
    )

    print("adCreativeID is ", adCreativeID)


    creative_id = adCreativeID["id"]
    #creative_id = "23843325933030510"
    adobjects = FacebookAdsApi.init(access_token=ad_tokens, debug=True)
    #创建广告
    fields = [
    ]
    params = {
        'name': 'My Ad ' ,
        'adset_id': adset_no,
        'creative': {'creative_id': creative_id },
        'status': 'PAUSED',
    }

    new_ad = AdAccount(adaccount_no).create_ad(
        fields=fields,
        params=params,
    )

    print("new ad is ", new_ad)


#自动准备广告图
def auto_prepare_image():
    #选择需要推广的page
    pages = MyPage.objects.filter(is_published=True, active=True, promotable=True)

    #遍历每个page
    for page in pages:
        #准备图片
        prepare_promote.apply_async((page.page_no,1), queue='post')


    return



#




    return


#自动生成post
@shared_task
def auto_post_longads():
    #选择需要推广的page
    pages = MyPage.objects.filter(is_published=True, active=True, promotable=True)

    #遍历每个page
    for page in pages:
        #从符合条件的相册里选一个相册,    #发post
        print("正在处理page", page)
        page_no = page.page_no
        page_post(page_no, 10,keyword=None,long_ad=True)





    return


#自动生成互动ad
@shared_task
def engagement_ads():
    #选择需要推广的page
    pages = MyPage.objects.filter(is_published=True, active=True, promotable=True)

    #遍历每个page
    for page in pages:
        #post_engagement_ads(page.page_no, 1)
        post_ads(page.page_no, "engagement",20)



    return

@shared_task
def engagement_ads_long():
    #选择需要推广的page
    pages = MyPage.objects.filter(is_published=True, active=True, promotable=True)

    #遍历每个page
    for page in pages:
        #post_engagement_ads(page.page_no, 1)
        page_no = page.page_no
        post_ads(page_no, "engagement",20,long_ad=True)



    return

@shared_task
def message_ads_long():
    #选择需要推广的page
    pages = MyPage.objects.filter(is_published=True, active=True, promotable=True)

    #遍历每个page
    for page in pages:
        #post_engagement_ads(page.page_no, 1)
        post_ads(page.page_no, "message",10,long_ad=True)



    return


# 自动生成消息ad
@shared_task
def message_ads():
    from fb.tasks import  update_feed

    # 选择需要推广的page

    pages = MyPage.objects.filter(is_published=True, active=True, promotable=True)

    # 遍历每个page
    for page in pages:
        #先更新feed信息，然后从活跃度较高的post开始打消息广告
        #update_feed(page.page_no)
        # 从符合条件的互动广告里，选一个发消息广告
        #post_message_ads(page.page_no, 1)
        post_ads(page.page_no, "message",10)


    return




#先post，然后基于post发广告
#每次每个cate发一张，尝试多样性或者专业性哪个更好
#这只适合互动型广告
@shared_task
def page_post(page_no, to_create_count,keyword=None,long_ad=False):
    import time
    # 取page对应的主推品类
    cates = PagePromoteCate.objects.filter(mypage__page_no=page_no).values_list("promote_cate__tags", flat=True)
    if cates:
        cates = list(cates)
    else:
        return


    access_token, long_token = get_token(page_no)
    print (access_token, long_token, page_no)
    if not long_token:
        return
    adobjects = FacebookAdsApi.init(access_token=access_token, debug=True)

    for cate in cates:
        if long_ad:
            ads = YallavipAd.objects.filter(active=True, published=False, page_no=page_no,cate=cate,
                                            long_ad=long_ad)
        else:
            ads = YallavipAd.objects.filter(active=True, published=False,yallavip_album__page__page_no=page_no, cate=cate,long_ad=long_ad )
        if keyword:
            ads = ads.filter(yallavip_album__rule__name__icontains=keyword)

        #如果数量不够，且不是长期广告就创建
        if ads.count() < to_create_count and not long_ad:
            prepare_promote(page_no, to_create_count - ads.count(), keyword)

        i=1
        for ad in ads:
            if i>to_create_count:
                break
            else:
                i += 1
            spus_count = len(ad.spus_name.split(","))
            if spus_count == 4:
                try:
                    # 创建page photo
                    fields = [
                    ]
                    params = {
                        'url': ad.image_marked_url,
                        'published': 'false',
                    }
                    photo_to_be_post = Page(page_no).create_photo(
                        fields=fields,
                        params=params,
                    )
                    photo_to_be_post_id = photo_to_be_post.get_id()

                    # 创建post
                    fields = [
                        'object_id',
                    ]

                    params = {
                        'message': ad.message,
                        # 'attached_media': [{'media_fbid': photo_to_be_post_id}],
                        'attached_media': [{'media_fbid': photo_to_be_post_id}],
                        "call_to_action": {"type": "MESSAGE_PAGE",
                                           "value": {"app_destination": "MESSENGER"}},
                    }

                    feed_post = Page(page_no).create_feed(
                        fields=fields,
                        params=params,
                    )
                    print (feed_post)

                    #object_story_id = feed_post.get_id()
                    ad.object_story_id = feed_post.get_id()
                    ad.published = True

                except Exception as e:
                    print(e)
                    error = e.api_error_message()
                    ad.publish_error = error
            if spus_count == 2:
                info, posted = link_page_post(page_no, access_token, ad)
                if posted:
                    ad.object_story_id = info
                    ad.published = True
                else:
                    ad.publish_error = info

                pass

            ad.save()
@shared_task
def page_post_v2(page_no, to_create_count):
    import time

    # 取page对应的待推ads
    ads_all, cates = get_promote_ads(page_no)
    if not ads_all:
        return

    ads_all = ads_all.filter(published=False)

    access_token, long_token = get_token(page_no)
    print (access_token, long_token, page_no)
    if not long_token:
        return
    adobjects = FacebookAdsApi.init(access_token=access_token, debug=True)

    for cate in cates:

        ads = ads_all.filter(cate=cate)
        print(cate,"有 %s 条post待发布"%ads.count())

        i=1
        for ad in ads:
            if i>to_create_count:
                break
            else:
                i += 1
            spus_count = len(ad.spus_name.split(","))

            #if spus_count == 2:
            info, posted = link_page_post(page_no, access_token, ad)
            if posted:
                ad.object_story_id = info
                ad.published = True
            else:
                ad.publish_error = info
            '''
            else:
                info, posted = photo_page_post(page_no, access_token, ad)
                if posted:
                    ad.object_story_id = info
                    ad.published = True
                else:
                    ad.publish_error = info
            '''
            ad.save()

def get_serial():
    #根据日期生成序列号，目的是为了便于跟踪每天的表现
    import datetime
    today = datetime.date.today()
    firstday = datetime.date(today.year, 1, 1)
    days = (today - firstday).days
    return str(days % 3 + 1)




@shared_task
def post_ads(page_no, ad_type, to_create_count=1,keyword=None, long_ad=False):
    import time
    from prs.fb_action import  choose_ad_set

    from django.db.models import Q

    if long_ad:
        serial = "0"
    else:
        serial = get_serial()


    #每天的广告放进同一个组，保持广告的持续性，先设成三组，看看效果
    #库存深的单独放一个组
    adset_no = choose_ad_set(page_no, ad_type,serial)
    if not adset_no:
        print("没有adset")
        return False

    adaccount_no = "act_1903121643086425"


    if ad_type == "engagement":
        #ads = YallavipAd.objects.filter(~Q(object_story_id="" ),  object_story_id__isnull = False,active=True, published=True,engagement_aded=False, yallavip_album__page__page_no=page_no )
        ads = YallavipAd.objects.filter(active=True, published=True, engagement_aded=False, long_ad=long_ad).order_by("-fb_feed__like_count")
    elif ad_type == "message":
        ads = YallavipAd.objects.filter(active=True, engagement_aded= True, message_aded=False, long_ad=long_ad).order_by("-fb_feed__like_count")
    else:
        return  False

    if long_ad:
        ads = ads.filter(page_no=page_no)
    else:
        ads= ads.filter(yallavip_album__page__page_no=page_no)



    if keyword:
        ads = ads.filter(yallavip_album__rule__name__icontains=keyword)

    if long_ad:
        ads = ads.filter(long_ad=True)

    adobjects = FacebookAdsApi.init(access_token=ad_tokens, debug=True)
    i=1
    for ad in ads:
        if i>to_create_count:
            break

        i += 1


        fb_ad = post_ad(page_no,adaccount_no, adset_no, serial, ad)
        print("new ad is ", fb_ad)
        if fb_ad:
            if ad_type == "engagement":
                ad.engagement_ad_id = fb_ad.get("id")

                ad.engagement_aded = True
                ad.engagement_ad_published_time = dt.now()
            elif ad_type == "message":
                ad.message_ad_id = fb_ad.get("id")
                ad.message_aded = True
                ad.message_ad_published_time = dt.now()


            ad.save()
            time.sleep(30)


@shared_task
def post_ads_v2(page_no, ad_type, to_create_count=1, keyword=None):
    import time
    from prs.fb_action import choose_ad_set

    from django.db.models import Q

    # 取page对应的待推ads
    ads_all , cates = get_promote_ads(page_no)
    if not ads_all:
        return
    ads_all = ads_all.filter(published=True)


    serial = get_serial()

    # 每天的广告放进同一个组，保持广告的持续性，先设成三组，看看效果
    # 库存深的单独放一个组
    adset_no = choose_ad_set(page_no, ad_type, serial)
    if not adset_no:
        print("没有adset")
        return False

    adaccount_no = "act_1903121643086425"

    if keyword:
        ads_all = ads_all.filter(yallavip_album__rule__name__icontains=keyword)

    if ad_type == "engagement":
        # ads = YallavipAd.objects.filter(~Q(object_story_id="" ),  object_story_id__isnull = False,active=True, published=True,engagement_aded=False, yallavip_album__page__page_no=page_no )
        ads_all = ads_all.filter( engagement_aded=False).order_by("-fb_feed__like_count")
    elif ad_type == "message":
        #ads_all = ads_all.filter( engagement_aded=True, message_aded=False).order_by("-fb_feed__like_count")
        ads_all = ads_all.filter( message_aded=False).order_by("-fb_feed__like_count")
    else:
        return False

    if keyword:
        ads_all = ads_all.filter(yallavip_album__rule__name__icontains=keyword)

    adobjects = FacebookAdsApi.init(access_token=ad_tokens, debug=True)
    for cate in cates:

        ads = ads_all.filter(cate=cate)
        print("品类 %s 有%s条 %s 广告可发布"%(cate, ads.count(), ad_type))
        i = 1
        for ad in ads:
            if i > to_create_count:
                break

            i += 1

            fb_ad = post_ad(page_no, adaccount_no, adset_no, serial, ad)
            print("new ad is ", fb_ad)
            if fb_ad:
                if ad_type == "engagement":
                    ad.engagement_ad_id = fb_ad.get("id")

                    ad.engagement_aded = True
                    ad.engagement_ad_published_time = dt.now()
                elif ad_type == "message":
                    ad.message_ad_id = fb_ad.get("id")
                    ad.message_aded = True
                    ad.message_ad_published_time = dt.now()

            else:
                ad.active=False

            ad.save()
            time.sleep(60)


def post_ad(page_no,adaccount_no, adset_no, serial, ad):
    from facebook_business.adobjects.adaccount import AdAccount

    name =    serial + "_"+ page_no+"_"+ad.spus_name

    try:

        # 在post的基础上创建广告

        if ad.creative_id:
            print("已经有creative，不用创建了")
            creative_id = ad.creative_id
        else:

            # 创建creative

            fields = [
            ]
            params = {
                'name':name,
                'object_story_id': ad.object_story_id,

            }
            adCreativeID = AdAccount(adaccount_no).create_ad_creative(
                fields=fields,
                params=params,
            )

            print("adCreativeID is ", adCreativeID)

            creative_id = adCreativeID["id"]

            ad.creative_id = creative_id
            ad.save()

        # 创建广告
        fields = [
        ]
        params = {
            'name': name,
            'adset_id': adset_no,
            'creative': {'creative_id': creative_id},
            #'status': 'PAUSED',
            'status': 'ACTIVE',
        }

        fb_ad = AdAccount(adaccount_no).create_ad(
            fields=fields,
            params=params,
        )
        return  fb_ad
    except Exception as e:
        print(e)
        error = e.api_error_message()
        ad.publish_error = error
        ad.save()
        return None




@shared_task
def post_engagement_ads(page_no, to_create_count=1,keyword=None):
    import time
    from prs.fb_action import  choose_ad_set

    from django.db.models import Q

    serial = get_serial()
    adset_no = choose_ad_set(page_no, 'engagement')


    adaccount_no = "act_1903121643086425"


    #adset_no = "23843303803340510"

    ads = YallavipAd.objects.filter(~Q(object_story_id="" ),  object_story_id__isnull = False,active=True, published=True,engagement_aded=False, yallavip_album__page__page_no=page_no )

    if keyword:
        ads = ads.filter(yallavip_album__rule__name__icontains=keyword)

    #如果数量不够，就创建
    if ads.count() < to_create_count:
        page_post(page_no, to_create_count - ads.count(), keyword)

    adobjects = FacebookAdsApi.init(access_token=ad_tokens, debug=True)
    i=1
    for ad in ads:
        if i>to_create_count:
            break

        i += 1
        post_engagement_ad(page_no,adaccount_no, adset_no, serial, ad)

def post_engagement_ad(page_no,adaccount_no, adset_no, serial, ad):
    from facebook_business.adobjects.adaccount import AdAccount
    name =    serial + "_"+ page_no+"_"+ad.spus_name

    if not adset_no:
        print("没有adset")
        return False

    try:

        # 在post的基础上创建广告
        # 创建creative

        fields = [
        ]
        params = {
            'name':name,
            'object_story_id': ad.object_story_id,

        }
        adCreativeID = AdAccount(adaccount_no).create_ad_creative(
            fields=fields,
            params=params,
        )

        print("adCreativeID is ", adCreativeID)

        creative_id = adCreativeID["id"]

        # 创建广告
        fields = [
        ]
        params = {
            'name': name,
            'adset_id': adset_no,
            'creative': {'creative_id': creative_id},
            #'status': 'PAUSED',ACTIVE
            'status': 'ACTIVE',
        }

        fb_ad = AdAccount(adaccount_no).create_ad(
            fields=fields,
            params=params,
        )
    except Exception as e:
        print(e)
        error = e.api_error_message()
        ad.publish_error = error
        ad.save()
        return

    print("new ad is ", fb_ad)
    ad.engagement_ad_id = fb_ad.get("id")

    ad.engagement_aded = True
    ad.engagement_ad_published_time = dt.now()
    ad.save()





def post_message_ads(page_no, to_create_count=1,keyword=None):
    import time
    from prs.fb_action import  choose_ad_set


    serial = get_serial()


    adaccount_no = "act_1903121643086425"
    adset_no = choose_ad_set(page_no, 'message' )

    ads = YallavipAd.objects.filter(active=True, engagement_aded= True, message_aded=False, yallavip_album__page__page_no=page_no,fb_feed__isnull=False).order_by("-fb_feed__like_count")
        #values("spus_name","fb_feed__like_count")
    if keyword:
        ads = ads.filter(yallavip_album__rule__name__icontains=keyword)

    adobjects = FacebookAdsApi.init(access_token=ad_tokens, debug=True)
    i=1
    for ad in ads:
        if i>to_create_count:
            break

        i += 1
        post_message_ad(page_no, adaccount_no, adset_no, serial, ad)

def post_message_ad(page_no, adaccount_no, adset_no, serial, ad):
    from facebook_business.adobjects.adaccount import AdAccount

    name = serial + "_" + page_no + "_" + ad.spus_name

    if not adset_no:
        print("没有adset")
        return False

    try:

        fields = [
        ]

        # link ad
        params = {
            'name': name,
            'object_story_spec': {'page_id': page_no,
                                  'link_data': {"call_to_action": {"type": "MESSAGE_PAGE",
                                                                   "value": {"app_destination": "MESSENGER"}},

                                                "picture": ad.image_marked_url,
                                                "link": "https://facebook.com/%s" % (page_no),

                                                "message": ad.message,
                                                "name": "Yallavip.com",
                                                "description": "Online Flash Sale Everyhour",
                                                "use_flexible_image_aspect_ratio": True, }},
        }
        adCreative = AdAccount(adaccount_no).create_ad_creative(
            fields=fields,
            params=params,
        )

        print("adCreative is ", adCreative)

        fields = [
        ]
        params = {
            'name': name,
            'adset_id': adset_no,
            'creative': {'creative_id': adCreative["id"]},
            #'status': 'PAUSED',
            'status': 'ACTIVE',
            # "access_token": my_access_token,
        }

        fb_ad = AdAccount(adaccount_no).create_ad(
            fields=fields,
            params=params,
        )
    except Exception as e:
        print(e)
        error = e.api_error_message()
        ad.publish_error = error
        ad.save()
        return

    print("new ad is ", fb_ad)
    ad.message_ad_id = fb_ad.get("id")
    ad.message_aded = True
    ad.message_ad_published_time = dt.now()
    ad.save()

def split_conversation_links():
    verifies = Verify.objects.filter(business_id__isnull=True)
    for verify in verifies:
        split_conversation_link(verify)

def split_conversation_link(verify):
    if verify.conversation_link:

        contents = re.split("\?|&", verify.conversation_link)
        id_dict = {}
        for content in contents:
            if content.find("=") >-1:
                items = content.split("=")
                id_dict[items[0]] =items[1]
        verify.business_id = id_dict.get("business_id")
        verify.mailbox_id = id_dict.get("mailbox_id")
        verify.selected_item_id = id_dict.get("selected_item_id")
        verify.save()

#计算某个spu的促销价，修改sku，spu的促销价
def update_promote_price(spu, free_delivery=False):


    if free_delivery:
        fee = 25
        spu.free_shipping = True
    else:
        fee = 0
        spu.free_shipping = False

    #供货价的5倍 0.25*3.75*5
    multiple_price = spu.vendor_supply_price * 5
    #供应商售价的6折 3.75*0.6
    discount_price = spu.vendor_sale_price * 2.25
    if multiple_price < discount_price:
        promote_price = round(discount_price)
    else:
        promote_price = round(multiple_price)

    promote_price += fee

    if promote_price != spu.yallavip_price :
        #修改spu价格
        spu.yallavip_price = promote_price

        spu.promoted = True
        spu.save()

        #修改spu对应的skus的价格
        spu.spu_sku.update(sku_price = promote_price )

        return  True
    else:
        return False

#计算某个spu的促销价，修改sku，spu的促销价
def update_free_shipping_price(spu, free_shipping=True):


    if free_shipping:
        fee = 25
        spu.free_shipping = True
    else:
        fee = 0
        spu.free_shipping = False

    #供货价的5倍 0.25*3.75*5
    multiple_price = spu.vendor_supply_price * 5
    #供应商售价的6折 3.75*0.6
    discount_price = spu.vendor_sale_price * 2.25
    if multiple_price < discount_price:
        promote_price = round(discount_price)
    else:
        promote_price = round(multiple_price)

    promote_price += fee

    if free_shipping:

        #修改spu价格
        spu.free_shipping_price = promote_price
        spu.free_shipping = True
        spu.save()
        #修改spu对应的skus的价格
        spu.spu_sku.update(free_shipping_price = promote_price )




#删除spu在所有相册中的图片
def clear_album(spu_pk):


    albums = LightinAlbum.objects.filter(lightin_spu__pk=spu_pk, published=True, deleted=False)
    if albums:
        albums.update(todelete=True)



#为促销做准备商品
@task
def prepare_promote(page_no,to_create_count, keyword=None):

    import random

    from django.db.models import Count


    # 取库存大、单价高、已经发布到相册 且还未打广告的商品
    lightinalbums_all = LightinAlbum.objects.filter(yallavip_album__isnull=False, yallavip_album__page__page_no=page_no,
                                            lightin_spu__sellable__gt=0, lightin_spu__SPU__istartswith = "s",
                                            lightin_spu__vendor_supply_price__gt=6,#lightin_spu__vendor_supply_price__lte=15,
                                            lightin_spu__aded=False,
                                            published=True)
    if keyword:
        lightinalbums_all = lightinalbums_all.filter(yallavip_album__rule__name__icontains=keyword)


    # 从符合条件的相册里随机抽取一个相册生成广告图片，如果有尺码，就把尺码加在图片下面
    yallavip_albums = lightinalbums_all.values("yallavip_album").annotate(spu_count = Count(id)).filter(spu_count__gte=2)



    if yallavip_albums:
        i = 0
        while i < to_create_count:

            yallavip_album = random.choice(yallavip_albums)
            yallavip_album_pk = yallavip_album.get("yallavip_album")

            prepare_promote_image_album_v2(yallavip_album_pk , lightinalbums_all)

            i += 1
    else:
        print("没有符合条件的相册了", page_no)


#为长期广告准备商品
@task
def prepare_long_ad(page_no):

    import random

    from django.db.models import Count

    #取page对应的主推品类
    cates =  PagePromoteCate.objects.filter(mypage__page_no = page_no).values_list("promote_cate__tags", flat=True)
    if cates:
        cates = list(cates)
    else:
        return


    # 取库存大、单价高、已经发布到相册 且还未打广告的商品
    spus_all = Lightin_SPU.objects.filter( vendor="lightin",longaded=False)



    #把主推品类的所有适合的产品都拿出来打广告

    for cate in cates:

        cate_spus = spus_all.filter(breadcrumb__icontains = cate, sellable__gt=3)
        #每次最多20个
        if cate_spus.count()>20:
            count = 10
        else:
            count = int(cate_spus.count()/2)
        print ("一共有%s个"%(count))

        for i in range(count):
            print("当前处理 ",i, cate_spus)
            spu_pks =  [cate_spus[0].pk, cate_spus[1].pk]
            prepare_promote_image_album_v3(cate, page_no ,spu_pks)




def prepare_promote_image_album_v2(yallavip_album_pk, lightinalbums_all):
    from prs.fb_action import combo_ad_image_v2
    ori_lightinalbums = lightinalbums_all.filter(yallavip_album__pk=yallavip_album_pk).order_by(
        "lightin_spu__sellable")[:4]

    yallavip_album_instance = YallavipAlbum.objects.get(pk=yallavip_album_pk)
    print ("正在处理相册 ", yallavip_album_instance.album.name)

    spu_pks = ori_lightinalbums.values_list("lightin_spu__pk", flat=True)
    album_pks = []

    print("待处理的相册图片pk",album_pks )


    #计算spu的促销价格，如果是价格有变动，删除原有fb图片，并重新生成新的图片
    for lightinalbum in ori_lightinalbums:
        album_pks.append(lightinalbum.pk)


        spu = lightinalbum.lightin_spu
        spu_pk = spu.pk
        print("正在处理spu", spu_pk )
        #updated = update_promote_price(spu)
        #only for debug 0430
        #updated=True
        if updated:
            clear_album(spu_pk)
            print("正在处理lightinalbum", lightinalbum.pk)
            prepare_a_album(lightinalbum.pk)

    #重新读取
    print(album_pks)
    lightinalbums = LightinAlbum.objects.filter(pk__in=list(album_pks))


    spu_ims = lightinalbums.filter(~Q(image_pure=""),image_pure__isnull=False).values_list("image_pure", flat=True)
    if spu_ims.count()<4:
        print(spu_ims)
        print("没有无logo图片")
        return False





    handles = lightinalbums.values_list("lightin_spu__handle", flat=True)

    # 把spus的图拼成一张
    handles_name = ','.join(handles)

    image_marked_url = combo_ad_image_v2(spu_ims, handles_name, yallavip_album_instance)
    print( image_marked_url )

    if not image_marked_url:
        print("没有生成广告图片")
        return
    '''
    message = "💋💋Flash Sale ！！！💋💋" \
              "90% off！Lowest Price Online ！！！" \
              "🥳🥳🥳 10:00-22:00 Everyday ,Update 100 New items Every Hour !! The quantity is limited !!😇😇" \
              "All goods are in Riyadh stock,It will be delivered to you in 3-5 days! ❣️❣️" \
              "How to order?Pls choice the product that you like it , then send us the picture, we will order it for you!🤩🤩"
    
    '''
    message = "[Buy 3 get 1 free]+[free Shipping]+[all spot goods] \n" \
              "Special Promotion big sale: “Buy 3 get 1 free”!!! \n" \
              "It means now if you buy 3 items, you can choose any 1 item of equal price or lower price for free, and the shipping fee is free too!!!! \nAll hot sale goods, limited quantity , all Riyadh warehouse spot, 3-5day deliver to your house!!!!\n" \
              "Don't wait, do it!!!!!"
    message = message + "\n[" + handles_name + "]"
    obj, created = YallavipAd.objects.update_or_create(yallavip_album=yallavip_album_instance,
                                                       spus_name=handles_name,
                                                       defaults={'image_marked_url': image_marked_url,
                                                                 'message': message,
                                                                 'active': True,

                                                                 }
                                                       )
    #把spu标示为已经打过广告了
    for lightinalbum in lightinalbums:
        spu = lightinalbum.lightin_spu
        spu.aded = True
        spu.save()

def make_spu_pure_image(target_page, spu):
    # 价格
    if spu.free_shipping:
        price1 = int(spu.free_shipping_price)
    else:
        price1 = int(spu.yallavip_price)

    price2 = int(price1 * random.uniform(5, 6))


    # 准备图片
    # 先取第一张，以后考虑根据实际有库存的sku的图片（待优化）
    error =""
    if spu.images_dict:
        image = json.loads(spu.images_dict).values()
        if image and len(image) > 0:
            a = "/"
            image_split = list(image)[0].split(a)

            image_split[4] = '800x800'
            image = a.join(image_split)

        # 打水印
        image_marked, image_pure_url, image_marked_url = yallavip_mark_image(image, spu.handle, str(price1),
                                                                             str(price2),
                                                                             target_page,spu.free_shipping)
        if not image_marked:
            error = "打水印失败"


    else:
        print(album, spu.SPU, "没有图片")
        error = "没有图片"

    if error == "":
        return image_pure_url
    else:
        return None




def prepare_promote_image_album_v3(cate, page_no, lightin_spus):
    from prs.fb_action import combo_ad_image_v3


    print ("正在处理page ", cate, page_no, lightin_spus)
    target_page= MyPage.objects.get(page_no=page_no)
    spus=[]
    spu_ims = []
    handles = []
    for spu in lightin_spus:
        #spu = Lightin_SPU.objects.get(pk=spu_pk)
        print("正在处理 handle ",spu.handle)
        spu_im = make_spu_pure_image(target_page, spu)
        #spu_im = LightinAlbum.objects.get(yallavip_album__page=target_page, lightin_spu=spu).image_pure
        if spu_im:
            spus.append(spu)
            spu_ims.append(spu_im)
            if spu.handle:
                handles.append(spu.handle)
            else:
                return  False
        else:
            return  False

    # 把spus的图拼成一张

    handles_name = ','.join(handles)

    image_marked_url = combo_ad_image_v3(spu_ims, handles_name,  page_no)
    #print( image_marked_url )

    if not image_marked_url:
        print("没有生成广告图片")
        return
    message = "💋💋Flash Sale ！！！💋💋" \
              "90% off！Lowest Price Online ！！！" \
              "🥳🥳🥳 10:00-22:00 Everyday ,Update 100 New items Every Hour !! The quantity is limited !!😇😇" \
              "All goods are in Riyadh stock,It will be delivered to you in 3-5 days! ❣️❣️" \
              "How to order?Pls choice the product that you like it , then send us the picture, we will order it for you!🤩🤩"
    message = message + "\n[" + handles_name+ "]"

    obj, created = YallavipAd.objects.update_or_create(page_no=page_no,
                                                       spus_name=handles_name,
                                                       defaults={'image_marked_url': image_marked_url,
                                                                 'message': message,
                                                                 'active': True,
                                                                 'long_ad':True,
                                                                 'cate':cate,

                                                                 }
                                                       )
    #把spu标示为已经打过广告了
    for spu in spus:

        spu.longaded = True
        spu.save()

#下载最新的feed
@shared_task
def auto_sync_feed():
    from fb.tasks import update_feed

    #选择需要推广的page
    pages = MyPage.objects.filter(is_published=True, active=True, promotable=True)

    #遍历每个page
    for page in pages:
        print("正在处理page", page)
        update_feed(page.page_no)

    return

def link_page_post(page_no,access_token, ad):
    import time


    adobjects = FacebookAdsApi.init(access_token=access_token, debug=True)

    try:
        # 创建post
        fields = [
            'object_id',
        ]

        params = {
            'message': ad.message,
            'link':"www.yallavip.com",
            'picture': ad.image_marked_url,
            'published':True,
            "call_to_action": {"type": "MESSAGE_PAGE",
                               "value": {"app_destination": "MESSENGER",
                                         'link':"www.yallavip.com"}},
        }

        feed_post = Page(page_no).create_feed(
            fields=fields,
            params=params,
        )
        return  feed_post.get_id(),True
    except Exception as e:
        print(e)
        error = e.api_error_message()
        return error, False

def photo_page_post(page_no,access_token, ad):
    import time


    adobjects = FacebookAdsApi.init(access_token=access_token, debug=True)

        # 创建page photo
    try:
        fields = [
        ]
        params = {
            'url': ad.image_marked_url,
            'published': 'false',
        }
        photo_to_be_post = Page(page_no).create_photo(
            fields=fields,
            params=params,
        )
        photo_to_be_post_id = photo_to_be_post.get_id()

        # 创建post
        fields = [
            'object_id',
        ]

        params = {
            'message': ad.message,
            # 'attached_media': [{'media_fbid': photo_to_be_post_id}],
            'attached_media': [{'media_fbid': photo_to_be_post_id}],
            "call_to_action": {"type": "MESSAGE_PAGE",
                               "value": {"app_destination": "MESSENGER"}},
        }
        feed_post = Page(page_no).create_feed(
            fields=fields,
            params=params,
        )
        return  feed_post.get_id(),True
    except Exception as e:
        print(e)
        error = e.api_error_message()
        return error, False






def delete_outdate_post(date):
    feed_dict={}

    feeds = MyFeed.objects.filter(created_time__lt=date,active=True)
    if feeds:
        print("有%s个feed待删除"%(feeds.count()))
        feed_nos = feeds.values_list("page_no", "feed_no").distinct()

        for feed_no in feed_nos:
            page_no = feed_no[0]
            feed_id = feed_no[1]
            feed_list = feed_dict.get(page_no)
            if not feed_list:
                feed_list = []

            if feed_id not in feed_list:
                feed_list.append(feed_id)

            feed_dict[page_no] = feed_list


    # 选择所有可用的page
    for page_no in feed_dict:


        feed_ids = feed_dict[page_no]
        print("page %s 待删除数量 %s  " % (page_no, len(feed_ids)))
        if feed_ids is None or len(feed_ids) == 0:
            continue

        delete_posts(page_no, feed_ids)
        #print(feed_ids)


#把在打广告的spu标识出来
def tag_aded_spus():
    ads = MyAd.objects.filter(active=True).values_list("ad_no", flat=True)

    spus_name_list = YallavipAd.objects.filter(engagement_ad_id__in=ads).values_list("spus_name",flat=True)

    spus_list = []

    for spus_name in spus_name_list:
        spus = spus_name.split(",")

        for spu in spus:
            print(spu)
            if spu not in spus_list:
                spus_list.append(spu)

    print (spus_list,len(spus_list))

    Lightin_SPU.objects.update(aded=False)
    Lightin_SPU.objects.filter(handle__in=spus_list).update(aded=True)



def cal_sku_size():
    skus = Lightin_SKU.objects.filter(lightin_spu__vendor="lightin",size="", skuattr__icontains="size")

    for sku in skus:

        option_sets = sku.skuattr.split(";")

        for option_set in option_sets:

            if option_set.lower().find("size")>-1 :
                options = option_set.split("=")
                print(options)
                if len(options) ==2 :
                    sku.size = size[1]
                    sku.save()
                    break
                else:
                    print("没有尺码",sku.skuattr , option_set)

def update_spu_cate():
    spus = Lightin_SPU.objects.filter(vendor="lightin", mycategory__isnull=True)
    for spu in spus:
        try:
            tags = spu.breadcrumb.split(",")[:3]
            new_tags = []
            for tag in tags:
                new_tag = tag.strip()
                new_tags.append(new_tag)

            spu.mycategory = MyCategory.objects.get(tags = ",".join(new_tags))
            print (spu.mycategory)
            spu.save()
        except Exception as e:
            print(e)
            print("对应不上cate", spu , spu.breadcrumb, spu.sellable)


def update_spu_sizecount():
    #先把所有的spu的size_count都置为0，再更新最新的状态
    Lightin_SPU.objects.update(size_count=0)
    spu_sizes = Lightin_SKU.objects.filter(~Q(size=""), lightin_spu__size_count=0, o_sellable__gt=0, lightin_spu__vendor="lightin").\
        values("SPU").annotate(size_count = Count("size", distinct=True))
    for spu_size in spu_sizes:
        try:
            spu = Lightin_SPU.objects.get(SPU=spu_size.get("SPU"))
            spu.size_count = spu_size.get("size_count")
            spu.save()
        except Exception as e:
            print(e)
            print("更新size_count 出错", spu_size )

def delete_outstock_album_sku():
    fb_dict ={}

    yallavip_albums = YallavipAlbum.objects.filter(active=True, rule__isnull =False, rule__attrs__isnull=False)
    for yallavip_album in yallavip_albums:
        page_no = yallavip_album.page.page_no
        size = yallavip_album.rule.attrs
        lightin_album = LightinAlbum.objects.filter(yallavip_album = yallavip_album, deleted=False)
        spus = lightin_album.values("lightin_spu")


        skus_all = Lightin_SKU.objects.filter(lightin_spu__in = spus, skuattr__icontains=size)
        spus_sellable =  skus_all.values("lightin_spu").annotate(sellable=Sum("o_sellable"))

        print(yallavip_album, size, spus.count())
        #print(spus_sellable)
        spu_todelete=[]
        for spu_sellable in spus_sellable:
            spu = spu_sellable["lightin_spu"]
            sellable = spu_sellable["sellable"]

            if sellable <= 0:
                spu_todelete.append(spu)

        fb_todelete = lightin_album.filter(lightin_spu__in = spu_todelete).values_list("fb_id",flat=True)

        fb_list = fb_dict.get(page_no)
        if not fb_list:
            fb_list = []

        fb_list +=  fb_todelete

        fb_dict[page_no] = fb_list

    # 选择所有可用的page
    for page_no in fb_dict:


        fb_ids = fb_dict[page_no]
        print("page %s 待删除数量 %s  " % (page_no, len(fb_ids)))
        if fb_ids is None or len(fb_ids) == 0:
            continue

        delete_photos(page_no, fb_ids)
        LightinAlbum.objects.filter(fb_id__in=fb_ids).update(deleted=True)

#自动生成post
@shared_task
def auto_prepare_promote():
    from prs.album import  prepare_promote_v2
    #选择需要推广的page
    pages = MyPage.objects.filter(is_published=True, active=True, promotable=True)

    #遍历每个page
    for page in pages:
        page_no = page.page_no
        prepare_promote_v2(page_no)

#自动生成post
@shared_task
def auto_page_post():
    #选择需要推广的page
    pages = MyPage.objects.filter(is_published=True, active=True, promotable=True)

    #遍历每个page
    for page in pages:
        #从符合条件的相册里选一个相册,    #发post
        print("正在处理page", page)
        page_no = page.page_no

        to_create_count = 5
        page_post_v2(page_no, to_create_count)


@shared_task
def auto_engagement_ads():
    #选择需要推广的page
    pages = MyPage.objects.filter(is_published=True, active=True, promotable=True)

    #遍历每个page
    for page in pages:

        page_no = page.page_no
        ad_type = "engagement"
        to_create_count = 3
        post_ads_v2(page_no, ad_type, to_create_count)

@shared_task
def auto_message_ads():
    #选择需要推广的page
    pages = MyPage.objects.filter(is_published=True, active=True, promotable=True)

    #遍历每个page
    for page in pages:

        page_no = page.page_no
        ad_type = "message"
        to_create_count = 3
        post_ads_v2(page_no, ad_type, to_create_count)

def test_funmart_product():
    url = "http://47.96.143.109:9527/api/getInfoBySku"
    param = dict()
    param["sku"] = "C-170809038"


    r = requests.post(url, data=json.dumps(param))
    print(r.status_code, r.text)

def test_funmart_order():
    url = " http://47.98.80.172/api/searchOrder"
    param = dict()
    param["order_no"] = "112115244631159272"


    r = requests.post(url, data=json.dumps(param))
    print(r.status_code, r.text)

def delete_outstock_yallavipad():

    import time

    ads = YallavipAd.objects.filter(active=True)
    ads_todelete = []

    for ad in ads:

        handles = ad.spus_name.split(",")
        spus_all = Lightin_SPU.objects.filter(handle__in=handles)
        spus_outstock = spus_all.filter(sellable__lte=0)
        if spus_outstock.count() > 0:
            print("有spu无库存了", spus_outstock, ad )
            spus_all.update(aded=False)
            ads_todelete.append(ad.pk)

    print("有 %s 条广告待删除" % len(ads_todelete))

    YallavipAd.objects.filter(pk__in=ads_todelete).delete()


#把价格大于40的，全部设置成单件包邮
def set_spu_free_delivery_price():


    spus = Lightin_SPU.objects.filter(vendor="lightin")
    for spu in spus:
      cal_promote_price(spu)

#计算某个spu的促销价，修改sku，spu的促销价
#原价大于40的，都设成单件包邮
def cal_promote_price(spu):

    #供货价的5倍 0.25*3.75*5
    # 供货价的3倍 0.25*3.75*3
    multiple_price = spu.vendor_supply_price * 2.8
    #供应商售价的6折 3.75*0.6
    # 供应商售价的4折 3.75*0.4
    discount_price = spu.vendor_sale_price * 1.5
    if multiple_price < discount_price:
        promote_price = round(discount_price)
    else:
        promote_price = round(multiple_price)

    #小于5块的都卖5块，小于十块都卖10块
    if promote_price <5:
        promote_price = 5
    elif promote_price <10:
        promote_price = 10

    #价格大于25的，都包邮
    if promote_price >= 25:
        spu.free_shipping = True
    else:
        spu.free_shipping = False

    free_shipping_price = promote_price + 25
    spu.spu_sku.update(free_shipping_price=free_shipping_price, sku_price = promote_price)

    #修改spu价格
    spu.free_shipping_price = free_shipping_price
    spu.yallavip_price = promote_price
    spu.promoted = True
    spu.save()
    return  True



#根据面包屑更新品类表
#从spu表取出所有distinct面包屑
#遍历所有面包屑
#分解成3级品类
#把品类更新到数据库
def breadcrumb_cates_v1():
    breadcrumbs = Lightin_SPU.objects.filter(vendor="lightin").values_list("breadcrumb",flat=True).distinct()
    catelist = []

    for breadcrumb in breadcrumbs:
        if not breadcrumb:
            continue
        cate = json.loads(breadcrumb)
        print(cates)

        if len(cate)>0:

            cate_1 = ("", cate[0].strip(), 1, ",".join(list(cate)[:1]))
            if cate_1 not in catelist:
                catelist.append(cate_1)
        if len(cate)>1:
            cate_2 = (cate[0].strip(), cate[1].strip(), 2, ",".join(list(cate)[:2]))
            if cate_2 not in catelist:
                catelist.append(cate_2)

        if len(cate)>2:
            cate_3 = (cate[1].strip(), cate[2].strip(), 3, ",".join(list(cate)[:3]))
            if cate_3 not in catelist:
                catelist.append(cate_3)

    for cate in catelist:
        obj, created = MyCategory.objects.update_or_create(
            tags=cate[3],

            defaults={
                "super_name": cate[0],
                "name": cate[1],
                "level": cate[2],
                "vendor": "lightin",

            }
        )

def spu_cates_v1():
    spus = Lightin_SPU.objects.filter(vendor="lightin")

    for spu in spus:
        if spu.breadcrumb :
            cates = json.loads(spu.breadcrumb)
        else:
            continue

        print(cates)

        if len(cates)>0:
            spu.cate_1 = cates[0].strip()

        if len(cates)>1:
            spu.cate_2 = cates[1].strip()
        if len(cates)>2:
            spu.cate_3 = cates[2].strip()

        spu.tags = ",".join(cates)

        spu.save()

def create_handle_funmart():
    spus = Lightin_SPU.objects.filter(Q(handle__isnull=True)|Q(handle=""),vendor="funmart")

    for spu in spus:

        spu.handle = 'F' + str(spu.pk).zfill(6)
        spu.save()

def split_skuattr():
    Lightin_SKU.objects.filter(Q(size="")|Q(color=""), ~Q(sku_attr=""), vendor="funmart")
