from .models import MyProductShopify,MyProductFb
from fb.models import MyFeed,MyPage,MyAd
from shop.models import ShopifyVariant
from django.db.models import Max
import random

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
def get_token(target_page):

    url = "https://graph.facebook.com/v3.2/{}?fields=access_token".format(target_page)

    param = dict()
    param["access_token"] = my_access_token

    r = requests.get(url, param)

    data = json.loads(r.text)

    #print("request response is ", data["access_token"])
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
        page_id = page.page_no

        fb = MyProductFb.objects.filter(published=False,obj_type="FEED",mypage_page_no= page_id).order_by("myresource__created_time").first()

        print("fb", fb)



        token = get_token(page_id)
        FacebookAdsApi.init(access_token=token)
        #domain = "http://dev.yallavip.com:8000"
        domain = "http://admin.yallavip.com"
        resource = str(fb.myresource.resource)
        destination_url = domain + os.path.join(settings.MEDIA_URL, resource)
        feed_post = None
        if fb.myresource.resource_cate == "VIDEO":
            print("视频")
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


        elif fb.myresource.resource_cate == "IMAGE":

            # 发图片post


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




        if feed_post:
            feed_post_id = feed_post.get_id()

            if feed_post_id:
                MyProductFb.objects.filter(pk=fb.pk).update(fb_id=feed_post_id, published=True,published_time=feed_post.created_time )

                print("Wow ", page_id, feed_post_id, feed_post.link)



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
    from shop.models import  ShopifyImage
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

