# -*- coding: utf-8 -*-
__author__ = 'Aaron'


import requests
import json
import time
from django.utils import timezone as datetime
import  re

import xadmin
from django.utils.safestring import mark_safe
from facebook_business.api import FacebookAdsApi
from facebook_business.exceptions import FacebookRequestError


from facebook_business.adobjects.systemuser import SystemUser
from facebook_business.adobjects.page import Page
from facebook_business.adobjects.pagepost import PagePost
from facebook_business.adobjects.album import Album
from facebook_business.adobjects.photo import Photo
from facebook_business.adobjects.adaccount import AdAccount
from facebook_business.adobjects.campaign import Campaign
from facebook_business.adobjects.adset import AdSet
from facebook_business.adobjects.ad import Ad
from facebook_business.adobjects.adsinsights import AdsInsights



from django.shortcuts import get_object_or_404,get_list_or_404,render
from import_export import resources,fields
from import_export.widgets import ForeignKeyWidget
from .models import  *



from .page_action import ConnectPageCategory
from  prs.models import  LightinAlbum

from prs.fb_action import  get_token

@xadmin.sites.register(MyPage)
class MyPageAdmin(object):
    def show_logo(self, obj):

        try:
            img = mark_safe('<img src="%s" width="100px" />' % (obj.logo.url,))
        except Exception as e:
            img = ''
        return img

    show_logo.short_description = 'Logo'
    show_logo.allow_tags = True

    def show_price(self, obj):

        try:
            img = mark_safe('<img src="%s" width="100px" />' % (obj.price.url,))
        except Exception as e:
            img = ''
        return img

    show_price.short_description = '价格标签'
    show_price.allow_tags = True

    def show_promote(self, obj):

        try:
            img = mark_safe('<img src="%s" width="100px" />' % (obj.promote.url,))
        except Exception as e:
            img = ''
        return img

    show_promote.short_description = '促销标签'
    show_promote.allow_tags = True

    def show_promote_1(self, obj):

        try:
            img = mark_safe('<img src="%s" width="100px" />' % (obj.promote_1.url,))
        except Exception as e:
            img = ''
        return img

    show_promote_1.short_description = '促销标签'
    show_promote_1.allow_tags = True



    #actions = ["batch_updatepage", ]
    list_display = ('page', 'page_no','is_published','active','link','message',  'show_logo','show_price','show_promote','show_promote_1','promote_template', 'promotable',
                   )

    list_editable = ['active','promotable',]
    #search_fields = ['logistic_no', ]
    list_filter = ('is_published','active',)
    actions = ["batch_update_accounts","batch_update_feed", ConnectPageCategory,"batch_update_albums","batch_update_ads",]

    filter_horizontal = ('promote_template',)
    style_fields = {'promote_template': 'm2m_transfer',
                    }

    def batch_update_accounts(self, request, queryset):

        url = "https://graph.facebook.com/v3.3/me/accounts"
        param = dict()
        param["access_token"] = my_access_token
        param["limit"] = "100"

        #param["fields"] = fields

        r = requests.get(url, param)

        data = json.loads(r.text)
        print("data is ",data)

        for page in data["data"]:


            # Switch access token to page access token
            page_id = page["id"]

            FacebookAdsApi.init(access_token=get_token(page_id))
            # Page feed create
            fields = ['about','is_published','link',
            ]
            params = {

            }
            page_info = Page(page_id).api_get(
                fields=fields,
                params=params,
            )
            print( 'page_info', page_info)

            obj, created = MyPage.objects.update_or_create(page_no=page["id"],
                                                           defaults={'page': page["name"],
                                                                     'access_token': page["access_token"],
                                                                     'is_published':page_info.get("is_published"),
                                                                     'link': page_info.get("link"),
                                                                     }
                                                           )

            print("page is ", page["access_token"], page["name"], page["id"])




    batch_update_accounts.short_description = "批量更新accounts"





    def batch_update_albums(self, request, queryset):
        adobjects = FacebookAdsApi.init(access_token=my_access_token, debug=True)
        for row in queryset:
            page_no = row.page_no
            #重置原有相册信息为不活跃
            MyAlbum.objects.filter(page_no=page_no).update(active=False)

            fields = ["created_time","description","id",
                      "name", "count", "updated_time", "link",
                      "likes.summary(true)","comments.summary(true)"
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
                                                                        'created_time': album["created_time"].split('+')[0],
                                                                        'updated_time': album["updated_time"].split('+')[0],
                                                                       
                                                                        'name': album["name"],
                                                                        'count': album["count"],
                                                                        'like_count': album["likes"]["summary"]["total_count"],
                                                                        'comment_count': album["comments"]["summary"]["total_count"],
                                                                        'link': album["link"],
                                                                         'active': True,
                                                                         }
                                                               )

                print("album is ", album)

        # 更新相册对应的主页外键
        # update fb_myalbum a , fb_mypage p set a.mypage_id = p.id where p.page_no = a.page_no
        from django.db import connection, transaction
        cursor = connection.cursor()
        cursor.execute("update fb_myalbum a , fb_mypage p set a.mypage_id = p.id where p.page_no = a.page_no")
        transaction.commit()


    batch_update_albums.short_description = "批量下载相册信息"

    def batch_update_feed(self, request, queryset):
        from fb.tasks import update_feed

        for row in queryset:
            update_feed(row.page_no)

    batch_update_feed.short_description = "批量下载feed信息"

    def batch_update_ad(self, request, queryset):
        adobjects = FacebookAdsApi.init(access_token=my_access_token, debug=True)
        for row in queryset:
            page_no = row.page_no
            # 重置原有相册信息为不活跃
            #MyFeed.objects.filter(page_no=page_no).update(active=False)

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

    batch_update_ad.short_description = "批量下载ad信息"

    def batch_update_ads(self, request, queryset):
        url = "https://graph.facebook.com/v3.3/me/adaccounts"
        param = dict()
        param["access_token"] = my_access_token
        param["limit"] = "100"


        param["fields"] = 'id,account_status,name'

        r = requests.get(url, param)

        data = json.loads(r.text)
        # print("data is ",data)

        for ad in data["data"]:
            obj, created = MyAdAccount.objects.update_or_create(adaccount_no=ad["id"],
                                                           defaults={'account_status': ad["account_status"],
                                                                     'name': ad["name"],
                                                                     }
                                                           )

            #print("page is ", page["access_token"], page["name"], page["id"])

    batch_update_ads.short_description = "批量更新广告账户"



