from .models import *
from shop.models import  Shop, ShopifyProduct, ShopifyVariant, ShopifyImage, ShopifyOptions,ProductCategory

import  re
import random


from orders.models import Order
from celery import shared_task

import requests
import json

#同步shopify信息到系统数据库
def sync_shop(shop, max_product_no =None):

    #获取店铺信息
    shop_obj = Shop.objects.get(shop_name=shop)
    shop_url = "https://%s:%s@%s.myshopify.com" % (shop_obj.apikey, shop_obj.password, shop_obj.shop_name)

    if not max_product_no:
        # 取得系统中已有的最大product_no
        product = ShopifyProduct.objects.filter(shop_name=shop).order_by('-product_no').first()
        if product is None:
            max_product_no = "0"
        else:
            max_product_no = product.product_no

    print("max_product_no", max_product_no)

    # 删除所有可能重复的产品信息

    ShopifyVariant.objects.filter(product_no__gt=max_product_no).delete()
    ShopifyImage.objects.filter(product_no__gt=max_product_no).delete()
    ShopifyOptions.objects.filter(product_no__gt=max_product_no).delete()

    # 获取新产品信息
    url = shop_url + "/admin/products/count.json"
    params = {
        "since_id": max_product_no
    }
    # print("url %s params %s"%(url, params))
    r = requests.get(url, params)
    data = json.loads(r.text)

    print("product count is ", data["count"])

    total_count = data["count"]

    #更新shopify信息到系统数据库
    i = 0
    limit = 100

    while True:
        try:

            if (i * limit > total_count):
                break

            i = i + 1

            # products = shopify.Product.find(page=i,limit=limit,updated_at_min=shop.updated_time)
            url = shop_url + "/admin/products.json"
            params = {
                "page": i,
                "limit": limit,
                "since_id": max_product_no,
                "fields": "id,handle,body_html,title,product_type,created_at,published_at,"
                          "updated_at,tags,vendor,variants,images,options",
                # "fields": "product_id",
            }
            print(("params is ", params))

            r = requests.get(url, params)
            products = json.loads(r.text)["products"]

            insert_product(shop, products)


        except KeyError:
            print("products for the shop {} completed".format(shop))
            break

#创建产品主体
def post_product_main(shop_url, handle_new, product, imgs_list):
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
    # 初始化SDK
    # shop_obj = Shop.objects.get(shop_name=shop_name)
    url = shop_url + "/admin/products.json"

    r = requests.post(url, headers=headers, data=json.dumps(params))
    data = json.loads(r.text)
    new_product = data.get("product")
    if new_product is None:
        print("post product error data is ", data)
        print("parmas is ", params)
        return  None
    else:
        return  new_product


def post_product_variant(shop_url, product_no,variants_list, option_list ):
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

    url = shop_url + "/admin/products/%s.json" % (product_no)
    r = requests.put(url, headers=headers, data=json.dumps(params))
    data = json.loads(r.text)

    new_product = data.get("product")
    if not new_product:
        print("创建变体失败")
        print("post variant error data is ", data)
        print("product.product_no is ", product_no)
        print("parmas is ", params)
        return None
    else:
        return  new_product



########################
####### 在主站创建一个新产品
####### 返回新产品
#######################
def post_new_product(shop_obj, product, handle_new ):
    print("开始创建新产品")
    #print(shop_obj)
    #print(product)
    print(handle_new)


    # 初始化SDK
    #shop_obj = Shop.objects.get(shop_name=shop_name)
    shop_url = "https://%s:%s@%s.myshopify.com" % (shop_obj.apikey, shop_obj.password, shop_obj.shop_name)
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
        return  None


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
        return  None

    print("new_product_no is", new_product.get("id"))
    return new_product

