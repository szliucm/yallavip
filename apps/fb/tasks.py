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
from django.utils import timezone as dt

from prs.models import  Lightin_SPU
from prs.fb_action import get_token, ad_update_status

from prs.tasks import my_custom_sql, ad_tokens
from celery import shared_task, task
from django.db.models import Q

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
            print ("开始获取相册%s图片"%album)
            update_album_photos(album)

    #update_photos_handle()

def update_album_photos(album):
    album_no = album.album_no
    page_no = album.page_no
    
    # 重置原有相册的图片信息为不活跃
    album.active=False
    album.save()

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

        print ("get photo", name)
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

    update_photos_handle()

def download_album_photos(album):
    album_no = album.album_no
    page_no = album.page_no

    # 重置原有相册的图片信息为不活跃
    print()
    album.delete("download_album_photos", album)

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

def update_feed(page_no,days=30):

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

    fields = ["created_time",  "id", "message","likes.summary(true)", "comments.summary(true)"
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
                                                                  'message': feed.get("message"),
                                                                  'like_count': feed["likes"]["summary"][
                                                                      "total_count"],
                                                                  'comment_count': feed["comments"]["summary"]["total_count"],


                                                                  }
                                                        )

    mysql = "update prs_yallavipad a , fb_myfeed f set a.fb_feed_id = f.id where f.feed_no=a.object_story_id"
    my_custom_sql(mysql)

    update_feeds_handles()




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
    adaccount_id = "1903121643086425"
    get_adaccount_ads(adaccount_id)

    '''
    queryset = MyAdAccount.objects.filter(account_status ='1',active=True)
    for adaccount in queryset:
        get_adaccount_ads(adaccount.adaccount_no)
    '''


def get_adaccount_campaigns(adaccount_id):
    adobjects = FacebookAdsApi.init(access_token=ad_tokens, debug=True)

    fields = ['id',  'name', 'status','objective',
              'effective_status', 'created_time', 'updated_time'

              ]
    params = {
        # 'effective_status': ["ACTIVE"," PAUSED"," DELETED"," PENDING_REVIEW"," DISAPPROVED"," PREAPPROVED"," PENDING_BILLING_INFO"," CAMPAIGN_PAUSED"," ARCHIVED"," ADSET_PAUSED"," WITH_ISSUES",],
    }

    adaccount_no = "act_" + adaccount_id
    campaigns = AdAccount(adaccount_no).get_campaigns(fields=fields, params=params, )

    # 重置原有ad信息为不活跃
    MyCampaign.objects.filter(adaccount_no=adaccount_id).update(active=False)
    for campaign in campaigns:

        obj, created = MyCampaign.objects.update_or_create(campaign_no=campaign["id"],
                                                     defaults={
                                                         'adaccount_no': adaccount_id,
                                                         'campaign_no': campaign.get("id"),
                                                         'name': campaign.get("name"),
                                                         'objective': campaign.get("objective"),
                                                         'status': campaign.get("status"),
                                                         'effective_status': campaign.get("effective_status"),
                                                         'created_time': campaign.get("created_time"),
                                                         'updated_time': campaign.get("updated_time"),
                                                         'active': True,

                                                     }
                                                     )


def get_adaccount_ads(adaccount_id):

    adobjects = FacebookAdsApi.init(access_token=ad_tokens, debug=True)




    fields =['id','account_id','ad_review_feedback','adlabels','adset_id', 'campaign_id','name','status',
             'effective_status','creative','created_time','updated_time'

    ]
    params = {
        #'effective_status': ["ACTIVE"," PAUSED"," DELETED"," PENDING_REVIEW"," DISAPPROVED"," PREAPPROVED"," PENDING_BILLING_INFO"," CAMPAIGN_PAUSED"," ARCHIVED"," ADSET_PAUSED"," WITH_ISSUES",],
    }



    adaccount_no = "act_"+ adaccount_id
    ads = AdAccount(adaccount_no).get_ads(fields=fields, params=params, )

    # 重置原有ad信息为不活跃
    MyAd.objects.filter(account_no=adaccount_id).update(active=False)
    for ad in ads:
        campaign_no = ad.get("campaign_id")

        campaign_name = MyCampaign.objects.get(campaign_no = campaign_no ).name
        page_name = campaign_name.split("_")[0]
        page_no = campaign_name.split("_")[1]
        objective = campaign_name.split("_")[2]

        obj, created = MyAd.objects.update_or_create(ad_no=ad["id"],
                                                        defaults={
                                                            'adset_no': ad.get("adset_id"),
                                                            'name': ad.get("name"),
                                                            #'ad_review_feedback': ad.get("ad_review_feedback"),
                                                            #'adlabels': ad.get("adlabels"),
                                                            'account_no': ad.get("account_id"),
                                                            'campaign_no': campaign_no,
                                                            'campaign_name': campaign_name,
                                                            'page_name': page_name,
                                                            'page_no': page_no,
                                                            'objective': objective,
                                                            'status': ad.get("status"),
                                                            'effective_status': ad.get("effective_status"),
                                                            'created_time': ad.get("created_time"),
                                                            'updated_time': ad.get("updated_time"),
                                                            'active': True,

                                                                  }
                                                        )