@xadmin.sites.register(MyFeed)
class MyFeedAdmin(object):
    def show_pic(self, obj):

        try:
            img = mark_safe(
                '<img src="%s" width="100px">' % (obj.full_picture))

        except Exception as e:
            img = ''
        return img

    show_pic.short_description = 'full_picture'
    show_pic.allow_tags = True

    list_display = ["page_no", "feed_no", "type","show_pic", "sku","created_time", "actions_link", "actions_name", "share_count",
                    "comment_count", "like_count", "message",]
    list_filter = ('page_no','active')
    search_fields = ['feed_no', "page_no","message",]
    actions = ["batch_delete_post",]


    def create_page_feed(self, request, queryset):
        # 发图片post
        page_id = "358078964734730"
        token = get_token(page_id)
        FacebookAdsApi.init(access_token=token)
        fields = [
        ]
        params = {
            'url': 'https://www.facebook.com/images/fb_icon_325x325.png',
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
            'message': 'I have something good for you!',
            #'link': "https://facebook.com/%s"%(page_id),
            'name': 'YallaVip great',
            'description': 'forever love',
            'picture': 'https://cdn.shopify.com/s/files/1/2729/0740/products/IL201712291311123168_796_1400x.jpg',
            'published': '0',
            "call_to_action": {
                    "type": "MESSAGE_PAGE",
                    "value": {
                      "link": "https://facebook.com/%s"%(page_id),
                      "link_title": "Yallavip Kids",
                      "link_description": "E-commerce Website"
                    }
                  },
        }
        feed_post_with_image = Page(page_id).create_feed(
            fields=fields,
            params=params,
        )
        feed_post_with_image_id = feed_post_with_image.get_id()

        print("feed_post_with_image_id", feed_post_with_image_id)
    create_page_feed.short_description = "创建新feed"

    def batch_delete_post(self, request, queryset):
        # 定义actions函数


        page_no = queryset[0].page_no

        access_token, long_access_token = get_token(page_no)
        adobjects = FacebookAdsApi.init(access_token=access_token, debug=True)
        for row in queryset:
            # 一次删除一个page的,不同page的直接跳过

            if row.page_no != page_no:
                continue

            fields = [
                      ]
            params = {


            }
            feeds = PagePost(row.feed_no).api_delete(
                fields=fields,
                params=params,
            )

            row.active = False
            row.save()

    batch_delete_post.short_description = "批量删除Post"


    def batch_update_sku(self, request, queryset):
        # 定义actions函数
        for row in queryset:

            tmp = re.split(r"\[|\]", str(row.message))

            if (1 < len(tmp)):
                sku = tmp[1]
                Feed.objects.filter(feed_no=row.feed_no).update(sku=sku)


    batch_update_sku.short_description = "批量更新sku"

@xadmin.sites.register(MyAdAccount)
class MyAdAccountAdmin(object):

    list_display = [ "adaccount_no",'name','account_status' ]
    search_fields = ['adaccount_no', ]
    actions = [ "batch_update_campaigns",'create_campaign']
    list_filter = ('active',)

    def create_campaign(self, request, queryset):

        FacebookAdsApi.init(access_token=my_access_token)
        for row in queryset:
            fields = [
            ]
            params = {
                'name': 'My campaign for messenger',
                'objective': 'LINK_CLICKS',
                'status': 'PAUSED',
            }

            campaign = AdAccount(row.adaccount_no).create_campaign(
                            fields=fields,
                            params=params,
                        )
            print("campaign is ", campaign)
    create_campaign.short_description = "创建campaign"


    def batch_update_campaigns(self, request, queryset):
        adobjects = FacebookAdsApi.init(access_token=my_access_token_dev, debug=True)
        for row in queryset:
            adaccount_no = row.adaccount_no
            fields = ['id','name',
                        'objective',
            ]
            params = {
                'effective_status': ['ACTIVE', 'PAUSED'],
            }
            campaigns = AdAccount(adaccount_no).get_campaigns(fields=fields, params=params, )
            MyCampaign.objects.filter(adaccount_no=adaccount_no).update(active = False)
            for campaign in campaigns:
                obj, created = MyCampaign.objects.update_or_create(campaign_no=campaign["id"],
                                                                defaults={
                                                                        'adaccount_no': adaccount_no,
                                                                          'name':campaign["name"],
                                                                          'objective':  campaign["objective"],
                                                                        'active':True

                                                                          }
                                                                )



    batch_update_campaigns.short_description = "批量更新广告系列"

    def update_ad(self, request, queryset):
        # 定义actions函数

        APP_SCOPED_SYSTEM_USER_ID = "100029952330435"
        #page_id = "437797513321974"
        #page_access_token = get_token(page_id)
        adobjects = FacebookAdsApi.init(access_token=my_access_token,debug=True)

        fields = [
                  ]
        params = {

        }
        pages = SystemUser(APP_SCOPED_SYSTEM_USER_ID).get_assigned_pages(fields=fields, params=params)
        #print("pages is ", pages)

        #for page in pages:
         #   print("page is ", page,page["name"],page["id"])



        '''
        my_account = AdAccount('act_1173703482769259')
        campaigns = my_account.get_campaigns()
        print(campaigns)
      

        fields = ["name",
        ]
        params = {

        }
        page = Page(page_id).api_get(fields=fields, params=params)
        print("page is ",page)
       
        #发起会话
        fields = [
        ]
        params = {
        }
        conversationss = Page( page_id).get_conversations(
            fields=fields,
            params=params,
        )
        conversations_id = conversationss[0].get_id()
        print("conversationss", conversationss)

        #发图片post

        fields = [
        ]
        params = {
            'url': 'https://www.facebook.com/images/fb_icon_325x325.png',
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
            'message': 'I have something good for you!',
            'attached_media': [{'media_fbid': photo_to_be_post_id}],
        }
        feed_post_with_image = Page(page_id).create_feed(
            fields=fields,
            params=params,
        )
        feed_post_with_image_id = feed_post_with_image.get_id()
        '''
        '''
        fields = [
        ]
        params = {
        }
        
        PagePost(feed_post_with_image_id).api_delete(
            fields=fields,
            params=params,
        )
       
        fields = [
        ]
        params = {
        }
        feeds = Page(page_id).get_feed(
                        fields=fields,
                        params=params,
                )

        print(len(feeds))

 '''

    update_ad.short_description = "批量更新ad"

