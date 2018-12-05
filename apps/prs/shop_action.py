from .models import *
from shop.models import  Shop, ShopifyProduct, ShopifyVariant, ShopifyImage, ShopifyOptions


from orders.models import Order

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

#插入shopify产品记录到系统数据库
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
            created_at=row["created_at"].split('+')[0],

            updated_at=row["updated_at"].split('+')[0],
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
                    created_at=variant_row["created_at"].split('+')[0],
                    updated_at=variant_row["updated_at"].split('+')[0],
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
                    created_at=image_row["created_at"].split('+')[0],
                    updated_at=image_row["updated_at"].split('+')[0],
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