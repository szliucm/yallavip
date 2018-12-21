from .models import MyProductShopify,MyProductFb
from fb.models import  MyPage,MyAlbum,MyPhoto
from shop.models import ShopifyProduct, ShopifyVariant,ShopifyOptions
from shop.models import  ShopifyImage
from .video import logo_video

from django.db.models import Max
from django.db.models import Q
import random
#from datetime import datetime

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
    import filetype
    from shop.photo_mark import  photo_mark

    pages = MyPage.objects.filter(active=True)  # .values_list('page_no', flat=True)
    # page_nos = ["358078964734730"]   #for debug
    for page in pages:
        page_id = page.page_no

        fbs = MyProductFb.objects.filter(~Q(myresource__handle='')&Q(myresource__handle__isnull=False),published=False,obj_type='FEED',mypage__page_no= page_id, ).order_by('myresource__created_time')

        if not fbs:
            print("no content to post ")
            continue

        fb= fbs.first()



        token = get_token(page_id)
        FacebookAdsApi.init(access_token=token)
        #domain = "http://dev.yallavip.com:8000"
        domain = "http://admin.yallavip.com"
        resource = str(fb.myresource.resource)
        local_resource = os.path.join(settings.MEDIA_ROOT, resource)
        kind = filetype.guess(local_resource)
        product = ShopifyProduct.objects.filter(handle=fb.myresource.handle).first()
        max_price = ShopifyVariant.objects.filter(product_no=product.product_no).aggregate(Max("price")).get(
            "price__max")
        if (max_price) is None:
            print("取最大价格出错")
            continue
        price1 = int(max_price)
        price2 = int(price1 * random.uniform(2, 3))

        feed_post = None
        if kind.mime.find("video")>=0:
            print("视频")
            product = ShopifyProduct.objects.filter(handle=fb.myresource.handle ).first()
            max_price = ShopifyVariant.objects.filter(product_no=product.product_no).aggregate(Max("price")).get(
                        "price__max")
            if(max_price) is None:
                print("取最大价格出错")
                continue
            price1 = int(max_price)
            price2 = int(price1 * random.uniform(2, 3))

            result = logo_video(resource, page.logo,page.price, fb.myresource.handle, str(price1),str(price2),no_logo=False)
            if not result:
                print("视频失败")
                continue
            destination_url = domain + os.path.join(settings.MEDIA_URL, resource.rpartition(".")[0] + "_watermark.mp4")
            fields = [
            ]
            params = {
                'title': fb.myresource.title,
                'description':fb.myresource.message,
                'file_url': destination_url,
                'published': 'true',
            }
            feed_post = Page(page_id).create_video(
                fields=fields,
                params=params,
            )


        elif kind.mime.find("image")>=0:
            print("图片")
            destination_url = domain + os.path.join(settings.MEDIA_URL, resource)
            # 发图片post
            if fb.myresource.resource_type == "RAW":
                #素材需要打标，否则直接发
                finale, final_url = photo_mark(destination_url, product, price1, price2, page, type="album")

            else:
                final_url = destination_url

            fields = [
            ]
            params = {
                'url': final_url,
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
            print("未知文件")
            continue




        if feed_post:
            feed_post_id = feed_post.get_id()

            if feed_post_id:
                MyProductFb.objects.filter(pk=fb.pk).update(fb_id=feed_post_id, published=True,published_time=datetime.utcnow() )

                print("Wow ", page_id, feed_post_id)



    return


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
            image, iamge_url = photo_mark(ori_image, product, str(price1), str(price2), page, type="album")
            if not image:
                print("打水印失败")
                continue

            dest_images.append(iamge_url)

        post_id = fb_slideshow(list(dest_images), page_no)

        print("postid ", post_id)





    return

#####################################
#########把表现较好的product发到feed
#########每个page,从产品排行榜里随机选七个产品，组成动图，发到feed里
#########太乱，暂时不用这个了
######################################
def post_7_products_feed():
    from .video import fb_slideshow

    page_nos = MyPage.objects.filter(active=True).values_list('page_no', flat=True)
    #page_nos = ["358078964734730"]   #for debug
    for page_no in page_nos:

        products = MyProductShopify.objects.order_by('?')[:7]
        images = []
        for product in products:
            print("result is ",page_no, product.handle, product.product_no)
            image = ShopifyImage.objects.filter(product_no=product.product_no).values_list('src', flat=True).order_by('?').first()



            images.append(image)

        images_count = len(images)
        if images_count<3:
            print("图片太少")
            continue


        post_id = fb_slideshow(list(images), page_no)

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

import time
#import datetime

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

def create_new_album(page_no , new_albums ):
    # 建相册要用开发账号

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

def post_photo_to_album(targer_page,album_no,product ):
    from django.db.models import Max
    # 检查产品是否已经在相册中了，如果不存在，就发布新图片
    #myphotos = MyPhoto.objects.filter(name=product.handle , album_no=album_no )

    page_no = targer_page.page_no
    myphotos = MyPhoto.objects.filter(name__icontains=product.handle, album_no=album_no)
    #print("args is  %s %s %s"%(page_no,album_no , product.handle ))
    if myphotos:
        print("photo exist")
        return False
    else:
        print("now we need to create new photos for %s"%(product.handle))


    adobjects = FacebookAdsApi.init(my_app_id, my_app_secret, access_token=get_token(page_no), debug=True)


    #print("product.product_no ", product.product_no)
    ori_images = ShopifyImage.objects.filter(product_no=product.product_no).order_by('position')
    if not ori_images :

        print("no image %s"%(product.product_no))
        return False

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
        return False

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