#################################
#####插入shopify产品记录到系统数据库
################################
def insert_product(shop_name, products):
    for j in range(len(products)):
        product_list = []
        variant_list = []
        image_list = []
        option_list = []

        row = products[j]

        if j == 1:
            print("row is ", row)

        product = ShopifyProduct(
            shop_name=shop_name,
            product_no=row["id"],
            handle=row["handle"],
            body_html=row["body_html"],
            title=row["title"],
            created_at=row["created_at"],

            updated_at=row["updated_at"],
            tags=row["tags"],
            vendor=row["vendor"],
            product_type=row["product_type"],

        )
        product_list.append(product)

        try:

            for k in range(len(row["variants"])):
                variant_row = row["variants"][k]

                variant = ShopifyVariant(
                    variant_no=variant_row["id"],
                    product_no=variant_row["product_id"],
                    created_at=variant_row["created_at"],
                    updated_at=variant_row["updated_at"],
                    sku=variant_row["sku"],
                    image_no=variant_row["image_id"],
                    title=variant_row["title"],
                    price=variant_row["price"],
                    option1=variant_row["option1"],
                    option2=variant_row["option2"],
                    option3=variant_row["option3"],

                )
                variant_list.append(variant)

        except KeyError:
            print("no variant ".format(row.shop_name))
            break

        try:

            for m in range(len(row["images"])):
                image_row = row["images"][m]

                image = ShopifyImage(
                    image_no=image_row["id"],
                    product_no=image_row["product_id"],
                    created_at=image_row["created_at"],
                    updated_at=image_row["updated_at"],
                    position=image_row["position"],
                    width=image_row["width"],
                    height=image_row["height"],
                    src=image_row["src"],
                    # variant_ids

                )
                image_list.append(image)
                # print(" variant_list  is ", variant_list)
        except KeyError:
            print("no image ".format(row.shop_name))
            break

        try:

            for n in range(len(row["options"])):
                option_row = row["options"][n]
                values = ','.join(option_row["values"])

                # print(" %s length of values %s "%(option_row["product_id"], len(values)))

                option = ShopifyOptions(
                    product_no=option_row["product_id"],
                    name=option_row["name"],

                    values=values
                )

                option_list.append(option)
                # print(" variant_list  is ", variant_list)
        except KeyError:
            print("no option ".format(row.shop_name))
            break

        # print(product_list)


        ShopifyVariant.objects.bulk_create(variant_list)
        ShopifyImage.objects.bulk_create(image_list)
        ShopifyOptions.objects.bulk_create(option_list)
        ShopifyProduct.objects.bulk_create(product_list)



#创建海外仓商品，先只考虑一个包裹对应一个订单的情况
def create_package_sku(dest_shop, order, discount):
    # 初始化SDK
    shop_obj = Shop.objects.get(shop_name=dest_shop)

    shop_url = "https://%s:%s@%s.myshopify.com" % (shop_obj.apikey, shop_obj.password, shop_obj.shop_name)

    # url = shop_url + "/admin/products.json"

    # 每100个包裹创建一个海外仓商品，包裹作为变体存放。，否则创建新的
    #以订单号为基准创建handle和sku



    #package_no = order.package_no
    #print("package_no is ", package_no)

    #handle_new = "S" + package_no[6:10]

    order_no = order.order_no
    handle_new = "S" + order_no[:-2]
    # 创建变体
    variants_list = []
    #sku = handle_new + "-" + package_no[10:]
    sku = order.order_no
    print("handle_new  sku", handle_new, sku)
    try:
        order_amount = float(order.order_amount)
    except:

        print("order_amount",order, order.order_amount)

        return None, False

    variant_item = {

        "price": int( order_amount* discount),
        "compare_at_price": order_amount,
        "sku": sku,
        "option1": order_no,

        "title": order_no,
        "taxable": "true",
        "inventory_management": "shopify",
        "fulfillment_service": "manual",
        "inventory_policy": "continue",

        "inventory_quantity": 1,
        "requires_shipping": "true",
        "weight": order.weight,
        "weight_unit": "g",

    }
    #print("variant_item", variant_item)
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
    #print("url %s, params %s , response %s" % (url, json.dumps(params), response))

    data = json.loads(response.text)
    #print("check ori_product data is ", data)

    headers = {
        "Content-Type": "application/json",
        "charset": "utf-8",

    }

    ori_products = data.get("products")

    #print("ori_products", ori_products, len(ori_products))

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
            return None,False
        else:
            print("product exist", ori_product["handle"])
            # 获取原有产品信息
            for k in range(len(ori_product["variants"])):
                variant_row = ori_product["variants"][k]
                #print("variant_row is ", variant_row)
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
        return None,False

    print("new product is ", new_product.get("id"))

    return ( new_product.get("id"), True)