@xadmin.sites.register(MyCampaign)
class MyCampaignAdmin(object):

    list_display = [ "adaccount_no","campaign_no",'name','objective' ]
    search_fields = ['campaign_no', ]
    actions = [ "batch_update_adset","batch_update_insight",]
    list_filter = ( "active",)



    def batch_update_adset(self, request, queryset):
        adobjects = FacebookAdsApi.init(access_token=my_access_token, debug=True)
        for row in queryset:
            adaccount_no = row.adaccount_no
            campaign_no = row.campaign_no
            fields =[ "attribution_spec","bid_amount","bid_info","billing_event","budget_remaining",
                      "campaign","configured_status","created_time","destination_type",
                      "effective_status","id","is_dynamic_creative","lifetime_imps","name",
                      "optimization_goal","recurring_budget_semantics","source_adset_id",
                      "start_time","status","targeting","updated_time","use_new_app_click",


            ]
            params = {
                #'effective_status': ['ACTIVE', 'PAUSED'],
            }
            adsets = Campaign(campaign_no).get_ad_sets(fields=fields, params=params, )
            print("campaign_no is ", campaign_no)
            print("adsets is ", adsets)

            for adset in adsets:
                obj, created = MyAdset.objects.update_or_create(adset_no=adset["id"],
                                                                defaults={
                                                                        'adaccount_no':adaccount_no,
                                                                        'campaign_no': campaign_no,
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
                                                                        'start_time': adset["start_time"].split('+')[0],
                                                                        'status': adset["status"],
                                                                        #'targeting': adset["targeting"],
                                                                        'updated_time': adset["updated_time"].split('+')[0],
                                                                        'use_new_app_click': adset["use_new_app_click"],

                                                                          }
                                                                )

    batch_update_adset.short_description = "批量更新广告组"

    def batch_update_insight(self, request, queryset):
        adobjects = FacebookAdsApi.init(access_token=my_access_token, debug=True)
        for row in queryset:
            campaign_no = row.campaign_no
            fields = [
                AdsInsights.Field.impressions,
                AdsInsights.Field.inline_link_clicks,
                AdsInsights.Field.spend,
            ]

            params = {
                'end_time': int(time.time()),
            }
            insights = Campaign(campaign_no).get_insights(fields=fields, params=params, )
            print("insights is ", insights)
            '''
            for adset in adsets:
                obj, created = MyAdset.objects.update_or_create(adset_no=adset["id"],
                                                                defaults={
                                                                        'campaign_no': campaign_no,
                                                                          'name':adset["name"],

                                                                          }
                                                                )
            '''
    batch_update_insight.short_description = "批量更新广告系列统计"

@xadmin.sites.register(MyAdset)
class MyAdsetAdmin(object):

    list_display = [ "adset_no","campaign_no",'name', ]
    search_fields = ['adset_no',"campaign_no", ]
    actions = ["batch_update_ad", ]

    def create_adset(self, request, queryset):
        app_secret = '<APP_SECRET>'
        app_id = '<APP_ID>'
        id = '<ID>'
        today = datetime.date.today()
        start_time = str(today + datetime.timedelta(weeks=1))
        end_time = str(today + datetime.timedelta(weeks=2))

        FacebookAdsApi.init(access_token=my_access_token)
        for row in queryset:
            ad_account = row.adaccount_no
            campaign = row.campaign_no
            adset = AdSet(parent_id='act_<AD_ACCOUNT_ID>')
            adset.update({
                             AdSet.Field.name: ad_account,
                             AdSet.Field.campaign_id: campaign,
                         AdSet.Field.daily_budget: 1000,
            AdSet.Field.billing_event: AdSet.BillingEvent.impressions,
            AdSet.Field.optimization_goal: AdSet.OptimizationGoal.reach,
            AdSet.Field.bid_amount: 2,
            AdSet.Field.targeting: "targeting",
            AdSet.Field.start_time: start_time,
            AdSet.Field.end_time: end_time,
            })

            new_adset = adset.remote_create(params={
                'status': AdSet.Status.paused,
            })
            print("new_adset is ", new_adset)

    create_adset.short_description = "创建adset"

    def batch_update_ad(self, request, queryset):
        adobjects = FacebookAdsApi.init(access_token=my_access_token, debug=True)

        for row in queryset:
            adset_no = row.adset_no

            fields =['id', 'name','configured_status','effective_status','creative',

            ]
            params = {
                'effective_status': [ 'ACTIVE',
                            'PAUSED',
                            'PENDING_REVIEW',
                            'PREAPPROVED',],
            }
            ad_set =  AdSet(adset_no)


            ads = ad_set.get_ads(fields=fields, params=params, )


            for ad in ads:
                obj, created = MyAd.objects.update_or_create(ad_no=ad["id"],
                                                                defaults={
                                                                        'adset_no': adset_no,
                                                                          'name':ad["name"],

                                                                          }
                                                                )

    batch_update_ad.short_description = "批量更新广告"

@xadmin.sites.register(MyAd)
class MyAdAdmin(object):
    def sellable(self, obj):
        try:
            print("*****************0801*******", obj,obj.handle)
            spu = Lightin_SPU.objects.filter(handle=obj.handle)[0]
            print("*****************0801*******", spu)
        except:
            return 0

        return spu.sellable


    sellable.short_description = "sellable"


    list_display = [ "ad_no","adset_no",'name','handle', 'sellable']
    search_fields = ['ad_no', 'name',]
    actions = ["delete_ad", ]

    def create_ad(self, request, queryset):
        adobjects = FacebookAdsApi.init(access_token=my_access_token, debug=True)
        adacount_no = "act_204167083636030"

        adset_no = "23843044646580352"
        page_no = "437797513321974"
        post_no = "517466685355056"
        object_story_id = "437797513321974_575184079583316"



        fields = [
        ]
        params = {
            'name': 'Sample Promoted Post',
            'object_story_id': object_story_id,


        }
        

        '''
        fields = [
        ]
        params = {
            'name': 'Creative',
            'object_story_spec': {'page_id':page_no,
                                  'link_data': {"call_to_action": {"type":"LEARN_MORE","value":{"app_destination":"MESSENGER"}},
                                                    "image_hash": "6d42665300dafb604e033806527b34b8",
                                                    "link": "https://business.facebook.com/yallavip",
                                                    "message": "Welcome to the fancy world!", }},
        }
        '''
        adCreativeID = AdAccount(adacount_no).create_ad_creative(
            fields=fields,
            params=params,
        )

        print("adCreativeID is ", adCreativeID)

        fields = [
        ]
        params = {
            'name': 'My Ad '+object_story_id,
            'adset_id': adset_no,
            'creative': {'creative_id': adCreativeID["id"]},
            'status': 'DFAFT',
        }

        new_ad =  AdAccount(adacount_no).create_ad(
            fields=fields,
            params=params,
        )

        print("new ad is ", new_ad)



    create_ad.short_description = "创建广告"

    def delete_ad(self, request, queryset):
        '''
        curl \
        - F
        "status=DELETED" \
        - F
        "access_token=<ACCESS_TOKEN>" \
        "https://graph.facebook.com/<API_VERSION>/<AD_ID>"
        '''

        for ad in queryset:

            url = "https://graph.facebook.com/v3.3/%s"%(ad.ad_no)
            param = dict()
            param["access_token"] = my_access_token
            param["status"] = "DELETED"

            r = requests.post(url, param)

            print("response of delete ad is ",r)

        #删掉本地数据库的记录
        queryset.update(local_status="DELETED")

        return


    delete_ad.short_description = "删除广告"
