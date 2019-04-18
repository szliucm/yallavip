from .models import MyProductShopify,MyProductFb,Token, LightinAlbum,Lightin_SPU,YallavipAd,YallavipAlbum
from fb.models import  MyPage,MyAlbum,MyPhoto,MyAdset
from shop.models import ShopifyProduct, ShopifyVariant,ShopifyOptions
from shop.models import  ShopifyImage
from .video import logo_video

from django.db.models import Max
from django.db.models import Q
import random
from django.utils import timezone as datetime

from django.utils.safestring import mark_safe
from facebook_business.api import FacebookAdsApi
from facebook_business.exceptions import FacebookRequestError


from facebook_business.adobjects.systemuser import SystemUser
from facebook_business.adobjects.page import Page
from facebook_business.adobjects.album import Album
from facebook_business.adobjects.photo import Photo
from facebook_business.adobjects.adaccount import AdAccount
from facebook_business.adobjects.campaign import Campaign
from facebook_business.adobjects.adset import AdSet
from facebook_business.adobjects.ad import Ad
from facebook_business.adobjects.adsinsights import AdsInsights

from django.utils import timezone as dt
import os
import requests
import json

from django.conf import settings


APP_SCOPED_SYSTEM_USER_ID=100029952330435
#aaron's
#my_access_token = "EAAcGAyHVbOEBAHRE4PAz3IGPW7O06aeccuYQSFrSo5KfVSKqWZAp1rj32pV7WNO42k2ppK480iExbH92DeIYodpHU38ZBwwRZAV1qYjCGdYa9pDNmdQOxm4q31n2XKVdjxKmOLDh7brq0tqVJZAk6kx9R4MJph0ZAxiD7CGuZCkMV3xFthPlim"

#another user
#my_access_token = "EAAcGAyHVbOEBAKgfka7uxoKnH3DnKcfuWZCnczE0bXCLaeiN2kY19woN24svib5TIlp3whXoV9ZCJF27UvZCmyoUZBwkVP6HlpWnfKX1eGyOd8FEzmJVjVZBhYRbgpEv1kNVbCRMJllYzVhOKs60N0yZBX9NXsEtpBvZCdXwTfObCzZAZAkCbqi6e8S0OvZASqrjhAlG627U2EggZDZD"
ad_tokens = "EAAHZCz2P7ZAuQBAI49YxZBpnxPjMKZCCu9SiRrgLlGuqQxytEHRzMWriEE1BArZBZAJe9pCVQS4EZBbnclPh8dPfu7Gc7lxSjXCcay7TJXiOOdyi4ZCc3AhijxZCDZCdIZCazziX3xOCT7D53xjDJVj8udnrfMjGUwQG8pE3oVwlaQKRvlYXL5h8FzH"
def get_token(target_page,token=None):

    pages = MyPage.objects.filter(page_no = target_page, active=True)
    if not pages:
        print ("page 不存在或者失活")
        return  None,None

    active_tokens = Token.objects.filter(active=True)
    # 先找page对应的token，如果没有可用的，就从还没有page占用的token里取一个
    my_access_tokens = active_tokens.filter(page_no=target_page)
    if not my_access_tokens:
        my_access_tokens = active_tokens.filter(page_no = "")

    for my_access_token in my_access_tokens:
        url = "https://graph.facebook.com/v3.2/{}?fields=access_token".format(target_page)
        param = dict()
        if token is None:
            param["access_token"] = my_access_token.long_token
        else:
            param["access_token"] = token

        r = requests.get(url, param)
        data = json.loads(r.text)
        #token可用，就要标识占用
        if r.status_code == 200:
            my_access_token.page_no = target_page
            my_access_token.save()
            return data["access_token"], my_access_token.long_token
        else:
            print(r, r.text)
            my_access_token.active = False
            my_access_token.save()
            continue

    return  None,None





def sycn_feed_product():
    products = MyProductShopify.objects.all()
    for product in products:



        handle = product.handle
        feeds = MyFeed.objects.filter(message__icontains=handle)



        for feed in feeds:
            print(feed)
            MyProductFb.objects.update_or_create(
                myfeed=feed, myproduct= product,
                defaults={
                    "mypage" : MyPage.objects.get(page_no =feed.page_no),
                    "obj_type": "FEED",
                    "published" : True,
                }
            )

    return

def sycn_ad_product():
    products = MyProductShopify.objects.all()
    for product in products:



        handle = product.handle
        ads = MyAd.objects.filter(name__icontains=handle)



        for ad in ads:
            print(ad)
            MyProductFb.objects.update_or_create(
                myad=ad, myproduct= product,
                defaults={
                    #"mypage" : MyPage.objects.get(page_no =ad.page_no),
                    "obj_type": "AD",
                    "published" : True,
                }
            )

    return

#####################################
#########把创意发到feed
######################################
def post_creative_feed():


    pages = MyPage.objects.filter(active=True,is_published=True)  # .values_list('page_no', flat=True)
    # page_nos = ["358078964734730"]   #for debug
    for page in pages:
        post_creative_feed_page(page)

    return


def post_creative_feed_page(page):

    from django.utils import timezone as datetime

    print("page is ", page.page)

    fbs = MyProductFb.objects.filter(published=False, obj_type='FEED', mypage__page_no=page.page_no, publish_error="").order_by( 'myresource__created_time')

    if not fbs:
        error = "no content to post "
        return error, None

    fb= fbs.first()

    error, feed_post_id = post_creative_feed_page_fb(page, fb)

    if feed_post_id is not None:
        MyProductFb.objects.filter(pk=fb.pk).update(fb_id=feed_post_id, published=True,
                                                        published_time=datetime.now())

        print("Wow ", page.page_no, feed_post_id)
        return "", feed_post_id
    else:

        MyProductFb.objects.filter(pk=fb.pk).update(fb_id="", published=False,
                                                    publish_error =error,
                                                        published_time=datetime.now())

        print("发布创意失败 ", page.page_no, error)

        return