def update_photos_handle():
    import  re
    myphotos = MyPhoto.objects.filter(active=True,handle="")
    for myphoto in myphotos:
        try:
            pattern = re.compile(r'[LlFf]\d{6}')
            m = pattern.search(myphoto.name)
            if m:
                myphoto.handle = m.group()
            else:
                myphoto.handle = ""

            '''
            tmp = re.split(r"\[|\]", myphoto.name)
            if (1 < len(tmp)):
                myphoto.handle = tmp[1]
            else:
                myphoto.handle = ""
            '''
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
    #mysql = " SELECT p.page_no, p.photo_no from fb_myphoto p, prs_lightin_spu s where p.active=True and p.handle = s.handle and s.handle<>'' and (s.sellable<=0  or s.fake=True)"
    mysql = " SELECT p.page_no, p.photo_no from fb_myphoto p, prs_lightin_spu s where p.active=True and p.handle = s.handle and s.handle<>'' and s.sellable<=0"
    photos = my_custom_sql(mysql)

    photo_miss = list_to_dict(photos)
    print("共有%s个图片待删除"%len(photo_miss))
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
            pattern = re.compile(r'[LlFf]\d{6}')
            m = pattern.findall(feed.message)

            handles = ",".join(m)

            '''
            tmp = re.split(r"\[|\]", feed.message)
            if 1 < len(tmp):
                handles = tmp[1]
            else:
                handles = ""
            '''
            print (handles)
            feed.handles = handles
            feed.save()

        except:
            print (feed.message)




@shared_task
def delete_outstock_feeds():
    from  prs.tasks import delete_posts
    import time

    feeds = MyFeed.objects.filter(~Q(handles=""), active=True, handles__isnull=False)
    feed_nos = []
    for feed in feeds:

        handles = feed.handles.split(",")
        spus_all = Lightin_SPU.objects.filter(handle__in=handles)
        spus_outstock = spus_all.filter(Q(sellable__lte=0)|Q(fake=True))
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
        spus_outstock = spus_all.filter(Q(sellable__lte=0),Q(fake=True))
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

def delete_nohandle_feeds(page_no, type):
    feeds = MyFeed.objects.filter(page_no=page_no, created_time__lt='2019-05-21')
    feed_nos = feeds.values_list("feed_no", flat=True)

    print("page %s 待删除数量 %s  " % (page_no, len(feed_nos)))


    delete_posts(page_no, feed_nos)

    MyFeed.objects.filter(feed_no__in=list(feed_nos)).update(active=False)

'''
@shared_task
def delete_outstock_ads():
    from prs.models import  YallavipAd

    #遍历所有活跃的广告，如果有spu已经无库存，就设置active为false，
    # 如果published为True,则将广告删除
    ads = YallavipAd.objects.filter(active=True)

    delete_outstock_ad(ads)



def delete_outstock_ad(ads):
    from prs.fb_action import ad_update_status
    import time
    ads_todelete = []

    for ad in ads:

        handles = ad.spus_name.split(",")
        spus_all = Lightin_SPU.objects.filter( handle__in=handles)
        spus_all.update(aded=False)

        spus_outstock = spus_all.filter(sellable__lte=0)
        if spus_outstock.count()>0:
            print("有spu无库存了", spus_outstock, ad, ad.ad_id)
            ads_todelete.append(ad)

    print("有 %s 条广告待删除"%len(ads_todelete))

    for ad in ads_todelete:

        # 修改广告状态
        ad_status = "DELETED"

        if ad.ad_status == "active":
            print("ad待删除")
            info, updated = ad_update_status(ad.ad_id, status=ad_status)
            if updated:
                ad.ad_status = ad_status
            else:
                ad.update_error = info
            time.sleep(20)

        if ad.engagement_ad_status == "active":
            print("engagement_ad待删除")
            info, updated = ad_update_status(ad.engagement_ad_id, status=ad_status)
            if updated:
                ad.engagement_ad_status = ad_status
            else:
                ad.engagement_ad_publish_error = info
            time.sleep(20)
        if ad.message_ad_status == "active":
            print("message_ad待删除")
            info, updated = ad_update_status(ad.message_ad_id, status=ad_status)
            if updated:
                ad.message_ad_status = ad_status
            else:
                ad.message_ad_publish_error = info
            time.sleep(20)

        ad.active=False
        ad.save()
'''
@shared_task
def delete_outstock_ads():
    ads = MyAd.objects.filter(active=True)
    delete_outstock_ad(ads)

