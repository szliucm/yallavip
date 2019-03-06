# Create your tasks here
from __future__ import absolute_import, unicode_literals
import numpy as np, re

from celery import shared_task

from datetime import datetime,timedelta
from django.utils import timezone as dt

from .photo_mark import  photo_mark
from shop.models import ProductCategory,ProductCategoryMypage
from fb.models import  MyPage,MyAlbum,MyPhoto
from orders.models import  Order,OrderDetail
from .models import *
from .shop_action import  *

from .fb_action import  *
from .adminx import  insert_product
from django.db.models import Q

@shared_task
def add(x, y):
    return x + y


@shared_task
def mul(x, y):
    return x * y


@shared_task
def xsum(numbers):
    return sum(numbers)


#从沙特站发布产品到主站
@shared_task
def post_to_mainshop():
    dest_shop = "yallasale-com"
    ori_shop = "yallavip-saudi"

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

        #insert_product(dest_shop, product_list)



        # shopify.ShopifyResource.clear_session()

#发布产品到Facebook的album
@shared_task
def post_to_album():
    #每个pange，每次发布一个新产品没发布过的产品到对应相册
    #选择产品ID比已有的大的产品
    #如果产品的品类不符合，就选下一条
    #如果相册不存在，就创建一个相册
    #把产品对应的图片进行打标
    #把打标后的图片发布到相册

    #选择所有可用的page
    mypages = MyPage.objects.filter(active=True)
    for mypage in mypages:

        print("当前处理主页", mypage)

        # 主页已有的相册
        album_dict = {}
        albums = MyAlbum.objects.filter(page_no=mypage.page_no,active=True)
        for album in albums:
            album_dict[album.name] = album.album_no

        #print("主页已有相册", album_dict)

        categories = mypage.category_page.filter(active=True)


        if not categories:
            print("类目为空，跳出")
            continue

       #至少发6 张图片# 每次随机选择一个类目，发6 张图片，如果类目没有可做的，则跳过，选择下一个类目
        posted = 0
        cates = 0
        categories_count = len(categories)

        while  posted <=5 and  cates <= categories_count:


            category = random.choice(categories)
            cates = cates + 1
            print("当前处理的类目 %s" % (category))

            # 找出每个品类下未发布的产品
            products = ShopifyProduct.objects.filter(category_code=category.productcategory.code,
                                                     shop_name="yallasale-com",
                                                     #published_at__gt='2018-11-01',
                                                   # product_no__gt=category.last_no,
                                                     handle__startswith='a'). \
                order_by("product_no")
            if not products :
                print("当前类目没有产品了，跳出")
                print(category.productcategory.code)
                #print(category.last_no)

                ProductCategoryMypage.objects.filter(pk= category.pk).update(active=False)

                continue

            # 这个品类是否已经建了相册
            category_album = category.album_name
            target_album = album_dict.get(category_album)

            #print("品类需要的相册 %s, 已有相册 %s" % (category_album, target_album))

            if not target_album :
                '''
                #print("此类目还没有相册，新建一个")
                album_list = []
                album_list.append(category_album)

                target_album = create_new_album(mypage.page_no, album_list)[0]
                '''
                print("此相册还没有创建，请新建一个")
                continue

            #print("target_album %s" % (target_album))

            # 发到指定相册
            n = 0
            for product in products:
                posted = posted + post_photo_to_album(mypage, target_album, product)

                obj, created = ProductCategoryMypage.objects.update_or_create(
                    mypage=mypage, productcategory=category.productcategory,
                    defaults={
                        #'last_no': product.product_no
                    },

                )
                #print("更新page_类目记录 %s %s %s" % (mypage, category.productcategory, product.product_no))
                #print("created is ", created)
                #print("obj is ", obj)
                n = n+1
                if n>5:
                    break




    return

#从Facebook删除已断货产品的图片（post待定）
@shared_task
def delete_stop_product():

    from facebook_business.api import FacebookAdsApi
    from facebook_business.adobjects.photo import Photo

    adobjects = FacebookAdsApi.init(my_app_id, my_app_secret, access_token=my_access_token, debug=True)

    products = ShopifyProduct.objects.filter( supply_status ="STOP" , listing_status = True)
    for product in products:
        myphotos = MyPhoto.objects.filter(name__icontains = product.handle)

        for myphoto in myphotos:
            fields = [
                      ]
            params = {

            }
            response = Photo(myphoto.photo_no).api_delete(
                fields=fields,
                params=params,
            )
            print("delte photo %s response is %s"%(myphoto.photo_no,response ))

        #修改数据库记录
        myphotos.update(listing_status=False)
        obj, created = ShopifyProduct.objects.update_or_create(product_no=product.product_no,
                                                               defaults={
                                                                   'listing_status': False,
                                                               }
                                                               )
    return

