from prs.fb_action import  get_token
from facebook_business.api import FacebookAdsApi
from facebook_business.adobjects.page import Page

from celery import shared_task

from django.utils import timezone as dt
from django.db.models import Q
import  json

from fb.models import MyPage, MyAlbum
from prs.models import *

from shop.photo_mark import yallavip_mark_image
from prs.fb_action import combo_ad_image_template_single, combo_ad_image_v3
from prs.common import *

import random

#根据page cate 规则，更新page的相册
#将page中失效的相册找出来并删掉
#未创建的则创建之

def create_album(page,cate, standard_size = "" ):

    page_no = page.page_no
    if cate.cate_type == "Product":
        if standard_size == "":
            #album_name = "%s %s" % (cate.super_name ,cate.name)
            album_name = cate.name
        else:
            album_name = "%s [%s]" % (cate.name,  standard_size)
    else:
        album_name = cate.name

    access_token, long_token = get_token(page_no)
    FacebookAdsApi.init(access_token=access_token, debug=True)

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
        YallavipAlbum.objects.create(
            page=page,
            cate=cate,
            standard_size=standard_size,
            album=obj,
            published=True,
            publish_error="",
            published_time=dt.now(),
            active=True
        )



        return  obj
    else:
        return  None

#根据page cate 创建相册
'''
def sync_cate_album(page_no=None):

    # 找出所有活跃的page
    pages = MyPage.objects.filter(is_published=True, active=True, promotable=True)
    if page_no:
        pages = pages.filter(page_no=page_no)

    for page in pages:

        print("page is ", page)
        yallvip_album = YallavipAlbum.objects.filter(page__pk=page.pk)
        #先全部设置成 active=False
        if yallvip_album:
            yallvip_album.update(active=False)

        # 一次处理一个cate
        cates  = PagePromoteCate.objects.get(mypage__pk=page.pk).cate.all().distinct()

        for cate in cates:
            #cate_sizes = cate.cate_size.all().distinct()
            cate_sizes = False
            #有尺码和无尺码的要分开处理
            if cate_sizes:
                # 相册已经有了的，就设为active=True
                yallvip_album.filter(catesize__in=cate_sizes).update(active=True)

                #相册里没有的，要创建

                catesize_to_add = cate_sizes.exclude(id__in = yallvip_album.filter(catesize__isnull=False).values_list("catesize__pk",flat=True)).distinct()
                # 根据规则创建相册，成功后记录到数据库里

                for catesize in catesize_to_add:
                    new_album = create_album(page.page_no, catesize.cate.name+ " "+ catesize.size)
                    YallavipAlbum.objects.create(
                        page=page,
                        cate=cate,
                        catesize=catesize,
                        album=new_album,
                        published=True,
                        publish_error="",
                        published_time=dt.now(),
                        active=True
                    )



            else:
                # 相册已经有了，置为active，否则要创建
                cate_album = yallvip_album.filter(cate = cate)
                if cate_album:
                    cate_album.update(active=True)
                else:
                    print (cate.name)
                    new_album = create_album(page.page_no, cate.name)
                    YallavipAlbum.objects.create(
                        page=page,
                        cate=cate,
                        #catesize=None,
                        album=new_album,
                        published=True,
                        publish_error="",
                        published_time=dt.now(),
                        active=True
                    )


#根据yallavip_album相册规则，生成相册图片记录
#这里只处理根据品类创建相册的情况
def prepare_yallavip_photoes(page_no=None):


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

            if album.cate:
                cate_name =  album.cate.tags

            elif album.catesize:
                cate_name = album.catesize.cate.tags

            q_cate.children.append(('breadcrumb__contains', cate_name))

            q_attr = Q()
            q_attr.connector = 'OR'
            if album.catesize:
                q_attr.children.append(('spu_sku__skuattr__contains',  album.catesize.size))

            con = Q()
            con.add(q_cate, 'AND')
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

'''