@xadmin.sites.register(MyAlbum)
class MyAlbumAdmin(object):

    def page_url_field(self, obj):
        return '<a href="%s">%s</a>' % ('http://url-to-prepend.com/', obj.url_field)

    page_url_field.allow_tags = True
    page_url_field.short_description = 'Page'

    def mypage(self, obj):
        return obj.myalbum.mypage.page

    mypage.short_description = "主页"

    def show_album_promte(self, obj):

        try:
            img = mark_safe('<img src="%s" width="100px" />' % (obj.album_promte.url))
        except Exception as e:
            img = ''
        return img

    show_album_promte.short_description = '相册促销标'
    show_album_promte.allow_tags = True

    def published_count(self, obj):
        return LightinAlbum.objects.filter(myalbum__pk = obj.pk,published= True).count()
    published_count.short_description = "已发布图片数量"

    def readypublish_count(self, obj):
        return LightinAlbum.objects.filter(myalbum__pk = obj.pk,published= False, material=True).count()
    readypublish_count.short_description = "待发布图片数量"

    def topublish_count(self, obj):
        return LightinAlbum.objects.filter(myalbum__pk = obj.pk,published= False).count()
    topublish_count.short_description = "可发布图片数量"


    list_display = [ "album_no","mypage", "name", "cates", "prices","attrs","show_album_promte", "count", "like_count", "comment_count","created_time",]
    #"published_count","readypublish_count","topublish_count",
    list_editable = ["cates", "prices","attrs",]
    search_fields = ['album_no',  "name",]
    list_filter = ("mypage","active", )
    ordering = ["-count"]
    actions = ["batch_update_albums", ]

    def get_data(self, target_page, token,  fields ):
        """
        This method will get the feed data
        """
        url = "https://graph.facebook.com/v3.3/{}/photos".format(target_page)
        param = dict()
        param["access_token"] = token
        param["limit"] = "100"

        param["fields"] = fields
        try:
            r = requests.get(url, param)
        except Exception as e:
            print("获取Facebook数据出错",fields, r,e)
            return  None


        data = json.loads(r.text)


        return data

    def convert_data(self, album_no, response_json_list):
        '''This method takes response json data and convert to csv'''
        for response_json in response_json_list:


            try:
                data = response_json["data"]
            except KeyError:
                print("convert_photo_data {} completed")
                break

            for i in range(len(data)):

                row = data[i]
                photo_no = row["id"]


                try:
                    created_time = row["created_time"].split('+')[0]
                except KeyError:
                    created_time = ""

                try:
                    #name = row["name"].encode('utf-8')[:499]
                    name = row["name"]
                except KeyError:
                    name = ""

                try:
                    image = row["images"][0]["source"]

                except KeyError:
                    image = ""

                try:
                    link = row["link"]
                except KeyError:
                    link = ""
                try:
                    comment_count = row["comments"]["summary"]["total_count"]
                except KeyError:
                    comment_count = ""
                try:
                    like_count = row["likes"]["summary"]["total_count"]
                except KeyError:
                    like_count = ""


                #print("feed %s长度 is name %s message %s, des %s"%(feed_no, len(name), len(message),len(description)) )
                #print("message is ", message)

                obj, created = MyPhoto.objects.update_or_create(photo_no=photo_no,
                                                                defaults={'album_no' : album_no,
                                                                          'photo_no': photo_no,

                                                                          'created_time': created_time,
                                                                          'name': name,

                                                                          'image': image,
                                                                          'link': link,

                                                                          'comment_count': comment_count,
                                                                          'like_count': like_count,
                                                                        }
                                                                     )
                #print("update feed %s ok"%(feed_no))



        return


    def update(self, album_no, token):
        field_input = 'id,created_time,name,images,link,\
                    likes.summary(true),comments.summary(true)'


        json_list = []
        i = 0

        try:
            data = self.get_data(album_no, token, field_input)
            if not data:
                return  None
            json_list.append(data)
        except KeyError:
            print("Error with get request.")
            return

        while True:
            try:
                i = i + 100
                print("i = %s"%(i))
                next = data["paging"]["next"]
                r = requests.get(next.replace("limit=25", "limit=100"))
                data = json.loads(r.text)
                json_list.append(data)
            except KeyError:
                print("Phontoes for the album {} completed".format(album_no))
                # conversation_dic[conversation_id] = date_since
                # createDictCSV('conversation_dic.csv', conversation_dic)

                break


        self.convert_data(album_no,json_list)
        #messages_table_list = self.convert_messages_data( json_list, date_since)
        #if(len(messages_table_list)>0):
        #    self.create_table(messages_table_list, '/root/data/messages_' + target_page + '_'+ now_time.strftime("%Y-%m-&d %H:%M:%S")+'.csv', target_page, "messages")

    def batch_update(self, request, queryset):
        # 定义actions函数



        for row in queryset:
            album_no = row.album_no
            page_no = Album.objects.get(album_no=row.album_no).page_no
            token = get_token(page_no)


            self.update(album_no, token)

    batch_update.short_description = "批量更新Album内容"


    def batch_update_albums(self, request, queryset):
        adobjects = FacebookAdsApi.init(access_token=my_access_token  , debug=True)
        for row in queryset:
            album_no = row.album_no
            # 重置原有相册的图片信息为不活跃

            MyPhoto.objects.filter(album_no=album_no).update(active=False)

            fields = ["id","name","created_time", "updated_time","picture","link",
                      "likes.summary(true)","comments.summary(true)"
                      ]
            params = {

            }
            try:
                photos = Album(album_no).get_photos(
                    fields=fields,
                    params=params,
                )
            except Exception as e:
                print("获取Facebook数据出错", fields,  e)
                continue

            for photo in photos:
                #print("photos is %s %s "%(photo["id"],photo["likes"]))
                '''
                photo_fields = [ ]
                metric_list = ["post_impressions", "post_impressions_paid","post_impressions_fan",
                                    "post_impressions_fan_unique", "post_impressions_fan_paid"]
                photo_params = {"metric" : metric_list}

                # "metric" : ["post_impressions", "post_impressions_paid"], post_impressions_fan, post_impressions_fan_unique, post_impressions_fan_paid],
                
                insight = Photo(photo["id"]).get_insights(
                            fields= photo_fields,
                            params= photo_params,
                             )
                print("insight is ", insight)

                myinsight_list = []
                
                for row in  insight:
                    #print("row is ",row)
                    myinsight = MyInsight(
                        obj_no = photo["id"],
                        insight_name = row["name"],
                        insight_value = row["values"][0]["value"],

                        updated_time = datetime.datetime.now()
                    )
                    myinsight_list.append(myinsight)

                MyInsight.objects.bulk_create(myinsight_list)
                '''

                try:
                    name = photo["name"]
                except KeyError:
                    name = ""


                obj, created = MyPhoto.objects.update_or_create(photo_no=photo["id"],
                                                              defaults={'page_no': row.page_no,
                                                                        'album_no': album_no,
                                                                        'created_time':
                                                                            photo["created_time"].split('+')[0],
                                                                        'updated_time':
                                                                            photo["updated_time"].split('+')[0],
                                                                        'active':True,
                                                                        'name':name,
                                                                        'picture': photo["picture"],
                                                                        'link': photo["link"],
                                                                        'like_count': photo["likes"]["summary"]["total_count"],
                                                                        'comment_count': photo["comments"]["summary"]["total_count"]


                                                                        }
                                                              )




    batch_update_albums.short_description = "批量更新相册"