#从Facebook删除已断货产品的图片（post待定）
@shared_task
def delete_stop_sku():

    from facebook_business.api import FacebookAdsApi
    from facebook_business.adobjects.photo import Photo

    adobjects = FacebookAdsApi.init(my_app_id, my_app_secret, access_token=my_access_token, debug=True)

    products = ShopifyVariant.objects.filter( supply_status ="STOP" , listing_status = True)
    for product in products:
        myphotos = MyPhoto.objects.filter(name__icontains = product.handle)

        for myphoto in myphotos:
            fields = [
                      ]
            params = {

            }
            response = Photo(myphoto.photo_no).api_delete(
                fields=fields,
                params=params,
            )
            print("delte photo %s response is %s"%(myphoto.photo_no,response ))

        #修改数据库记录
        myphotos.update(listing_status=False)
        obj, created = ShopifyProduct.objects.update_or_create(product_no=product.product_no,
                                                               defaults={
                                                                   'listing_status': False,
                                                               }
                                                               )
    return

#发布产品到Facebook的page
@shared_task
def post_to_page():
    # 选择所有可用的page
    mypages = MyPage.objects.filter(active=True)
    for mypage in mypages:
        # 每次随机选择1 张未发布过的图片，如果没有可做的，则跳过
        myphotos = MyPhoto.objects.filter(page_no=mypage.page_no, posted_times =0)

        if not myphotos:
            print("待发布的图片为空，跳出")
            continue

        myphoto = random.choice(myphotos)

        print("当前处理的图片 %s" % (myphoto))

        create_page_feed(mypage, myphoto)

        # 修改数据库记录
        myphotos.update(posted_times=myphoto.posted_times+1)


    return

def get_orders(minutes=10):
    shop_name = "yallasale-com"
    shop_obj = Shop.objects.get(shop_name=shop_name)
    '''
    # 取得系统中30天内最早的订单号

   
    shoporiorder = ShopOriOrder.objects.filter(Q(created_at__gt=(dt.now() - timedelta(days=60)))).order_by("order_id").first()
    if shoporiorder is None:
        max_shoporiorder_no = "0"
    else:
        max_shoporiorder_no = shoporiorder.order_id

    print("max_shoporiorder_no", max_shoporiorder_no)

    # 删除所有可能重复的订单信息

    ShopOriOrder.objects.filter(order_id__gt=max_shoporiorder_no).delete()
    

    # 获取新订单信息
    shop_url = "https://%s:%s@%s.myshopify.com" % (shop_obj.apikey, shop_obj.password, shop_obj.shop_name)
    # shop_url = "https://12222a833afcad263c5cc593eca7af10:47aea3fe8f4b9430b1bac56c886c9bae@yallasale-com.myshopify.com/admin"
    # shopify.ShopifyResource.set_site(shop_url)


    status = ["open", "closed", "cancelled"]

    for stat in status:
        url = shop_url + "/admin/orders/count.json"
        params = {
            
            "since_id": max_shoporiorder_no,
            "status": stat,
        }
        # print("url %s params %s"%(url, params))
        r = requests.get(url, params)
        data = json.loads(r.text)

        if not data:
            print("返回为空", data)
            continue

        print("order count is ", data.get("count"))




        total_count = data["count"]

        i = 0
        limit = 100

        while True:
            try:

                if (i * limit > total_count):
                    break

                i = i + 1

                # products = shopify.Product.find(page=i,limit=limit,updated_at_min=shop.updated_time)
                url = shop_url + "/admin/orders.json"
                params = {
                    "page": i,
                    "limit": limit,
                    "since_id": max_shoporiorder_no,
                    "status":stat,
                    #"fields": "id,handle,body_html,title,product_type,created_at,published_at,"
                    #          "updated_at,tags,vendor,variants,images,options",
                    # "fields": "product_id",
                }
                print(("params is ", params))

                r = requests.get(url, params)
                oriorders = json.loads(r.text)["orders"]
                oriorders_list = []
                for row in oriorders:
                    # print("row is ",row)
                    oriorder = ShopOriOrder(
                        order_id=row["id"],
                        order_no=row["order_number"],
                        created_at = row["created_at"],
                        status = stat,
                        order_json=json.dumps( row),
                    )
                    oriorders_list.append(oriorder)

                ShopOriOrder.objects.bulk_create(oriorders_list)
                #insert_product(shop.shop_name, products)



            except Exception as e:
                print("orders  completed", e)
                continue
    '''




    # 获取新订单信息
    shop_url = "https://%s:%s@%s.myshopify.com" % (shop_obj.apikey, shop_obj.password, shop_obj.shop_name)
    # shop_url = "https://12222a833afcad263c5cc593eca7af10:47aea3fe8f4b9430b1bac56c886c9bae@yallasale-com.myshopify.com/admin"
    # shopify.ShopifyResource.set_site(shop_url)

    status = ["open", "closed", "cancelled"]
    updated_at_min = (dt.now() - timedelta(minutes=minutes)).strftime("%Y-%m-%dT%H:%M:%S+00:00")
    for stat in status:
        url = shop_url + "/admin/orders/count.json"
        params = {


            "updated_at_min": updated_at_min ,
            "status": stat,
        }
        # print("url %s params %s"%(url, params))
        r = requests.get(url, params)
        data = json.loads(r.text)

        if not data:
            print("返回为空", data)
            continue

        print("order count is ", data.get("count"))

        total_count = data["count"]
        print(stat, "共有 %s 个订单待获取" % (total_count))

        i = 0
        limit = 100

        while True:
            try:
                order_id_list = []
                if (i * limit > total_count):
                    break

                i = i + 1

                # products = shopify.Product.find(page=i,limit=limit,updated_at_min=shop.updated_time)
                url = shop_url + "/admin/orders.json"
                params = {
                    "page": i,
                    "limit": limit,
                    "updated_at_min": updated_at_min,
                    "status": stat,
                    # "fields": "id,handle,body_html,title,product_type,created_at,published_at,"
                    #          "updated_at,tags,vendor,variants,images,options",
                    # "fields": "product_id",
                }
                print(("params is ", params))

                r = requests.get(url, params)
                oriorders = json.loads(r.text)["orders"]

                print("oriorders ", len(oriorders))
                oriorders_list = []
                for row in oriorders:
                    # print("row is ",row)
                    order_id_list.append(row["id"])
                    oriorder = ShopOriOrder(
                        order_id=row["id"],
                        order_no=row["order_number"],
                        created_at=row["created_at"],
                        status=stat,
                        order_json=json.dumps(row),
                        updated = True,
                    )
                    oriorders_list.append(oriorder)


                # 删除所有可能重复的订单信息
                ShopOriOrder.objects.filter(order_id__in=order_id_list).delete()

                ShopOriOrder.objects.bulk_create(oriorders_list)
                # insert_product(shop.shop_name, products)



            except Exception as e:
                print("orders  completed", e)
                continue

    update_orders()

