# Create your tasks here
from __future__ import absolute_import, unicode_literals
import numpy as np, re
from celery import shared_task,task
from django.db.models import Q,Count
import requests
import json
import random
from django.utils import timezone as datetime



from .models import *
from shop.models import  Shop, ShopifyProduct, ShopifyVariant, ShopifyImage, ShopifyOptions
from shop.models import ProductCategoryMypage
from fb.models import MyPage
from .shop_action import sync_shop
from orders.models import Order, OrderDetail


my_app_id = "562741177444068"
my_app_secret = "e6df363351fb5ce4b7f0080adad08a4d"
my_access_token = "EAAHZCz2P7ZAuQBABHO6LywLswkIwvScVqBP2eF5CrUt4wErhesp8fJUQVqRli9MxspKRYYA4JVihu7s5TL3LfyA0ZACBaKZAfZCMoFDx7Tc57DLWj38uwTopJH4aeDpLdYoEF4JVXHf5Ei06p7soWmpih8BBzadiPUAEM8Fw4DuW5q8ZAkSc07PrAX4pGZA4zbSU70ZCqLZAMTQZDZD"
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
@shared_task
def product_feed():
    from .fb_action import post_product_feed

    post_product_feed()

    return




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

    aliproducts = AliProduct.objects.filter(published=False)
    print("一共有%d 个1688产品信息待发布" % (aliproducts.count()))
    for aliproduct in aliproducts:
        post_to_shopify.delay(aliproduct.pk)

@task
def post_to_shopify(aliproduct_pk, ):
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

            # 根据品类找已经上架到shopify 但还未添加到fb接触点（新）的产品
            products_to_add = AliProduct.objects.raw('SELECT * FROM prs_aliproduct  A WHERE '
                                                         'cate_code = %s and created = TRUE  '  
                                                         'and id  NOT  IN  ( SELECT  B.myaliproduct_id FROM prs_myfbproduct B where mypage_id=%s and B.myaliproduct_id is not NULL) order by rand() limit 30',[cate_code,page.pk], )
            print("products_to_add", page, cate_code, len(products_to_add))

            myfbproduct_list = []
            for product_to_add in products_to_add:
                #n += 1
                #print("     %d is %s" % (n, product_to_add))

                myfbproduct = MyFbProduct(
                    myaliproduct=AliProduct.objects.get(pk=product_to_add.pk),
                    myproduct=ShopifyProduct.objects.filter(vendor=product_to_add.offer_id).first(),
                    mypage=MyPage.objects.get(pk=page.pk),
                    obj_type="PHOTO",
                    cate_code = cate_code,
                    album_name = album_name,



                )
#                print(myfbproduct, AliProduct.objects.get(pk=product_to_add.pk),MyPage.objects.get(pk=page.pk),cate_code,album_name, )
                myfbproduct_list.append(myfbproduct)


            print(myfbproduct_list)
            MyFbProduct.objects.bulk_create(myfbproduct_list)


#4,1 将shopify产品发布到相册
#发布产品到Facebook的album
@shared_task
def post_newproduct_album():
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

        print("主页已有相册", album_dict)


        #print("当前主页已有相册", album_dict)

        albums = MyFbProduct.objects.filter(mypage__pk=mypage.pk, published=False,myaliproduct__handle__startswith='b') \
            .values_list('album_name').annotate(product_count=Count('id')).order_by('-product_count')

        print("当前主页待处理产品相册", albums)


        album_list =[]
        for album in albums:

            if album[1]>0 and len(album[0])>3:
                    album_list.append(album[0])

            else:
                print("相册名为空或者没有产品要发布了")
                continue

        print("当前主页可处理产品相册", album_list)

        if len(album_list) == 0:
            print("没有相册需要处理了")
            continue


        album_name = random.choice(album_list)
        print("这次要处理的相册", album_name)

        products = MyFbProduct.objects.filter(mypage__pk=mypage.pk, published=False, album_name=album_name,
                                              myaliproduct__handle__startswith='b').order_by("-id")
        print("###############这次需要发的产品", products.count(), products.query)
        if products is None or products.count()==0:
            print("没有产品可发布了")
            continue

        # 是否已经建了相册

        target_album_no = album_dict.get(album_name)



        if not target_album_no :
            print("此相册还没有创建，请新建一个")
            continue




        # 发到指定相册

        n = 0
        for product in products:
            myproduct = product.myaliproduct

            error, posted = post_photo_to_album(mypage, target_album_no, myproduct)


            if posted is not None:
                MyFbProduct.objects.filter(mypage__pk=mypage.pk ,myaliproduct__pk=product.myaliproduct.pk).update(
                    myproduct= myproduct,
                    fb_id = posted,
                    published = True,
                    published_time = datetime.now()
                )
                print("发布新产品到相册成功 page_pk %s  product_pk %s   photo_id   %s" % (mypage.pk, myproduct.pk, posted))
                #print("created is ", created)
                #print("obj is ", obj)
                n += 1
                if n>5:
                    break
            else:
                MyFbProduct.objects.filter(mypage__pk=mypage.pk ,myaliproduct__pk=product.myaliproduct.pk).update(
                    myproduct=myproduct,
                    published=False,
                    publish_error=error,
                    published_time=datetime.now()
                )

    return


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
    from .fb_action import post_product_feed

    post_product_feed()

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