@xadmin.sites.register(MyPhoto)
class MyPhotoAdmin(object):

    list_display = [ "photo_no","page_no","album","impression","like_count","comment_count","created_time",  "updated_time", "img", "name",]

    search_fields = ['photo_no',"album_no", "name"]
    list_filter = ("page_no","album_no","like_count")
    actions = [ "batch_delete_local_photos", "batch_get_insight","batch_delete_photos",]

    def album(self,obj):
        return  MyAlbum.objects.get(album_no=obj.album_no).name

    album.short_description = 'album'

    def img(self, obj):
        try:
            img = mark_safe('<a href="%s" target="view_window"><img src="%s" width="100px"></a>' % (obj.link, obj.picture))

        except Exception as e:
            img = ''
        return img

    img.short_description = 'Thumb'
    img.allow_tags = True

    def impression(self,obj):
        impression = MyInsight.objects.filter(obj_no=obj.photo_no,insight_name="post_impressions" ).first()
        return  impression.insight_value

    impression.short_description = 'impression'

    def batch_get_insight(self, request, queryset):
        adobjects = FacebookAdsApi.init(access_token=my_access_token, debug=True)

        for photo in queryset:
            # print("photos is %s %s "%(photo["id"],photo["likes"]))
            photo_no = photo.photo_no
            photo_fields = []
            metric_list = ["post_impressions", "post_impressions_paid", "post_impressions_fan",
                           "post_impressions_fan_unique", "post_impressions_fan_paid"]
            photo_params = {"metric": metric_list}

            # "metric" : ["post_impressions", "post_impressions_paid"], post_impressions_fan, post_impressions_fan_unique, post_impressions_fan_paid],
            try:

                insight = Photo(photo_no).get_insights(
                    fields=photo_fields,
                    params=photo_params,
                )
                print("insight is ", insight)
                myinsight_list = []

                for row in insight:
                    # print("row is ",row)
                    myinsight = MyInsight(
                        obj_no=photo_no,
                        insight_name=row["name"],
                        insight_value=row["values"][0]["value"],

                        updated_time=datetime.datetime.now()
                    )
                    myinsight_list.append(myinsight)
                MyInsight.objects.bulk_create(myinsight_list)
            except:
                #print(insight.error())
                pass




    batch_get_insight.short_description = "更新图片insight"

    def batch_delete_photos(self, request, queryset):
        #删除Facebook图片
        adobjects = FacebookAdsApi.init(access_token=my_access_token, debug=True)
        for row in queryset:
            try:
                photo_no = row.photo_no
                fields = [
                          ]
                params = {

                }
                photos = Photo(photo_no).api_delete(
                    fields=fields,
                    params=params,
                )
            except:
                continue

        #删除本地数据库信息
        queryset.delete()




    batch_delete_photos.short_description = "批量删除图片"

    def batch_delete_local_photos(self, request, queryset):
        queryset.delete()

    batch_delete_local_photos.short_description = "批量删除本地图片"


class ConversationResource(resources.ModelResource):

    class Meta:
        model = Conversation
        skip_unchanged = True
        report_skipped = True
        import_id_fields = ('conversation_no',)
        fields = ('page_no','conversation_no','link','updated_time','customer')
        # exclude = ()



@xadmin.sites.register(Conversation)
class ConversationAdmin(object):

    import_export_args = {'import_resource_class': ConversationResource, 'export_resource_class': ConversationResource}

    list_display = ["conversation_no", "page_no", "link", "updated_time", ]
    search_fields = ['conversation_no', ]

    class MessageInline(object):
        model = Message
        extra = 1
        style = 'tab'

    inlines = [MessageInline]


class MessageResource(resources.ModelResource):


    class Meta:
        model = Message
        skip_unchanged = True
        report_skipped = True
        import_id_fields = ('message_no',)
        fields = ( 'conversation_no', 'message_no','message_content','from_id','from_name','to_id','to_name',)
        # exclude = ()

@xadmin.sites.register(Message)
class MessageAdmin(object):
    import_export_args = {'import_resource_class': MessageResource, 'export_resource_class': MessageResource}

    list_display = ["conversation_no", "message_no", "message_content", "created_time",'from_name', ]



