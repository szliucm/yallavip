# Create your tasks here
from __future__ import absolute_import, unicode_literals
import numpy as np, re
from celery import shared_task
from django.db.models import Q
import requests
import json
import random


from .models import *
from shop.models import  Shop, ShopifyProduct, ShopifyVariant, ShopifyImage, ShopifyOptions

from .shop_action import sync_shop
from orders.models import Order


#更新ali产品数据，把vendor和产品信息连接起来
@shared_task
def update_myproductali():
    dest_shop = "yallasale-com"

    products = MyProductAli.objects.filter(listing=False)

    for ali_product in products:

        #从链接获取供应商编号
        url = ali_product.url
        vendor_no = url.partition(".html")[0].rpartition("/")[1]
        print("url %s vendor_no %s" % (url, vendor_no))

        #用供应商编号获取产品信息
        product =  ShopifyProduct.objects.filter(vendor__exact = vendor_no,shop_name=dest_shop ).first()
        print("product", product)
        print("vendor", vendor_no)

        #在爆款管理中创建记录，并连接爆款记录和ali产品记录
        if product:
            obj, created= MyProduct.objects.update_or_create(
                            product_no = product.product_no,
                            vendor_no=vendor_no,
                            defaults={

                            }

            )

            MyProductAli.objects.filter(pk=ali_product.pk).update(
                myproduct=obj,
                vendor_no=vendor_no,

            )


    return True

#从沙特站发布产品到主站
@shared_task
def post_to_mainshop():
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
    shop_obj = Shop.objects.get(shop_name=dest_shop)
    shop_url = "https://%s:%s@%s.myshopify.com" % (shop_obj.apikey, shop_obj.password, shop_obj.shop_name)


    for product in ori_products:
        handle_i = handle_i + 1
        handle_new = "A" + str(handle_i).zfill(4)

        # Create a new product

        url = shop_url + "/admin/products.json"

        imgs_list = []

        imgs = ShopifyImage.objects.filter(product_no=product.product_no).values('image_no', 'src').order_by(
            'position')

        for img in imgs:
            image = {
                "src": img["src"],
                "image_no": img["image_no"]
            }
            imgs_list.append(image)


        params = {
            "product": {
                "handle": handle_new,
                "title": product.title,
                "body_html": product.body_html,
                "vendor": product.vendor,
                "product_type": product.product_type,
                "tags": product.tags,
                "images": imgs_list,
                # "variants": variants_list,
                # "options": option_list
            }
        }
        headers = {
            "Content-Type": "application/json",
            "charset": "utf-8",

        }

        r = requests.post(url, headers=headers, data=json.dumps(params))
        data = json.loads(r.text)
        new_product = data.get("product")
        if new_product is None:
            print("post product error data is ", data)
            print("parmas is ", params)
            continue

        new_product_no = new_product.get("id")

        # 增加变体

        # image
        image_dict = {}
        for k_img in range(len(new_product["images"])):
            image_row = new_product["images"][k_img]
            new_image_no = image_row["id"]
            # new_image_list.append(image_no)
            old_image_no = imgs_list[k_img]["image_no"]

            image_dict[old_image_no] = new_image_no
            # print("old image %s new image %s"%(old_image_no, new_image_no ))

        # option
        option_list = []

        options = ShopifyOptions.objects.filter(product_no=product.product_no).values('name', 'values')
        for row in options:
            option = {
                "name": row["name"],
                "values": re.split('[.]', row["values"])
            }
            option_list.append(option)

        # variant
        variants_list = []

        variants = ShopifyVariant.objects.filter(product_no=product.product_no).values()

        for variant in variants:
            old_image_no = variant.get("image_no")
            new_image_no = image_dict.get(old_image_no)
            print("image dict  %s %s " % (old_image_no, new_image_no))

            sku = handle_new
            option1 = variant.get("option1")
            option2 = variant.get("option2")
            option3 = variant.get("option3")

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
                "price": int(float(variant.get("price")) * 2.3),
                "compare_at_price": int(float(variant.get("price")) * 2.3 * random.uniform(2, 3)),
                "sku": sku,
                "position": variant.get("position"),
                "image_id": new_image_no,
                "grams": variant.get("grams"),
                "title": variant.get("title"),
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

        params = {
            "product": {
                "variants": variants_list,
                "options": option_list,

            }
        }
        headers = {
            "Content-Type": "application/json",
            "charset": "utf-8",

        }

        # print("upload data is ",json.dumps(params))

        url = shop_url + "/admin/products/%s.json" % (new_product_no)
        r = requests.put(url, headers=headers, data=json.dumps(params))
        data = json.loads(r.text)

        new_product = data.get("product")
        if new_product is None:
            print("post variant error data is ", data)
            print("product.product_no is ", product.product_no)
            print("parmas is ",params )
            continue

        print("new_product_no is", new_product.get("id"))
        total_to_update = total_to_update - 1
        print("沙特站最新的还有 %d 需要发布" % (total_to_update))

        product_list = []
        product_list.append(new_product)

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
def ad_sycn_product():
    from .fb_action import sycn_ad_product

    sycn_ad_product()
    return



