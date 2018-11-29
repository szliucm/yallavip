from facebook_business.api import FacebookAdsApi
from facebook_business.adobjects.page import Page
from facebook_business.adobjects.photo import Photo

import requests
import json

APP_SCOPED_SYSTEM_USER_ID=100029952330435
my_access_token = "EAAHZCz2P7ZAuQBABHO6LywLswkIwvScVqBP2eF5CrUt4wErhesp8fJUQVqRli9MxspKRYYA4JVihu7s5TL3LfyA0ZACBaKZAfZCMoFDx7Tc57DLWj38uwTopJH4aeDpLdYoEF4JVXHf5Ei06p7soWmpih8BBzadiPUAEM8Fw4DuW5q8ZAkSc07PrAX4pGZA4zbSU70ZCqLZAMTQZDZD"

def get_token(target_page):

    url = "https://graph.facebook.com/v3.2/{}?fields=access_token".format(target_page)
    param = dict()
    param["access_token"] = my_access_token

    r = requests.get(url, param)

    data = json.loads(r.text)

    #print("request response is ", data["access_token"])
    return data["access_token"]


def create_page_feed(mypage, myphoto):
    # 发图片post
    page_id = mypage.page_no

    FacebookAdsApi.init(access_token=get_token(page_id))

    #获取图片地址
    url = "https://graph.facebook.com/v3.2/{}?fields=height,images".format(myphoto.photo_no)
    param = dict()
    param["access_token"] = my_access_token

    r = requests.get(url, param)

    data = json.loads(r.text)
    print("data is ", data)

    '''
    fields = ["height","images"
              ]
    params = {

    }
    photo = Photo(myphoto.photo_no).api_get(
        fields=fields,
        params=params,
    )
    print("photo is ", photo)
    '''




    image_url = None
    images = data.get("images")
    height = data.get("height")
    for image in images:
        if image.get("height") == height:
            image_url = image.get("source")
            break
        else:
            continue

    if not image_url:
        print("no image exist ")
        return

    fields = [
    ]
    params = {
        'url': image_url,
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
        'message': mypage.message + "\n" +  myphoto.name,
        'attached_media': [{'media_fbid': photo_to_be_post_id}],
    }
    feed_post_with_image = Page(page_id).create_feed(
        fields=fields,
        params=params,
    )
    feed_post_with_image_id = feed_post_with_image.get_id()

    print("Wow ", feed_post_with_image_id)

    return