#@xadmin.sites.register(FeedUpdate)
class FeedUpdateAdmin(object):
    actions = ["batch_update", ]
    list_display = ('page',  'feed_create_time','page_no','show_feed'
                   )
    #list_editable = ['feed_create_time']
    #search_fields = ['logistic_no', ]
    # list_filter = ("update_time", )
    ordering = ['-feed_create_time']

    def    show_feed(self, obj):
        return Feed.objects.filter(page_no=obj.page_no).first().created_time

    show_feed.short_description = "最后更新时间"

    def get_feed_data(self, target_page, token, offset, fields,  datetime_since ):
        """
        This method will get the feed data
        """
        url = "https://graph.facebook.com/v3.1/{}/feed".format(target_page)
        param = dict()
        param["access_token"] = token
        param["limit"] = "100"
        param["offset"] = offset
        param["fields"] = fields
        param["since"] = int(time.mktime(datetime_since.timetuple()))

        r = requests.get(url, param)

        data = json.loads(r.text)

        return data

    def convert_feed_data(self, target_page, response_json_list, date_since):
        '''This method takes response json data and convert to csv'''



        for response_json in response_json_list:


            try:
                data = response_json["data"]
            except KeyError:
                print("convert_conversation_data {} completed")
                break

            for i in range(len(data)):

                row = data[i]
                feed_no = row["id"]



                try:
                    type = row["type"]
                except KeyError:
                    type = ""
                try:
                    created_time = row["created_time"].split('+')[0]
                except KeyError:
                    created_time = ""
                try:
                    message = row["message"]
                except KeyError:
                    message = ""

                try:
                    tmp = re.split(r"\[|\]", str(message))
                    if (1 < len(tmp)):
                        sku = tmp[1]
                    else:
                        sku = ""

                except KeyError:
                    sku = ""


                try:
                    name = row["name"]
                except KeyError:
                    name = ""
                try:
                    description = row["description"]
                except KeyError:
                    description = ""
                try:
                    actions_link = row["actions"][0]["link"]
                except KeyError:
                    actions_link = ""
                try:
                    actions_name = row["actions"][0]["name"]
                except KeyError:
                    actions_name = ""
                try:
                    share_count = row["shares"]["count"]
                except KeyError:
                    share_count = ""
                try:
                    comment_count = row["comments"]["summary"]["total_count"]
                except KeyError:
                    comment_count = ""
                try:
                    like_count = row["likes"]["summary"]["total_count"]
                except KeyError:
                    like_count = ""

                #print("feed %s长度 is name %s message %s, des %s"%(feed_no, len(name), len(message),len(description)) )
                #print("message is ", message)

                obj, created = Feed.objects.update_or_create(feed_no=feed_no,
                                                                defaults={'feed_no' : feed_no,
                                                                          'page_no': target_page,
                                                                          'type' : type,
                                                                          'created_time': created_time,
                                                                          'message': message[:1000],
                                                                          'sku': sku,
                                                                          'name' : name[:500],
                                                                          'description': description[:1000],
                                                                          'actions_link': actions_link,
                                                                          'actions_name': actions_name,
                                                                          'share_count': share_count,
                                                                          'comment_count': comment_count,
                                                                          'like_count': like_count,
                                                                        }
                                                                     )
                #print("update feed %s ok"%(feed_no))



        return


    def create_table(self, list_rows, file_path, page_name,table_name):
        '''This method will create a table according to header and table name'''


        if table_name == "feed":
            header = ["page_name", "id", "type", "created_time", "message", "name", \
                      "description", "actions_link", "actions_name", "share_count", \
                      "comment_count", "like_count"]
        else:
            print("Specified table name is not valid.")
            quit()

        file = open(file_path, 'w',encoding='utf-8')
        file.write(','.join(header) + '\n')
        for i in list_rows:
            file.write('"' + page_name + '",')
            for j in range(len(i)):
                row_string = ''
                if j < len(i) - 1:
                    row_string += '"' + str(i[j]).replace('"', '').replace('\n', '') + '"' + ','
                else:
                    row_string += '"' + str(i[j]).replace('"', '').replace('\n', '') + '"' + '\n'
                file.write(row_string)
        file.close()
        print("Generated {} table csv File for {}".format(table_name, page_name))


    def update(self, target_page, token,  datetime_since, now_time):
        field_input = 'id,created_time,name,message,comments.summary(true),\
                        shares,type,published,link,likes.summary(true),actions,place,tags,\
                        object_attachment,targeting,feed_targeting,scheduled_publish_time,\
                        backdated_time,description'

        offset = 0
        json_list = []

        date_since = datetime_since.strftime("%Y-%m-%dT%H:%M:%S+0000")

        while True:
            try:

                data = self.get_feed_data(target_page, token, str(offset), field_input, datetime_since)

                check = data['data']


                if ( check[0]["created_time"] < date_since):
                    print("无新可更", check[0]["created_time"] , date_since)
                    break

                json_list.append(data)

                if (len(check) >= 100):

                    offset += 100
                else:
                    print("End of loop for obtaining more than 100 feed records.")
                    break

            except KeyError:
                print("Error with get request.")
                return


        self.convert_feed_data(target_page,json_list,date_since)
        #messages_table_list = self.convert_messages_data( json_list, date_since)
        #if(len(messages_table_list)>0):
        #    self.create_table(messages_table_list, '/root/data/messages_' + target_page + '_'+ now_time.strftime("%Y-%m-&d %H:%M:%S")+'.csv', target_page, "messages")

    def batch_update(self, request, queryset):
        # 定义actions函数



        for row in queryset:
            target_page = row.page_no
            token = row.token
            datetime_since = row.feed_create_time
            now_time = datetime.datetime.utcnow()

            self.update(target_page, token, datetime_since, now_time)

            FeedUpdate.objects.filter(page_no = target_page).update(feed_create_time = now_time )

    batch_update.short_description = "批量更新主页Feed"

