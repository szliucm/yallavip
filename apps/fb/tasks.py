# Create your tasks here
from __future__ import absolute_import, unicode_literals

import json
import requests
from facebook_business.adobjects.ad import Ad
from facebook_business.adobjects.adaccount import AdAccount
from facebook_business.adobjects.adset import AdSet
from facebook_business.adobjects.adsinsights import AdsInsights
from facebook_business.adobjects.album import Album
from facebook_business.adobjects.business import Business
from facebook_business.adobjects.campaign import Campaign
from facebook_business.adobjects.page import Page
from facebook_business.adobjects.photo import Photo
from facebook_business.adobjects.systemuser import SystemUser
from facebook_business.adobjects.user import User
from facebook_business.api import FacebookAdsApi
from facebook_business.exceptions import FacebookRequestError
from fb.models import *

from prs.models import  Lightin_SPU
from prs.fb_action import get_token

from prs.tasks import my_custom_sql, ad_tokens
from celery import shared_task, task

#更新相册信息
def update_albums():

    queryset = MyPage.objects.filter(active= True, is_published= True,promotable=True)

    for row in queryset:
        page_no = row.page_no
        access_token, long_token = get_token(page_no)

        if not access_token:
            error = "获取token失败"
            return error, None

        adobjects = FacebookAdsApi.init(access_token=access_token, debug=True)

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
                                                                      'created_time': album["created_time"],
                                                                      'updated_time': album["updated_time"],

                                                                      'name': album["name"],
                                                                      'count': album["count"],

                                                                      'link': album["link"],
                                                                      'active': True,
                                                                      'updated': False
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

#批量更新图片
def batch_update_photos(limit = None):
    page_no_list = MyPage.objects.filter(active=True, is_published=True, promotable=True).values_list("page_no",flat=True)
    for page_no in page_no_list:
        access_token, long_token = get_token(page_no)

        if not access_token:
            error = "获取token失败"
            print (error)
            continue
        queryset = MyAlbum.objects.filter(active=True,updated= False, page_no=page_no)
        adobjects = FacebookAdsApi.init(access_token=access_token, debug=True)
        
        for album in queryset:
            update_album_photos(album)