def delete_outstock_ad(ads):

    import time

    ads_todelete = []

    for ad in ads:

        handles = ad.name.split("_")[-1].split(",")
        spus_all = Lightin_SPU.objects.filter(handle__in=handles)


        spus_outstock = spus_all.filter(Q(sellable__lte=0)|Q(fake=True))
        if spus_outstock.count() > 0:
            print("有spu无库存了", spus_outstock, ad )
            spus_all.update(aded=False)
            ads_todelete.append(ad)

    print("有 %s 条广告待删除" % len(ads_todelete))

    for ad in ads_todelete:

        # 修改广告状态
        ad_status = "DELETED"


        print("ad待删除")
        info, updated = ad_update_status(ad.ad_no, status=ad_status)
        if updated:
            ad.ad_status = ad_status
        else:
            ad.update_error = info
        time.sleep(30)



        ad.active = False
        ad.save()




@shared_task
def delete_outstock():
    update_albums()
    batch_update_photos(limit=None)
    batch_update_feed()
    batch_update_ad()

    delete_outstock_photos.apply_async((), queue='outstock')
    delete_outstock_feeds.apply_async((), queue='outstock')
    delete_outstock_ads.apply_async((), queue='outstock')



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


        for album in queryset:
            album_no = album.album_no
            page_no = album.page_no


            download_album_photos(access_token,page_no,album_no)
            album.updated = True
            album.save()

def download_album_photos(access_token,page_no,album_no):
    # 删掉原有相册的图片
    MyPhoto.objects.filter(album_no=album_no).delete()

    adobjects = FacebookAdsApi.init(access_token=access_token, debug=True)

    fields = ["id", "name"
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

                          active=True,
                          name=name,
                          handle=handle


                          )
        myphoto_list.append(myphoto)
    MyPhoto.objects.bulk_create(myphoto_list)
    #update_photos_handle()

def get_today():
    import pytz
    from datetime import datetime,timedelta
    from django.db.models.functions import TruncDate

    dubai = pytz.timezone('Asia/Dubai')
    now = datetime.now(dubai)
    today = datetime(now.year, now.month, now.day, tzinfo=dubai)

    return  today

def get_message_ads_insights():
    ads = MyAd.objects.filter(active=True, objective="message", effective_status__in=["PAUSED", "ACTIVE"])
    AdInsights.objects.update(active=False)

    for ad in ads:
        get_ads_insights(ad)

def get_ads_insights(ad):

    ad_no = ad.ad_no

    adobjects = FacebookAdsApi.init(access_token=ad_tokens, debug=True)

    fields =['spend','reach','actions','cost_per_action_type',

    ]
    params = {
        'date_preset' : 'today'

    }


    ads_insights = Ad(ad_no).get_insights(fields=fields, params=params )

    try:
        ads_insight = ads_insights[0]
    except:
        print("获取insight失败 ",ad, ads_insights)
        return

    actions = ads_insight.get("actions")
    cost_per_action_types = ads_insight.get("cost_per_action_type")

    conversaion_count = 0
    conversaion_cost = 0
    if actions:
        for action in actions:
            if action.get('action_type') == "onsite_conversion.messaging_first_reply":
                conversaion_count = action.get('value')
                break

        if int(conversaion_count) >0:
            for cost_per_action_type in cost_per_action_types:
                if cost_per_action_type.get('action_type') == "onsite_conversion.messaging_first_reply":
                    conversaion_cost = cost_per_action_type.get('value')
                    break


        obj, created = AdInsights.objects.update_or_create(ad_no=ad_no,
                                                           myad = ad,
                                                           ad_time = get_today(),
                                                        defaults={
                                                                  'reach' : int(ads_insight.get("reach")),
                                                                  'spend': int(float(ads_insight.get("spend"))),

                                                                  'action_type': "conversation",
                                                                  'action_count': int(conversaion_count),
                                                                  'action_cost': int(float(conversaion_cost)),
                                                                  'effective_status': ad.effective_status,
                                                                  'updated_time' : dt.now(),
                                                                  'active' : True

                                                                  }
                                                           )

def update_ads_status(ads, ad_status):
    import time

    for ad in ads:

        # 修改广告状态
        ad_status = ad_status

        # print("ad待删除")
        info, updated = ad_update_status(ad.ad_no, status=ad_status)
        if updated:
            ad.ad_status = ad_status
        else:
            ad.update_error = info
        time.sleep(30)

        ad.active = False
        ad.save()


def control_ads():

    today = get_today()
    #关闭效果不佳的活跃广告

    #花费超过10元，但没有成效的
    ads_topause = list(AdInsights.objects.filter(ad_time=today, effective_status="ACTIVE",action_count=0,spend__gt=10))
    print("没有成效的一共%s条 "%len(ads_topause))

    #单价超过7元的广告
    ads_topause += list(AdInsights.objects.filter(ad_time=today, effective_status="ACTIVE",action_cost__gte=7))
    print("贵的一共%s条 " % len(ads_topause))

    update_ads_status(ads_topause, "PAUSED")


    #重启便宜的广告
    ads_toactive = list(AdInsights.objects.filter(ad_time=today, effective_status="PAUSED", action_cost__lt=7))
    print("便宜的一共%s条 " % len(ads_toactive))
    update_ads_status(ads_toactive, "ACTIVE")