def post_creative_feed_page_fb(page,fb):

    import filetype
    from shop.photo_mark import  photo_mark_url

    page_id = page.page_no

    access_token, long_token = get_token(page_id)
    if not access_token:
        error = "获取token失败"
        print("获取token失败", access_token,page_id)
        return error, None
    FacebookAdsApi.init(access_token=access_token)

    # domain = "http://dev.yallavip.com:8000"
    domain = "http://admin.yallavip.com"
    resource = str(fb.myresource.resource)
    local_resource = os.path.join(settings.MEDIA_ROOT, resource)
    kind = filetype.guess(local_resource)

    # 素材需要取相关信息，以便打标
    if fb.myresource.resource_type == "RAW":
        product = ShopifyProduct.objects.filter(handle=fb.myresource.handle).first()
        if product is None:
            error =  "找不到handle"
            return error, None

        max_price = ShopifyVariant.objects.filter(product_no=product.product_no).aggregate(Max("price")).get(
            "price__max")
        if max_price is None or max_price == 0:
            error = "取最大价格出错"
            return error, None

        price1 = int(max_price)
        price2 = int(price1 * random.uniform(2, 3))




    if kind.mime.find("video") >= 0:
        print("视频")

        if fb.myresource.resource_type == "RAW":

            result = logo_video(resource, page.logo, page.price, fb.myresource.handle, str(price1), str(price2),
                                no_logo=False)
            if not result:
                error = "视频失败"

                return error, None
            destination_url = domain + os.path.join(settings.MEDIA_URL, resource.rpartition(".")[0] + "_watermark.mp4")
        else:
            destination_url = domain + os.path.join(settings.MEDIA_URL, resource)

        fields = [
        ]
        params = {
            'title': fb.myresource.title,
            'description': fb.myresource.message,
            'file_url': destination_url,
            'published': 'true',
        }
        feed_post = Page(page_id).create_video(
            fields=fields,
            params=params,
        )


    elif kind.mime.find("image") >= 0:
        print("图片")
        image_url = domain + os.path.join(settings.MEDIA_URL, resource)
        # 发图片post
        if fb.myresource.resource_type == "RAW":
            # 素材需要打标，否则直接发
            print("#######",image_url, product, price1, price2, page)
            finale, destination_url = photo_mark_url(image_url, product.handle, str(price1), str(price2), page, type="album")

        else:
            destination_url = image_url

        fields = [
        ]
        params = {
            'url': destination_url,
            'published': 'false',
        }
        photo_to_be_post = Page(page_id).create_photo(
            fields=fields,
            params=params,
        )
        photo_to_be_post_id = photo_to_be_post.get_id()

        fields = [
            'object_id',
        ]
        params = {
            'message': fb.myresource.message,
            'attached_media': [{'media_fbid': photo_to_be_post_id}],
        }
        feed_post = Page(page_id).create_feed(
            fields=fields,
            params=params,
        )
    else:
        error = "未知文件"
        return error, None

    if feed_post:
        feed_post_id = feed_post.get_id()


        return "", feed_post_id
    else:
        return "Facebook创建feed失败", None

#####################################
#########把表现较好的product发到feed
#########每个page从产品排行榜里随机选一个产品，组成动图，发到feed里
######################################
def post_product_feed():
    from .video import fb_slideshow
    from shop.models import  ShopifyImage
    from shop.photo_mark import photo_mark

    pages = MyPage.objects.filter(active=True)      #.values_list('page_no', flat=True)
    #page_nos = ["358078964734730"]   #for debug
    for page in pages:
        page_no= page.page_no

        product = MyProductShopify.objects.order_by('?')[:1].first()

        images = ShopifyImage.objects.filter(product_no=product.product_no).order_by("position")

        images_count = len(images)
        if images_count<3:
            print("图片太少")
            print("result is ", page_no, product.handle, product.product_no)
            print(images)
            continue
        elif images_count>7:
            images = images[:7]

        #######################
            # 打标
            # name = product.title + "  [" + product.handle + "]"
            # options = ShopifyOptions.objects.filter(product_no=product.product_no).values()
            # for option in options:
            #   name = name + "\n\n   " + option.get("name") + " : " + option.get("values")

        max_price = ShopifyVariant.objects.filter(product_no=product.product_no).aggregate(Max("price")).get(
            "price__max")
        # name = name + "\n\nPrice:  " + str(int(max_price)) + "SAR"

        # 打标
        price1 = int(max_price)
        price2 = int(price1 * random.uniform(2, 3))

        dest_images =[]
        for ori_image in images:
            image, iamge_url = photo_mark(ori_image.src, product.handle, str(price1), str(price2), page, type="album")
            if not image:
                print("打水印失败")
                continue

            dest_images.append(iamge_url)

        post_id = fb_slideshow(list(dest_images), page_no)

        print("postid ", post_id)





    return

#####################################
#########从相册里挑一个product发到feed
#########每个page从相册里随机选一个产品，组成动图，发到feed里
######################################
def post_album_feed():
    from .video import fb_slideshow
    from shop.models import  ShopifyImage
    from shop.photo_mark import photo_mark_url

    pages = MyPage.objects.filter(active=True)      #.values_list('page_no', flat=True)
    #page_nos = ["358078964734730"]   #for debug
    for page in pages:
        page_no= page.page_no

        fbproduct = MyFbProduct.objects.filter(mypage__pk=page.pk,published=True).order_by('?')[:1].first()
        if fbproduct is None:
            print("没有fb产品", page)
            continue
        myaliproduct = fbproduct.myaliproduct
        if myaliproduct is None:
            print("没有产品", fbproduct)
            continue

        #images = ShopifyImage.objects.filter(product_no=myaliproduct.product_no).order_by("position")
        images = json.loads(myaliproduct.images)
        images_count = len(images)
        if images_count<3:
            print("图片太少")
            print("result is ", page_no, myaliproduct.handle, myaliproduct.product_no)
            print(images)
            continue
        elif images_count>7:
            images = images[:7]

        #######################
            # 打标
            # name = product.title + "  [" + product.handle + "]"
            # options = ShopifyOptions.objects.filter(product_no=product.product_no).values()
            # for option in options:
            #   name = name + "\n\n   " + option.get("name") + " : " + option.get("values")

        price_rate = myaliproduct.price_rate
        if price_rate == 0:
            price_rate = 3

        if myaliproduct.maxprice == 0:
            price_range = myaliproduct.price_range

            if len(price_range) > 0:

                if price_range.find("-") >= 0:
                    print("here", price_range)
                    maxprice = float(price_range.partition("-")[0]) * price_rate
                else:

                    maxprice = float(price_range) * price_rate
            else:
                error = "价格为0"
                return error, None
        else:
            maxprice = int(myaliproduct.maxprice * price_rate)

        # name = name + "\n\nPrice:  " + str(int(max_price)) + "SAR"

        # 打标
        price1 = int(maxprice)
        price2 = int(price1 * random.uniform(2, 3))

        dest_images =[]
        for ori_image in images:
            image, iamge_url = photo_mark_url(ori_image, myaliproduct.handle, str(price1), str(price2), page, type="album")
            if not image:
                print("打水印失败")
                continue

            dest_images.append(iamge_url)

        post_id = fb_slideshow(list(dest_images), page_no)

        print("postid ", post_id)





    return



#####################################
#########把海外仓包裹发到feed
#########每个sku对应的图片组成动图，发到feed里
######################################
def post_order_feed():
    from .video import get_order_image_src, fb_slideshow

    page_nos = MyPage.objects.filter(active=True).values_list('page_no', flat=True)

    for page_no in page_nos:
        images = get_order_image_src(order)
        fb_slideshow(images, page_no)

    return