@xadmin.sites.register(AlbumUpdate)
class AlbumUpdateAdmin(object):
    actions = ["batch_update", ]
    list_display = ('page',  'page_no',
                   )
    #list_editable = ['feed_create_time']
    #search_fields = ['logistic_no', ]
    # list_filter = ("update_time", )
    ordering = []



    def get_data(self, target_page, token, offset, fields ):
        """
        This method will get the feed data
        """
        url = "https://graph.facebook.com/v3.3/{}/albums".format(target_page)
        param = dict()
        param["access_token"] = token
        param["limit"] = "100"
        param["offset"] = offset
        param["fields"] = fields


        r = requests.get(url, param)

        data = json.loads(r.text)

        return data

    def convert_data(self, target_page, response_json_list):
        '''This method takes response json data and convert to csv'''



        for response_json in response_json_list:


            try:
                data = response_json["data"]
            except KeyError:
                print("convert_conversation_data {} completed")
                break

            for i in range(len(data)):

                row = data[i]
                album_no = row["id"]

                try:
                    created_time = row["created_time"].split('+')[0]
                except KeyError:
                    created_time = ""

                try:
                    name = row["name"]
                except KeyError:
                    name = ""
                try:
                    count = row["count"]
                except KeyError:
                    count = ""

                try:
                    comment_count = row["comments"]["summary"]["total_count"]
                except KeyError:
                    comment_count = ""
                try:
                    like_count = row["likes"]["summary"]["total_count"]
                except KeyError:
                    like_count = ""



                #print("feed %s长度 is name %s message %s, des %s"%(feed_no, len(name), len(message),len(description)) )
                #print("message is ", message)

                obj, created = Album.objects.update_or_create(album_no=album_no,
                                                                defaults={'album_no' : album_no,
                                                                          'page_no': target_page,

                                                                          'created_time': created_time,
                                                                          'name': name,

                                                                          'count': count,


                                                                          'comment_count': comment_count,
                                                                          'like_count': like_count,
                                                                        }
                                                                     )
                #print("update feed %s ok"%(feed_no))



        return


    def update(self, target_page, token):
        field_input = 'id,created_time,name,count,comments.summary(true),likes.summary(true)'

        offset = 0
        json_list = []



        while True:
            try:

                data = self.get_data(target_page, token, str(offset), field_input)

                check = data['data']




                json_list.append(data)

                if (len(check) >= 100):

                    offset += 100
                else:
                    print("End of loop for obtaining more than 100 album records.")
                    break

            except KeyError:
                print("Error with get request.")
                return


        self.convert_data(target_page,json_list)
        #messages_table_list = self.convert_messages_data( json_list, date_since)
        #if(len(messages_table_list)>0):
        #    self.create_table(messages_table_list, '/root/data/messages_' + target_page + '_'+ now_time.strftime("%Y-%m-&d %H:%M:%S")+'.csv', target_page, "messages")

    def batch_update(self, request, queryset):
        # 定义actions函数



        for row in queryset:
            target_page = row.page_no
            token = get_token(target_page)
            now_time = datetime.datetime.utcnow()

            self.update(target_page, token)

            #AlbumUpdate.objects.filter(page_no = target_page).update(album_create_time = now_time )

    batch_update.short_description = "批量更新主页Album"


