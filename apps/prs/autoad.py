from celery import shared_task

@shared_task
#自动生成post
def auto_post():
    #选择需要推广的page
    pages = MyPage.objects.filter(is_published=True, active=True, promotable=True)

    #遍历每个page
    for page in pages:
        #从符合条件的相册里选一个相册


    #发post

    return

#自动生成互动ad
def engagement_ads():
    #选择需要推广的page

    #遍历每个page

    #更新post的insight

    #从符合条件的post里选一个post

    #发互动ad

    return


# 自动生成消息ad
def message_ads():
    # 选择需要推广的page

    # 遍历每个page

    # 发消息ad

    return

#为page_no创建一个广告图
def prepare_promote_image(page_no):
    from shop.photo_mark import lightin_mark_image_page
    import random
    import requests
    import base64
    import time
    from django.db.models import Count


    # 取库存大、单价高、已经发布到相册 且还未打广告的商品
    lightinalbums_all = LightinAlbum.objects.filter(yallavip_album__isnull=False, yallavip_album__page__page_no=page_no,
                                            lightin_spu__sellable__gt=0, lightin_spu__SPU__istartswith = "s",
                                            lightin_spu__shopify_price__gt=50,lightin_spu__shopify_price__lte=100,
                                            lightin_spu__aded=False,
                                            published=True)

    # 从符合条件的相册里随机抽取一个相册生成广告图片，如果有尺码，就把尺码加在图片下面
    yallavip_albums = lightinalbums_all.values("yallavip_album").annotate(spu_count = Count(id)).filter(spu_count__gte=4)
    yallavip_album = random.choice(yallavip_albums)

    if yallavip_album:
        lightinalbums = lightinalbums_all.filter(yallavip_album__pk=yallavip_album_pk).order_by(
            "lightin_spu__sellable")[:4]
        prepare_promote_image_album(yallavip_album.get("yallavip_album"), lightinalbums)
    else:
        print("没有符合条件的相册了", page_no)

def prepare_promote_image_album(yallavip_album_pk, lightinalbums):
    from prs.fb_action import combo_ad_image

    #从库存多的开始推
    yallavip_album_instance = YallavipAlbum.objects.get(pk=yallavip_album_pk)
    print ("正在处理相册 ", yallavip_album_instance.album.name)

    spu_ims = lightinalbums.values_list("image_marked", flat=True)
    spus = lightinalbums.values_list("lightin_spu__handle", flat=True)

    # 把spus的图拼成一张

    spus_name = ','.join(spus)

    image_marked_url = combo_ad_image(spu_ims, spus_name, yallavip_album_instance.album.name)
    if not image_marked_url:
        print("没有生成广告图片")
        return
    message = "💋💋Flash Sale ！！！💋💋" \
              "90% off！Lowest Price Online ！！！" \
              "🥳🥳🥳 10:00-22:00 Everyday ,Update 100 New items Every Hour !! The quantity is limited !!😇😇" \
              "All goods are in Riyadh stock,It will be delivered to you in 3-5 days! ❣️❣️" \
              "How to order?Pls choice the product that you like it , then send us the picture, we will order it for you!🤩🤩"
    message = message + "\n" + spus_name

    obj, created = YallavipAd.objects.update_or_create(yallavip_album=yallavip_album_instance,
                                                       spus_name=spus_name,
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