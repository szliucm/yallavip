from .models import MyProductShopify,MyProductFb
from fb.models import MyFeed,MyPage,MyAd


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
    fbs = MyProductFb.objects.filter(published=False,obj_type="FEED")

    print("fbs", fbs)
    for fb in fbs:

        if fb.myresource.resource_cate != "IMAGE":
            print("不是图片")
            continue
        elif fb.myresource.resource_cate == "IMAGE":

            # 发图片post
            page_id = fb.mypage.page_no
            token = get_token(page_id)
            FacebookAdsApi.init(access_token=token)
            domain = "http://admin.yallavip.com"
            resource = str(fb.myresource.resource)
            destination_url = domain + os.path.join(settings.MEDIA_URL, resource)

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
            feed_post_with_image = Page(page_id).create_feed(
                fields=fields,
                params=params,
            )


            feed_post_with_image_id = feed_post_with_image.get_id()

            MyProductFb.objects.get(pk=fb.pk).update(fb_id=feed_post_with_image_id)

            print("Wow ", page_id, feed_post_with_image_id)




    return


#####################################
#########把表现较好的product发到feed
######################################
def post_product_feed():


    return