def update_orders():
    oriorders = ShopOriOrder.objects.filter(updated=True)
    print("有 %s 个订单待更新"%(oriorders.count()))

    for row in oriorders:
        print(row.order_id)


        order = json.loads(row.order_json)
        customer = order.get("customer")

        if customer is not None :

            buyer_name = ""
            first_name = order["customer"].get("first_name","")
            last_name = order["customer"].get("last_name", "")
            if first_name is not None :
                buyer_name += first_name
            if last_name is not None :
                buyer_name += last_name



        else:
            buyer_name = ""

        shipping_address = order.get("shipping_address")
        if shipping_address is not None:
            receiver_name =  shipping_address.get("first_name","")
            if shipping_address.get("last_name","") is not None:
                receiver_name += " " +  shipping_address.get("last_name","")

            address1 = shipping_address.get("address1","")

            address2 = shipping_address.get("address2","")
            if address2 is None:
                address2 = ""
            city = shipping_address.get("city","")
            country = shipping_address.get("country","")
            phone = shipping_address.get("phone","")

        else:
            receiver_name = ""
            address1 = ""
            address2 = ""
            city = ""
            country = ""
            phone = ""


        obj, created = Order.objects.update_or_create(order_no= "579815-" + str(order["order_number"]),
                        defaults={
                                    'order_id':row.order_id,
                                    'order_time': order["created_at"],
                                    'status':row.status,
                                    'financial_status': order["financial_status"],
                                    'fulfillment_status': order["fulfillment_status"],
                                    'buyer_name':buyer_name ,
                                    'order_amount':order["total_price"],
                                    'order_comment':order["note"],
                                    'receiver_name':receiver_name,
                                    'receiver_addr1':address1,
                                    'receiver_addr2':address2,
                                    'receiver_city':city,
                                    'receiver_country':country,
                                    'receiver_phone':phone,
                                    "updated": True,
                                }
                                )
        print("####obj", obj, type(obj) )
        if obj is None:
            print("#############soemthing get wrong ",order["order_number"] )
            continue

        if created :
            for order_item in  order["line_items"]:
                print(obj, order_item["sku"],order_item["quantity"],order_item["price"])
                sku =order_item["sku"]
                if sku == "" or sku is None:
                    sku = order_item["variant_id"]
                    if sku == "" or sku is None:
                        sku = order_item["id"]
                obj_orderdetail, created = OrderDetail.objects.update_or_create(order=obj,
                                                                    sku = sku,
                                                          defaults={
                                                              'product_quantity': order_item["quantity"],
                                                              'price': order_item["price"],
                                                               }
                                                          )

    oriorders.update(updated=False)

