from shop.models import  Shop, ShopifyProduct, ShopifyVariant, ShopifyImage, ShopifyOptions
import requests
import json

#同步shopify信息到系统数据库
def sync_shop(shop):

    #获取店铺信息
    shop_obj = Shop.objects.get(shop_name=shop)
    shop_url = "https://%s:%s@%s.myshopify.com" % (shop_obj.apikey, shop_obj.password, shop_obj.shop_name)

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