def create_new_album(page_no , new_albums ):
    access_token, long_token = get_token(page_no)
    FacebookAdsApi.init(access_token=access_token)

    new_album_list = []
    #print("new_albums",new_albums )
    for new_album in new_albums:
        fields = ["created_time", "description", "id",
                  "name", "count", "updated_time", "link",
                  "likes.summary(true)", "comments.summary(true)"
                  ]
        params = {
                'name': new_album,
                'location': 'Riyadh Region, Saudi Arabia',
                #'privacy': 'everyone',
                #'place': '111953658894021',
                'message':"Yallavip's most fashion "+ new_album,

                    }
        album = Page(page_no).create_album(
                                fields=fields,
                                params=params,
                            )
        #插入到待返回的相册列表中
        if album:

            new_album_list.append(album.get("id"))
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



        #print("created albums ", album)
    return  new_album_list



'''
#之前的，从shopify中生成相册
def post_photo_to_album(targer_page,album_no,product ):
    from django.db.models import Max
    # 检查产品是否已经在相册中了，如果不存在，就发布新图片
    #myphotos = MyPhoto.objects.filter(name=product.handle , album_no=album_no )

    page_no = targer_page.page_no
    myphotos = MyPhoto.objects.filter(name__icontains=product.handle, album_no=album_no)
    #print("args is  %s %s %s"%(page_no,album_no , product.handle ))
    if myphotos:
        print("photo exist")
        return None
    else:
        print("now we need to create new photos for %s"%(product.handle))


    adobjects = FacebookAdsApi.init(my_app_id, my_app_secret, access_token=get_token(page_no), debug=True)


    #print("product.product_no ", product.product_no)
    ori_images = ShopifyImage.objects.filter(product_no=product.product_no).order_by('position')
    if not ori_images :

        print("no image %s"%(product.product_no))
        return None

    ori_image = random.choice(ori_images)

    #print("position is ", ori_image.position)



    name = product.title + "  [" + product.handle+"]"
    options = ShopifyOptions.objects.filter(product_no=product.product_no).values()
    for option in options:
        name = name + "\n\n   " + option.get("name") + " : " + option.get("values")

    max_price = ShopifyVariant.objects.filter(product_no=product.product_no).aggregate(Max("price")).get("price__max")
    name = name + "\n\nPrice:  " + str(int(max_price)) + "SAR"

    #打标

    price1 = int(max_price)


    price2 = int(price1 *  random.uniform(2, 3))

    image, iamge_url = photo_mark(ori_image ,product,str(price1), str(price2),  targer_page, type="album" )
    if not image:
        print("打水印失败")
        return None

    #print("after photo mark", iamge_url)

    fields = ["id","name","created_time", "updated_time","picture","link",
                      "likes.summary(true)","comments.summary(true)"
    ]
    params = {
        "published": "true",

        "url": iamge_url,
        "name": name,
        "qn":product.handle

    }
    photo = Album(album_no).create_photo(
        fields=fields,
        params=params,
    )

    obj, created = MyPhoto.objects.update_or_create(photo_no=photo["id"],
                                                    defaults={
                                                            'page_no': page_no,
                                                                'album_no': album_no,
                                                              "product_no": product.product_no,
                                                                'listing_status':True,
                                                              'created_time':
                                                                  photo["created_time"],#.split('+')[0],
                                                              'updated_time':
                                                                  photo["updated_time"],#.split('+')[0],

                                                              'name': photo.get("name"),
                                                              'picture': photo["picture"],
                                                              'link': photo["link"],
                                                              'like_count': photo["likes"]["summary"]["total_count"],
                                                              'comment_count': photo["comments"]["summary"][
                                                                  "total_count"]

                                                              }
                                                    )

    #print("new_photo saved ", obj, created)
    return  photo["id"]
'''

#直接从aliproduct发布到相册
def post_photo_to_album(targer_page,album_no,aliproduct ):
    from shop.photo_mark import photo_mark_image, get_remote_image
    from .ali import  fanyi
    #价格不正确，直接返回
    price_rate = aliproduct.price_rate
    if price_rate == 0:
        price_rate = 3

    if aliproduct.maxprice ==0:
        price_range = aliproduct.price_range

        if len(price_range) >0:

            if price_range.find("-") >= 0:
                print("here", price_range)
                maxprice = float(price_range.partition("-")[0]) * price_rate
            else:

                maxprice = float(price_range) * price_rate
        else:
            error = "价格为0"
            return  error,None
    else:
        maxprice = int(aliproduct.maxprice * price_rate)

    # 检查产品是否已经在相册中了，如果不存在，就发布新图片
    #myphotos = MyPhoto.objects.filter(name=product.handle , album_no=album_no )

    page_no = targer_page.page_no
    myphotos = MyPhoto.objects.filter(name__icontains=aliproduct.handle, album_no=album_no)
    #print("args is  %s %s %s"%(page_no,album_no , product.handle ))
    if myphotos:
        error = "图片已发布"
        return error, None
    else:
        print("now we need to create new photos for %s"%(aliproduct.handle))

    access_token, long_token = get_token(page_no)
    FacebookAdsApi.init(access_token=access_token)


    #print("product.product_no ", product.product_no)



    #print("position is ", ori_image.position)

    value_list = None
    value_name = None
    if len(aliproduct.title_zh) >0:
        handle_new = 'b' + str(aliproduct.pk).zfill(5)
        title = fanyi(aliproduct.title_zh)
        print(handle_new, aliproduct.title_zh, title)
        name = title + "  [" + handle_new + "]"
        print("######### name", name)

        for sku in json.loads(aliproduct.sku_info):
            if type(sku) == str:
                print("没有规格信息")
                break

            value_name = sku.get("label")

            print("###value_name", value_name)

            try:
                values = sku.get("values")

                if values is None:
                    continue
                print("#### values", values)
            except:
                continue

            value_list = []
            for value in values:
                desc_zh = value.get("desc")
                print("$$$$$$$$$$$ desc_zh", desc_zh)

                if desc_zh is not None:
                    desc = fanyi(desc_zh)
                    if desc in value_list:
                        desc = desc + "_" + str(len(value_list))

                    value_list.append(desc)
                    print("############ desc", value_list)
                else:
                    continue

            if value_list is not None and value_name is not None:
                name = name + "\n\n   " + fanyi(value_name) + " : " + ', '.join(value_list)
            else:
                error = str(sku) + "option 取信息出错"
                return error, None



    else:
        handle_new = aliproduct.handle
        title = aliproduct.title
        name = title + "  [" + handle_new + "]"

        alioptions = aliproduct.options
        if alioptions is None or len(alioptions) == 0:
            error = handle_new + "option 取信息出错"
            return error, None

        print(handle_new, alioptions)

        options = json.loads(alioptions)
        #print( options)
        for option in options:
            value_list = option.get("values")
            value_name = option.get("name")
            for i in range(value_list.count(None)):
                value_list.remove(None)



            if value_list is not None and value_name is not None:
                name = name + "\n\n   " + value_name + " : " + ', '.join(value_list)
            else:
                error = str(options) + "option 取信息出错"
                return error, None







    name = name + "\n\nPrice:  " + str(int(maxprice)) + "SAR"

    #打标

    price1 = int(maxprice)
    '''
    if price1 == 0:
        print("价格为0")
        return None
    '''

    price2 = int(price1 *  random.uniform(2, 3))



    ori_images = json.loads(aliproduct.images)

    if not ori_images or len(ori_images) == 0:
        error = "没有图片"
        return error, None

    #选择尺寸合适的图片
    n=0
    while(1):
        ori_image = random.choice(ori_images)
        n +=1

        image = get_remote_image(ori_image)
        print("###############", n , image)
        if image is None:
            print("远程图片打不开")
            if n <15:
                continue
            else:
                image = None
                break
        else:
            ori_w, ori_h = image.size
            if ori_w >= 600 :
                break
            else:
                print("图片分辨率太低", ori_w)
                if n < 15:
                    continue
                else:
                    image = None
                    break



    if image is None :
        return  "没有合适的图片",None


    image, iamge_url = photo_mark_image(image ,aliproduct.handle,str(price1), str(price2),  targer_page, type="album" )
    if not image:
        error = "打水印失败"
        return error, None

    #print("after photo mark", iamge_url)

    fields = ["id","name","created_time", "updated_time","picture","link",
                      "likes.summary(true)","comments.summary(true)"
    ]
    params = {
        "published": "true",

        "url": iamge_url,
        "name": name,
        "qn":aliproduct.handle

    }
    try:
        photo = Album(album_no).create_photo(
            fields=fields,
            params=params,
        )
    except Exception as e:
        error = str(e)
        return error, None

    obj, created = MyPhoto.objects.update_or_create(photo_no=photo["id"],
                                                    defaults={
                                                            'page_no': page_no,
                                                                'album_no': album_no,
                                                              "product_no": aliproduct.product_no,
                                                                'listing_status':True,
                                                              'created_time':
                                                                  photo["created_time"],#.split('+')[0],
                                                              'updated_time':
                                                                  photo["updated_time"],#.split('+')[0],

                                                              'name': photo.get("name"),
                                                              'picture': photo["picture"],
                                                              'link': photo["link"],
                                                              'like_count': photo["likes"]["summary"]["total_count"],
                                                              'comment_count': photo["comments"]["summary"][
                                                                  "total_count"]

                                                              }
                                                    )

    #print("new_photo saved ", obj, created)
    return  "成功", photo["id"]