#################################################################################################
#根据page cate 创建相册
#不分尺码
def sync_cate_album_v2(page_no=None):

    # 找出所有活跃的page
    pages = MyPage.objects.filter(is_published=True, active=True, promotable=True)
    if page_no:
        pages = pages.filter(page_no=page_no)

    for page in pages:

        print("page is ", page)
        yallvip_album = YallavipAlbum.objects.filter(page__pk=page.pk)
        #先全部设置成 active=False
        if yallvip_album:
            yallvip_album.update(active=False)

        # 一次处理一个cate
        cates  = PagePromoteCate.objects.get(mypage__pk=page.pk).cate.all().distinct()

        for cate in cates:
            # 相册已经有了，置为active，否则要创建

            if cate.one_size:
                cate_album = yallvip_album.filter(cate=cate)
                if cate_album:
                    cate_album.update(active=True)
                else:
                    print(cate.name)
                    create_album(page, cate )
                    #create_album(page.page_no, "%s %s" % (cate.super_name ,cate.name))

            else:
                standard_sizes = cate.cate_size.all()
                for standard_size in standard_sizes:
                    cate_album = yallvip_album.filter(cate=cate, standard_size=standard_size)
                    if cate_album:
                        cate_album.update(active=True)
                    else:
                        create_album(page,cate,standard_size)
                        #create_album(page.page_no, "%s %s [%s]" % (cate.super_name, cate.name, size), standard_size)