def sycn_package():
    variants =  ShopifyVariant.objects.filter(sku__startswith ="579815")
    print(variants)
    for variant in variants:
        MyProductPackage.objects.update_or_create(
            order_no=variant.sku,
            defaults={
                "shopifyvariant" : variant,
                "obj_type": "OVERSEAS"
            }
        )
    return


################################
#####发一个产品到主站
###############################
def post_mainshop(ori_product,max_id,shop_obj):

    new_product = post_new_product(shop_obj, ori_product, 'a' + str(max_id ))

    if new_product:
        products = []
        products.append(new_product)
        # 插入到系统数据库
        insert_product(shop_obj.shop_name, products)

        # 修改handle最大值
        Shop.objects.filter(shop_name=shop_obj.shop_name).update(max_id=max_id)

        print("产品发布成功！！！！" )
        return new_product
    else:

        print("产品发布失败！！！！")
        return  False

##################################
####把沙特站未发的发到主站
####################################
@shared_task
def post_saudi():
    dest_shop = "yallasale-com"
    ori_shop = "yallavip-saudi"

    sync_shop(ori_shop)
    sync_shop(dest_shop)

    shop_obj = Shop.objects.get(shop_name=dest_shop)

    max_id = Shop.objects.get(shop_name=dest_shop).max_id
    handle = 'a' + str(max_id)
    product_init = ShopifyProduct.objects.filter(shop_name=dest_shop, handle= handle).order_by('-product_no').first()
    print("主店最新的产品 handle 是%s  供应商是 %s" % ( product_init.handle, product_init.vendor))

    latest_ori_product = ShopifyProduct.objects.filter(shop_name=ori_shop, vendor=product_init.vendor).order_by(
        '-product_no').first()
    print("沙特站最后更新的产品是 供应商是 %s,product_no is %d " % (
         latest_ori_product.vendor, latest_ori_product.product_no))

    ori_products = ShopifyProduct.objects.filter(shop_name=ori_shop,
                                                 product_no__gt=latest_ori_product.product_no).order_by('product_no')

    total_to_update = ori_products.count()
    print("沙特站最新的还有 %d 需要发布" % (total_to_update))


    n=1
    for ori_product in ori_products:

        vendor_no = ori_product.vendor
        print("vendor_no", vendor_no)

        dest_product = ShopifyProduct.objects.filter(shop_name=dest_shop, vendor=vendor_no).count()

        if dest_product > 0:
            print("这个产品已经发布过了！！！！", vendor_no)
            continue

        print("********************ord_product",ori_product,shop_obj )
        posted = post_mainshop(ori_product, max_id+n, shop_obj)
        # 修改发布状态
        if posted:
            #MyProductAli.objects.filter(pk=aliproduct.pk).update(posted_mainshop=True)
            n = n + 1
        else:
            #MyProductAli.objects.filter(pk=aliproduct.pk).update(post_error=True)
            continue


#####################################
#########把单独找的1688链接发到主站
######################################
def post_ali():
    dest_shop = "yallasale-com"
    ori_shop = "yallavip-saudi"

    sync_shop(ori_shop)
    sync_shop(dest_shop)
    shop_obj = Shop.objects.get(shop_name=dest_shop)
    max_id = Shop.objects.get(shop_name=dest_shop).max_id

    print("max_id ", max_id)

    n = 1
    aliproducts = MyProductAli.objects.filter(listing=True,posted_mainshop=False)

    for aliproduct in aliproducts:
        vendor_no = aliproduct.url.partition(".html")[0].rpartition("/")[2]
        print("vendor_no", vendor_no)

        dest_product = ShopifyProduct.objects.filter(shop_name=dest_shop, vendor=vendor_no).first()

        if dest_product > 0:
            print("这个产品已经发布过了！！！！", vendor_no)
            MyProductAli.objects.filter(pk=aliproduct.pk).update(posted_mainshop=True,handle=dest_product.get("handle"),
                                                                 product_no=dest_product.get("product_no"), )
            continue

        ori_product = ShopifyProduct.objects.filter(shop_name=ori_shop, vendor=vendor_no).order_by('product_no').first()
        if not ori_product:
            print("这个产品还没发布到沙特站！！！！", vendor_no)
            MyProductAli.objects.filter(pk=aliproduct.pk).update(listing=False)
            continue

        posted = post_mainshop(ori_product, max_id+n, shop_obj)
        # 修改发布状态
        if not posted:
            print("创建新产品失败")
            MyProductAli.objects.filter(pk=aliproduct.pk).update(post_error=True)
            continue

        else:
            #shopify返回的产品结构里，id 对应product_no
            MyProductAli.objects.filter(pk=aliproduct.pk).update(posted_mainshop=True, handle=posted.get("handle"),
                                                                 product_no=posted.get("id"), )
            n = n + 1

    return

