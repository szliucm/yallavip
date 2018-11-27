# Create your tasks here
from __future__ import absolute_import, unicode_literals
import numpy as np, re
from celery import shared_task



from .photo_mark import  photo_mark
from shop.models import ProductCategory,ProductCategoryMypage
from fb.models import  MyPage,MyAlbum,MyPhoto
from .models import *
from .shop_action import  *
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
            print("data is ", data)
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
            print("data is ", data)
            continue

        print("new_product_no is", new_product.get("id"))
        total_to_update = total_to_update - 1
        print("沙特站最新的还有 %d 需要发布" % (total_to_update))

        product_list = []
        product_list.append(new_product)

        insert_product(dest_shop, product_list)



        # shopify.ShopifyResource.clear_session()


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
        posted = 0

        # 主页已有的相册
        album_dict = {}
        albums = MyAlbum.objects.filter(page_no=mypage.page_no)
        for album in albums:
            album_dict[album.name] = album.album_no

        print("主页已有相册", album_dict)

        categories = mypage.category_page.all()
        for category in categories:
            print("当前处理的类目 %s"%( category))

            #找出每个品类下未发布的产品， 每次只发一张
            product = ShopifyProduct.objects.filter(category_code = category.productcategory.code,product_no__gt= category.last_no ).\
                                                order_by("product_no").first()
            if product is None:
                print("当前类目没有产品了，跳出")
                continue

            #这个品类是否已经建了相册
            category_album = category.productcategory.album_name
            target_album = album_dict.get(category_album)

            print("品类需要的相册 %s, 已有相册 %s"%(category_album, target_album))

            if target_album is None:
                print("此类目还没有相册，新建一个")
                album_list = []
                album_list.append(category_album)

                target_album = create_new_album(mypage.page_no, album_list)[0]

            print("target_album %s" % (target_album))

            posted = posted + post_photo_to_album(mypage, target_album, product)


            obj, created = ProductCategoryMypage.objects.update_or_create(
                mypage=mypage, productcategory=category.productcategory,
                defaults={
                     'last_no': product.product_no
                },

            )
            print("更新page_类目记录 %s %s %s" % (mypage, category.productcategory, product.product_no))
            print("created is ", created)
            print("obj is ", obj)




    return