#直接从aliproduct发布到相册
def post_lightin_album(lightinalbum):
    page_no = lightinalbum.myalbum.page_no
    album_no = lightinalbum.myalbum.album_no
    if lightinalbum.lightin_spu:

        product_no = lightinalbum.lightin_spu.SPU
    else:
        product_no = lightinalbum.lightin_sku.SKU

    access_token, long_token = get_token(page_no)
    FacebookAdsApi.init(access_token=access_token)
    fields = ["id","name","created_time", "updated_time","picture","link",
                      "likes.summary(true)","comments.summary(true)"
    ]
    params = {
        "published": "true",

        "url": lightinalbum.image_marked,

        "name": lightinalbum.name,


    }
    try:
        photo = Album(album_no).create_photo(
            fields=fields,
            params=params,
        )
    except Exception as e:
        error = str(e)
        return error, None

    obj, created = MyPhoto.objects.update_or_create(photo_no=photo["id"],
                                                    defaults={
                                                            'page_no': page_no,
                                                                'album_no': album_no,
                                                              "product_no": product_no,
                                                                'listing_status':True,
                                                              'created_time':
                                                                  photo["created_time"],#.split('+')[0],
                                                              'updated_time':
                                                                  photo["updated_time"],#.split('+')[0],

                                                              'name': photo.get("name"),
                                                              'picture': photo["picture"],
                                                              'link': photo["link"],
                                                              'like_count': photo["likes"]["summary"]["total_count"],
                                                              'comment_count': photo["comments"]["summary"][
                                                                  "total_count"]

                                                              }
                                                    )

    #print("new_photo saved ", obj, created)
    return  "成功", photo["id"]


def post_lightin_album_v0330(lightinalbum):
    page_no = lightinalbum.myalbum.page_no
    album_no = lightinalbum.myalbum.album_no
    if lightinalbum.lightin_spu:

        product_no = lightinalbum.lightin_spu.SPU
    else:
        product_no = lightinalbum.lightin_sku.SKU

    '''
    adobjects = FacebookAdsApi.init(my_app_id, my_app_secret, access_token=get_token(page_no), debug=True)
    fields = ["id", "name", "created_time", "updated_time", "picture", "link",
              "likes.summary(true)", "comments.summary(true)"
              ]
    params = {
        "published": "true",

        "url": lightinalbum.image_marked,

        "name": lightinalbum.name,

    }
    try:
        photo = Album(album_no).create_photo(
            fields=fields,
            params=params,
        )
    except Exception as e:
        error = str(e)
        return error, None
    '''

    url = "https://graph.facebook.com/v3.2/%s"/photos % (album_no)
    param = dict()
    param[
        "access_token"] = "EAAcGAyHVbOEBAEtwMPUeTci0x3G6XqlAwIhuQiZBZCVhZBRx88Rki0Lo7WNSxvAw7jAhhRlxsLjARbAZCnDvIoQ68Baj9TJrQC8KvEzyDhRWlnILGxRyc49b02aPInvpI9bcfgRowJfDrIt0kFE01LGD86vLKuLixtB0aTvTHww9SkedBzFZA"
    param["published"] = True
    param["url"] = lightinalbum.image_marked
    param["caption"] = lightinalbum.name
    param["fields"] = "id, name, created_time, updated_time, picture, link,likes.summary(true), comments.summary(true)"

    r = requests.post(url, param)
    if r.code == 200:
        photo = json.loads(r.text)
        obj, created = MyPhoto.objects.update_or_create(photo_no=photo["id"],
                                                        defaults={
                                                            'page_no': page_no,
                                                            'album_no': album_no,
                                                            "product_no": product_no,
                                                            'listing_status': True,
                                                            'created_time':
                                                                photo["created_time"],  # .split('+')[0],
                                                            'updated_time':
                                                                photo["updated_time"],  # .split('+')[0],

                                                            'name': photo.get("name"),
                                                            'picture': photo["picture"],
                                                            'link': photo["link"],
                                                            'like_count': photo["likes"]["summary"]["total_count"],
                                                            'comment_count': photo["comments"]["summary"][
                                                                "total_count"]

                                                        }
                                                        )

    # print("new_photo saved ", obj, created)
    return "成功", photo["id"]