def update_album_photos(album):
    album_no = album.album_no
    page_no = album.page_no
    
    # 重置原有相册的图片信息为不活跃
    album.update(active=False)

    fields = ["id", "name", "created_time", "updated_time", "picture", "link",
              "likes.summary(true)", "comments.summary(true)"
              ]
    params = {
        'limit':100,

    }
    try:
        photos = Album(album_no).get_photos(
            fields=fields,
            params=params,
        )
    except Exception as e:
        print("获取Facebook数据出错", fields, e)
        return

    for photo in photos:
        try:
            name = photo["name"]
        except KeyError:
            name = ""

        obj, created = MyPhoto.objects.update_or_create(photo_no=photo["id"],
                                                        defaults={'page_no': page_no,
                                                                  'album_no': album_no,
                                                                  'created_time':
                                                                      photo["created_time"],
                                                                  'updated_time':
                                                                      photo["updated_time"],
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
    album.updated = True
    album.save()


# 批量更新图片
def batch_download_photos(limit=None):
    page_no_list = MyPage.objects.filter(active=True, is_published=True, promotable=True).values_list("page_no",
                                                                                                      flat=True)
    for page_no in page_no_list:
        access_token, long_token = get_token(page_no)

        if not access_token:
            error = "获取token失败"
            print(error)
            continue
        queryset = MyAlbum.objects.filter(active=True, updated=False, page_no=page_no)
        adobjects = FacebookAdsApi.init(access_token=access_token, debug=True)

        for album in queryset:
            download_album_photos(album)
            album.updated = True
            album.save()

def download_album_photos(album):
    album_no = album.album_no
    page_no = album.page_no

    # 重置原有相册的图片信息为不活跃
    album.delete()

    fields = ["id", "name", "created_time", "updated_time", "picture", "link",
              "likes.summary(true)", "comments.summary(true)"
              ]
    params = {
        'limit': 100,

    }
    try:
        photos = Album(album_no).get_photos(
            fields=fields,
            params=params,
        )
    except Exception as e:
        print("获取Facebook数据出错", fields, e)
        return
    myphoto_list = []
    for photo in photos:
        name = photo.get("name", ""),
        try:
            tmp = re.split(r"\[|\]", name)
            if (1 < len(tmp)):
                handle = tmp[1]
            else:
                handle = ""

        except:
            handle = ""

        myphoto = MyPhoto(photo_no=photo["id"],
                          page_no=page_no,
                          album_no=album_no,
                          created_time=photo["created_time"],
                          updated_time=photo["updated_time"],
                          active=True,
                          name=name,
                          handle=handle,
                          picture=photo["picture"],
                          link=photo["link"],
                          like_count=photo["likes"]["summary"]["total_count"],
                          comment_count=photo["comments"]["summary"]["total_count"]

                          )
        myphoto_list.append(myphoto)
    MyPhoto.objects.bulk_create(myphoto_list)


def batch_update_feed():

    page_no_list = MyPage.objects.filter(active=True, is_published=True, promotable=True).values_list("page_no",flat=True)
    for page_no in page_no_list:

        update_feed(page_no)

def update_feed(page_no,days=2):

    import  datetime
    access_token, long_token = get_token(page_no)
    if not access_token:
        error = "获取token失败"
        print (error)
        return
    adobjects = FacebookAdsApi.init(access_token=access_token, debug=True)

    today = datetime.date.today()
    start_time = str(today - datetime.timedelta(days=days))

    # 重置原有feed信息为不活跃
    MyFeed.objects.filter(page_no=page_no, created_time__gt=start_time).update(active=False)

    fields = ["created_time", "description", "id","full_picture",
              "type", "message", "name",
              "actions_link","actions_name",
              "likes.summary(true)", "comments.summary(true)"
              ]
    params = {
        'limit': 100,

    }
    feeds = Page(page_no).get_feed(
        fields=fields,
        params=params,
    )

    for feed in feeds:
        created_time = feed.get("created_time")
        print(created_time)
        if created_time < start_time:
            print ("%s天前的就不看了"%days)
            break

        obj, created = MyFeed.objects.update_or_create(feed_no=feed["id"],
                                                        defaults={'page_no': page_no,
                                                                  'created_time':
                                                                      feed["created_time"],
                                                                  'active': True,
                                                                  'message': feed.get("message"),
                                                                  "full_picture":feed.get("full_picture"),
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

    mysql = "update prs_yallavipad a , fb_myfeed f set a.fb_feed_id = f.id where f.feed_no=a.object_story_id"
    my_custom_sql(mysql)


def update_conversation(page_no,days=2):

    import  datetime
    access_token, long_token = get_token(page_no)
    if not access_token:
        error = "获取token失败"
        print (error)
        return
    adobjects = FacebookAdsApi.init(access_token=access_token, debug=True)

    today = datetime.date.today()
    start_time = str(today - datetime.timedelta(days=days))

    # 重置原有feed信息为不活跃
    MyFeed.objects.filter(page_no=page_no, created_time__gt=start_time).update(active=False)

    fields = ["created_time", "description", "id","full_picture",
              "type", "message", "name",
              "actions_link","actions_name",
              "likes.summary(true)", "comments.summary(true)"
              ]
    params = {
        'limit': 100,

    }
    feeds = Page(page_no).get_feed(
        fields=fields,
        params=params,
    )

    for feed in feeds:
        created_time = feed.get("created_time")
        print(created_time)
        if created_time < start_time:
            print ("%s天前的就不看了"%days)
            break

        obj, created = MyFeed.objects.update_or_create(feed_no=feed["id"],
                                                        defaults={'page_no': page_no,
                                                                  'created_time':
                                                                      feed["created_time"],
                                                                  'active': True,
                                                                  'message': feed.get("message"),
                                                                  "full_picture":feed.get("full_picture"),
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

    mysql = "update prs_yallavipad a , fb_myfeed f set a.fb_feed_id = f.id where f.feed_no=a.object_story_id"
    my_custom_sql(mysql)


def batch_update_adaccount():

    adobjects = FacebookAdsApi.init(access_token = my_access_token, debug=True)

    fields =["account_id","account_status","name","disable_reason",
    ]
    params = {

    }

    id = "2076017356044262"
    adaccounts = User(id).get_ad_accounts(fields=fields, params=params, )


    MyAdAccount.objects.update(active=False)
    for adaccount in adaccounts:
        print(adaccount)
        obj, created = MyAdAccount.objects.update_or_create(adaccount_no=adaccount["id"],
                                                        defaults={
                                                            'account_status': adaccount.get("account_status"),
                                                            'name': adaccount.get("name"),
                                                            'disable_reason': adaccount.get("disable_reason"),
                                                            'active': True



                                                                  }
                                                        )


def batch_update_ad():


    queryset = MyAdAccount.objects.filter(account_status ='1',active=True)
    for adaccount in queryset:
        get_adaccount_ads(adaccount)


def get_adaccount_ads(adaccount_no):

    adobjects = FacebookAdsApi.init(access_token=ad_tokens, debug=True)

    fields =['id','account_id','ad_review_feedback','adlabels','adset_id','campaign_id', 'name','status',
             'effective_status','creative','created_time','updated_time'

    ]
    params = {
        #'effective_status': ["ACTIVE"," PAUSED"," DELETED"," PENDING_REVIEW"," DISAPPROVED"," PREAPPROVED"," PENDING_BILLING_INFO"," CAMPAIGN_PAUSED"," ARCHIVED"," ADSET_PAUSED"," WITH_ISSUES",],
    }

    adaccount_no = "act_"+ adaccount_no
    ads = AdAccount(adaccount_no).get_ads(fields=fields, params=params, )

    # 重置原有ad信息为不活跃
    MyAd.objects.update(active=False)
    for ad in ads:
        obj, created = MyAd.objects.update_or_create(ad_no=ad["id"],
                                                        defaults={
                                                            'adset_no': ad.get("adset_id"),
                                                            'name': ad.get("name"),
                                                            #'ad_review_feedback': ad.get("ad_review_feedback"),
                                                            #'adlabels': ad.get("adlabels"),
                                                            'account_no': ad.get("account_id"),
                                                            'campaign_no': ad.get("campaign_id"),
                                                            'status': ad.get("status"),
                                                            'effective_status': ad.get("effective_status"),
                                                            'created_time': ad.get("created_time"),
                                                            'updated_time': ad.get("updated_time"),
                                                            'active': True,

                                                                  }
                                                        )





def update_photos_handle():
    import  re
    myphotos = MyPhoto.objects.filter(active=True)
    for myphoto in myphotos:
        try:
            tmp = re.split(r"\[|\]", myphoto.name)
            if (1 < len(tmp)):
                myphoto.handle = tmp[1]
            else:
                myphoto.handle = ""

        except:
            myphoto.handle = ""

        myphoto.save()


def delete_photos(page_no, photo_nos):
    from facebook_business.adobjects.photo import Photo
    access_token, long_token = get_token(page_no)
    if not access_token:
        error = "获取token失败"
        print(error, page_no)

        return error, None

    FacebookAdsApi.init(access_token=access_token)
    photo_deleted = []
    for photo_no in photo_nos:

        fields = [
        ]
        params = {

        }
        try:
            response = Photo(photo_no).api_delete(
                fields=fields,
                params=params,
            )
        except Exception as e:
            print("删除图片出错", photo_no, e)

        print("删除相册图片 LightinAlbum %s" % (photo_no))
        photo_deleted.append(photo_no)
    MyPhoto.objects.filter(photo_no__in = photo_deleted).delete()

def list_to_dict(photos):
    photo_miss = {}

    for photo in photos:
        page_no = photo[0]
        fb_id = photo[1]
        photo_list = photo_miss.get(page_no)
        if not photo_list:
            photo_list = []

        if fb_id not in photo_list:
            photo_list.append(fb_id)

        photo_miss[page_no] = photo_list
    return photo_miss

@shared_task
def delete_outstock_photos():
    mysql = " SELECT p.page_no, p.photo_no from fb_myphoto p, prs_lightin_spu s where p.handle = s.handle and sellable<=0"
    photos = my_custom_sql(mysql)

    photo_miss = list_to_dict(photos)
    for page_no in photo_miss:

        photo_nos = photo_miss[page_no]
        print("page %s 待删除数量 %s  " % (page_no, len(photo_nos)))


        if photo_nos is None or len(photo_nos) == 0:
            continue

        delete_photos(page_no, photo_nos)

def update_feeds_handles():
    import re
    feeds = MyFeed.objects.filter(active=True)
    for feed in feeds:
        try:
            tmp = re.split(r"\[|\]", feed.message)
            if 1 < len(tmp):
                handles = tmp[1]
            else:
                handles = ""
            print (handles)
            feed.handles = handles
            feed.save()

        except:
            print (feed.message)




@shared_task
def delete_outstock_feeds():
    from  prs.tasks import delete_posts
    import time

    feeds = MyFeed.objects.filter(active=True, handles__isnull=False)
    feed_nos = []
    for feed in feeds:

        handles = feed.handles.split(",")
        spus_all = Lightin_SPU.objects.filter(handle__in=handles)
        spus_outstock = spus_all.filter(sellable__lte=0)
        if spus_outstock.count() > 0:
            print("有spu无库存了", spus_outstock, feed, feed.feed_no)
            feed_nos.append((feed.page_no,feed.feed_no))

    feed_miss = list_to_dict(feed_nos)
    for page_no in feed_miss:

        feed_nos = feed_miss[page_no]
        print("page %s 待删除数量 %s  " % (page_no, len(feed_nos)))
        if feed_nos is None or len(feed_nos) == 0:
            continue

        delete_posts(page_no, feed_nos)

        MyFeed.objects.filter(feed_no__in=feed_nos).update(active=False)

def delete_nohandle_feeds():
    feeds = MyFeed.objects.filter(active=True, handle__isnull=True)
    feed_nos = []
    for feed in feeds:

        spus_all = Lightin_SPU.objects.filter(handle__in=handles)
        spus_outstock = spus_all.filter(sellable__lte=0)
        if spus_outstock.count() > 0:
            print("有spu无库存了", spus_outstock, feed, feed.feed_no)
            feed_nos.append((feed.page_no, feed.feed_no))

    feed_miss = list_to_dict(feed_nos)
    for page_no in feed_miss:

        feed_nos = feed_miss[page_no]
        print("page %s 待删除数量 %s  " % (page_no, len(feed_nos)))
        if photo_nos is None or len(photo_nos) == 0:
            continue

        delete_posts(page_no, feed_nos)

        MyFeed.objects.filter(feed_no__in=feed_nos).update(active=False)




