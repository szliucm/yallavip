from .models import MyProductShopify,MyProductFb
from fb.models import  MyPage,MyAlbum,MyPhoto
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

import os
import requests
import json

from django.conf import settings


APP_SCOPED_SYSTEM_USER_ID=100029952330435
my_access_token = "EAAHZCz2P7ZAuQBABHO6LywLswkIwvScVqBP2eF5CrUt4wErhesp8fJUQVqRli9MxspKRYYA4JVihu7s5TL3LfyA0ZACBaKZAfZCMoFDx7Tc57DLWj38uwTopJH4aeDpLdYoEF4JVXHf5Ei06p7soWmpih8BBzadiPUAEM8Fw4DuW5q8ZAkSc07PrAX4pGZA4zbSU70ZCqLZAMTQZDZD"
my_access_token_dev = "EAAcGAyHVbOEBAAL2mne8lmKC55lbDMndPYEVR2TRmOWf9ePUN97SiZCqwCd3KOZBrEkC57rVt3ZClhXi6oxxf1i0hRCK50QALuAQOCs60U30FjNYimeP97xLjfl7wZAAjThdkXPJujsWcAXOwkTNKvKlmP6tZBPUtSYb3i4i1vUs40MZAUOzNIG9v7HNjnyyIZD"
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


    pages = MyPage.objects.filter(active=True)  # .values_list('page_no', flat=True)
    # page_nos = ["358078964734730"]   #for debug
    for page in pages:
        post_creative_feed_page(page)

    return


def post_creative_feed_page(page):

    from django.utils import timezone as datetime


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
    token = get_token(page_id)
    FacebookAdsApi.init(access_token=token,debug=True)
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
    from shop.photo_mark import photo_mark

    pages = MyPage.objects.filter(active=True)      #.values_list('page_no', flat=True)
    #page_nos = ["358078964734730"]   #for debug
    for page in pages:
        page_no= page.page_no

        fbproduct = MyFbProduct.objects.filter(mypage__pk=page.pk,published=True).order_by('?')[:1].first()
        if fbproduct is None:
            print("没有fb产品", page)
            continue
        product = fbproduct.myproduct
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
            image, iamge_url = photo_mark(ori_image, product.handle, str(price1), str(price2), page, type="album")
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


from xadmin.plugins.actions import BaseActionView

from django.http import HttpResponse, HttpResponseRedirect
from django.template.context import RequestContext

from xadmin import views
from .models import *
# 自定义动作所需
from django import forms, VERSION as django_version
from django.core.exceptions import PermissionDenied
from django.db import router
from django.template.response import TemplateResponse
from django.utils.encoding import force_text
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext as _
from django.contrib.admin.utils import get_deleted_objects
from xadmin.util import model_ngettext
from xadmin.views.base import filter_hook
from shop.models import ProductCategory,ProductCategoryMypage
from fb.models import  MyPage,MyAlbum,MyPhoto



from facebook_business.api import FacebookAdsApi
from facebook_business.exceptions import FacebookRequestError
from facebook_business.adobjects.systemuser import SystemUser
from facebook_business.adobjects.page import Page
from facebook_business.adobjects.pagepost import PagePost
from facebook_business.adobjects.album import Album
from facebook_business.adobjects.photo import Photo
#from facebookads.adobjects.adimage import AdImage
from facebook_business.adobjects.adaccount import AdAccount
from facebook_business.adobjects.campaign import Campaign
from facebook_business.adobjects.adset import AdSet
from facebook_business.adobjects.ad import Ad
from facebook_business.adobjects.adsinsights import AdsInsights

import  random

#import time


from shop.photo_mark import  photo_mark


my_app_id = "562741177444068"
my_app_secret = "e6df363351fb5ce4b7f0080adad08a4d"
my_access_token = "EAAHZCz2P7ZAuQBABHO6LywLswkIwvScVqBP2eF5CrUt4wErhesp8fJUQVqRli9MxspKRYYA4JVihu7s5TL3LfyA0ZACBaKZAfZCMoFDx7Tc57DLWj38uwTopJH4aeDpLdYoEF4JVXHf5Ei06p7soWmpih8BBzadiPUAEM8Fw4DuW5q8ZAkSc07PrAX4pGZA4zbSU70ZCqLZAMTQZDZD"


my_app_id_dev = "1976935359278305"
my_app_secret_dev = "f4ee797596ed236c0bc74d33f52e6a54"
my_access_token_dev = "EAAcGAyHVbOEBAAL2mne8lmKC55lbDMndPYEVR2TRmOWf9ePUN97SiZCqwCd3KOZBrEkC57rVt3ZClhXi6oxxf1i0hRCK50QALuAQOCs60U30FjNYimeP97xLjfl7wZAAjThdkXPJujsWcAXOwkTNKvKlmP6tZBPUtSYb3i4i1vUs40MZAUOzNIG9v7HNjnyyIZD"

second_app_id = "437855903410360"
second_token = "EAAGOOkWV6LgBAIGWTMe3IRKJQNp5ld7nxmiafOdWwlPn8BksJxFUsCiAqzMQ1ZC1LJipR2tcHXZBO949i0ZB5xOOfHbut2hk7sIP3YZB5MfuqjFtm9LGq3J7xrBtUFPLZBT9pe2UcUTXann8DXhwMPQOlIBANiNJE6RA11vNrZC0fGijUsDJds"

import requests
import json

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
'''
def create_new_album(page_no , new_albums ):
    # 建相册要用开发账号
    #建出来的相册普通客户看不到，所以暂不启用此功能

    adobjects = FacebookAdsApi.init(access_token=get_token(page_no, my_access_token_dev), debug=True)
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
                'place': '111953658894021',
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
                                                                  'created_time': album["created_time"].split('+')[0],
                                                                  'updated_time': album["updated_time"].split('+')[0],

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


    adobjects = FacebookAdsApi.init(my_app_id, my_app_secret, access_token=get_token(page_no), debug=True)


    #print("product.product_no ", product.product_no)



    #print("position is ", ori_image.position)
    value_list = None
    value_name = None
    if aliproduct.title is None or len(aliproduct.title) == 0:
        handle_new = 'b' + str(aliproduct.pk).zfill(5)
        title = fanyi(aliproduct.title_zh)

        options = json.loads(aliproduct.sku_info)
        #print( options)
        for option in options:
            values = option.get("values")
            value_name = option.get("label")
            value_list =[]
            for value in values:
                desc = value.get("desc")
                if desc is not None:
                    value_list.append(desc)

    else:
        handle_new = aliproduct.handle
        title = aliproduct.title

        options = json.loads(aliproduct.options)
        #print( options)
        for option in options:
            value_list = option.get("values")
            value_name = option.get("name")
            for i in range(value_list.count(None)):
                value_list.remove(None)


    name = title + "  [" + handle_new + "]"
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