def post_ads():
    page_nos = MyPage.objects.filter(active=True, is_published=True).values_list('page_no', flat=True)
    #page_nos = ["2084015718575745"]   #for debug



    for page_no in page_nos:
        print("processing ",page_no)
        post_ad(page_no)

def post_ad(page_no):

    from shop.photo_mark import lightin_mark_image_page

    import requests
    import base64
    import time



    adobjects = FacebookAdsApi.init(access_token=my_access_token, debug=True)
    adacount_no = "act_1903121643086425"
    adset_no = "23843265435620510"

    #取库存大、单价高、已经发布到相册 且还未打广告的商品

    #spus = Lightin_SPU.objects.filter(sellable__gt=5,shopify_price__gt= 50,shopify_price__lt= 100, aded = False ).order_by('?')
    lightinalbums = LightinAlbum.objects.filter(lightin_spu__sellable__gt=5,
                                                lightin_spu__shopify_price__gt=50, lightin_spu__shopify_price__lt=100,
                                                lightin_spu__aded=False,
                                                myalbum__page_no=page_no, published=True).distinct()

    limit = 1
    n = 1

    for lightinalbum in lightinalbums:
        spu = lightinalbum.lightin_spu
        print("spu ", spu)
        name = "💋💋Flash Sale ！！！💋💋" \
               "90% off！Lowest Price Online ！！！" \
               "🥳🥳🥳 10:00-22:00 Everyday ,Update 100 New items Every Hour !! The quantity is limited !!😇😇" \
               "All goods are in Riyadh stock,It will be delivered to you in 3-5 days! ❣️❣️" \
               "How to order?Pls choice the product that you like it , then send us the picture, we will order it for you!🤩🤩"
        name = name + "\n[" +spu.handle +"]"

        # 价格
        price1 = int(spu.shopify_price)
        price2 = int(price1 * random.uniform(5, 6))
        # 为了减少促销的麻烦，文案里不写价格了
        # name = name + "\n\nPrice:  " + str(price1) + "SAR"

        # 准备图片
        # 先取第一张，以后考虑根据实际有库存的sku的图片（待优化）
        error = ""
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
            target_page =  MyPage.objects.get(page_no= page_no)
            image_marked, image_marked_url = lightin_mark_image_page(image, spu.handle, str(price1), str(price2),target_page)
            if not image_marked:
                error = "打水印失败"

        else:
            print(page_no, spu.SPU, "没有图片")
            error = "没有图片"

        if not error == "":
            spu.ad_error = error
            spu.save()
            continue

        # 上传到adimage

        # 使用 adaccount 的 SDK
        '''
        with open(image_marked, 'rb') as f:
            base64_data = base64.b64encode(f.read())
            bytes = base64_data.decode()

        print("type of bytes", type(bytes))

        fields = {

        }
        params = {
            "bytes": bytes,
            # 'filename': destination,
        }
        adimage = AdAccount(adacount_no).create_ad_image(
            fields=fields,
            params=params,
        )

        print("adimage", adimage)

        # 创建adCreative
        adimagehash = adimage["hash"]
        
        adimagehash = "9b5b76dcc1e92eba0048d2501b74e7e3"
        '''
        fields = [
        ]

        #link ad
        params = {
            'name': 'Creative for ' + spu.handle,
            'object_story_spec': {'page_id': page_no,
                                  'link_data': {"call_to_action": {"type": "MESSAGE_PAGE",
                                                                   "value": {"app_destination": "MESSENGER"}},
                                                #"image_hash": adimagehash,
                                                "picture": image_marked_url,
                                                "link": "https://facebook.com/%s" % (page_no),

                                                "message": name,
                                                "name": "Yallavip.com",
                                                "description": "Online Flash Sale Everyhour",
                                                "use_flexible_image_aspect_ratio": True,}},
        }
        '''
        #photo ad
        params = {
            'name': 'Creative for ' + spu.handle,
            'object_story_spec': {'page_id': page_no,
                                  'photo_data': {
                                                "image_hash": adimagehash,


                                                "caption": name,
                                                }},
        }
        '''

        adCreative = AdAccount(adacount_no).create_ad_creative(
            fields=fields,
            params=params,
        )

        print("adCreative is ", adCreative)

        fields = [
        ]
        params = {
             'name': page_no + '_'+ spu.handle,
            'adset_id': adset_no,
            'creative': {'creative_id': adCreative["id"]},
            'status': 'PAUSED',
            # "access_token": my_access_token,
        }

        ad = AdAccount(adacount_no).create_ad(
            fields=fields,
            params=params,
        )

        print("ad is ", ad)
        spu.aded = True
        spu.save()

        n+=1

        if n > limit:
            break
        else:

            time.sleep(10)

def post_album_ad(page_no):
    import requests
    import base64

    adobjects = FacebookAdsApi.init(access_token=my_access_token, debug=True)
    adacount_no = "act_1903121643086425"
    adset_no = "23843265435620510"

    #取库存大、单价高且还未打广告的商品

    lightinalbums  = LightinAlbum.objects.filter(lightin_spu__sellable__gt=9,
                                        lightin_spu__shopify_price__gt= 50,lightin_spu__shopify_price__lt= 100, lightin_spu__aded = False,
                                        myalbum__page_no = page_no,published= True ).distinct()

    #spus = Lightin_SPU.objects.filter(sellable__gt=5,shopify_price__gt= 50,shopify_price__lt= 90, aded = False )
    limit = 1
    n = 0

    for lightinalbum in lightinalbums:
        spu = lightinalbum.lightin_spu
        print("spu ", spu)
        name = "💋💋Flash Sale ！！！💋💋" \
               "90% off！Lowest Price Online ！！！" \
               "🥳🥳🥳 10:00-22:00 Everyday ,Update 100 New items Every Hour !! The quantity is limited !!😇😇" \
               "All goods are in Riyadh stock,It will be delivered to you in 3-5 days! ❣️❣️" \
               "How to order?Pls choice the product that you like it , then send us the picture, we will order it for you!🤩🤩"
        name = name + "\n[" +spu.handle +"]"

        # 创建adCreative
        fields = [
        ]

        #link ad
        params = {
            'name': 'Creative for ' + spu.handle,
            'object_story_spec': {'page_id': page_no,
                                  'link_data': {"call_to_action": {"type": "MESSAGE_PAGE",
                                                                   "value": {"app_destination": "MESSENGER"}},
                                                "picture": lightinalbum.image_marked,
                                                "link": "https://facebook.com/%s" % (page_no),

                                                "message": name,
                                                "name": "Yallavip.com",
                                                "description": "Online Flash Sale Everyhour",
                                                "use_flexible_image_aspect_ratio": True,}},
        }

        adCreative = AdAccount(adacount_no).create_ad_creative(
            fields=fields,
            params=params,
        )

        print("adCreative is ", adCreative)

        fields = [
        ]
        params = {
            'name': page_no + '_'+ spu.handle,
            'adset_id': adset_no,
            'creative': {'creative_id': adCreative["id"]},
            'status': 'PAUSED',
            # "access_token": my_access_token,
        }

        ad = AdAccount(adacount_no).create_ad(
            fields=fields,
            params=params,
        )

        print("ad is ", ad)
        spu.aded =True
        spu.save()

        n+=1

        if n > limit:
            break