#根据yallavip_album相册规则，生成相册图片记录
#这里只处理根据品类创建相册的情况
#不分尺码，但是要根据库存数量和尺码数量来筛选商品发布
def prepare_yallavip_photoes_v2(page_no=None):


    # 找出所有活跃的page
    pages = MyPage.objects.filter(is_published=True, active=True, promotable=True)
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
            con = filter_product(album.cate, album.standard_size)


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
                products_to_add = Lightin_SPU.objects.filter(~Q(handle=""),vendor="funmart",sellable__gt=0).filter(con).exclude(id__in=
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


#根据yallavip_album相册规则，生成相册图片记录
#根据品类和尺码创建相册的情况
#分尺码，根据库存数量来筛选商品发布
def prepare_yallavip_photoes_v3(page_no=None):


    # 找出所有活跃的page
    pages = MyPage.objects.filter(is_published=True, active=True, promotable=True)
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
            con = filter_product(album.cate,album.standard_size,"album")

            # 根据品类找已经上架到shopify 但还未添加到相册的产品
            product_list = []

            if is_sku:
                skus_to_add = Lightin_SKU.objects.filter(con, listed=True, locked=True, imaged=True,o_sellable__gt=0).\
                    exclude(id__in = LightinAlbum.objects.filter(
                                            yallavip_album__pk=album.pk,
                                            lightin_sku__isnull=False).values_list('lightin_sku__id',flat=True)).distinct().order_by("?")

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
                if album.standard_size == "":
                    products_to_add = Lightin_SPU.objects.filter(~Q(handle=""),vendor="funmart",sellable__gt=0)\
                        .filter(con)\
                        .exclude(id__in=
                                        LightinAlbum.objects.filter(
                                            yallavip_album__pk=album.pk,
                                            lightin_spu__isnull=False).values_list(
                                            'lightin_spu__id',
                                            flat=True))\
                        .values_list('id', 'title').distinct()
                else:
                    products_to_add = Lightin_SKU.objects.filter(~Q(lightin_spu__handle=""),lightin_spu__vendor="funmart",o_sellable__gt=0)\
                        .filter(con)\
                        .exclude(lightin_spu__id__in=
                                                    LightinAlbum.objects.filter(
                                                        yallavip_album__pk=album.pk,
                                                        lightin_spu__isnull=False).values_list(
                                                        'lightin_spu__id',
                                                        ))\
                        .values_list('lightin_spu__id', 'lightin_spu__title').distinct()


                for product_to_add in products_to_add:
                    obj, created = LightinAlbum.objects.update_or_create(lightin_spu_id=product_to_add[0],
                                                                         yallavip_album=album,
                                                                   defaults={'name': product_to_add[1]

                                                                             }
                                                                   )

def prepare_yallavip_album_material(page_no=None):
    from django.db.models import Max


   #每次每个相册处理最多100张图片

    lightinalbums_all = LightinAlbum.objects.filter( published=False, publish_error="无", material=False,
                                                    material_error="无",lightin_spu__sellable__gt=0,

                                                    yallavip_album__isnull = False,yallavip_album__active = True

                                                    )
    if page_no:
        lightinalbums_all = lightinalbums_all.filter(yallavip_album__page__page_no=page_no)


    albums_list = lightinalbums_all.values_list('yallavip_album', flat=True).distinct()
    print("albums_list is ", albums_list)

    for album in albums_list:
        #lightinalbums = lightinalbums_all.filter(yallavip_album=album).order_by("lightin_spu__sellable")[:100]
        lightinalbums = lightinalbums_all.filter(yallavip_album=album).order_by("?")[:100]
        print(lightinalbums)

        for lightinalbum in lightinalbums:
            prepare_a_album_v2.apply_async((lightinalbum.pk,), queue='photo')

#为促销做准备商品
#相册和主推品类结合选品，打广告

def prepare_promote_v2(page_no, free_shipping=True):


    from django.db.models import Count


    # 取page对应的主推品类
    try:
        cates = PagePromoteCate.objects.get(mypage__page_no=page_no).promote_cate.all()
    except:

        print ("没有促销品类")
        return

    # 取库存大、单价高、已经发布到相册 且还未打广告，单件包邮的商品
    spus_all = Lightin_SPU.objects.filter(~Q(handle=""),handle__isnull=False,vendor="lightin", aded=False,sellable__gt=5, free_shipping=free_shipping)
    # 把主推品类的所有适合的产品都拿出来打广告

    for cate in cates:
        con = filter_product(cate)
        cate_spus = spus_all.filter(con).distinct().order_by("?")

        # 每次最多20个
        if cate_spus.count() > 20:
            count = 10
        else:
            count = int(cate_spus.count() / 2)
        print (cate, "一共有%s个广告可以准备" % (count))
        cate_spus = list(cate_spus[:count*2])

        for i in range(int(count)):

            #spu_pks = [cate_spus[i*2].pk, cate_spus[i*2+1].pk]
            spus = [cate_spus[i * 2], cate_spus[i * 2 + 1]]
            print("当前处理 ", i, cate.tags, page_no, cate_spus[i*2].handle,cate_spus[i*2+1].handle)
            #prepare_promote_image_album_v3(cate.tags, page_no, spu_pks)
            prepare_promote_image_album_v4(cate, page_no, spus,free_shipping)

def init_cate_sellable():

    cates = MyCategory.objects.all()

    for cate in cates:
        if cate.cate_size.all():
            cate.sellable=10
            cate.save()

def init_spu_one_size():
    from prs.models import Lightin_SKU,Lightin_SPU
    skus = Lightin_SKU.objects.filter(lightin_spu__vendor="lightin")

    q_size = Q()
    q_size.connector = 'OR'
    q_size.children.append(('skuattr__icontains', "Free size"))
    q_size.children.append(('skuattr__icontains', "One-Size"))
    q_size.children.append(('skuattr__icontains', "One Size"))

    q_nosize = ~Q()
    q_nosize.connector = 'OR'
    q_nosize.children.append(('skuattr__icontains', "size"))

    con = Q()
    con.add(q_size, 'OR')
    con.add(q_nosize, 'OR')

    spus = skus.filter(con).values_list("lightin_spu",flat=True).distinct()

    Lightin_SPU.objects.filter(pk__in=list(spus)).update(one_size=True)

# 根据 MyCategory 拼接筛选产品的条件
#如果没有尺码，则返回spu的过滤条件
#如果有尺码，则返回sku的过滤条件
def filter_product(cate, standard_size="",type="album"):
    cate_3 = ["Activewear","Anklet","Bracelets","Casual Shoes","Clutches/Wallets","Creative Watches","Dresses","Flats","Jeans","Lingerie","Lips","Lovers Watches","Makeup Tools","Maxi Dresses","Men's Hoodies & Swea","Outerwear","Pajamas","Panties","Pants","Polo Shirts","Print Dresses","Pumps & Heels","Quartz Watches","Rings","Robes & Sleepwear","Romantic Lace Dresse","Sexy Bodies","Shirts","Shoulder Bags","Skin Care Tools","Skirts","Slippers","Sneakers","Sports Bra Collectio","Suits&Blazers","Teeth & Mouth Care","Two Pieces Suits","Women's Blazers & Ja","Women's Hats","Women's Jumpsuits &","Women's Tops","Women's Two Piece Se",]

    con = Q()
    con.connector = "AND"

    if cate.cate_type == "Product":
        q_cate = Q()
        q_cate.connector = 'OR'

        if standard_size == "":
            q_cate.children.append(('tags__contains', cate.tags))
        else:
            q_cate.children.append(('lightin_spu__tags__contains', cate.tags))

            q_size = Q()
            q_size.connector = 'OR'

            q_size.children.append(('size', standard_size))
            con.add(q_size, 'AND')

        con.add(q_cate, 'AND')

    elif cate.cate_type == "Promote":
        con.children.append(('promote_count', "M100-1"))

    if type == "promote":
        if standard_size == "":
            con.children.append(('cate_3__in', cate_3))
        else:
            con.children.append(('lightin_spu__cate_3__in', cate_3))

    return con

def get_promote_ads(page_no):
    from prs.models import YallavipAd
    from  prs.tasks import  delete_outstock_yallavipad

    # 取page对应的主推品类
    cates = PagePromoteCate.objects.filter(mypage__page_no=page_no).values_list("promote_cate", flat=True)
    if cates:
        cates = list(cates)
    else:
        return None, None
    delete_outstock_yallavipad()
    ads = YallavipAd.objects.filter(page_no=page_no, active=True,  cate__in=cates, )

    return ads, cates

#把page对应品类的sku全部设置包邮
def chang_page_free_delivery(page_no):
    from prs.tasks import update_promote_price

    albums = YallavipAlbum.objects.filter(page__page_no= page_no, active=True)
    for album in albums:


        spus = Lightin_SPU.objects.filter(breadcrumb__contains=album.cate.tags).distinct()
        print(album.cate, spus.count())

        for spu in spus:
            update_promote_price(spu, True)

def prepare_promote_singles(free_shipping_count, one_size):
    # 找出所有活跃的page
    pages = MyPage.objects.filter(is_published=True, active=True, promotable=True)
    if page_no:
        pages = pages.filter(page_no=page_no)

    for page in pages:
        prepare_promote_single(page.page_no, free_shipping_count, one_size)


def prepare_promote_single(page_no,free_shipping_count, one_size):
    import random

    from django.db.models import Count
    from prs.tasks import  prepare_promote_image_album_v3

    # 取page对应的主推品类
    try:
        cates = PagePromoteCate.objects.get(mypage__page_no=page_no).promote_cate.all()
    except:

        print ("没有促销品类")
        return

    # 取库存大、单价高、已经发布到相册 且还未打广告，不是仿牌，单件包邮的商品
    if one_size:
        spus_all = Lightin_SPU.objects.filter(~Q(handle=""),handle__isnull=False,fake=False,
                                          vendor="funmart", aded=False,sellable__gt=3,
                                          #yallavip_price__gte=30,yallavip_price__lte=100,
                                          images_count__gte=3,
                                          free_shipping_count=free_shipping_count, one_size=one_size)
    else:
        #有尺码的，要选主流尺码有库存的spu
        spus_list = Lightin_SKU.objects.filter(size__in=NORMAL_SIZE ,o_sellable__gt=3).values_list("lightin_spu",flat=True)
        spus_all = Lightin_SPU.objects.filter(~Q(handle=""),handle__isnull=False,fake=False,
                                              pk__in=list(spus_list),
                                          vendor="funmart", aded=False,sellable__gt=3,
                                          images_count__gte=3,
                                          free_shipping_count=free_shipping_count)


    # 把主推品类的所有适合的产品都拿出来打广告

    for cate in cates:
        con = filter_product(cate)
        cate_spus = spus_all.filter(con).distinct().order_by("?")

        # 每次最多5个
        if cate_spus.count() > 5:
            count = 5
        else:
            count = cate_spus.count()
        print (cate, "一共有%s个广告可以准备" % (count))
        cate_spus = list(cate_spus[:count])

        for i in range(int(count)):

            spus = [cate_spus[i]]
            print("当前处理 ", i, cate.tags, page_no, cate_spus[i].handle)
            #prepare_promote_image_album_v3(cate.tags, page_no, spu_pks)
            prepare_promote_image_album_single(cate, page_no, spus, cate_spus[i].vendor, free_shipping_count)




def prepare_promote_image_album_single(cate, page_no, lightin_spus, vendor,free_shipping_count):

    print ("正在处理page ", cate, page_no, lightin_spus)
    target_page= MyPage.objects.get(page_no=page_no)
    spus=[]
    spu_ims = []
    handles = []
    for spu in lightin_spus:

        if spu.handle:
            handles.append(spu.handle)
        else:
            return False

        print("正在处理 handle ",spu.handle)
        images = json.loads(spu.images)

        if images and len(images) >= 3:
            for image in images:
                if vendor =="lightin":
                    a = "/"
                    image_split = image.split(a)

                    image_split[4] = '800x800'
                    spu_im = a.join(image_split)
                else:
                    spu_im=image

                spus.append(spu)
                spu_ims.append(spu_im)

        else:
            print("图片数量太少")
            return  False

    # 把spu的图和模版拼在一起

    handles_name = ','.join(handles)

    image_marked_url = combo_ad_image_template_single(spu_ims, handles_name, lightin_spus,page_no,"ad")
    #print( image_marked_url )

    if not image_marked_url:
        print("没有生成广告图片")
        return False
    '''
    message = "💋💋Flash Sale ！！！💋💋" \
              "90% off！Lowest Price Online ！！！" \
              "🥳🥳🥳 10:00-22:00 Everyday ,Update 100 New items Every Hour !! The quantity is limited !!😇😇" \
              "All goods are in Riyadh stock,It will be delivered to you in 3-5 days! ❣️❣️" \
              "How to order?Pls choice the product that you like it , then send us the picture, we will order it for you!🤩🤩"
    '''
    if free_shipping_count == "0":
        message = "💋💋Buy 100SAR get 1 more free gift ++all spot goods 💋💋\n" \
              "🥳🥳🥳Special Promotion big sale: “Buy 100SAR get 1 more free gift”!!! 🥳🥳🥳\n" \
              "It means now if you buy every 100 Sar, you can choose 1 more gift for free!!!! \n" \
              "All hot sale goods, limited quantity , all Riyadh warehouse spot, 3-5day deliver to your house!!!!❣️❣️\n" \
              "Don't wait, do it!!!!!🤩🤩"
    elif free_shipping_count == "1":
        message = "💋💋Buy 1 free Shipping + Buy 2 get 1 more free++all spot goods 💋💋\n" \
              "🥳🥳🥳Special Promotion big sale: “Buy 2 get 1 more free”!!! 🥳🥳🥳\n" \
              "It means now if you buy 2 of this type of items, you can choose any 1 more item of equal price or lower price for free!!!! \n" \
              "All hot sale goods, limited quantity , all Riyadh warehouse spot, 3-5day deliver to your house!!!!❣️❣️\n" \
              "Don't wait, do it!!!!!🤩🤩"
    elif free_shipping_count == "2":
        message = "💋💋Buy 2 free Shipping + Buy 3 get 1 more free++all spot goods 💋💋\n" \
              "🥳🥳🥳Special Promotion big sale: “Buy 3 get 1 more free”!!! 🥳🥳🥳\n" \
              "It means now if you buy 3 of this type of items, you can choose any 1 more item of equal price or lower price for free!!!! \n" \
              "All hot sale goods, limited quantity , all Riyadh warehouse spot, 3-5day deliver to your house!!!!❣️❣️\n" \
              "Don't wait, do it!!!!!🤩🤩"
    elif free_shipping_count == "3":
        message = "💋💋Buy 3 free Shipping + Buy 5 get 1 more free++all spot goods 💋💋\n" \
              "🥳🥳🥳Special Promotion big sale: “Buy 5 get 1 more free”!!! 🥳🥳🥳\n" \
              "It means now if you buy 5 of this type of items, you can choose any 1 more item of equal price or lower price for free!!!! \n" \
              "All hot sale goods, limited quantity , all Riyadh warehouse spot, 3-5day deliver to your house!!!!❣️❣️\n" \
              "Don't wait, do it!!!!!🤩🤩"
    elif free_shipping_count == "5":
        message = "💋💋Buy 5 free Shipping + Buy 8 get 2 more free++all spot goods 💋💋\n" \
              "🥳🥳🥳Special Promotion big sale: “Buy 8 get 2 more free”!!! 🥳🥳🥳\n" \
              "It means now if you buy 8 of this type of items, you can choose any 2 more item of equal price or lower price for free!!!! \n" \
              "All hot sale goods, limited quantity , all Riyadh warehouse spot, 3-5day deliver to your house!!!!❣️❣️\n" \
              "Don't wait, do it!!!!!🤩🤩"



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

        spu.aded = True
        spu.save()

    return  True



def prepare_promote_image_album_v4(cate, page_no, lightin_spus,freeshipping):
    from prs.fb_action import combo_ad_image_v4


    print ("正在处理page ", cate, page_no, lightin_spus)
    target_page= MyPage.objects.get(page_no=page_no)
    spus=[]
    spu_ims = []
    handles = []
    for spu in lightin_spus:
        #spu = Lightin_SPU.objects.get(pk=spu_pk)
        print("正在处理 handle ",spu.handle)
        image = json.loads(spu.images)
        if image and len(image) > 0:
            a = "/"
            image_split = list(image)[0].split(a)

            image_split[4] = '800x800'
            spu_im = a.join(image_split)
        else:
            spu_im = None

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

    image_marked_url = combo_ad_image_v4(spu_ims, handles_name, lightin_spus, page_no)
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






#生成单主图的多图
@shared_task
def prepare_a_album_v2(lightinalbum_pk):


    ori_lightinalbum = LightinAlbum.objects.get(pk=lightinalbum_pk)
    page_no = ori_lightinalbum.yallavip_album.page.page_no

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
        '''
        if spu.free_shipping:
            price1 = int(spu.free_shipping_price)
        else:
            price1 = int(spu.yallavip_price)
        '''
        price1 =  int(spu.yallavip_price)

        price2 = int(price1 * random.uniform(5, 6))
        # 为了减少促销的麻烦，文案里不写价格了
        # name = name + "\n\nPrice:  " + str(price1) + "SAR"

        # 准备图片
        # 如果图片大于等于3张，就生成多图拼图，否则就发第一张
        if spu.images:
            spu_ims = json.loads(spu.images)
            if spu_ims :
                if len(spu_ims) >0 :
                    handles_name = spu.handle


                    image_marked_url = combo_ad_image_v3(spu_ims, handles_name, spu, page_no,"album")

                #else:



                    # 打水印
                    # logo， page促销标
                    # 如果有相册促销标，就打相册促销标，否则打价格标签

                    #image_marked, image_pure_url, image_marked_url = yallavip_mark_image(spu_ims[0], spu.handle, str(price1), str(price2),
                     #                                                    lightinalbum.yallavip_album.page, spu.free_shipping)
                else:
                    image_marked_url=None

                if not image_marked_url:
                    error = "打水印失败"

        else:
            print(album, spu.SPU, "没有图片")
            error = "没有图片"

        print("打水印",lightinalbum.pk, error)
        if error == "":
            LightinAlbum.objects.filter(pk=lightinalbum.pk).update(
                name=name,
                #image_pure=image_pure_url,
                image_marked=image_marked_url,

                # batch_no=batch_no,
                material=True
            )
        else:
            LightinAlbum.objects.filter(pk=lightinalbum.pk).update(
                material_error=error
            )

#重置page的所有产品
def reset_yallavip_album_ad(page_no):
    spus = LightinAlbum.objects.filter(yallavip_album__page__page_no=page_no).values_list("lightin_spu",flat=True)
    Lightin_SPU.objects.filter(pk__in = list(spus)).update(aded=False)



def prepare_promote_image_album(cate, page_no, lightin_spus, vendor,free_shipping_count, single=True):

    print ("正在处理page ", cate, page_no, lightin_spus)
    target_page= MyPage.objects.get(page_no=page_no)
    spus=[]
    spu_ims = []
    handles = []
    for spu in lightin_spus:

        if spu.handle:
            handles.append(spu.handle)
        else:
            return False

        print("正在处理 handle ",spu.handle)
        images = json.loads(spu.images)

        if images and len(images) >= 3:
            for image in images:
                if vendor =="lightin":
                    a = "/"
                    image_split = image.split(a)

                    image_split[4] = '800x800'
                    spu_im = a.join(image_split)
                else:
                    spu_im=image

                spus.append(spu)
                spu_ims.append(spu_im)

        else:
            print("图片数量太少")
            return  False

    # 把spu的图和模版拼在一起

    handles_name = ','.join(handles)

    image_marked_url = combo_ad_image_template_single(spu_ims, handles_name, lightin_spus,page_no,"ad")
    #print( image_marked_url )

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
    if free_shipping_count == "0":
        message = "💋💋Buy 100SAR get 1 more free gift ++all spot goods 💋💋\n" \
              "🥳🥳🥳Special Promotion big sale: “Buy 100SAR get 1 more free gift”!!! 🥳🥳🥳\n" \
              "It means now if you buy every 100 Sar, you can choose 1 more gift for free!!!! \n" \
              "All hot sale goods, limited quantity , all Riyadh warehouse spot, 3-5day deliver to your house!!!!❣️❣️\n" \
              "Don't wait, do it!!!!!🤩🤩"
    elif free_shipping_count == "1":
        message = "💋💋Buy 1 free Shipping + Buy 2 get 1 more free++all spot goods 💋💋\n" \
              "🥳🥳🥳Special Promotion big sale: “Buy 2 get 1 more free”!!! 🥳🥳🥳\n" \
              "It means now if you buy 2 of this type of items, you can choose any 1 more item of equal price or lower price for free!!!! \n" \
              "All hot sale goods, limited quantity , all Riyadh warehouse spot, 3-5day deliver to your house!!!!❣️❣️\n" \
              "Don't wait, do it!!!!!🤩🤩"
    elif free_shipping_count == "2":
        message = "💋💋Buy 2 free Shipping + Buy 3 get 1 more free++all spot goods 💋💋\n" \
              "🥳🥳🥳Special Promotion big sale: “Buy 3 get 1 more free”!!! 🥳🥳🥳\n" \
              "It means now if you buy 3 of this type of items, you can choose any 1 more item of equal price or lower price for free!!!! \n" \
              "All hot sale goods, limited quantity , all Riyadh warehouse spot, 3-5day deliver to your house!!!!❣️❣️\n" \
              "Don't wait, do it!!!!!🤩🤩"
    elif free_shipping_count == "3":
        message = "💋💋Buy 3 free Shipping + Buy 5 get 1 more free++all spot goods 💋💋\n" \
              "🥳🥳🥳Special Promotion big sale: “Buy 5 get 1 more free”!!! 🥳🥳🥳\n" \
              "It means now if you buy 5 of this type of items, you can choose any 1 more item of equal price or lower price for free!!!! \n" \
              "All hot sale goods, limited quantity , all Riyadh warehouse spot, 3-5day deliver to your house!!!!❣️❣️\n" \
              "Don't wait, do it!!!!!🤩🤩"
    elif free_shipping_count == "5":
        message = "💋💋Buy 5 free Shipping + Buy 8 get 2 more free++all spot goods 💋💋\n" \
              "🥳🥳🥳Special Promotion big sale: “Buy 8 get 2 more free”!!! 🥳🥳🥳\n" \
              "It means now if you buy 8 of this type of items, you can choose any 2 more item of equal price or lower price for free!!!! \n" \
              "All hot sale goods, limited quantity , all Riyadh warehouse spot, 3-5day deliver to your house!!!!❣️❣️\n" \
              "Don't wait, do it!!!!!🤩🤩"



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

        spu.aded = True
        spu.save()



#0722新的广告系统
#每个page的主推品类每次生成一个广告
def prepare_promote_single_v2(page_no):
    import random

    from django.db.models import Count
    from prs.tasks import  prepare_promote_image_album_v3

    # 取page对应的主推品类
    try:
        cates = PagePromoteCate.objects.get(mypage__page_no=page_no).promote_cate.all()
    except:

        print ("没有促销品类")
        return

    for cate in cates:
        con = filter_product(cate)
        spus_all = Lightin_SPU.objects.filter(~Q(handle=""), handle__isnull=False, fake=False,
                                              vendor="funmart", aded=False,
                                              images_count__gte=3, free_shipping_count__in=["1", "2", "3"],sellable__gt=3)

        cate_spus = spus_all.filter(con).distinct().order_by("?")
        if cate_spus.count() == 0:
            print("############没有可投放的广告了###########", cate, con)
        for spu in cate_spus:
            print("当前处理 ", page_no, cate.tags, spu.handle)
            if spu.one_size:
                if spu.sellable < 3:
                    continue
            else:
                sizes = []
                if spu.cate_2 == "Clothing":
                    sizes = ["M","L"]
                elif spu.cate_2 == "Shoes":
                    if spu.cate_1 == "Women":
                        sizes = ["37","38","39"]
                    elif spu.cate_1 == "Men":
                        sizes = ["42","43","44"]
                sellable = spu.spu_sku.filter(size__in=sizes).aggregate(sum_sellable=Sum("o_sellable"))
                if sellable <= 3:
                    continue
            print("可以投放！！！")
            spus = [spu]
            ret = prepare_promote_image_album_single(cate, page_no, spus, spu.vendor, spu.free_shipping_count)
            if ret:
                break
            else:
                continue