def update_cate():


    product_cates = ProductCategory.objects.values()

    cate_dict = {}
    cate_level_dict = {}
    for product_cate in product_cates:
        cate_dict[product_cate["cate_1"].lower()] = product_cate["cate_1"]
        cate_dict[product_cate["cate_2"].lower()] = product_cate["cate_2"]
        cate_dict[product_cate["cate_3"].lower()] = product_cate["cate_3"]

        cate_level_dict[product_cate["cate_1"].lower()] = 1
        cate_level_dict[product_cate["cate_2"].lower()] = 2
        cate_level_dict[product_cate["cate_3"].lower()] = 3

    queryset = ShopifyProduct.objects.filter(category_code="", shop_name = "yallasale-com")
    for product in queryset:
        cate_1 = ""
        cate_2 = ""
        cate_3 = ""
        category_code = ""
        tags = product.tags.lower().split(",")

        for tag_tmp in tags:
            #print("cate_dict", cate_dict)
            #print("cate_level_dict", cate_level_dict)
            print("tag_tmp", tag_tmp)
            tag_level = cate_level_dict.get(tag_tmp.strip())

            print("tag_tmp %s ------- cate_level %s"%(tag_tmp,tag_level))

            if tag_level is None:
                continue
            elif tag_level == 1:
                cate_1 = cate_dict.get(tag_tmp.strip(),"")
            elif tag_level == 2:
                cate_2 = cate_dict.get(tag_tmp.strip(),"")

            elif tag_level == 3:
                cate_3 = cate_dict.get(tag_tmp.strip(),"")



        if len(cate_1)>0  and len(cate_2)>0 and len(cate_3)>0:
            category_code = cate_1 + "_" + cate_2 + "_" + cate_3
        else:
            category_code = ""

        ShopifyProduct.objects.filter(product_no=product.product_no).update(
            category_code=category_code,
            cate_1=cate_1,
            cate_2=cate_2,
            cate_3=cate_3,

            )
        print("product %s 更新类目%s成功 "%(product.handle, category_code))

    return

#####################################
#########把单独找的1688链接直接发到主站，不经过沙特站
######################################
def post_ali_direct():
    from .ali import  list_ali_product
    dest_shop = "yallasale-com"
    #ori_shop = "yallavip-saudi"

    #sync_shop(ori_shop)
    sync_shop(dest_shop)
    shop_obj = Shop.objects.get(shop_name=dest_shop)
    max_id = Shop.objects.get(shop_name=dest_shop).max_id

    print("max_id ", max_id)

    n = 1
    aliproducts = MyProductAli.objects.filter(listing=True,posted_mainshop=False)

    for aliproduct in aliproducts:
        vendor_no = aliproduct.url.partition(".html")[0].rpartition("/")[2]
        print("vendor_no", vendor_no)

        dest_product = ShopifyProduct.objects.filter(shop_name=dest_shop, vendor=vendor_no).first()

        if dest_product :
            print("这个产品已经发布过了！！！！", vendor_no)
            MyProductAli.objects.filter(pk=aliproduct.pk).update(posted_mainshop=True,handle=dest_product.handle,
                                                                 product_no=dest_product.product_no )

            continue

        ##############
        ####发布到主站
        #############
        posted = list_ali_product(vendor_no, max_id+n, shop_obj)

        # 修改发布状态
        if not posted:
            print("创建新产品失败")
            MyProductAli.objects.filter(pk=aliproduct.pk).update(post_error=True)
            continue

        else:
            #shopify返回的产品结构里，id 对应product_no
            MyProductAli.objects.filter(pk=aliproduct.pk).update(posted_mainshop=True, handle=posted.get("handle"),
                                                                 product_no=posted.get("id"), )
            n = n + 1

    return
