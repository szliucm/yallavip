# Create your tasks here
from __future__ import absolute_import, unicode_literals

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


from fb.models import  *

import  requests, json

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
    print(r, r.text)


    # print("request response is ", data["access_token"])
    return data["access_token"]

def update_albums():
    adobjects = FacebookAdsApi.init(access_token=my_access_token, debug=True)
    queryset = MyPage.objects.filter(active= True, is_published= True)

    for row in queryset:
        page_no = row.page_no
        # 重置原有相册信息为不活跃
        myalbums =  MyAlbum.objects.filter(page_no=page_no)
        myalbums.update(active=False)


        fields = ["created_time", "description", "id",
                  "name", "count", "updated_time", "link",
                  #"likes.summary(true)", "comments.summary(true)"
                  ]
        params = {

        }
        albums = Page(page_no).get_albums(
            fields=fields,
            params=params,
        )

        for album in albums:
            obj, created = MyAlbum.objects.update_or_create(album_no=album["id"],
                                                            defaults={'page_no': page_no,
                                                                      'created_time': album["created_time"].split('+')[
                                                                          0],
                                                                      'updated_time': album["updated_time"].split('+')[
                                                                          0],

                                                                      'name': album["name"],
                                                                      'count': album["count"],

                                                                      'link': album["link"],
                                                                      'active': True,
                                                                      }
                                                            )
            #'like_count': album["likes"]["summary"]["total_count"],
            #'comment_count': album["comments"]["summary"]["total_count"],

            print("album is ", album)

    # 更新相册对应的主页外键
    # update fb_myalbum a , fb_mypage p set a.mypage_id = p.id where p.page_no = a.page_no
    from django.db import connection, transaction
    cursor = connection.cursor()
    cursor.execute("update fb_myalbum a , fb_mypage p set a.mypage_id = p.id where p.page_no = a.page_no")
    transaction.commit()

#批量更新相册内容
def batch_update_albums():

    queryset = MyAlbum.objects.filter(active=True)

    for row in queryset:
        album_no = row.album_no
        page = row.page_no
        adobjects = FacebookAdsApi.init(access_token=get_token(page), debug=True)
        # 重置原有相册的图片信息为不活跃
        MyPhoto.objects.filter(album_no=album_no).update(active=False)

        fields = ["id", "name", "created_time", "updated_time", "picture", "link",
                  "likes.summary(true)", "comments.summary(true)"
                  ]
        params = {

        }
        try:
            photos = Album(album_no).get_photos(
                fields=fields,
                params=params,
            )
        except Exception as e:
            print("获取Facebook数据出错", fields, e)
            continue
        n=0
        myphoto_list = []
        for photo in photos:
            try:
                name = photo["name"]
            except KeyError:
                name = ""
            '''
            obj, created = MyPhoto.objects.update_or_create(photo_no=photo["id"],
                                                            defaults={'page_no': row.page_no,
                                                                      'album_no': album_no,
                                                                      'created_time':
                                                                          photo["created_time"].split('+')[0],
                                                                      'updated_time':
                                                                          photo["updated_time"].split('+')[0],
                                                                      'active': True,
                                                                      'name': name,
                                                                      'picture': photo["picture"],
                                                                      'link': photo["link"],
                                                                      'like_count': photo["likes"]["summary"][
                                                                          "total_count"],
                                                                      'comment_count': photo["comments"]["summary"][
                                                                          "total_count"]

                                                                      }
                                                            )
            '''
            
            myphoto = MyPhoto(
                photo_no=photo["id"],
                page_no = row.page_no,
                          album_no = album_no,
                          created_time = photo["created_time"],
                          updated_time = photo["updated_time"],
                          active = True,
                          name = name,
                          picture = photo["picture"],
                          link = photo["link"],
                          like_count = photo["likes"]["summary"]["total_count"],
                          comment_count = photo["comments"]["summary"]["total_count"]
            )
            myphoto_list.append(myphoto)
            n += 1
            if n % 100 == 0:
                MyPhoto.objects.bulk_create(myphoto_list)
                myphoto_list = []


def batch_update_feed(self, request, queryset):
    adobjects = FacebookAdsApi.init(access_token=my_access_token, debug=True)
    queryset = MyPage.objects.filter(active=True, is_published=True)
    for row in queryset:
        page_no = row.page_no
        # 重置原有feed信息为不活跃
        MyFeed.objects.filter(page_no=page_no).update(active=False)

        fields = ["created_time", "description", "id",
                  "type", "message", "name",
                  "actions_link","actions_name",
                  "likes.summary(true)", "comments.summary(true)"
                  ]
        params = {

        }
        feeds = Page(page_no).get_feed(
            fields=fields,
            params=params,
        )

        for feed in feeds:
            obj, created = MyFeed.objects.update_or_create(feed_no=feed["id"],
                                                            defaults={'page_no': page_no,
                                                                      'created_time':
                                                                          feed["created_time"],
                                                                      'active': True,
                                                                      'message': feed.get("message"),
                                                                      'description': feed.get("description"),
                                                                      'name': feed.get("name"),
                                                                      'type': feed.get("type"),
                                                                      'actions_link': feed.get("actions_link"),
                                                                      'actions_name': feed.get("actions_name"),
                                                                      'like_count': feed["likes"]["summary"][
                                                                          "total_count"],
                                                                      'comment_count': feed["comments"]["summary"][
                                                                          "total_count"],


                                                                      }
                                                            )

            print("feed is ", feed)