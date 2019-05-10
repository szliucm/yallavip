from prs.fb_action import  get_token
from facebook_business.api import FacebookAdsApi
from facebook_business.adobjects.page import Page

from celery import shared_task

from django.utils import timezone as dt
from django.db.models import Q

from fb.models import MyPage, MyAlbum
from prs.models import YallavipAlbum,PagePromoteCate,Lightin_SPU,LightinAlbum

from shop.photo_mark import yallavip_mark_image

#根据page cate 规则，更新page的相册
#将page中失效的相册找出来并删掉
#未创建的则创建之

def create_album(page_no , album_name ):
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




    return  obj

#根据page cate 创建相册
def sync_cate_album(page_no=None):

    # 找出所有活跃的page
    pages = MyPage.objects.filter(active=True)
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
            cate_sizes = cate.cate_size.all().distinct()
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
                        catesize=None,
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

def prepare_yallavip_album_material(page_no=None):
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
        #lightinalbums = lightinalbums_all.filter(yallavip_album=album).order_by("lightin_spu__sellable")[:100]
        lightinalbums = lightinalbums_all.filter(yallavip_album=album).order_by("lightin_spu__sellable")
        print(lightinalbums)

        for lightinalbum in lightinalbums:
            prepare_a_album.apply_async((lightinalbum.pk,), queue='photo')

@shared_task
def prepare_a_album(lightinalbum_pk):

    ori_lightinalbum = LightinAlbum.objects.get(pk=lightinalbum_pk)

    spu = lightinalbum.lightin_spu
    spu_pk = spu.pk
    print("正在处理spu", spu_pk)
    updated = update_promote_price(spu)

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
                                                                 lightinalbum.yallavip_album.page)
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