def post_yallavip_album(lightinalbum):
    page_no = lightinalbum.yallavip_album.page.page_no
    album_no = lightinalbum.yallavip_album.album.album_no
    print("###########",page_no, album_no)

    if lightinalbum.lightin_spu:

        product_no = lightinalbum.lightin_spu.SPU
    else:
        product_no = lightinalbum.lightin_sku.SKU

    access_token, long_token = get_token(page_no)

    if not access_token:
        error = "获取token失败"
        return error, None

    adobjects = FacebookAdsApi.init( access_token=access_token, debug=True)
    fields = ["id","name","created_time", "updated_time","picture","link",
                      "likes.summary(true)","comments.summary(true)"
    ]
    params = {
        "published": "true",

        "url": lightinalbum.image_marked,

        "name": lightinalbum.name,


    }
    try:
        photo = Album(album_no).create_photo(
            fields=fields,
            params=params,
        )
    except Exception as e:
        print(e)
        error = e.api_error_message()

        #如果是token的问题，就要把token暂停
        type = e.api_error_type()
        print(type)
        if type == "OAuthException":
            print("更新token状态", long_token, error)
            Token.objects.filter(long_token = long_token).update(active=False,info=error,page_no="")
        return error, None

    obj, created = MyPhoto.objects.update_or_create(photo_no=photo["id"],
                                                    defaults={
                                                            'page_no': page_no,
                                                                'album_no': album_no,
                                                              "product_no": product_no,
                                                                'listing_status':True,
                                                              'created_time':
                                                                  photo["created_time"],#.split('+')[0],
                                                              'updated_time':
                                                                  photo["updated_time"],#.split('+')[0],

                                                              'name': photo.get("name"),
                                                              'picture': photo["picture"],
                                                              'link': photo["link"],
                                                              'like_count': photo["likes"]["summary"]["total_count"],
                                                              'comment_count': photo["comments"]["summary"][
                                                                  "total_count"]

                                                              }
                                                    )

    #print("new_photo saved ", obj, created)
    return  "成功", photo["id"]



def prepare_yallavip_ad(page_no=None):
    from shop.photo_mark import lightin_mark_image_page

    import requests
    import base64
    import time

    # 取库存大、单价高、已经发布到相册 且还未打广告的商品


    lightinalbums_all = LightinAlbum.objects.filter(lightin_spu__sellable__gt=0,lightin_spu__SPU__istartswith = "s",
                                                lightin_spu__shopify_price__gt=50, #lightin_spu__shopify_price__lt=50,
                                                aded=False,
                                                yallavip_album__page__active=True,yallavip_album__page__is_published=True,
                                                    yallavip_album__isnull=False,
                                                    published=True).distinct()
    if page_no:
        lightinalbums_all.filter(yallavip_album__page__page_no=page_no)

    limit = 10
    n = 1
    #每次处理一个相册， 从相册里选4张拼成一张，发广告
    yallavip_albums = lightinalbums_all.values_list("yallavip_album",flat=True).distinct()
    for yallavip_album in yallavip_albums:

        prepare_yallavip_ad_album(yallavip_album, lightinalbums_all)

        n += 1

        if n > limit:
            break
        else:

            time.sleep(10)


def prepare_yallavip_ad_album(yallavip_album_pk, lightinalbums_all):
    #从库存多的开始推
    yallavip_album_instance = YallavipAlbum.objects.get(pk=yallavip_album_pk)
    print ("正在处理相册 ", yallavip_album_instance.album.name)
    lightinalbums = lightinalbums_all.filter(yallavip_album__pk=yallavip_album_pk).order_by("lightin_spu__sellable")[:4]

    spu_ims = lightinalbums.values_list("image_marked", flat=True)
    spus = lightinalbums.values_list("lightin_spu__handle", flat=True)
    if spus.count() < 4:
        print (yallavip_album_pk, "数量不够", spus.count())
        return

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
    for lightinalbum in lightinalbums:
        lightinalbum.aded = True
        lightinalbum.save()