@xadmin.sites.register(ConversationUpdate)
class ConversationUpdateAdmin(object):
    actions = ["batch_update", ]
    list_display = ('page', 'page_no', 'conversation_update_time',
                   )
    #list_editable = ['conversation_update_time']
    #search_fields = ['logistic_no', ]
    # list_filter = ("update_time", )
    ordering = ['-conversation_update_time']

    def get_conversation_data(self, target_page, token, offset, fields,  datetime_since ):
        """
        This method will get the feed data
        """
        url = "https://graph.facebook.com/v3.3/{}/conversations".format(target_page)
        param = dict()
        param["access_token"] = token
        param["limit"] = "100"
        param["offset"] = offset
        param["fields"] = fields
        param["since"] = int(time.mktime(datetime_since.timetuple()))

        r = requests.get(url, param)

        data = json.loads(r.text)

        print("request response is ", data)
        return data

    def convert_conversation_data(self, target_page, response_json_list, date_since):
        '''This method takes response json data and convert to csv'''



        for response_json in response_json_list:


            try:
                data = response_json["data"]
            except KeyError:
                print("convert_conversation_data {} completed")
                break

            for i in range(len(data)):

                row = data[i]
                conversation_no = row["id"]



                try:
                    link = row["link"]
                except KeyError:
                    link = ""
                try:
                    updated_time = row["updated_time"].split('+')[0]
                except KeyError:
                    updated_time = ""

                print("update: ", conversation_no, updated_time)

                if ( updated_time < date_since ):
                    break

                try:
                    customer = row["participants"]["data"][0]["name"]
                except KeyError:
                    customer = ""





                obj, created = Conversation.objects.update_or_create(conversation_no=conversation_no,
                                                                    defaults={'conversation_no' : conversation_no,
                                                                              'page_no' : target_page,
                                                                              'link': link,
                                                                              'updated_time': updated_time,
                                                                              'customer' : customer
                                                                            }
                                                                         )



        return

    def convert_messages_data(self, response_json_list,date_since ):
        '''This will get the list of people who commented on the post,
        which can be joined to the feed table by post_id. '''
        print("start update messages")
        list_all = []

        if(len(response_json_list) ==0):
            return list_all;

        for messages_data in response_json_list:
            try:
                data = messages_data["data"]
            except KeyError:
                print("convert_messages_data  completed")
                break

            for i in range(len(data)):
                likes_count = 0
                row = data[i]
                conversation_no = row["id"]


                try:
                    message_count = row["message_count"]
                except KeyError:
                    message_count = ""
                if message_count > 0:
                    messages = row["messages"]["data"]
                    for message in messages:
                        row_list = []
                        message_no = message["id"]
                        created_time = message["created_time"].split('+')[0]

                        print("update message : ", message_no, created_time)

                        if (created_time < date_since):
                            print("无新可更")
                            break


                        message_content = message["message"].encode('utf-8')

                        from_id = message["from"]["id"]
                        from_name = message["from"]["name"]
                        to_id = message["to"]["data"][0]["id"]
                        to_name = message["to"]["data"][0]["name"]

                        row_list.extend((conversation_no, message_no, created_time, message_content,
                                         from_id, from_name, to_id, to_name))
                        list_all.append(row_list)

                        '''
                        obj, created = Message.objects.update_or_create(conversation_no=conversation_no,message_no= message_no,
                                                                     defaults={'conversation_no': conversation_no,
                                                                               'message_no': message_no,
                                                                               'created_time': created_time,
                                                                               'message_content': message_content,
                                                                               'from_id': from_id,
                                                                               'from_name': from_name,
                                                                               'to_id': to_id,
                                                                               'to_name': to_name,

                                                                               },
                                                                     )
                        '''


                # Check if the next link exists
                try:
                    next_link = row["messages"]["paging"]["next"]
                except KeyError:
                    next_link = None
                    continue

                if next_link is not None:
                    r = requests.get(next_link.replace("limit=25", "limit=100"))
                    try:
                        messages_data = json.loads(r.text)

                    except KeyError:
                        print("convert_messages_data  completed")
                        break

                    while True:

                        for i in range(len(messages_data["data"])):
                            row_list=[]
                            message = messages_data["data"][i]

                            message_no = message["id"]
                            created_time = message["created_time"].split('+')[0]

                            print("update message : ", message_no, created_time)

                            if (created_time < date_since):
                                print("无新可更")
                                break

                            message_content = message["message"].encode('utf-8')

                            from_id = message["from"]["id"]
                            from_name = message["from"]["name"]
                            to_id = message["to"]["data"][0]["id"]
                            to_name = message["to"]["data"][0]["name"]



                            row_list.extend((conversation_no, message_no, created_time, message_content,
                                             from_id, from_name, to_id, to_name))
                            list_all.append(row_list)

                        try:
                            next = messages_data["paging"]["next"]
                            r = requests.get(next.replace("limit=25", "limit=100"))
                            messages_data = json.loads(r.text)
                        except KeyError:
                            print("Messages for the conversation {} completed".format(conversation_no))
                            break

        return list_all

    def create_table(self, list_rows, file_path, page_name,table_name):
        '''This method will create a table according to header and table name'''


        if table_name == "messages":
            header = ["page_name","conversation_no","message_no","created_time",\
                      "message_content","from_id","from_name","to_id","to_name"]
        else:
            print("Specified table name is not valid.")
            quit()

        file = open(file_path, 'w',encoding='utf-8')
        file.write(','.join(header) + '\n')
        for i in list_rows:
            file.write('"' + page_name + '",')
            for j in range(len(i)):
                row_string = ''
                if j < len(i) - 1:
                    row_string += '"' + str(i[j]).replace('"', '').replace('\n', '') + '"' + ','
                else:
                    row_string += '"' + str(i[j]).replace('"', '').replace('\n', '') + '"' + '\n'
                file.write(row_string)
        file.close()
        print("Generated {} table csv File for {}".format(table_name, page_name))


    def update(self, target_page, token,  datetime_since, now_time):
        field_input = 'id,is_subscribed,link,participants,message_count,unread_count,\
                                updated_time,messages{created_time,id,message,\
                                sticker,tags,from,to,attachments}'

        offset = 0
        json_list = []

        date_since = datetime_since.strftime("%Y-%m-%dT%H:%M:%S+0000")

        while True:
            try:

                data = self.get_conversation_data(target_page, token, str(offset), field_input, datetime_since)

                check = data['data']


                if ( check[0]["updated_time"] < date_since):
                    print("无新可更")
                    break

                json_list.append(data)

                if (len(check) >= 100):
                    offset += 100
                else:
                    print("End of loop for obtaining more than 100 conversation records.")
                    break

            except KeyError:
                print("Error with get request.")
                return


        self.convert_conversation_data(target_page,json_list,date_since)
        #messages_table_list = self.convert_messages_data( json_list, date_since)
        #if(len(messages_table_list)>0):
        #    self.create_table(messages_table_list, '/root/data/messages_' + target_page + '_'+ now_time.strftime("%Y-%m-&d %H:%M:%S")+'.csv', target_page, "messages")

    def batch_update(self, request, queryset):
        # 定义actions函数





        for row in queryset:
            target_page = row.page_no
            token = get_token(target_page)
            datetime_since = row.conversation_update_time
            now_time = datetime.datetime.utcnow()

            self.update(target_page, token, datetime_since, now_time)

            ConversationUpdate.objects.filter(page_no = target_page).update(conversation_update_time = now_time )

    batch_update.short_description = "批量更新主页会话"

@xadmin.sites.register(PostToFeed)
class PostToFeedAdmin(object):
    def page(self, obj):
        return obj.mypage.page
    page.short_description = "Page"

    actions = [ ]
    list_display = ('page', 'feed_no', 'message','created_time',)
    list_editable = []
    search_fields = ['message', ]
    list_filter = ('mypage', 'feed_no',)
    #model_icon = '<i class="fa fa-camera-retro fa-5x"></i> fa-5x'

    exclude = ["created_time","feed_no"]
    ordering = ['-created_time']



    def save_models(self):
        from django.utils import timezone as dt
        obj = self.new_obj
        if not obj.posted:
            page_no = obj.mypage.page_no


            sysuser_token = SysConfig.objects.first().token

            token = get_token(page_no,sysuser_token)
            FacebookAdsApi.init(access_token=token, debug=True)

            fields = [
                'object_id',
            ]
            params = {
                'message': obj.message,

            }

            feed = Page(page_no).create_feed(
                fields=fields,
                params=params,
            )

            #feed_no = "123"

            obj.feed_no = feed.get("id")
            obj.created_time = dt.now()
            obj.posted = True

        obj.save()

@xadmin.sites.register(SysConfig)
class SysConfigAdmin(object):

    actions = [ ]
    list_display = ('user', 'token')
    list_editable = ['user', 'token',]
    search_fields = [ ]
    list_filter = ()

    exclude = []
    ordering = []

@xadmin.sites.register(PromoteTemplate)
class PromoteTemplateAdmin(object):
    def show_promote_template(self, obj):

        try:
            img = mark_safe('<img src="%s" width="100px" />' % (obj.promote_template.url,))
        except Exception as e:
            img = ''
        return img

    show_promote_template.short_description = 'Promote_Template'
    show_promote_template.allow_tags = True

    list_display = ('batch_name', 'size', 'free_shipping_count','promote_count','show_promote_template','main_image_count','sub_image_count','price_postion','oriprice_postion','update_time',)
    list_editable = ['batch_name', 'size','free_shipping_count', 'promote_count', 'main_image_count','sub_image_count','price_postion','oriprice_postion',]
    search_fields = []
    list_filter = ('batch_name', 'batch_name',"size","free_shipping","main_image_count",)
    #model_icon = '<i class="fa fa-camera-retro fa-5x"></i> fa-5x'

    exclude = []
    ordering = ['batch_name', 'size',]
    actions = [ ]