def combo_ad_image(spu_ims, spus_name,album_name):
    from shop.photo_mark import clipResizeImg_new, get_remote_image
    import os
    from django.conf import settings
    domain = "http://admin.yallavip.com"

    try:
        from PIL import Image, ImageDraw, ImageFont, ImageEnhance

    except ImportError:
        import Image, ImageDraw, ImageFont, ImageEnhance


    ims=[]

    for spu_im in spu_ims:
        im = get_remote_image(spu_im)
        if not im:
            print ("image打不开")
            return None
        ims.append(im)

    # 开始拼图exit


    item_count = spu_ims.count()
    print("图片数量", item_count)
    if item_count == 4:
        # 四张图
        # 先做个1080x1080的画布

        layer = Image.new("RGB", (1080, 1080), "red")

        layer.paste(clipResizeImg_new(ims[0], 540, 540), (0, 0))
        layer.paste(clipResizeImg_new(ims[1], 540, 540), (0, 540))
        layer.paste(clipResizeImg_new(ims[2], 540, 540), (540, 0))
        layer.paste(clipResizeImg_new(ims[3], 540, 540), (540, 540))
        '''

        layer = Image.new("RGB", (1080, 1130), "red")

        layer.paste(clipResizeImg_new(ims[0], 540, 540), (0, 0))
        layer.paste(clipResizeImg_new(ims[1], 540, 540), (0, 540))
        layer.paste(clipResizeImg_new(ims[2], 540, 540), (540, 0))
        layer.paste(clipResizeImg_new(ims[3], 540, 540), (540, 540))

        # 最下面写相册名字
        font = ImageFont.truetype(FONT, 35)
        draw1 = ImageDraw.Draw(layer)

        lw, lh = layer.size
        x = 0
        y = lh - 50
        # 写货号
        draw1.rectangle((x + 10, y + 5, x + 10 + length(album_name)*5 , y + 45), fill='yellow')
        draw1.text((x + 30, y + 10), album_name, font=font,
                   fill="black")  # 设置文字位置/内容/颜色/字体

        # 写包邮
        promote = "Free Shipping"
        draw1.rectangle((x + 50 + length(album_name)*5, y + 55, x + 150 + length(album_name)*5, y + 95), fill='yellow')
        draw1.text((x + 60 + length(album_name)*5, y + 60), promote, font=font,
                   fill=(0, 0, 0))  # 设置文字位置/内容/颜色/字体
       '''
    elif item_count == 5:
        # 五张图
        # 先做个900x1000的画布
        layer = Image.new("RGB", (900, 1180), "red")
        layer.paste(clipResizeImg_new(ims[0], 540, 540), (0, 0))
        layer.paste(clipResizeImg_new(ims[1], 540, 540), (0, 540))
        layer.paste(clipResizeImg_new(ims[2], 360, 360), (540, 0))
        layer.paste(clipResizeImg_new(ims[3], 360, 360), (540, 360))
        layer.paste(clipResizeImg_new(ims[4], 360, 360), (540, 720))

    elif item_count == 6:
        # 六张图
        # 先做个900x900的画布
        layer = Image.new("RGB", (900, 1000), "red")

        layer.paste(clipResizeImg_new(ims[0], 600, 600), (0, 0))
        layer.paste(clipResizeImg_new(ims[1], 300, 300), (0, 600))
        layer.paste(clipResizeImg_new(ims[2], 300, 300), (300, 600))
        layer.paste(clipResizeImg_new(ims[3], 300, 300), (600, 0))
        layer.paste(clipResizeImg_new(ims[4], 300, 300), (600, 300))
        layer.paste(clipResizeImg_new(ims[5], 300, 300), (600, 600))
    elif item_count == 7:
        # 先做个900x130的画布
        layer = Image.new("RGB", (900, 1300), "red")
        layer.paste(clipResizeImg_new(ims[0], 450, 450), (0, 0))
        layer.paste(clipResizeImg_new(ims[1], 450, 450), (450, 0))
        layer.paste(clipResizeImg_new(ims[2], 450, 450), (0, 450))
        layer.paste(clipResizeImg_new(ims[3], 450, 450), (450, 450))
        layer.paste(clipResizeImg_new(ims[4], 300, 300), (0, 900))
        layer.paste(clipResizeImg_new(ims[5], 300, 300), (300, 900))
        layer.paste(clipResizeImg_new(ims[6], 300, 300), (600, 900))
    elif item_count == 8:
        # 先做个900x1150的画布
        layer = Image.new("RGB", (900, 1150), "red")
        layer.paste(clipResizeImg_new(ims[0], 450, 450), (0, 0))
        layer.paste(clipResizeImg_new(ims[1], 450, 450), (450, 0))
        layer.paste(clipResizeImg_new(ims[2], 300, 300), (0, 450))
        layer.paste(clipResizeImg_new(ims[3], 300, 300), (0, 750))
        layer.paste(clipResizeImg_new(ims[4], 300, 300), (300, 450))
        layer.paste(clipResizeImg_new(ims[5], 300, 300), (300, 750))
        layer.paste(clipResizeImg_new(ims[6], 300, 300), (600, 450))
        layer.paste(clipResizeImg_new(ims[7], 300, 300), (600, 750))
    elif item_count == 9:
        # 先做个900x1000的画布
        layer = Image.new("RGB", (900, 1000), "red")
        layer.paste(clipResizeImg_new(ims[0], 300, 300), (0, 0))
        layer.paste(clipResizeImg_new(ims[1], 300, 300), (0, 300))
        layer.paste(clipResizeImg_new(ims[2], 300, 300), (0, 600))
        layer.paste(clipResizeImg_new(ims[3], 300, 300), (300, 0))
        layer.paste(clipResizeImg_new(ims[4], 300, 300), (300, 300))
        layer.paste(clipResizeImg_new(ims[5], 300, 300), (300, 600))
        layer.paste(clipResizeImg_new(ims[6], 300, 300), (600, 0))
        layer.paste(clipResizeImg_new(ims[7], 300, 300), (600, 300))
        layer.paste(clipResizeImg_new(ims[8], 300, 300), (600, 600))
    elif item_count == 10:
        # 先做个900x130的画布
        layer = Image.new("RGB", (900, 925), "red")
        layer.paste(clipResizeImg_new(ims[0], 300, 300), (0, 0))
        layer.paste(clipResizeImg_new(ims[1], 300, 300), (0, 300))
        layer.paste(clipResizeImg_new(ims[2], 300, 300), (300, 0))
        layer.paste(clipResizeImg_new(ims[3], 300, 300), (300, 300))
        layer.paste(clipResizeImg_new(ims[4], 300, 300), (600, 0))
        layer.paste(clipResizeImg_new(ims[5], 300, 300), (600, 300))
        layer.paste(clipResizeImg_new(ims[6], 225, 225), (0, 600))
        layer.paste(clipResizeImg_new(ims[7], 225, 225), (225, 600))
        layer.paste(clipResizeImg_new(ims[8], 225, 225), (450, 600))
        layer.paste(clipResizeImg_new(ims[9], 225, 225), (675, 600))
    else:
        layer = None

    if layer:
        out = layer.convert('RGB')


        image_filename = spus_name+'.jpg'

        destination = os.path.join(settings.MEDIA_ROOT, "ad/", image_filename)

        out.save(destination, 'JPEG', quality=95)
        # out.save('target%s.jpg'%(combo.SKU), 'JPEG')

        destination_url = domain + os.path.join(settings.MEDIA_URL, "ad/", image_filename)
        print("destination_url", destination_url)
        return  destination_url



    else:
        print( "items数量问题")
        destination_url =  None

    for im in ims:
        im.close()

    return  destination_url

def get_ad_sets(adaccount_no):
    adobjects = FacebookAdsApi.init(access_token=ad_tokens, debug=True)

    fields =[ "attribution_spec","bid_amount","bid_info","billing_event","budget_remaining",
              "campaign","configured_status","created_time","destination_type",
              "effective_status","id","is_dynamic_creative","lifetime_imps","name",
              "optimization_goal","recurring_budget_semantics","source_adset_id",
              "start_time","status","targeting","updated_time","use_new_app_click",


    ]
    params = {

    }
    adsets = AdAccount(adaccount_no).get_ad_sets(fields=fields, params=params, )
    print("adaccount_no is ", adaccount_no)
    print("adsets is ", adsets)


    #先把这个adaccount_no的adset全部置为false
    MyAdset.objects.filter(adaccount_no=adaccount_no).update(active=False)

    for adset in adsets:
        print("#################", adset)
        obj, created = MyAdset.objects.update_or_create(adset_no=adset["id"],
                                                        defaults={
                                                                'adaccount_no':adaccount_no,
                                                                'campaign_no': adset["campaign"]["id"],
                                                                'name':adset["name"],

                                                                'attribution_spec': adset.get("attribution_spec"),
                                                                #'bid_amount': adset["bid_amount"],
                                                                #'bid_info': adset["bid_info"],
                                                                'billing_event': adset["billing_event"],
                                                                'budget_remaining': adset["budget_remaining"],

                                                                'configured_status': adset["configured_status"],
                                                                'created_time': adset["created_time"],
                                                                'destination_type': adset["destination_type"],
                                                                'effective_status': adset["effective_status"],

                                                                'is_dynamic_creative': adset["is_dynamic_creative"],
                                                                'lifetime_imps': adset["lifetime_imps"],

                                                                'optimization_goal': adset["optimization_goal"],
                                                                'recurring_budget_semantics': adset[
                                                                           "recurring_budget_semantics"],
                                                                'source_adset_id': adset["source_adset_id"],
                                                                'start_time': adset["start_time"],
                                                                'status': adset["status"],
                                                                #'targeting': adset["targeting"],
                                                                'updated_time': adset["updated_time"],
                                                                'use_new_app_click': adset["use_new_app_click"],
                                                                'active':True

                                                                  }
                                                        )


def choose_ad_set(page_no):
    try:

        adsets = MyAdset.objects.filter(name__icontains=page_no,active=True)
        return adsets[0].adset_no
    except:
        return  None


def post_yallavip_ad(page_no= None):

    adobjects = FacebookAdsApi.init(access_token=ad_tokens, debug=True)
    adaccount_no = "act_1903121643086425"
    #yallavip 加速
    #adset_no = "23843303803340510"
    # yallavip mall  匀速
    #adset_no = "23843310378170510"
    adset_no = choose_ad_set(page_no)
    #adset_no = "23843265435590510"

    ads = YallavipAd.objects.filter(active=True, published=False )
    if page_no:
        ads.filter(yallavip_album__page__page_no=page_no)

    page_nos = ads.values_list("yallavip_album__page__page_no",flat=True).distinct()
    for ad_page_no in page_nos:
        ad = ads.filter(yallavip_album__page__page_no = ad_page_no).first()
        error = ""
        # 上传到adimage
        try:
            fields = [
            ]

            # link ad
            params = {
                'name': ad_page_no + '_' + ad.spus_name,
                'object_story_spec': {'page_id': ad_page_no,
                                      'link_data': {"call_to_action": {"type": "MESSAGE_PAGE",
                                                                       "value": {"app_destination": "MESSENGER"}},
                                                    # "image_hash": adimagehash,
                                                    "picture": ad.image_marked_url,
                                                    "link": "https://facebook.com/%s" % (ad_page_no),

                                                    "message": ad.message,
                                                    "name": "Yallavip.com",
                                                    "description": "Online Flash Sale Everyhour",
                                                    "use_flexible_image_aspect_ratio": True, }},
            }
            adCreative = AdAccount(adaccount_no).create_ad_creative(
                fields=fields,
                params=params,
            )

            print("adCreative is ", adCreative)

            fields = [
            ]
            params = {
                'name': ad_page_no + '_' + ad.spus_name,
                'adset_id': adset_no,
                'creative': {'creative_id': adCreative["id"]},
                'status': 'PAUSED',
                # "access_token": my_access_token,
            }

            fb_ad = AdAccount(adaccount_no).create_ad(
                fields=fields,
                params=params,
            )
        except Exception as e:
            print(e)
            error = e.api_error_message()


        if error == "":
            print("fb ad is ", fb_ad)
            ad.published= True
            ad.published_time = dt.now()
        else:
            ad.publish_error = error

        ad.save()

#创建系统用户的密钥
def get_appsecret_proof(msg):
    import hashlib
    import hmac
    #appsecret
    key = b'e6df363351fb5ce4b7f0080adad08a4d'
    #token
    #msg = b'EAAHZCz2P7ZAuQBADxdcqbOZCw8R8mKl4R4AZCTU8er02GNwzNu7Oj9ZAJZB6zxoVZBKmLZA4qZBeznC8TFcE90uZCNprKkdTUPCNGniH7q9vsALK4AW95VR2wH6oo9ypk6tjyAsqc5aFFZAgZCVCP32c7IeJcnCUsNhILrz4QqCbjA3aOoxOfcqEStoVjAg6doROP9Fbln5MjEfFczgw8PGiYr00'

    h = hmac.new(key, msg, digestmod='sha256')
    #appsecret_proof
    print(h.hexdigest())
    #还需要


#原文

'''
curl -i -X POST \
    https://graph.facebook.com/v3.2/100029952330435/access_tokens?business_app=562741177444068&scope=ads_management%2Cads_read%2Cbusiness_management%2Cmanage_pages%2Cpages_manage_cta%2Cpages_manage_instant_articles%2Cpages_show_list%2Cpublish_pages%2Cread_insights%2Cread_page_mailboxes&appsecret_proof=7f47c397a667ca645a375863fcc00df53d8bef08ae1b158e22b49b2be4c91282&access_token=
    
    APP_SCOPED_SYSTEM_USER_ID 100029952330435
    business_app 562741177444068
    scope ads_management,ads_read,business_management,manage_pages,pages_manage_cta,pages_manage_instant_articles,pages_show_list,publish_pages,read_insights,read_page_mailboxes




获取system user token
https://developers.facebook.com/docs/marketing-api/businessmanager/systemuser#systemuser


import hashlib
import hmac
key = b'e6df363351fb5ce4b7f0080adad08a4d'
msg = b'EAAHZCz2P7ZAuQBADxdcqbOZCw8R8mKl4R4AZCTU8er02GNwzNu7Oj9ZAJZB6zxoVZBKmLZA4qZBeznC8TFcE90uZCNprKkdTUPCNGniH7q9vsALK4AW95VR2wH6oo9ypk6tjyAsqc5aFFZAgZCVCP32c7IeJcnCUsNhILrz4QqCbjA3aOoxOfcqEStoVjAg6doROP9Fbln5MjEfFczgw8PGiYr00'

h = hmac.new(key, msg, digestmod='sha256')
print(h.hexdigest())

fa8c74c300fdc57ab7128d50f96fe6b073d749f1f61292c2f27a48d84b37d99e

APP_SCOPED_SYSTEM_USER_ID 100029952330435
business_app 562741177444068
scope ads_management,ads_read,business_management,manage_pages,pages_manage_cta,pages_manage_instant_articles,pages_show_list,publish_pages,read_insights,read_page_mailboxes
appsecret_proof 0810bd9dce0f345ffdb7d3440dbead7c9714ba221d03a8084a42f66ae5c6db2b

access_token 
EAAHZCz2P7ZAuQBABHO6LywLswkIwvScVqBP2eF5CrUt4wErhesp8fJUQVqRli9MxspKRYYA4JVihu7s5TL3LfyA0ZACBaKZAfZCMoFDx7Tc57DLWj38uwTopJH4aeDpLdYoEF4JVXHf5Ei06p7soWmpih8BBzadiPUAEM8Fw4DuW5q8ZAkSc07PrAX4pGZA4zbSU70ZCqLZAMTQZDZD

'''