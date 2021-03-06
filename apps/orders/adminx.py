# -*- coding: utf-8 -*-
__author__ = 'bobby'

import requests
import json
import time
from datetime import datetime, timedelta, timezone
import base64

import numpy as np, re
import xadmin
from xadmin.layout import Main, Side, Fieldset, Row, AppendedText
from django.shortcuts import get_object_or_404, get_list_or_404, render
from django.contrib.auth.models import Group,User
from import_export import resources, fields
from import_export.widgets import ForeignKeyWidget
from .models import *
'''
    Order, OrderDetail,OrderDetail_lightin, Verify, OrderConversation,ClientService,Verification,\
        Logistic_winlink,Logistic_jiacheng,Logistic_status,Logistic_trail, Sms,\
        LogisticAccount,OverseaOrder,OverseaSkuRank,MyOrder,MyOrderDetail, Order_History
'''
from shop.models import ShopifyProduct, ShopifyVariant,Combination,ShopifyImage
from fb.models import MyPhoto,MyPage

#from conversations.models import Conversation
from logistic.models import Package
from product.models import Product
from django.db import models
from yunpian_python_sdk.model import constant as YC
from yunpian_python_sdk.ypclient import YunpianClient
from datetime import datetime
import urllib
import random
from django.db.models import Q
from django.utils.safestring import mark_safe
from django import forms
from django.contrib import admin, messages
from django.http import HttpResponseRedirect
from django.template import RequestContext
from xadmin.filters import manager as filter_manager, FILTER_PREFIX, SEARCH_VAR, DateFieldListFilter, \
    RelatedFieldSearchFilter
from django.utils.html import format_html

import os

from django.conf import settings

my_app_id = "562741177444068"
my_app_secret = "e6df363351fb5ce4b7f0080adad08a4d"
my_access_token = "EAAHZCz2P7ZAuQBABHO6LywLswkIwvScVqBP2eF5CrUt4wErhesp8fJUQVqRli9MxspKRYYA4JVihu7s5TL3LfyA0ZACBaKZAfZCMoFDx7Tc57DLWj38uwTopJH4aeDpLdYoEF4JVXHf5Ei06p7soWmpih8BBzadiPUAEM8Fw4DuW5q8ZAkSc07PrAX4pGZA4zbSU70ZCqLZAMTQZDZD"
def get_token(target_page,token=None):


    url = "https://graph.facebook.com/v3.3/{}?fields=access_token".format(target_page)
    param = dict()
    if token is None:
        param["access_token"] = my_access_token
    else:
        param["access_token"] = token

    r = requests.get(url, param)

    data = json.loads(r.text)

    # print("request response is ", data["access_token"])
    return data["access_token"]


#批量导入，修改时区
'''
from django.utils.timezone import localtime
from import_export.widgets import DateTimeWidget
from django.conf import settings

from pytz import timezone
from datetime import datetime
#import datetime


class TzDateTimeWidget(DateTimeWidget):

    def render(self, value, obj=None):
        if settings.USE_TZ:
            #dubai_tz = timezone("Asia/Dubai")
            dubai_tz = timezone("Asia/Shanghai")
            #value_time = datetime.strptime(value,'%Y-%m-%d %H:%M:%S')
            #value = value_time.astimezone(dubai_tz)
            value = value.replace(tzinfo=dubai_tz)
        return super(TzDateTimeWidget, self).render(value)
'''


def valid_phone(x):
    x = str(x)
    x = x.replace(' ', '')
    x = x.replace('o', '')
    x = x.replace('O', '')

    if x.find('966') > -1:
        a = x.find('966') + 3
        x = x[a:]
    x = x.lstrip('0')

    return x


def show_conversation_tmp( obj):
    #print('orderconversation')
    if obj.conversation_link:
        return mark_safe(
            u'<a href="%s" target="view_window">%s</a>' % (obj.conversation_link, u'会话'))


    orderconversation = OrderConversation.objects.filter(order=obj.order)

    #print(orderconversation)

    links = ''
    for item in orderconversation:
        conversation = item.conversation
        #print("conversation")
        #print(conversation)

        if (conversation == None):
            continue

        #print(conversation.link)

        link = mark_safe(
            u'<a href="http://business.facebook.com%s" target="view_window">%s</a>' % (conversation.link, u'会话'))
        links = links + link



    return (links)

class OrderResource(resources.ModelResource):
    order_no = fields.Field(attribute='order_no', column_name='订单号')
    order_status = fields.Field(attribute='order_status', column_name='订单状态')

    buyer_name = fields.Field(attribute='buyer_name', column_name='买家姓名')
    '''
    order = fields.Field(
        column_name='order',
        attribute='order',
        widget=ForeignKeyWidget(Order, 'order_no'))
    '''

    #product_quantity = fields.Field(attribute='product_quantity', column_name='产品数量')
    order_amount = fields.Field(attribute='order_amount', column_name='订单金额')
    real_amount = fields.Field(attribute='real_amount', column_name='实收金额')

    order_comment = fields.Field(attribute='order_comment', column_name='订单备注')
    warhouse_comment = fields.Field(attribute='warhouse_comment', column_name='拣货备注')
    cs_comment = fields.Field(attribute='cs_comment', column_name='客服备注')

    receiver_name = fields.Field(attribute='receiver_name', column_name='收货人姓名')
    receiver_addr1 = fields.Field(attribute='receiver_addr1', column_name='地址1')
    receiver_addr2 = fields.Field(attribute='receiver_addr2', column_name='地址2')
    receiver_city = fields.Field(attribute='receiver_city', column_name='收货人城市')
    receiver_country = fields.Field(attribute='receiver_country', column_name='收货人国家')
    receiver_phone = fields.Field(attribute='receiver_phone', column_name='收货人电话')

    package_no = fields.Field(attribute='package_no', column_name='包裹号')
    #weight = fields.Field(attribute='weight', column_name='称重重量(g)')
    logistic_no = fields.Field(attribute='logistic_no', column_name='物流追踪号') #物流号由运营系统直接从佳成系统取，不用店小秘生成的，合联的如果需要，就另外做个入口
    logistic_type = fields.Field(attribute='logistic_type', column_name='物流方式')

    order_time = fields.Field(attribute='order_time', column_name='下单时间')#,widget=TzDateTimeWidget())

    send_time = fields.Field(attribute='send_time', column_name='发货时间')#,widget=TzDateTimeWidget())



    class Meta:
        model = Order
        skip_unchanged = True
        report_skipped = True
        import_id_fields = ('order_no',)
        fields = ('order_no', 'order_status', 'buyer_name',  'order_amount','real_amount', 'order_comment',
                  'warhouse_comment', 'cs_comment', 'receiver_name', 'receiver_addr1', 'receiver_addr2',
                  'receiver_city', 'receiver_country', 'receiver_phone', 'package_no','logistic_no','logistic_type',
                  'order_time','send_time')
        # exclude = ()
    '''
    def dehydrate_facebook_user_name(self, order):
        tmp = re.split(r"\[|\]", str(order.order_comment)[:100])
        if(1 < len(tmp)):
            return tmp[1]
        else:
            return None
  

    def dehydrate_sales(self, order):
        tmp = re.split(r"\[|\]", str(order.order_comment)[:100])
        if (3 < len(tmp) ):
            return tmp[3]
        else:
            return None
    '''

class OrderAdmin(object):
    def trail_status(self, obj):
        logistic_trail = Logistic_trail.objects.filter(logistic_no=obj.logistic_no).last()


        return logistic_trail.trail_status

    trail_status.short_description = "物流轨迹"

    def show_settle_status(self, obj):
         return  LogisticAccount.objects.filter(logistic_no=obj.logistic_no).first().settle_status

    show_settle_status.short_description = "结算状态"

    def cal_amount(self, obj):
        details = obj.order_orderdetail.all()
        amount = 0
        for detail in details:
            amount += float(detail.product_quantity) * float(detail.price)

        return int(amount)

    cal_amount.short_description = "产品金额小计"

    def show_conversation(self, obj):


        return show_conversation_tmp(obj)

    show_conversation.allow_tags = True

    show_conversation.short_description = "会话"



    import_export_args = {"import_resource_class": OrderResource, "export_resource_class": OrderResource}

    #"stock", "cal_barcode", "inventory_status",
    list_display = ["order_no", "status", "receiver_city", "receiver_addr1","order_amount", "order_time", "logistic_no","order_comment","buyer_name",]
    list_editable = ["receiver_addr1","receiver_city",]
    # list_display_links = ["show_conversation"]
    search_fields = ["order_no",'logistic_no', "buyer_name", ]
    list_filter = ( "status","wms_status","track_status","order_time")
    ordering = ['-order_time']
    '''
    def queryset(self):
        qs = super().queryset()
        try:
            # 获取当前登录用户所在组
            groups = self.request.user.groups #获取当前登录用户所在组
            print(groups)
            #获取当前登录用户所在组名称
            if groups.filter(name="主管"):
                return  qs
            else:
                #获取当前登录用户用户名
                return qs.filter(Q(sales=self.request.user)  )
        except Exception as e:
            print(e)
            return  qs
    '''

    #def has_delete_permission(self):
    #    return False
    #data_charts = {
    #    "order_count": {'title': u"订单统计","x-field": "order_time", "y-field": ("order_no", ), "order": ('order_time',)},
    #}


    actions = [ 'batch_copy','batch_refused',"batch_delivered",]
    #'start_verify','fullfill','start_package_track',"batch_overseas_stop", "mapping_lightin",

    def batch_refused(self, request, queryset):
        queryset.update(status="refused")

    batch_refused.short_description = "批量拒签"

    def batch_delivered(self, request, queryset):
        queryset.update(status="delivered")

    batch_delivered.short_description = "批量签收"

    def mapping_lightin(self, request, queryset):
        from django.db.models import Sum
        from prs.models import  Lightin_barcode

        #处理每个订单
        for row in queryset:
            inventory_list = []


            orderdetails = row.order_orderdetail.all()

            # 每个订单项
            for orderdetail in orderdetails:
                sku = orderdetail.sku
                if sku.find("S") == 0:
                    #兰亭的产品，需要映射到barcode

                    lightin_barcodes = Lightin_barcode.objects.filter(SKU=sku)
                    quantity = int(orderdetail.product_quantity)
                    if quantity > lightin_barcodes.aggregate(nums = Sum('quantity')).get("nums"):
                        #库存不足，标记订单为问题单
                        #
                        #
                        continue

                    # 每个可能的条码
                    for lightin_barcode in lightin_barcodes:
                        if quantity == 0:
                            break

                        sellable = lightin_barcode.sellable
                        occupied = lightin_barcode.occupied

                        if quantity > lightin_barcode.sellable:
                            # 条码的库存数量比订单项所需的少

                            sellable = 0
                            occupied += lightin_barcode.sellable
                            quantity -= lightin_barcode.sellable

                        else:
                            sellable -= quantity
                            occupied += quantity
                            quantity = 0


                        inventory_list.append([lightin_barcode.pk, sellable, occupied])

                        print(inventory_list)


            #更新订单所有相关barcode数据库记录,同时插入到OrderDetail_lightin
            '''
            for inventory in inventory_list:

                Lightin_barcode.objects.filter(pk = inventory[0]).update(
                                                    sellable= inventory[1],
                                                    occupied =  inventory[2]
                                
                                                )

            '''

















    def fullfill(self, request, queryset):
        from prs.ali import fanyi_en

        for row in queryset:
            #统计订单明细
            orderdetails  = row.order_orderdetail.all()
            package = {}
            total_amount = 0

            city = row.verify.city

            if city == "暂不支持" or city is None:
                print("城市暂不支持")
                continue

            for orderdetail in orderdetails:
                sku = orderdetail.sku.lower()
                if sku.find("zh") ==0:
                    #组合商品
                    combinations = Combination.objects.filter(handle =sku)

                    for combination in combinations:
                        variant = ShopifyVariant.objects.filter(sku = combination.sku).first()

                        if variant:

                            product = ShopifyProduct.objects.filter(product_no=variant.product_no).first()

                            if product:
                                cat = product.cate_1 + ' ' + product.cate_2

                                if len(cat)>3 :
                                    total_amount = total_amount + int(
                                        combination.quantity * float(variant.price))
                                    # 超过1000 就不登记了
                                    if total_amount > 1000:

                                        print("金额太高了",total_amount)
                                        break

                                    values = package.get(cat, {})

                                    #print("\n before update",values)

                                    values["quantity"] = int(values.get("quantity", "0")) + int(
                                        float(orderdetail.product_quantity))
                                    values["amount"] = int(values.get("amount", "0")) + int(
                                        float(orderdetail.product_quantity) * float(orderdetail.price))

                                    #print("\n after update", values)
                                    package[cat] = values
                                    print("product", product, cat, values)


                else:
                #elif sku.find("a") ==0:
                    #常规商品

                    variant = ShopifyVariant.objects.filter(sku = orderdetail.sku).first()
                    if variant:
                        product = ShopifyProduct.objects.filter(product_no = variant.product_no).first()

                        if product:
                            cat = product.cate_1 +' ' + product.cate_2

                            if len(cat) > 3 :
                                total_amount = total_amount + int(float(orderdetail.product_quantity) * float(orderdetail.price))
                                #超过1000 就不登记了
                                if total_amount >1000:
                                    break

                                values = package.get(cat,{})
                                values["quantity"] = int(values.get("quantity", "0")) + int(float(orderdetail.product_quantity))
                                values["amount"] = int(values.get("amount", "0")) + int(float(orderdetail.product_quantity) * float(orderdetail.price))
                                package[cat]=  values
                                print("product", product, cat, values, len(cat), type(cat))
                '''
                else:
                    print("暂不支持")
                    continue
                '''

            invoiceinformation_list = []
            item_list = []


            for key, value in package.items():
                print(key, ' value : ', value)

                invoiceinformation = {
                    "chinesename": fanyi_en(key),
                    "englishname": key,
                    "hscode": "",
                    "inpieces": str(value.get("quantity", "0")),
                    "unitpriceamount": str(value.get("amount", "0")*0.26/value.get("quantity", "0")).strip(".")[0],
                    "declarationamount": str(value.get("amount", "0")*0.26).strip(".")[0],
                    "declarationcurrency": "USD",
                    "materialquality": "",
                    "purpose": "",
                    "measurementunit": "",
                    "specificationmodel": ""
                    }
                invoiceinformation_list.append(invoiceinformation)

                item={
                        "englishname": key,
                        "hscode": "",
                        "inpieces": str(value.get("quantity")),
                        "unitpriceamount": str(value.get("amount", "0")*0.26/value.get("quantity", "0")).strip(".")[0],
                        "unitpriceweight": "1",
                        "declarationamount": str(value.get("amount", "0")*0.26).strip(".")[0],
                        "declarationcurrency": "USD",
                    }
                item_list.append(item)

            print(invoiceinformation_list,"\n\n", item_list)




            ############准备参数
            requrl = "http://api.jcex.com/JcexJson/api/notify/sendmsg"
            param = dict()
            param["service"] = 'orders'

            param_data = dict()
            # param_data["customerid"] = "3c917d0c-6290-11e8-a277-6c92bf623ff2"


            param_data["Data"] = {
                    "apiplatform": "平台名称",
                    "jcexkey": "NET",
                    "customerid": "3c917d0c-6290-11e8-a277-6c92bf623ff2",
                    "customer": "SZFY6214",
                    "packages": [
                        {
                            "paymentmethod": "",
                            "branchoffice": "",
                            "waybillnumber": row.logistic_no,
                            "platnumber": "",
                            "referencenumber": row.package_no,
                            "transfernumber": "",
                            "productid": "PK1280",
                            "productname": "华南-沙特专线-COD电商小包",
                            "servicetype": "",
                            "pickupservice": [],
                            "expressnetwork": "",
                            "estimatedfee": "",
                            "feenotes": "",
                            "feenotesperson": "",
                            "feenotestime": "",
                            "operationnotes": "",
                            "operationnotesperson": "",
                            "operationnotestime": "",
                            "returnsign": "",
                            "returnperson": "",
                            "returntime": "",
                            "returnreason": "",
                            "receivewarehouse": "",
                            "status": "",
                            "waybillcompleted": "",
                            "inputname": "",
                            "inputtime": "",
                            "senderinformation": [
                                {
                                    "sendername": "Yallavip.com",
                                    "senderchinesename": "Yallavip.com",
                                    "sendercompany": "Yallavip.com",
                                    "senderphone": "86-157-6887-9089",
                                    "sendercountry": "CN",
                                    "sendercity": "shenzhen",
                                    "sendertown": "",
                                    "senderpostcode": "",
                                    "senderaddress": re.sub('[!@#&]', '', "#26-1 Yayuan Road ,BanTian Street LongGang District,ShenZhen City,China") ,
                                    "senderemail": "",
                                    "sendercustomsregistrationcode": "",
                                    "sendercustomsoperatingunits": "",
                                    "senderproxycode": ""
                                }
                            ],
                            "recipientinformation": [
                                {
                                    "recipientname": row.receiver_name,
                                    "recipientphone": row.receiver_phone,
                                    "recipientcountry": "SA",
                                    "recipientpostcode": "",
                                    "recipientcity": row.receiver_city,
                                    "recipientcity": city,
                                    "recipientstate": "",
                                    "recipienttown": "",
                                    "recipienthousenumber": "",
                                    "recipientaddress": re.sub('[!@#&]', '', row.receiver_addr1 + row.receiver_addr2),
                                    "recipientcompany": row.receiver_name,
                                    "recipientemail": "",
                                    "recipientdutyparagraph": ""
                                }
                            ],
                            "invoiceinformation":invoiceinformation_list,
                            "weightinformation": [
                                {
                                    "weightmethod": "",
                                    "totalpackages": "1",
                                    "itemtype": "包裹",
                                    "totalweight": row.weight,
                                }
                            ],
                            "detailpackage": [
                                {
                                    "actualweight": row.weight,
                                    "child_number": "",
                                    "length": "1",
                                    "width": "1",
                                    "height": "1",
                                    "volume": "",
                                    "volumeweight": "",
                                    "item":item_list,
                                }
                            ],
                            "specialservice": [
                                {
                                    "servicename": "W7",
                                    #"costamount": row.order_amount.split(".")[0],
                                    "costamount": row.real_amount.split(".")[0],
                                    "costcurrency": "SAR",
                                    "description": ""
                                }
                            ],
                        }
                    ]

            }
            '''
            "invoiceinformation": [

                {
                    "chinesename": "包包",
                    "englishname": "bag",
                    "hscode": "",
                    "inpieces": "5",
                    "unitpriceamount": "4.00",
                    "declarationamount": "20.00",
                    "declarationcurrency": "USD",
                    "materialquality": "",
                    "purpose": "",
                    "measurementunit": "",
                    "specificationmodel": ""
                }

            ],
            
             "item":[
                                    {
                                        "englishname": "bag",
                                        "hscode": "",
                                        "inpieces": "5",
                                        "unitpriceamount": "4",
                                        "unitpriceweight": "1",
                                        "declarationamount": "20",
                                        "declarationcurrency": "USD",
                                    }
                                    ]
            '''



            data_body = base64.b64encode(json.dumps(param_data).encode('utf-8'))
            param["data_body"] = data_body

            ########################提交
            print("start update track \n requrl is %s \ndata_body is %s " % (requrl, json.dumps(param_data)))

            ###调试用，导出请求的内容

            #with open("./hmm.json", 'w', encoding='utf-8') as json_file:
                #json.dump(param_data, json_file, ensure_ascii=False)


            res = requests.post(requrl, params=param)

            ####################处理返回结果
            print("response is ", res)

            data = json.loads(res.text).get("data")[0]

            ###################记日志###########################
            with open("wuliu.log", encoding="utf-8", mode="a+") as logfile:
                json.dump(param_data,logfile)
                json.dump(data, logfile, ensure_ascii=False)

            print("data", data)

            if data.get("resultcode") == "failure":
                print("发货失败")
                waybillnumber = "error"
            else:
                print("发货成功")
                waybillnumber = data.get("waybillnumber")


            Order.objects.filter(pk=row.pk).update(logistic_no=waybillnumber, waybillnumber=waybillnumber)


        return

    fullfill.short_description = "批量发货"

    def batch_overseas_stop(self, request, queryset):
        # 定义actions函数

        from facebook_business.adobjects.photo import Photo
        from fb.models import MyPage, MyAlbum, MyPhoto
        from facebook_business.api import FacebookAdsApi

        for row in queryset:
            mypages = MyPage.objects.filter(active=True)
            for mypage in mypages:

                myphotos = MyPhoto.objects.filter(name__icontains=row.order_no,page_no=mypage.page_no,listing_status=True)

                print("myphotos %s"%(myphotos))
                if myphotos is None or myphotos.count() == 0:
                    continue
                FacebookAdsApi.init(access_token=get_token(mypage.page_no))

                for myphoto in myphotos:

                    fields = [
                    ]
                    params = {

                    }

                    response = Photo(myphoto.photo_no).api_delete(
                        fields=fields,
                        params=params,
                    )
                    print("response is %s" %( response))

                    print("delte photo %s "% (myphoto.photo_no))


                # 修改数据库记录
                myphotos.update(listing_status=False)

                ShopifyVariant.objects.filter(sku__icontains = row.order_no).update( supply_status="STOP", listing_status=False)


    batch_overseas_stop.short_description = "海外仓批量下架"


    def start_verify(self, request, queryset):
        # 定义actions函数

        #qsList = list(queryset)
        #VerifyList = []
        for row in queryset:
            #order = Order.objects.get(id=row.id),
            facebook_user_name = ''
            sales = ''
            tmp = re.split(r"\[|\]", str(row.order_comment)[:100])
            if ( len(tmp)>3):
                facebook_user_name = tmp[1]
                sales = tmp[3]
            elif( len(tmp)>1):
                facebook_user_name = tmp[1]


            v = Verify(

                    #order_ptr = order,

                    #order_nos=row.order_no,
                order = Order.objects.get(id=row.id),

                verify_status="PROCESSING",
                phone_1=valid_phone(row.receiver_phone),
                sms_status="NOSTART",
                start_time=datetime.now(),

                final_time=datetime.now(),
                facebook_user_name = facebook_user_name,
                sales = sales,
                )

            v.save()


        rows_updated = queryset.update(verify_time=datetime.now(), )

        #rows_updated = len(rows_updated)
        if rows_updated == 1:
            message_bit = '1 story wa'
        else:
            message_bit = "%s stories were" % rows_updated
        self.message_user(request, "%s successfully marked as verified." % message_bit)

    start_verify.short_description = "批量开始审核"

    def start_package_track(self, request, queryset):
        # 定义actions函数


        for row in queryset:
            if(row.logistic_no is None ):
                continue

            obj, created = Package.objects.update_or_create(
                logistic_no=row.logistic_no,
                ref_order = row,
                defaults={
                    'send_time': row.send_time,
                },
            )
        queryset.update(package_status="START")
    start_package_track.short_description = "批量启动包裹追踪"

    def batch_updatelogistic_trail(self, request, queryset):
        # 定义actions函数
        requrl = "http://api.jcex.com/JcexJson/api/notify/sendmsg"

        param_data= dict()
        param_data["customerid"] = -1
        #param_data["waybillnumber"] = "989384782"
        param_data["isdisplaydetail"] = "false"

        #data_body =base64.b64encode(json.dumps(param_data).encode('utf-8'))
        #  base64.b64encode()


        param = dict()
        param["service"] = 'track'
        #param["data_body"] = data_body

        res = requests.post(requrl,params =param)

        for row in queryset:
            param_data["waybillnumber"] = row.logistic_no
            data_body = base64.b64encode(json.dumps(param_data).encode('utf-8'))
            param["data_body"] = data_body
            res = requests.post(requrl, params=param)

            data = json.loads(res.text)

            waybillnumber = data["waybillnumber"]
            #recipientcountry = data["recipientcountry"]

            statusdetail = data["displaydetail"][0]["statusdetail"]


            for i in range(len(statusdetail)):
                status_d = statusdetail[i]



                obj, created = Logistic_trail.objects.update_or_create(
                    logistic_no=waybillnumber,  update_time=status_d["time"],
                    defaults={
                        'trail_status' : status_d["status"],

                        'update_locate' : status_d["locate"]
                    },

                )

    batch_updatelogistic_trail.short_description = "批量更新物流轨迹"

    def batch_copy(self, request, queryset):
        # 定义actions函数
        qsList = list(queryset)
        orderList = []
        for row in qsList:
            # orderList.append(row.order_no)
            orderList.append(row.order_no)

        message_bit = ','.join(orderList)

        # self.message_user(request, "[ %s ] successfully copied." %message_bit)
        self.message_user("[ %s ] successfully copied." % message_bit)
        return

    batch_copy.short_description = "复制所选单号"

    # def get_search_results(self, request, queryset, search_term):
    '''
    def get_list_queryset(self):
        """批量查询订单号"""
        queryset = super().get_list_queryset( )


        query = self.request.GET.get(SEARCH_VAR, '')

        if (len(query) > 0):
            queryset |= self.model.objects.filter(order_no__in=query.split(","))

        return queryset
    '''

    def get_list_queryset(self):
        """批量查询订单号"""
        queryset = super().get_list_queryset()

        query = self.request.GET.get(SEARCH_VAR, '')

        if (len(query) > 0):
            queryset |= self.model.objects.filter(order_no__in=query.split(","))
        if (len(query) > 0):
            queryset |= self.model.objects.filter(logistic_no__in=query.split(","))
        return queryset

    def queryset(self):
        qs = super().queryset()
        return qs.filter(order_time__gt="2019-03-01")

class OrderDetailResource(resources.ModelResource):
    order = fields.Field(
        column_name='订单号',
        attribute='order',
        widget=ForeignKeyWidget(Order, 'order_no'))

    sku = fields.Field(attribute='sku', column_name='SKU')

    #product = fields.Field(attribute='product', column_name='产品名称')
    barcode = fields.Field(attribute='barcode', column_name='barcode')
    product_quantity = fields.Field(attribute='product_quantity', column_name='产品数量')
    #money_type = fields.Field(attribute='money_type', column_name='币种缩写')
    price = fields.Field(attribute='price', column_name='产品售价')
    #pic_url = fields.Field(attribute='pic_url', column_name='图片网址')




    class Meta:
        model = OrderDetail
        skip_unchanged = True
        report_skipped = True
        import_id_fields = ('order','sku')
        fields = ('order', 'sku','barcode', 'product_quantity',  'price', )
        # exclude = ()




class OrderDetailAdmin(object):
    def handle(self,obj):
        from prs.models import Lightin_SKU

        return Lightin_SKU.objects.get(SKU = obj.sku).lightin_spu.handle

    handle.short_description = "handle"

    def free_shipping_count(self,obj):
        from prs.models import Lightin_SKU

        return Lightin_SKU.objects.get(SKU = obj.sku).get_free_shipping_count_display()

    free_shipping_count.short_description = "几件包邮"

    def promote_count(self,obj):
        from prs.models import Lightin_SKU

        return Lightin_SKU.objects.get(SKU = obj.sku).get_promote_count_display()

    promote_count.short_description = "买送"

    def skuattr(self,obj):
        from prs.models import Lightin_SKU

        return Lightin_SKU.objects.get(SKU = obj.sku).skuattr

    skuattr.short_description = "skuattr"


    def fb_photo(self, obj):

        sku = obj.sku
        variant = ShopifyVariant.objects.filter(sku=sku).first()
        handle = ShopifyProduct.objects.filter(product_no=variant.product_no).first().handle
        img = ""
        for photo in MyPhoto.objects.filter(name__icontains=handle):
            #photo = MyPhoto.objects.filter(name__icontains=handle).first()
            try:
                img += '<a href="%s" target="view_window"><img src="%s" width="150px"></a>' % (
                photo.link, photo.picture)
            except Exception as e:
                print("获取图片出错", e)

        return mark_safe(img)

    fb_photo.short_description = "fb photo"

    def show_image(self, obj):
        handle = ""
        img = ""
        try:
            #img = mark_safe('<img src="%s" width="100px" />' % (obj.logo.url,))
            variant =  ShopifyVariant.objects.get(sku=obj.sku)
            image_no = variant.image_no
            handle = ShopifyProduct.objects.get(product_no=variant.product_no).handle


            img = mark_safe(
                '<a href="%s" target="view_window"><img src="%s" width="150px"></a>' % (
                    "https://www.yallavip.com/products/"+handle,
                    ShopifyImage.objects.get(image_no=image_no).src,
                    ))

        except Exception as e:
            img = mark_safe(
                '<a href="%s" target="view_window"><img src="%s" width="150px"></a>' % (
                    "https://www.yallavip.com/products/"+handle,
                    'http://admin.yallavip.com/media/material/sale-10_dbk3GIA.png'
                    ))

        return img

    show_image.short_description = "Product Photo"



    def findfile(self, keyword, root):
        print(keyword, root)

        filelist = []
        for root, dirs, files in os.walk(root):
            for name in files:
                filelist.append(os.path.join(root, name))

                #print(os.path.join(root, name))
        # print(filelist)
        print('...........................................', filelist)
        for i in filelist:

            if os.path.isfile(i):
                # print(i)
                filename = os.path.split(i)[1]
                if keyword in filename:
                    print('yes!', i)  # 绝对路径
                    return  filename
                # else:
                # print('......no keyword!')

    def show_local_image(self, obj):
        domain = "http://admin.yallavip.com/"
        handle = ""
        img = ""



        try:
            #img = mark_safe('<img src="%s" width="100px" />' % (obj.logo.url,))
            variant =  ShopifyVariant.objects.get(sku=obj.sku)
            if variant is not None:

                handle = ShopifyProduct.objects.get(product_no=variant.product_no).handle
            else:
                handle = obj.sku.partition('-')[0]
            print("###################", handle)

            image_filename = "1_"+handle+".jpg"

            print(os.path.join(settings.MEDIA_ROOT, "photos/", image_filename))

            print(os.path.exists(os.path.join(settings.MEDIA_ROOT, "photos/", image_filename)))

            if os.path.exists( os.path.join(settings.MEDIA_ROOT, "photos/",image_filename)):
                destination_url = domain + os.path.join(settings.MEDIA_URL, "photos/", image_filename)
            else:
                image_filename = handle+"_1.jpg"
                if os.path.exists(os.path.join(settings.MEDIA_ROOT, "photos/", image_filename)):
                    destination_url = domain + os.path.join(settings.MEDIA_URL, "photos/", image_filename)
                else:
                    destination_url = 'http://admin.yallavip.com/media/material/sale-10_dbk3GIA.png'



            img = mark_safe(
                '<a href="%s" target="view_window"><img src="%s" width="150px"></a>' % (
                    "https://www.yallavip.com/products/"+handle,
                    destination_url,
                    ))

        except Exception as e:
            print(e)
            img = ''

        return img

    show_local_image.short_description = "Local Photo"


    def show_supply_status(self, obj):
        supply_status = Product.objects.get(sku=obj.sku).supply_status

        if supply_status == "NORMAL":
            color_code = 'green'
        else:
            color_code = 'red'

        return format_html(
            '<span style="color:{};">{}</span>',
            color_code,
            supply_status,
        )

    show_supply_status.short_description = u"供应状态"

    def order_status(self, obj):
        return obj.order.status

    order_status.short_description = u"订单状态"

    def alternative(self, obj):
        return Product.objects.get(sku=obj.sku).alternative

    alternative.short_description = u"替代产品"


    import_export_args = {"import_resource_class": OrderDetailResource, "export_resource_class": OrderDetailResource}

    #为了快速做海外仓包裹，所以把可能的图片显示出来
    #"fb_photo", "show_image", 'show_local_image','show_supply_status','alternative',
    list_display = ['order', 'sku',"handle","skuattr", 'product_quantity',"free_shipping_count", "promote_count", 'stock',  'price','order_status', ]

    search_fields = ["order__order_no",'sku',"order__logistic_no", ]

    ordering = ['-order__order_time']
    list_filter = ("order__status","order__verify__verify_status","order__verify__sms_status",)

    actions = ["batch_overseas_stop",]

    def batch_overseas_stop(self, request, queryset):
        # 定义actions函数

        from facebook_business.adobjects.photo import Photo
        from fb.models import MyPage, MyAlbum, MyPhoto
        from facebook_business.api import FacebookAdsApi

        #订单状态已付款， 订单明细sku名字中含overseas的订单找出来

        order_details = OrderDetail.objects.filter(order__order_status="已付款", sku__icontains="overseas" ).order_by("order__order_no")
        n = 0
        for order_detail in order_details:
            sku = order_detail.sku
            #删除Facebook上的图片


            sku_name = sku.partition("-")[2]

            print("sku is %s, sku_name is %s"%(sku, sku_name))

            myphotos = MyPhoto.objects.filter(name__icontains=sku_name)

            print("myphotos %s"%(myphotos))

            for myphoto in myphotos:
                FacebookAdsApi.init(access_token=get_token(myphoto.page_no))
                fields = [
                ]
                params = {

                }
                response = Photo(myphoto.photo_no).api_delete(
                    fields=fields,
                    params=params,
                )
                print("response is %s" %( response))

                print("delte photo %s "% (myphoto.photo_no))


            # 修改数据库记录
            myphotos.update(listing_status=False)

            ShopifyVariant.objects.filter(sku = sku).update( supply_status="STOP", listing_status=False)


    batch_overseas_stop.short_description = "海外仓批量下架"

    '''
    def queryset(self):
        qs = super().queryset()
        return qs.filter(order__status="OPEN" )
    '''
'''
class OrderConverstaionResource(resources.ModelResource):
    order = fields.Field(
        column_name='order_no',
        attribute='order',
        widget=ForeignKeyWidget(Order, 'order_no'))

    conversation = fields.Field(
        column_name='conversation_no',
        attribute='conversation',
        widget=ForeignKeyWidget(Conversation, 'conversation_no'))

    class Meta:
        model = OrderConversation
        skip_unchanged = True
        report_skipped = True
        import_id_fields = ('order','conversation')
        fields = ('order', 'conversation')
        # exclude = ()
'''

class OrderConverstaionAdmin(object):
    #import_export_args = {'import_resource_class': OrderConverstaionResource,
    #                      'export_resource_class': OrderConverstaionResource}

    def show_conversation(self, obj):
        return  mark_safe(
            u'<a href="http://business.facebook.com%s" target="view_window">%s</a>' % (obj.conversation.link, u'会话'))


    show_conversation.allow_tags = True

    show_conversation.short_description = "会话"

    list_display = ["order", "conversation",'show_conversation']
    search_fields = ['order__order_no', 'conversation__conversation_no' ]
    ordering = ['-order__order_no']
'''
class VerificationResource(resources.ModelResource):
    conversation = fields.Field(
        column_name='conversation_no',
        attribute='conversation',
        widget=ForeignKeyWidget(Conversation, 'conversation_no'))

    #order_no = fields.Field(attribute='order_no', column_name='订单号')
    verify_code = fields.Field(attribute='verify_code', column_name='verify_code')
    verify_time = fields.Field(attribute='verify_time',column_name='verify_time')
    message_content = fields.Field(attribute='message_content',column_name='message_content')


    def before_import_row(self,row, **kwargs):
        print( "the first param is: ")
        print(row)
        for key in kwargs:
            print( "the key is: %s, and the value is: %s" % (str(key), str(kwargs[key])))
        #row.verification_time = datetime.fromtimestamp(row.verification_time_unix)

    class Meta:
        model = Verification
        skip_unchanged = True
        report_skipped = True
        import_id_fields = ("conversation","verify_code",)
        fields = ( "conversation","verify_code","verify_time","message_content")
        # exclude = ()
'''

class VerificationAdmin(object):
    def show_conversation(self, obj):


        return  mark_safe(
            u'<a href="http://business.facebook.com%s" target="view_window">%s</a>' % (obj.conversation.link, u'会话'))


    show_conversation.allow_tags = True

    show_conversation.short_description = "会话"

    #import_export_args = {'import_resource_class': VerificationResource,
    #                      'export_resource_class': VerificationResource}

    list_display = [ "conversation","verify_code","verify_time","valid","message_content"]
    search_fields = ["conversation__conversation_no","verify_code"]
    list_editable = ["valid"]
    list_filter = []
    ordering = ['-verify_time']


class VerifyResource(resources.ModelResource):

    class Meta:
        model = Verify
        skip_unchanged = True
        report_skipped = True
        import_id_fields = ('order_no',)
        fields = ('order_no', 'order_status', 'buyer_name',  'order_amount','real_amount', 'order_comment',
                  'warhouse_comment', 'cs_comment', 'receiver_name', 'receiver_addr1', 'receiver_addr2',
                  'receiver_city', 'receiver_country', 'receiver_phone', 'package_no','logistic_no','logistic_type',
                  'order_time','send_time')


class VerifyAdmin(object):
    # import_export_args = {'import_resource_class': MessageResource, 'export_resource_class': MessageResource}
    def page(self, obj):
        return MyPage.objects.get(page_no = obj.mailbox_id)

    page.short_description = "Page"

    def order_sku_count(self, obj):
        return  obj.order.order_orderdetail.all().count()

    order_sku_count.short_description = "订单sku数"


    def fulfill_error(self, obj):
        return  obj.order.fulfill_error

    fulfill_error.short_description = "wms发货错误"

    def show_conversation(self, obj):

        return  show_conversation_tmp(obj)

    show_conversation.allow_tags = True

    show_conversation.short_description = "会话"



    '''
    def show_verification(self, obj):
        conversation = OrderConversation.objects.filter(order=obj.order).conversation
        verification = Verification.objects.filter(conversation=conversation)
        #conversation = obj.order.conversation


        verify = verification.verify_code

        if(verify>0):
            color_code = 'red'

        else:
            color_code = 'yellow'

        return format_html(
                '<span style="background-color:{};">{}</span>',
                color_code, verify,
            )

    show_verification.short_description = "验证码"
    '''

    def get_list_queryset(self):
        """批量查询订单号"""
        queryset = super().get_list_queryset()

        query = self.request.GET.get(SEARCH_VAR, '')

        if (len(query) > 0):
            queryset |= self.model.objects.filter(order__order_no__in=query.split(","))
        if (len(query) > 0):
            queryset |= self.model.objects.filter(order__order_no__in=query.split(","))

        return queryset

    def order_no(self, obj):
        #return obj.order.order_no
        return obj.order.order_no

    order_no.short_description = "订单号"

    def order_time(self, obj):
        return obj.order.order_time.astimezone(timezone(timedelta(hours=3)))

    order_time.short_description = "订单时间"

    def warhouse_comment(self, obj):
        #return obj.order.order_no
        return obj.order.warhouse_comment

    warhouse_comment.short_description = "拣货备注"


    def receiver_phone(self, obj):
        return obj.order.receiver_phone

    receiver_phone.short_description = "收货人电话"

    def stock(self, obj):
        return obj.order.stock

    stock.short_description = "库存"



    def order_status(self, obj):
        return obj.order.status

    order_status.short_description = "订单状态"

    def order_fulfillment_status(self, obj):
        return obj.order.fulfillment_status

    order_fulfillment_status.short_description = "订单仓配状态"


    def order_amount(self, obj):
        return obj.order.order_amount

    order_amount.short_description = "订单金额"

    def receiver_addr(self, obj):
        return obj.order.receiver_addr1

    receiver_addr.short_description = "收货人地址"

    def receiver_city(self, obj):
        return obj.order.receiver_city

    receiver_city.short_description = "收货人城市"

    def buyer_name(self, obj):
        return obj.order.buyer_name

    buyer_name.short_description = "买家姓名"


    '''
    def queryset(self):
        qs = super(VerifyAdmin, self).queryset()
        return qs.filter(verify_status='PROCESSING')
    '''

    readonly_fields = ('order', 'order_time',)
    list_display = ('order','page','show_conversation','order_time',"order_amount", "order_status","stock",'colored_verify_status', \
                    'colored_sms_status',"sms_code",
                    'city','receiver_addr',

                    'receiver_phone','phone_1', 'phone_2', 'verify_comments','verify_time',"final_staff",'cs_reply',\
                   'facebook_user_name', 'sales','conversation_link',)

    #'cancel', 'error_money', 'error_contact', \    'error_address', 'error_cod', 'error_note','warhouse_comment','wait_status',

    ordering = ['-order__order_time']
    list_editable = ['phone_1', 'phone_2','verify_comments','city',"sms_code","conversation_link",]
    search_fields = ['order__order_no','order__logistic_no','verify_comments','cs_reply',"phone_1", "order__receiver_city",]
    list_filter = ('order__status','order__financial_status','order__fulfillment_status',"order__wms_status", 'verify_status', 'sms_status', 'error_contact',"city",'order__order_time',)

    model_icon = 'fa fa-address-book-o'

    actions = ['batch_paid', 'batch_copy',  'batch_simple','batch_complex', 'batch_sms', 'batch_confirmSMS','batch_timeoutSMS','batch_verify', 'batch_customercancel','batch_cscancel','batch_timeoutcancel', 'batch_notstart','batch_restart','batch_cancel_order', ]
    #'batch_error_money', 'batch_error_contact', 'batch_error_address', 'batch_error_cod', 'batch_error_note',
    #自定义django的admin后台action

    def has_delete_permission(self):
        return False

    def batch_paid(self, request, queryset):
        # 定义actions函数
        for row in queryset:
            row.order.financial_status = "paid"
            row.order.save()


    batch_paid.short_description = "shopify订单确认支付"

    '''
    def batch_submit(self, request, queryset):
        # 定义actions函数
        rows_updated = queryset.filter(error_money=True, error_contact=True,
                                       error_address=True, error_cod=True, error_note=True).update(verify_status='SUCCESS')

        rows_updated += queryset.filter(Q(error_money=False) | Q(error_contact=False) |
                                        Q(error_address=False) | Q(error_cod=False) | Q(error_note=False)).update(
            verify_status='SIMPLE')

        rows_updated = queryset.filter(cancel=False).update(verify_status='CLOSED')

        # rows_updated += Verify.objects.filter(error_money=False).update(verify_status='问题单')

        if rows_updated == 1:
            message_bit = '1 story was'
        else:
            message_bit = "%s stories were" % rows_updated
        self.message_user(request, "%s successfully marked as verified." % message_bit)

    batch_submit.short_description = "批量提交"

    def batch_error_money(self, request, queryset):
        # 定义actions函数
        rows_updated = queryset.update(error_money=False)
        if rows_updated == 1:
            message_bit = '1 story was'
        else:
            message_bit = "%s stories were" % rows_updated
        self.message_user(request, "%s successfully marked as error." % message_bit)

    batch_error_money.short_description = "批量价格问题"

    def batch_error_contact(self, request, queryset):
        # 定义actions函数
        rows_updated = queryset.update(error_contact=False)
        if rows_updated == 1:
            message_bit = '1 story was'
        else:
            message_bit = "%s stories were" % rows_updated
        self.message_user(request, "%s successfully marked as error." % message_bit)

    batch_error_contact.short_description = "批量电话问题"

    def batch_error_address(self, request, queryset):
        # 定义actions函数
        rows_updated = queryset.update(error_address=False)
        if rows_updated == 1:
            message_bit = '1 story was'
        else:
            message_bit = "%s stories were" % rows_updated
        self.message_user(request, "%s successfully marked as error." % message_bit)

    batch_error_address.short_description = "批量地址问题"

    def batch_error_cod(self, request, queryset):
        # 定义actions函数
        rows_updated = queryset.update(error_cod=False)
        if rows_updated == 1:
            message_bit = '1 story was'
        else:
            message_bit = "%s stories were" % rows_updated
        self.message_user(request, "%s successfully marked as error." % message_bit)

    batch_error_cod.short_description = "批量COD问题"

    def batch_error_note(self, request, queryset):
        # 定义actions函数
        rows_updated = queryset.update(error_note=False)
        if rows_updated == 1:
            message_bit = '1 story was'
        else:
            message_bit = "%s stories were" % rows_updated
        self.message_user(request, "%s successfully marked as error." % message_bit)

    batch_error_note.short_description = "批量备注问题"

    def batch_timeout(self, request, queryset):
        # 定义actions函数
        rows_updated = queryset.update( sms_status='TIMEOUT')
        if rows_updated == 1:
            message_bit = '1 story was'
        else:
            message_bit = "%s stories were" % rows_updated
        self.message_user(request, "%s successfully marked as timeout." % message_bit)

    batch_timeout.short_description = "批量超时"

   

    '''

    def batch_customercancel(self, request, queryset):
        # 定义actions函数
        rows_updated = queryset.update( verify_status='CUSTOMERCLOSED')
        if rows_updated == 1:
            message_bit = '1 story was'
        else:
            message_bit = "%s stories were" % rows_updated
        self.message_user(request, "%s successfully marked as error." % message_bit)

    batch_customercancel.short_description = "批量客户关闭订单"

    def batch_cscancel(self, request, queryset):
        # 定义actions函数
        rows_updated = queryset.update( verify_status='CSCLOSED')
        if rows_updated == 1:
            message_bit = '1 story was'
        else:
            message_bit = "%s stories were" % rows_updated
        self.message_user(request, "%s successfully marked as error." % message_bit)

    batch_cscancel.short_description = "批量客服关闭订单"

    def batch_timeoutcancel(self, request, queryset):
        # 定义actions函数
        rows_updated = queryset.update( verify_status='TIMEOUTCLOSED')
        if rows_updated == 1:
            message_bit = '1 story was'
        else:
            message_bit = "%s stories were" % rows_updated
        self.message_user(request, "%s successfully marked as error." % message_bit)

    batch_timeoutcancel.short_description = "批量超时关闭订单"



    def batch_simple(self, request, queryset):
        # 定义actions函数
        rows_updated = queryset.update( verify_status='SIMPLE')
        if rows_updated == 1:
            message_bit = '1 story was'
        else:
            message_bit = "%s stories were" % rows_updated
        self.message_user(request, "%s successfully marked as error." % message_bit)

    batch_simple.short_description = "批量简单问题"

    def batch_complex(self, request, queryset):
        # 定义actions函数
        rows_updated = queryset.update( verify_status='COMPLEX')
        if rows_updated == 1:
            message_bit = '1 story was'
        else:
            message_bit = "%s stories were" % rows_updated
        self.message_user(request, "%s successfully marked as error." % message_bit)

    batch_complex.short_description = "批量复杂问题"

    def batch_verify(self, request, queryset):
        # 定义actions函数
        rows_updated = queryset.update(verify_status='SUCCESS', error_money=True, error_contact=True,
                                       error_address=True, error_cod=True, error_note=True,
                                       final_staff = str(self.request.user))
        if rows_updated == 1:
            message_bit = '1 story was'
        else:
            message_bit = "%s stories were" % rows_updated
        self.message_user(request, "%s successfully marked as confirmed." % message_bit)

    batch_verify.short_description = "批量通过审核"

    def batch_notstart(self, request, queryset):
        # 定义actions函数
        rows_updated = queryset.update(verify_status='NOSTART', error_money=False, error_contact=False,
                                       error_address=False, error_cod=False, error_note=False)
        if rows_updated == 1:
            message_bit = '1 story was'
        else:
            message_bit = "%s stories were" % rows_updated
        self.message_user(request, "%s successfully marked as confirmed." % message_bit)

    batch_notstart.short_description = "批量搁置审核"

    def batch_restart(self, request, queryset):
        # 定义actions函数
        rows_updated = queryset.update(verify_status='PROCESSING', cancel=None, error_money=None, error_contact=None,
                                       error_address=None, error_cod=None, error_note=None)
        if rows_updated == 1:
            message_bit = '1 story was'
        else:
            message_bit = "%s stories were" % rows_updated
        self.message_user(request, "%s successfully marked as confirmed." % message_bit)

    batch_restart.short_description = "批量重新审核"

    def batch_sms(self, request, queryset):
        # 定义actions函数
        # qsList = list(queryset)
        orderList = []
        clnt = YunpianClient('2f22880b34b7dc5c6d93ce21047601f9')

        for row in queryset:

            #orderList.append(row.order_no)

            if (row.phone_1 != None):
                code = 'Y' + str(random.randint(100000, 999999))
                param = {YC.MOBILE: '+966' + row.phone_1,
                         # YC.TEXT: '【YallaVIP】Please send  YallaVIP\'s confirmation code#%s# to us by facebook messanger. We will deliver your order when we get your code.'%row[1]}
                         YC.TEXT: '【YallaVip】Please send  YallaVIP\'s confirmation code#%s# to us by facebook messanger. We will deliver your order when we get your code.' % code}
                #print(param)
                #print(urllib.parse.urlencode(param))
                #r = clnt.sms().single_send(param)

            if (row.phone_2 != None):
                code = 'Y' + str(random.randint(100000, 999999))
                param = {YC.MOBILE: '+966' + row.phone_2,
                         # YC.TEXT: '【YallaVIP】Please send  YallaVIP\'s shopping code#%s# to us by facebook messanger. We will deliver your order when we get your code.'%row[1]}
                         YC.TEXT: '【YallaVip】Please send  YallaVIP\'s shopping code#%s# to us by facebook messanger. We will deliver your order when we get your code.' % code}
                #print(param)
                #print(urllib.parse.urlencode(param))
                # r = clnt.sms().single_send(param)
            if (row.phone_3 != None):
                code = 'Y' + str(random.randint(100000, 999999))
                param = {YC.MOBILE: '+966' + row.phone_3,
                         # YC.TEXT: '【YallaVIP】Please send  YallaVIP\'s shopping code#%s# to us by facebook messanger. We will deliver your order when we get your code.'%row[1]}
                         YC.TEXT: '【YallaVip】Please send  YallaVIP\'s shopping code#%s# to us by facebook messanger. We will deliver your order when we get your code.' % code}
                #print(param)
                #print(urllib.parse.urlencode(param))
                # r = clnt.sms().single_send(param)

            # r = clnt.sms().single_send(param)

        rows_updated = queryset.update(sms_status='WAIT')

        # message_bit = ','.join(orderList)
        self.message_user(request, "[ %s ] orders successfully send sms code." % rows_updated)

        """
        if rows_updated == 1:
            message_bit = '1 story was'
        else:
            message_bit = "%s stories were" %rows_updated
        self.message_user(request,"%s successfully marked as send." %message_bit)
        """

    batch_sms.short_description = "批量发送验证码"

    def batch_confirmSMS(self, request, queryset):
        # 定义actions函数
        rows_updated = queryset.update(sms_status='CHECKED',final_staff = str(self.request.user))
        if rows_updated == 1:
            message_bit = '1 story was'
        else:
            message_bit = "%s stories were" % rows_updated
        self.message_user(request, "%s successfully marked as confirmed." % message_bit)

    batch_confirmSMS.short_description = "批量确认验证码"

    def batch_timeoutSMS(self, request, queryset):
        # 定义actions函数
        rows_updated = queryset.update(sms_status='TIMEOUT')
        if rows_updated == 1:
            message_bit = '1 story was'
        else:
            message_bit = "%s stories were" % rows_updated
        self.message_user(request, "%s successfully marked as confirmed." % message_bit)

    batch_timeoutSMS.short_description = "批量验证码超时"




    def batch_copy(self, request, queryset):
        # 定义actions函数
        qsList = list(queryset)
        orderList = []
        for row in qsList:
            # orderList.append(row.order_no)
            orderList.append(row.order.order_no)

        message_bit = ','.join(orderList)

        # self.message_user(request, "[ %s ] successfully copied." %message_bit)
        self.message_user("[ %s ] successfully copied." % message_bit)
        return

    batch_copy.short_description = "复制所选单号"

    def batch_cancel_order(self, request, queryset):

        for verify in queryset:
            if verify.order.status == "open":
                verify.order.status = "cancelled"
                verify.order.save()

            # 记录操作日志
            #self.deal_log(queryset, "取消订单", customer.name )

        return

    batch_cancel_order.short_description = "取消订单"


    def get_search_results(self, request, queryset, search_term):
        """批量查询订单号"""
        queryset, use_distinct = super().get_search_results(request, queryset, search_term)

        if (len(search_term) > 0):
            queryset |= self.model.objects.filter(order_no__in=search_term.split(","))
        return queryset, use_distinct
    '''

    def get_list_queryset(self):
        """批量查询订单号"""
        queryset = super().get_list_queryset()

        query = self.request.GET.get(SEARCH_VAR, '')

        if (len(query) > 0):
            queryset |= self.model.objects.filter(order_no__in=query.split(","))

        return queryset
    '''
    '''
    def queryset(self):
        qs = super().queryset()
        return qs.filter(order__status="OPEN")
    '''

class ClientServiceAdmin(object):
    def receiver_city(self, obj):
        return obj.order.receiver_city

    receiver_city.short_description = "收货人城市"

    def receiver_addr(self, obj):
        return obj.order.receiver_addr1

    receiver_addr.short_description = "收货人地址"

    def order_status(self, obj):
        return obj.order.status
    order_status.short_description = "订单状态"

    def stock(self, obj):
        return obj.order.stock

    stock.short_description = "库存"

    def order_logistic_update_status(self, obj):

        package = Package.objects.filter(logistic_no=obj.order.logistic_no).first()

        return package.logistic_update_status
        #return obj.order.logistic_update_status
    order_logistic_update_status.short_description = "物流状态"

    def receiver_phone(self, obj):
        return obj.order.receiver_phone

    receiver_phone.short_description = "收货人电话"

    def order_time(self, obj):
        return obj.order.order_time

    order_time.short_description = "订单时间"

    def show_conversation(self, obj):



        return show_conversation_tmp(obj)

    show_conversation.allow_tags = True

    show_conversation.short_description = "会话"

    #定义 action
    def batch_stop(self, request, queryset):
        # 定义actions函数
        rows_updated = queryset.update(supply_status='STOP')
        if rows_updated == 1:
            message_bit = '1 story was'
        else:
            message_bit = "%s stories were" % rows_updated
        self.message_user(request, "%s successfully marked as error." % message_bit)

    batch_stop.short_description = "批量断货"

    def batch_pause(self, request, queryset):
        # 定义actions函数
        rows_updated = queryset.update(supply_status='PAUSE')
        if rows_updated == 1:
            message_bit = '1 story was'
        else:
            message_bit = "%s stories were" % rows_updated
        self.message_user(request, "%s successfully marked as error." % message_bit)

    batch_pause.short_description = "批量缺货"

    def batch_normal(self, request, queryset):
        # 定义actions函数
        rows_updated = queryset.update(supply_status='NORMAL')
        if rows_updated == 1:
            message_bit = '1 story was'
        else:
            message_bit = "%s stories were" % rows_updated
        self.message_user(request, "%s successfully marked as error." % message_bit)

    batch_normal.short_description = "批量正常"

    ordering = ['-order__order_time']
    list_display = ('order',  'order_time','order_status','stock','order_logistic_update_status', 'colored_verify_status', \
                    'receiver_city', 'city','receiver_addr',
                    'colored_sms_status',"sms_code",
                    "deal_outofstock","real_amount",
                    #'cancel', 'error_money', 'error_contact', \
                    #'error_address', 'error_cod', 'error_note','error_timeout',
                     'receiver_phone', 'phone_1', 'phone_2','verify_comments', 'cs_reply', \
                    'facebook_user_name', 'sales', 'show_conversation')

    list_editable = ['phone_1', 'phone_2', 'cs_reply',  'city',"deal_outofstock","real_amount","sms_code",]
    search_fields = ['order__order_no','verify_comments', 'phone_1','phone_2','facebook_user_name','order__receiver_city']
    list_filter = ('verify_status','supply_status', 'sms_status', 'error_money', 'order__order_status','sales','city',"deal_outofstock",)
    actions = ['batch_stop', 'batch_pause', 'batch_normal', ]
    readonly_fields  =('order',  'order_time','order_status','stock','order_logistic_update_status', 'colored_verify_status', \
                    'receiver_city', 'city','receiver_addr',
                    'colored_sms_status',"sms_code",
                    "deal_outofstock","real_amount",

                     'receiver_phone', 'phone_1', 'phone_2','verify_comments',  \
                    'facebook_user_name', 'sales', 'show_conversation')
    '''
    def queryset(self):
        qs = super().queryset()
        try:
            # 获取当前登录用户所在组
            groups = self.request.user.groups #获取当前登录用户所在组
            print(groups)
            #获取当前登录用户所在组名称
            if groups.filter(name="主管"):
                return  qs
            else:
                #获取当前登录用户用户名
                return qs.filter(Q(sales=self.request.user)  )
        except Exception as e:
            print(e)
            return  qs
    '''


    def get_list_queryset(self):
        """xadmin 有效的批量查询订单号"""
        queryset = super().get_list_queryset()

        query = self.request.GET.get(SEARCH_VAR, '')

        if (len(query) > 0):
            queryset |= self.model.objects.filter(order__order_no__in=query.split(","))

        return queryset



class Logistic_winlinkResource(resources.ModelResource):

    logistic_no = fields.Field(attribute='logistic_no', column_name='单号')
    order_no = fields.Field(attribute='order_no', column_name='原单号')
    logistic_status = fields.Field(attribute='logistic_status', column_name='订单状态1')
    comments = fields.Field(attribute='comments', column_name='异常说明')
    his_comments = fields.Field(attribute='his_comments', column_name='所有异常')
    logistic_update = fields.Field(attribute='logistic_update', column_name='更新时间')




    class Meta:
        model = Logistic_winlink
        skip_unchanged = True
        report_skipped = True
        import_id_fields = ('logistic_no',)
        fields = ('logistic_no', 'order_no','logistic_status','comments','his_comments', 'logistic_update',)

class Logistic_winlinkAdmin(object):


    def order_status(self, obj):
        return obj.order.order_status

    order_status.short_description = "订单状态"

    def show_conversation(self, obj):
        # print('orderconversation')
        orders = Order.objects.filter(logistic_no=obj.logistic_no)

        # print(orderconversation)

        links = ''
        for order in orders:



            if (order == None):
                continue

            orderconversation = OrderConversation.objects.filter(order=order)
            for item in orderconversation:
                conversation = item.conversation



                if (conversation != None):
                    '''
                    link = mark_safe(
                        u'<a href="http://business.facebook.com%s" target="view_window">%s</a>' % (
                            u'one', u'  ' + order.order_no))
                    links = links  + order.order_no
                else:
                '''
                    link = mark_safe(
                        u'<a href="http://business.facebook.com%s" target="view_window">%s</a>' % (
                        conversation.link, u'  '+ order.order_no))
                    links = links + link

                #print(links)

        return (links)

    show_conversation.allow_tags = True
    show_conversation.short_description = "会话"



    def show_order(self, obj):
        orders = Order.objects.filter(logistic_no=obj.logistic_no)

        # print(orderconversation)

        order_nos = ''
        for order in orders:
            order_no = order.order_no
            order_nos = order_nos +'  '+  order_no

        return order_nos

    show_order.allow_tags = True

    show_order.short_description = "订单"

    def show_ordercomment(self, obj):
        orders = Order.objects.filter(logistic_no=obj.logistic_no)

        # print(orderconversation)

        order_comments = ''
        for order in orders:
            order_comment = order.order_comment
            order_comments = order_comments +'  '+  order_comment

        return order_comments

    show_ordercomment.allow_tags = True

    show_ordercomment.short_description = "订单备注"

    def show_orderphone(self, obj):
        orders = Order.objects.filter(logistic_no=obj.logistic_no)

        # print(orderconversation)

        order_phones = ''
        for order in orders:

            order_phones = order_phones +'  '+  order.receiver_phone

        return order_phones

        show_orderphone.allow_tags = True


    show_orderphone.short_description = "收货人电话"




    import_export_args = {"import_resource_class": Logistic_winlinkResource, "export_resource_class": Logistic_winlinkResource}


    def batch_deliver_response(self, request, queryset):
        # 定义actions函数
        rows_updated = queryset.update(response="DELIVER")
        if rows_updated == 1:
            message_bit = '1 story was'
        else:
            message_bit = "%s stories were" % rows_updated
        self.message_user(request, "%s successfully marked as error." % message_bit)

    batch_deliver_response.short_description = "批量派送员责任"

    def batch_customer_response(self, request, queryset):
        # 定义actions函数
        rows_updated = queryset.update(response="CUSTOMER")
        if rows_updated == 1:
            message_bit = '1 story was'
        else:
            message_bit = "%s stories were" % rows_updated
        self.message_user(request, "%s successfully marked as error." % message_bit)

    batch_customer_response.short_description = "批量客户责任"

    def batch_yallavip_response(self, request, queryset):
        # 定义actions函数
        rows_updated = queryset.update(response="YALLAVIP")
        if rows_updated == 1:
            message_bit = '1 story was'
        else:
            message_bit = "%s stories were" % rows_updated
        self.message_user(request, "%s successfully marked as error." % message_bit)

    batch_yallavip_response.short_description = "批量yallavip责任"

    def batch_done(self, request, queryset):
        # 定义actions函数
        rows_updated = queryset.update(deal="DONE")
        if rows_updated == 1:
            message_bit = '1 story was'
        else:
            message_bit = "%s stories were" % rows_updated
        self.message_user(request, "%s successfully marked as error." % message_bit)

    batch_done.short_description = "批量完成"

    def batch_settle(self, request, queryset):
        # 定义actions函数
        rows_updated = queryset.update(deal="SETTLE")
        if rows_updated == 1:
            message_bit = '1 story was'
        else:
            message_bit = "%s stories were" % rows_updated
        self.message_user(request, "%s successfully marked as error." % message_bit)

    batch_settle.short_description = "批量待结算"

    def batch_return(self, request, queryset):
        # 定义actions函数
        rows_updated = queryset.update(deal="RETURN")
        if rows_updated == 1:
            message_bit = '1 story was'
        else:
            message_bit = "%s stories were" % rows_updated
        self.message_user(request, "%s successfully marked as error." % message_bit)

    batch_return.short_description = "批量退仓"

    def batch_returned(self, request, queryset):
        # 定义actions函数
        rows_updated = queryset.update(deal="RETURNED")
        if rows_updated == 1:
            message_bit = '1 story was'
        else:
            message_bit = "%s stories were" % rows_updated
        self.message_user(request, "%s successfully marked as error." % message_bit)

    batch_returned.short_description = "批量已退到仓库"

    def batch_listing(self, request, queryset):
        # 定义actions函数
        rows_updated = queryset.update(deal="LISTING")
        if rows_updated == 1:
            message_bit = '1 story was'
        else:
            message_bit = "%s stories were" % rows_updated
        self.message_user(request, "%s successfully marked as error." % message_bit)

    batch_listing.short_description = "批量上架"

    def batch_re_deliver(self, request, queryset):
        # 定义actions函数
        rows_updated = queryset.update(deal="RE_DELIVER")
        if rows_updated == 1:
            message_bit = '1 story was'
        else:
            message_bit = "%s stories were" % rows_updated
        self.message_user(request, "%s successfully marked as error." % message_bit)

    batch_re_deliver.short_description = "重新派送"



    def batch_sec_delivering(self, request, queryset):
        # 定义actions函数
        rows_updated = queryset.update(deal="SEC_DELIVERING")
        if rows_updated == 1:
            message_bit = '1 story was'
        else:
            message_bit = "%s stories were" % rows_updated
        self.message_user(request, "%s successfully marked as error." % message_bit)

    batch_sec_delivering.short_description = "二次派送中"

    def batch_tri_delivering(self, request, queryset):
        # 定义actions函数
        rows_updated = queryset.update(deal="TRI_DELIVERING")
        if rows_updated == 1:
            message_bit = '1 story was'
        else:
            message_bit = "%s stories were" % rows_updated
        self.message_user(request, "%s successfully marked as error." % message_bit)

    batch_tri_delivering.short_description = "三次派送中"

    def batch_received(self, request, queryset):
        # 定义actions函数
        rows_updated = queryset.update(deal="RECEIVED")
        if rows_updated == 1:
            message_bit = '1 story was'
        else:
            message_bit = "%s stories were" % rows_updated
        self.message_user(request, "%s successfully marked as error." % message_bit)

    batch_received.short_description = "已签收"

    def batch_wait(self, request, queryset):
        # 定义actions函数
        rows_updated = queryset.update(deal="WAIT")
        if rows_updated == 1:
            message_bit = '1 story was'
        else:
            message_bit = "%s stories were" % rows_updated
        self.message_user(request, "%s successfully marked as error." % message_bit)

    batch_wait.short_description = "沟通中"

    def batch_noresponse(self, request, queryset):
        # 定义actions函数
        rows_updated = queryset.update(deal="NORESPONSE")
        if rows_updated == 1:
            message_bit = '1 story was'
        else:
            message_bit = "%s stories were" % rows_updated
        self.message_user(request, "%s successfully marked as error." % message_bit)

    batch_noresponse.short_description = "联系不到客户"

    actions = ['batch_deliver_response','batch_customer_response','batch_yallavip_response',
                    'batch_done','batch_settle',
                    'batch_return','batch_returned','batch_listing', 'batch_re_moeny','batch_re_addr',
                    'batch_re_phone','batch_re_time','batch_re_deliver','batch_sec_delivering','batch_tri_delivering','batch_received'
                    'batch_wait','batch_noresponse']


    list_display = ('logistic_no','order_no','logistic_status','comments','his_comments','logistic_update','response','feedback','deal',
                        'show_order','show_ordercomment','show_orderphone','show_conversation' ,'image_tag')
    list_editable = ['response','feedback', 'deal',]
    search_fields = ['logistic_no','feedback','order_no' ]
    list_filter = ("logistic_status","comments",'response','feedback', 'deal',)

    def get_list_queryset(self):
        """批量查询订单号"""
        queryset = super().get_list_queryset( )


        query = self.request.GET.get(SEARCH_VAR, '')

        if (len(query) > 0):
            queryset |= self.model.objects.filter(order_no__in=query.split(","))

        if (len(query) > 0):
            queryset |= self.model.objects.filter(logistic_no__in=query.split(","))

        return queryset

class Logistic_jiachengResource(resources.ModelResource):
    in_date = fields.Field(attribute='in_date', column_name='签入时间')
    shipping_date = fields.Field(attribute='shipping_date', column_name='出货时间')

    logistic_no = fields.Field(attribute='logistic_no', column_name='服务商单号')
    order_no = fields.Field(attribute='order_no', column_name='订单号')
    tracking_no = fields.Field(attribute='tracking_no', column_name='转单号')

    country = fields.Field(attribute='country', column_name='国家 ')
    localphone = fields.Field(attribute='localphone', column_name='当地电话 ')

    comments = fields.Field(attribute='comments', column_name='问题件类型')


    class Meta:
        model = Logistic_jiacheng
        skip_unchanged = True
        report_skipped = True
        import_id_fields = ('logistic_no',)
        fields = ('in_date','shipping_date','logistic_no', 'tracking_no','country',
                    'localphone','comments',)


class Logistic_jiachengAdmin(object):

    def trail_status(self, obj):
        logistic_trail = Logistic_trail.objects.filter(logistic_no=obj.logistic_no).last()


        return logistic_trail.trail_status

    trail_status.short_description = "物流轨迹"

    def update_time(self, obj):
        logistic_trail = Logistic_trail.objects.filter(logistic_no=obj.logistic_no).last()


        return logistic_trail.update_time

    update_time.short_description = "更新时间"

    def update_locate(self, obj):
        logistic_trail = Logistic_trail.objects.filter(logistic_no=obj.logistic_no).last()


        return logistic_trail.update_locate

    update_locate.short_description = "更新地点"

    def show_conversation(self, obj):
        # print('orderconversation')
        orders = Order.objects.filter(logistic_no=obj.logistic_no)

        # print(orderconversation)

        links = ''
        for order in orders:

            if (order == None):
                continue

            orderconversation = OrderConversation.objects.filter(order=order)
            for item in orderconversation:
                conversation = item.conversation

                if (conversation != None):
                    '''
                    link = mark_safe(
                        u'<a href="http://business.facebook.com%s" target="view_window">%s</a>' % (
                            u'one', u'  ' + order.order_no))
                    links = links + order.order_no
                else:
                '''
                    link = mark_safe(
                        u'<a href="http://business.facebook.com%s" target="view_window">%s</a>' % (
                            conversation.link, u'  ' + order.order_no))
                    links = links + link

                # print(links)

        return (links)

    show_conversation.allow_tags = True
    show_conversation.short_description = "会话"

    def show_order(self, obj):
        orders = Order.objects.filter(logistic_no=obj.logistic_no)

        # print(orderconversation)

        order_nos = ''
        for order in orders:
            order_no = order.order_no
            order_nos = order_nos + '  ' + order_no

        return order_nos

    show_order.allow_tags = True

    show_order.short_description = "订单"

    def show_ordercomment(self, obj):
        orders = Order.objects.filter(logistic_no=obj.logistic_no)

        # print(orderconversation)

        order_comments = ''
        for order in orders:
            order_comment = order.order_comment
            order_comments = order_comments + '  ' + order_comment

        return order_comments

    show_ordercomment.allow_tags = True

    show_ordercomment.short_description = "订单备注"

    def show_orderphone(self, obj):
        orders = Order.objects.filter(logistic_no=obj.logistic_no)

        # print(orderconversation)

        order_phones = ''
        for order in orders:
            order_phones = order_phones + '  ' + order.receiver_phone

        return order_phones

        show_orderphone.allow_tags = True

    show_orderphone.short_description = "收货人电话"

    import_export_args = {"import_resource_class": Logistic_jiachengResource,
                          "export_resource_class": Logistic_jiachengResource}

    def batch_deliver_response(self, request, queryset):
        # 定义actions函数
        rows_updated = queryset.update(response="DELIVER")
        if rows_updated == 1:
            message_bit = '1 story was'
        else:
            message_bit = "%s stories were" % rows_updated
        self.message_user(request, "%s successfully marked as error." % message_bit)

    batch_deliver_response.short_description = "批量派送员责任"

    def batch_customer_response(self, request, queryset):
        # 定义actions函数
        rows_updated = queryset.update(response="CUSTOMER")
        if rows_updated == 1:
            message_bit = '1 story was'
        else:
            message_bit = "%s stories were" % rows_updated
        self.message_user(request, "%s successfully marked as error." % message_bit)

    batch_customer_response.short_description = "批量客户责任"

    def batch_yallavip_response(self, request, queryset):
        # 定义actions函数
        rows_updated = queryset.update(response="YALLAVIP")
        if rows_updated == 1:
            message_bit = '1 story was'
        else:
            message_bit = "%s stories were" % rows_updated
        self.message_user(request, "%s successfully marked as error." % message_bit)

    batch_yallavip_response.short_description = "批量yallavip责任"

    def batch_done(self, request, queryset):
        # 定义actions函数
        rows_updated = queryset.update(deal="DONE")
        if rows_updated == 1:
            message_bit = '1 story was'
        else:
            message_bit = "%s stories were" % rows_updated
        self.message_user(request, "%s successfully marked as error." % message_bit)

    batch_done.short_description = "批量完成"

    def batch_settle(self, request, queryset):
        # 定义actions函数
        rows_updated = queryset.update(deal="SETTLE")
        if rows_updated == 1:
            message_bit = '1 story was'
        else:
            message_bit = "%s stories were" % rows_updated
        self.message_user(request, "%s successfully marked as error." % message_bit)

    batch_settle.short_description = "批量待结算"

    def batch_return(self, request, queryset):
        # 定义actions函数
        rows_updated = queryset.update(deal="RETURN")
        if rows_updated == 1:
            message_bit = '1 story was'
        else:
            message_bit = "%s stories were" % rows_updated
        self.message_user(request, "%s successfully marked as error." % message_bit)

    batch_return.short_description = "批量退仓"

    def batch_returned(self, request, queryset):
        # 定义actions函数
        rows_updated = queryset.update(deal="RETURNED")
        if rows_updated == 1:
            message_bit = '1 story was'
        else:
            message_bit = "%s stories were" % rows_updated
        self.message_user(request, "%s successfully marked as error." % message_bit)

    batch_returned.short_description = "批量已退到仓库"

    def batch_listing(self, request, queryset):
        # 定义actions函数
        rows_updated = queryset.update(deal="LISTING")
        if rows_updated == 1:
            message_bit = '1 story was'
        else:
            message_bit = "%s stories were" % rows_updated
        self.message_user(request, "%s successfully marked as error." % message_bit)

    batch_listing.short_description = "批量上架"

    def batch_re_deliver(self, request, queryset):
        # 定义actions函数
        rows_updated = queryset.update(deal="RE_DELIVER")
        if rows_updated == 1:
            message_bit = '1 story was'
        else:
            message_bit = "%s stories were" % rows_updated
        self.message_user(request, "%s successfully marked as error." % message_bit)

    batch_re_deliver.short_description = "重新派送"

    def batch_re_delivering(self, request, queryset):
        # 定义actions函数
        rows_updated = queryset.update(deal="RE_DELIVERING")
        if rows_updated == 1:
            message_bit = '1 story was'
        else:
            message_bit = "%s stories were" % rows_updated
        self.message_user(request, "%s successfully marked as error." % message_bit)

    batch_re_delivering.short_description = "二次派送中"

    def batch_wait(self, request, queryset):
        # 定义actions函数
        rows_updated = queryset.update(deal="WAIT")
        if rows_updated == 1:
            message_bit = '1 story was'
        else:
            message_bit = "%s stories were" % rows_updated
        self.message_user(request, "%s successfully marked as error." % message_bit)

    batch_wait.short_description = "沟通中"

    def batch_noresponse(self, request, queryset):
        # 定义actions函数
        rows_updated = queryset.update(deal="NORESPONSE")
        if rows_updated == 1:
            message_bit = '1 story was'
        else:
            message_bit = "%s stories were" % rows_updated
        self.message_user(request, "%s successfully marked as error." % message_bit)

    batch_noresponse.short_description = "联系不到客户"

    def batch_updatelogistic_trail(self, request, queryset):
        # 定义actions函数
        requrl = "http://api.jcex.com/JcexJson/api/notify/sendmsg"

        param_data= dict()
        param_data["customerid"] = -1
        #param_data["waybillnumber"] = "989384782"
        param_data["isdisplaydetail"] = "false"


        #data_body =base64.b64encode(json.dumps(param_data).encode('utf-8'))
        #  base64.b64encode()


        param = dict()
        param["service"] = 'track'
        #param["data_body"] = data_body


        res = requests.post(requrl,params =param)

        for row in queryset:
            param_data["waybillnumber"] = row.logistic_no
            data_body = base64.b64encode(json.dumps(param_data).encode('utf-8'))
            param["data_body"] = data_body
            res = requests.post(requrl, params=param)

            data = json.loads(res.text)

            waybillnumber = data["waybillnumber"]
            #recipientcountry = data["recipientcountry"]

            statusdetail = data["displaydetail"][0]["statusdetail"]


            for i in range(len(statusdetail)):
                status_d = statusdetail[i]



                obj, created = Logistic_trail.objects.update_or_create(
                    logistic_no=waybillnumber,update_time=status_d["time"],
                    defaults={
                        'trail_status' : status_d["status"],

                        'update_locate' : status_d["locate"]
                    },


                )

    batch_updatelogistic_trail.short_description = "批量更新物流轨迹"

    actions = ['batch_deliver_response', 'batch_customer_response', 'batch_yallavip_response',
               'batch_done', 'batch_settle',
               'batch_return','batch_returned','batch_listing', 'batch_re_moeny', 'batch_re_addr',
               'batch_re_phone', 'batch_re_time', 'batch_re_deliver','batch_re_delivering',
               'batch_wait', 'batch_noresponse','batch_updatelogistic_trail']

    list_display = ('logistic_no','shipping_date','update_time','trail_status','update_locate', 'comments', 'response', 'feedback', 'deal',
                    'show_order', 'show_ordercomment', 'show_orderphone', 'show_conversation', 'image_tag')
    list_editable = ['response', 'feedback', 'deal', ]
    search_fields = ['logistic_no', 'feedback','order_no',]
    list_filter = ("comments", 'response', 'feedback', 'deal',)
    ordering = ['-shipping_date']


    def get_list_queryset(self):
        """批量查询订单号"""
        queryset = super().get_list_queryset( )


        query = self.request.GET.get(SEARCH_VAR, '')

        if (len(query) > 0):
            queryset |= self.model.objects.filter(order_no__in=query.split(","))

        if (len(query) > 0):
            queryset |= self.model.objects.filter(logistic_no__in=query.split(","))

        return queryset

class Logistic_statusResource(resources.ModelResource):

    shipping_date = fields.Field(attribute='shipping_date', column_name='到货日期')
    logistic_no = fields.Field(attribute='logistic_no', column_name='客户单号')
    refer_no = fields.Field(attribute='refer_no', column_name='参考号')



    tracking_no = fields.Field(attribute='tracking_no', column_name='渠道转单号')

    real_weight = fields.Field(attribute='real_weight', column_name='实重')
    size_weight = fields.Field(attribute='size_weight', column_name='体积重')
    charge_weight = fields.Field(attribute='charge_weight', column_name='计费重')

    '''
    update_date = fields.Field(attribute='update_date', column_name='更新时间')
    update_info = fields.Field(attribute='update_info', column_name='更新地点')
    logistic_status = fields.Field(attribute='logistic_status', column_name='签收状态')
    '''



    class Meta:
        model = Logistic_status
        skip_unchanged = True
        report_skipped = True
        import_id_fields = ('logistic_no',)
        fields = ('shipping_date','logistic_no','refer_no', 'tracking_no',
                    'real_weight','size_weight','charge_weight',
                    )

class Logistic_statusAdmin(object):

    import_export_args = {"import_resource_class": Logistic_statusResource,
                          "export_resource_class": Logistic_statusResource}


    def trail_status(self, obj):
        logistic_trail = Logistic_trail.objects.filter(logistic_no=obj.logistic_no).last()


        return logistic_trail.trail_status

    trail_status.short_description = "物流轨迹"

    def update_time(self, obj):
        logistic_trail = Logistic_trail.objects.filter(logistic_no=obj.logistic_no).last()


        return logistic_trail.update_time

    update_time.short_description = "更新时间"

    def update_locate(self, obj):
        logistic_trail = Logistic_trail.objects.filter(logistic_no=obj.logistic_no).last()


        return logistic_trail.update_locate

    update_locate.short_description = "更新地点"


    actions = ["batch_updatelogistic_trail",]

    list_display = ('shipping_date','logistic_no','refer_no', 'tracking_no',
                    'real_weight','size_weight','charge_weight',
                    'update_time','trail_status','update_locate')
    list_editable = []
    search_fields = ['logistic_no',]
    #list_filter = ("update_time", )
    ordering = ['-shipping_date']



    def get_list_queryset(self):
        """批量查询订单号"""
        queryset = super().get_list_queryset( )


        query = self.request.GET.get(SEARCH_VAR, '')

        if (len(query) > 0):
            queryset |= self.model.objects.filter(logistic_no=query.split(","))

        return queryset
    '''
    def batch_updatelogistic_info(self, request, queryset):
        # 定义actions函数
        requrl = "http://api.jcex.com/JcexJson/api/notify/sendmsg"

        param_data= dict()
        param_data["customerid"] = -1

        param_data["isdisplaydetail"] = "true"


        #data_body =base64.b64encode(json.dumps(param_data).encode('utf-8'))
        #  base64.b64encode()


        param = dict()
        param["service"] = 'track'
        #param["data_body"] = data_body


        res = requests.post(requrl,params =param)

        for row in queryset:
            param_data["waybillnumber"] = row.logistic_no
            data_body = base64.b64encode(json.dumps(param_data).encode('utf-8'))
            param["data_body"] = data_body
            res = requests.post(requrl, params=param)

            data = json.loads(res.text)

            waybillnumber = data["waybillnumber"]
            displaydetail = data["displaydetail"]

            #statusdetail = data["statusdetail"]

            print(displaydetail)



    batch_updatelogistic_info.short_description = "批量更新物流信息"
    '''

    def batch_updatelogistic_trail(self, request, queryset):
        # 定义actions函数
        requrl = "http://api.jcex.com/JcexJson/api/notify/sendmsg"

        param_data= dict()
        param_data["customerid"] = -1
        #param_data["waybillnumber"] = "989384782"
        param_data["isdisplaydetail"] = "false"


        #data_body =base64.b64encode(json.dumps(param_data).encode('utf-8'))
        #  base64.b64encode()


        param = dict()
        param["service"] = 'track'
        #param["data_body"] = data_body


        res = requests.post(requrl,params =param)

        for row in queryset:
            param_data["waybillnumber"] = row.logistic_no
            data_body = base64.b64encode(json.dumps(param_data).encode('utf-8'))
            param["data_body"] = data_body
            res = requests.post(requrl, params=param)

            data = json.loads(res.text)

            waybillnumber = data["waybillnumber"]
            #recipientcountry = data["recipientcountry"]

            statusdetail = data["displaydetail"][0]["statusdetail"]


            for i in range(len(statusdetail)):
                status_d = statusdetail[i]

                obj, created = Logistic_trail.objects.update_or_create(
                    logistic_no=waybillnumber, update_time=status_d["time"],
                    defaults={
                        'trail_status': status_d["status"],

                        'update_locate': status_d["locate"]
                    },

                )

    batch_updatelogistic_trail.short_description = "批量更新物流轨迹"


class Logistic_trailAdmin(object):


    list_display = ('logistic_no', 'update_time', 'update_locate', 'trail_status',)
    list_editable = []
    search_fields = ['logistic_no' ]

    #ordering = ['-order_no']

    def get_list_queryset(self):
        """批量查询订单号"""
        queryset = super().get_list_queryset()

        query = self.request.GET.get(SEARCH_VAR, '')

        if (len(query) > 0):
            queryset |= self.model.objects.filter(logistic_no__in=query.split(","))

        return queryset

class SmsResource(resources.ModelResource):
    send_time = fields.Field(attribute='send_time', column_name='发送时间')
    send_status = fields.Field(attribute='send_status', column_name='发送状态')
    content = fields.Field(attribute='content', column_name='内容')
    phone = fields.Field(attribute='phone', column_name='手机号')

    receive_status = fields.Field(attribute='receive_status', column_name='接收状态')

    fail_reason = fields.Field(attribute='fail_reason', column_name='失败原因')


    class Meta:
        model = Sms
        skip_unchanged = True
        report_skipped = True
        import_id_fields = ('send_time','phone',)
        fields = ('send_time', 'send_status', 'content', 'phone', 'receive_status',
                  'fail_reason')


class SmsAdmin(object):
    import_export_args = {"import_resource_class": SmsResource,
                          "export_resource_class": SmsResource}

    #actions = ["batch_updatelogisticinfo", ]

    list_display = ('send_time', 'send_status', 'content', 'phone', 'receive_status',
                  'fail_reason')
    list_editable = []
    search_fields = ['phone', 'content','receive_status', ]
    list_filter = ("phone",'receive_status',)
    #ordering = ['-order_no']

    def get_list_queryset(self):
        """批量查询订单号"""
        queryset = super().get_list_queryset()

        query = self.request.GET.get(SEARCH_VAR, '')

        if (len(query) > 0):
            queryset |= self.model.objects.filter(phone__in=query.split(","))

        return queryset







class LogisticAccountResource(resources.ModelResource):
    #shipping_time = fields.Field(attribute='shipping_time', column_name='到货日期')
    logistic_no = fields.Field(attribute='logistic_no', column_name='客户单号')
    #tracking_no = fields.Field(attribute='tracking_no', column_name='渠道转单号')
    #refer_no = fields.Field(attribute='refer_no', column_name='参考号')

    real_weight = fields.Field(attribute='real_weight', column_name='实重')
    size_weight = fields.Field(attribute='size_weight', column_name='体积重')
    charge_weight = fields.Field(attribute='charge_weight', column_name='计费重')

    COD = fields.Field(attribute='COD', column_name='代收货款')
    exchange = fields.Field(attribute='exchange', column_name='汇率')
    currency = fields.Field(attribute='currency', column_name='币种')
    standard_currency = fields.Field(attribute='standard_currency', column_name='本位币金额')
    fee = fields.Field(attribute='fee', column_name='运费')
    other_fee = fields.Field(attribute='other_fee', column_name='其他杂费')
    total_fee = fields.Field(attribute='total_fee', column_name='运杂费')
    refund = fields.Field(attribute='refund', column_name='应退金额')
    settle_type = fields.Field(attribute='settle_type', column_name='结算类型')
    package_status = fields.Field(attribute='package_status', column_name='包裹状态')

    class Meta:
        model = LogisticAccount
        skip_unchanged = True
        report_skipped = True
        import_id_fields = ('logistic_no',)
        fields = ('logistic_no',
                    'real_weight','size_weight','charge_weight',
                   'COD','exchange','currency','standard_currency',
                  'fee','other_fee','total_fee','refund','settle_type',
                  'package_status',)

class LogisticAccountAdmin(object):

    def logistic_status(self, obj):
        return Logistic.objects.filter(logistic_no=obj.logistic_no).first().logistic_update_status
    logistic_status.short_description = "物流状态"

    def logistic_type(self, obj):
        return Logistic.objects.filter(logistic_no=obj.logistic_no).first().logistic_type

    logistic_type.short_description = "物流公司"

    import_export_args = {"import_resource_class": LogisticAccountResource,
                          "export_resource_class": LogisticAccountResource}

    list_display = ( 'logistic_no', 'logistic_type', 'logistic_status',
                    'real_weight', 'size_weight', 'charge_weight',
                    'COD', 'exchange', 'currency','standard_currency', 'fee','other_fee','total_fee', 'refund',
                     'settle_type','package_status'
                   )
    list_editable = []
    search_fields = ['logistic_no', ]
    list_filter = ("settle_type", "package_status",)
    ordering = ['-logistic_no']
    actions = ["COD_settle","Fee_settle"
                ]

    def COD_settle(self, request, queryset):
        # 定义actions函数
        for row in queryset:

            Order.objects.filter(logistic_no=row.logistic_no).update(settle_status="COD")

    COD_settle.short_description = "COD结算"

    def Fee_settle(self, request, queryset):
        # 定义actions函数
        for row in queryset:

            Order.objects.filter(logistic_no=row.logistic_no).update(settle_status="FEE")

    Fee_settle.short_description = "运费结算"



    def get_list_queryset(self):
        """批量查询订单号"""
        queryset = super().get_list_queryset()

        query = self.request.GET.get(SEARCH_VAR, '')

        if (len(query) > 0):
            queryset |= self.model.objects.filter(logistic_no__in=query.split(","))

        return queryset

class OrderTrackAdminResource(resources.ModelResource):

    logistic_no = fields.Field(attribute='logistic_no', column_name='客户单号')

    package_status = fields.Field(attribute='package_status', column_name='包裹状态')


    class Meta:
        model = LogisticAccount
        skip_unchanged = True
        report_skipped = True
        import_id_fields = ('logistic_no',)
        fields = ('logistic_no', 'package_status')


class OrderTrackAdmin(object):
    import_export_args = {"import_resource_class": OrderTrackAdminResource,
                          "export_resource_class": OrderTrackAdminResource}

    list_display = ('order_no','logistic_no','logistic_update_date','file_status',
                    'logistic_update_status','package_status', 'customer_status',
                    'postsale_status','settle_status','resell_status',)
    list_editable = []
    search_fields = ['order_no','logistic_no' ]
    list_filter = ('file_status', 'logistic_update_status','package_status', 'customer_status','postsale_status','settle_status',)
    actions = ["batch_file"]
    #ordering = ['-order_no']

    def batch_file(self, request, queryset):
        # 定义actions函数
        return queryset.update(file_status="CLOSED")
    batch_file.short_description = "批量归档"

    def get_list_queryset(self):
        """批量查询订单号"""
        queryset = super().get_list_queryset()

        query = self.request.GET.get(SEARCH_VAR, '')

        if (len(query) > 0):
            queryset |= self.model.objects.filter(logistic_no__in=query.split(","))

        return queryset

    def queryset(self):
        qs = super(OrderTrackAdmin, self).queryset()
        return qs.filter( Q(order_status='已发货') )


xadmin.site.register(Order, OrderAdmin)
xadmin.site.register(OrderDetail, OrderDetailAdmin)
xadmin.site.register(Verify, VerifyAdmin)
xadmin.site.register(ClientService,ClientServiceAdmin)


xadmin.site.register(OrderConversation, OrderConverstaionAdmin)
xadmin.site.register(Verification,VerificationAdmin)
#xadmin.site.register(Logistic_winlink,Logistic_winlinkAdmin)
#xadmin.site.register(Logistic_jiacheng,Logistic_jiachengAdmin)
#xadmin.site.register(Logistic_status,Logistic_statusAdmin)
#xadmin.site.register(Logistic_trail,Logistic_trailAdmin)
xadmin.site.register(Sms,SmsAdmin)
#xadmin.site.register(Logistic,LogisticAdmin)
#xadmin.site.register(OrderTrack,OrderTrackAdmin)
#xadmin.site.register(LogisticAccount,LogisticAccountAdmin)

@xadmin.sites.register(OverseaOrder)
class OverseaOrderAdmin(object):
    def photo(self, obj):
        #order_no = Order.objects.filter(logistic_no=self.logistic_no).first().order_no
        order_no = obj.order_no

        if order_no is not None and order_no != "":
            photos = MyPhoto.objects.filter(name__icontains=order_no)
            img = ''

            for photo in photos:
                try:
                    img = img + '<a href="%s" target="view_window"><img src="%s" width="100px"></a>' % (
                    photo.link, photo.picture)
                except Exception as e:
                    print("获取图片出错", e)

            return mark_safe(img)

        else:
            photos = "no photo"
    photo.short_description = "ref photo"

    def fb_photo(self, obj):
        #order_no = Order.objects.filter(logistic_no=self.logistic_no).first().order_no
        ordetails = obj.order_orderdetail.all()

        img = ""
        for ordetail in ordetails:
            sku = ordetail.sku
            variant = ShopifyVariant.objects.filter(sku=sku).first()
            handle = ShopifyProduct.objects.filter(product_no=variant.product_no).first().handle
            photo = MyPhoto.objects.filter(name__icontains=handle).first()
            try:
                img += '<a href="%s" target="view_window"><img src="%s" width="100px"></a>' % (
                photo.link, photo.picture)
            except Exception as e:
                print("获取图片出错", e)

        return mark_safe(img)

    fb_photo.short_description = "fb photo"




    '''
    def show_images(self, obj):

        img = ''
        ordetails = obj.order_orderdetail.all()
        for ordetail in ordetails:
            try:
                #img = mark_safe('<img src="%s" width="100px" />' % (obj.logo.url,))
                variant =  ShopifyVariant.objects.get(sku=ordetail.sku)
                image_no = variant.image_no

                handle = ShopifyProduct.objects.get(product_no=variant.product_no).handle


                img += mark_safe(
                    '<a href="%s" target="view_window"><img src="%s" width="150px"></a>' % (
                        "https://www.yallavip.com/products/"+handle,
                        ShopifyImage.objects.get(image_no=image_no).src,
                        ))

            except Exception as e:
                print("获取图片出错", e)
        return img

    show_images.short_description = "product photoes"
    '''

    list_display = ('logistic_no', 'order_no', 'order_amount','photo', )
    list_editable = []
    search_fields = ['order_orderdetail__sku','order_no', ]

    #ordering = ['-order_no']
    '''
    def get_list_queryset(self):
        """批量查询订单号"""
        queryset = super().get_list_queryset()

        query = self.request.GET.get(SEARCH_VAR, '')

        if (len(query) > 0):
            queryset |= self.model.objects.filter(order_no__in=query.split(","))
        if (len(query) > 0):
            queryset |= self.model.objects.filter(logistic_no__in=query.split(","))
        return queryset
    '''


    def queryset(self):
        qs = super().queryset()
        deal_list = ["RETURNED",
                     #"REDELIVERING",
                     ]
        return qs.filter(~Q(resell_status = 'SELLING'),order_package__yallavip_package_status__in=deal_list)

@xadmin.sites.register(OverseaSkuRank)
class OverseaSkuRankAdmin(object):
    list_display = ('sku', 'orders', )
    list_editable = []
    search_fields = ['sku', ]

@xadmin.sites.register(OrderDetail_lightin)
class OrderDetail_lightinAdmin(object):
    def order_status(self, obj):
        return obj.order.status

    order_status.short_description = u"订单状态"

    list_display = ['order',  'SKU',"barcode", 'quantity', 'price', 'order_status', ]

    search_fields = ["order__order_no", 'SKU', "barcode__barcode",]

    ordering = ['-order__order_no']
    list_filter = ("order__status", "order__verify__verify_status", "order__verify__sms_status",)

    actions = [ ]



'''
@xadmin.sites.register(MyOrder)
class MyOrderAdmin(object):
    class MyOrderDetailInline(object):
        model = MyOrderDetail
        extra = 1
        #style = 'tab'
        form_layout = (
            Main(
                Fieldset('订单明细',
                         #Row( 'lightin_sku','product_quantity','price',),
                         'handle', 'lightin_sku','price', 'quantity', 'amount',

                         ),

            )
        )


    list_display = ['buyer_name',  ]

    search_fields = []

    ordering = []
    list_filter = ()

    actions = [ ]
    relfield_style = 'fk_ajax'

    form_layout = (
        Main(
            Fieldset('客户信息',
                     Row('buyer_name', ),
                     ),


        ),
        Side(
            Fieldset('最近订单',

                     ),
        )
    )
    inlines = [MyOrderDetailInline, ]




@xadmin.sites.register(MyOrderDetail)
class MyOrderDetailAdmin(object):
    list_display = ['order','handle', 'lightin_sku', 'quantity','price','amount', ]

    search_fields = []

    ordering = []
    list_filter = ()

    actions = []
'''




@xadmin.sites.register(Order_History)
class Order_HistoryAdmin(object):
    def trail_status(self, obj):
        logistic_trail = Logistic_trail.objects.filter(logistic_no=obj.logistic_no).last()

        return logistic_trail.trail_status

    trail_status.short_description = "物流轨迹"

    def show_settle_status(self, obj):
        return LogisticAccount.objects.filter(logistic_no=obj.logistic_no).first().settle_status

    show_settle_status.short_description = "结算状态"

    def show_conversation(self, obj):
        return show_conversation_tmp(obj)

    show_conversation.allow_tags = True

    show_conversation.short_description = "会话"

    # "stock", "cal_barcode", "inventory_status",
    list_display = ["order_no", "status", "stock", "wms_status", "fulfill_error", "order_amount", "order_time",
                    "logistic_no", "order_comment"]
    list_editable = ["status"]
    # list_display_links = ["show_conversation"]
    search_fields = ["order_no", 'logistic_no', ]
    list_filter = (
    "status", "wms_status", "financial_status", "fulfillment_status", "package_status", "verify_time", "order_time",
    "send_time", "verify__verify_status", "verify__sms_status",)
    ordering = ['-order_time']


'''
@xadmin.sites.register(CsOrder)
class CsOrderAdmin(object):

    def photo(self, obj):
        handles = obj.handles.split()
        lightin_spus = Lightin_SPU.objects.filter(handle__in=handles).distinct()
        img = ''

        for lightin_spu in lightin_spus:
            img += '<br><a>handle: %s</a><br><br>' % (lightin_spu.handle)

            lightin_skus = lightin_spu.spu_sku.filter(o_sellable__gt=0).distinct()
            skus = lightin_skus.values_list("SKU",   "o_sellable","sku_price", "skuattr",)
            for sku in skus:
                #img += '<br><a>%s<br>规格: %s<br>库存: %s</a><br>' % ( sku[0], sku[1], str(sku[2]))
                img += '<a>%s   %s  %s    %s</a><br>' % (sku[0],  str(sku[1]),sku[2], sku[3])


            if lightin_spu.images_dict :
                images= json.loads(lightin_spu.images_dict).values()

                for image in images:

                    a = "/"
                    image_split = image.split(a)

                    image_split[4] = '800x800'
                    photo = a.join(image_split)
                    print("spu 图片", lightin_spu, photo)
                    img = img + '<a><img src="%s" width="100px"></a>' % (photo)

                    img = img + '<a><img src="%s" width="100px"></a>' % (image)






            else:
                img = img + "no photo"





        return mark_safe(img)

    photo.short_description = "产品图片"

    def abs_order(self, obj):
        #遍历草稿表，把所有数量大于0的加起来

        img = ""
        subtotal = 0
        count = 0
        error = ""
        if not obj.discount:
            discount = 0
        else:
            discount = obj.discount

        details =  obj.cs_order_detail.filter(quantity__gt=0)

        for detail in details:
            try:
                sku = detail.lightin_sku
                subtotal += sku.sku_price *  detail.quantity
                count += detail.quantity

                image = None

                if sku.image:
                    image = sku.image
                    print("sku 图片")
                else:

                    spu = sku.lightin_spu
                    if spu.images_dict:
                        images = json.loads(spu.images_dict).values()

                        if images and len(images) > 0:
      
                            a = "/"
                            image_split = list(image)[0].split(a)

                            image_split[4] = '800x800'
                            image = a.join(image_split)
                            print("spu 图片", spu, image)

                            image = list(images)[0]
                if image:
                    img += '<a><img src="%s" width="100px"></a>' % (image)

                img += '<br><a>%s %s   (%s sets)</a><br>' % (sku, sku.skuattr, detail.quantity)

            except Exception as e:
                print(e)
                error = "计算出错" + detail.lightin_sku.SKU
                break


        if error == "":
            tax = subtotal * 0.05
            COD = 20
            content = "<br><a>Subtotal  %sitems    %s SR<a><br>"%(count,subtotal)
            content += "<a>COD Fee              %s SR<a><br>" % (COD)
            content += "<a>VAT Tax              %s SR<a><br>"%(tax)
            content += "<a>Discount             %s SR<a><br>" % (discount)
            content += "<a>Total                %s SR<a><br>" % (int(subtotal+COD+tax-float(discount)))

            img += content
            return mark_safe(img)
        else:
            return  error

    abs_order.short_description = "订单摘要"

    #客户收件信息摘要
    def abs_customer(self, obj):
        content =""

        content += "<span>phone_1  %s<span><br>" % (obj.customer.phone_1)
        content += "<span>address  %s<span><br>" % (obj.customer.address1)

        #return  mark_safe(content)

        return format_html(content)



    abs_customer.short_description = "收件信息摘要"



    list_display = ['customer','handles', 'photo', "discount", "abs_order","abs_customer", ]
    list_editable = ["handles","discount", ]

    search_fields = []

    ordering = []
    list_filter = ()

    actions = ['batch_prepare_draft',]
    relfield_style = 'fk_ajax'

    def batch_prepare_draft(self, request, queryset):
        # 定义actions函数
        #根据货号找到所有有库存的sku，把sku插到草稿表里，供进一步编辑
        #如果对应的sku已经有了，就什么也不做
        for row in queryset:
            handles = row.handles.split()
            lightin_skus = Lightin_SKU.objects.filter(lightin_spu__handle__in = handles, o_sellable__gt=0)

            for lightin_sku in lightin_skus:
                obj, created = CsOrderDetail.objects.get_or_create(
                    csorder=row,
                    lightin_sku = lightin_sku,
                    defaults={'quantity': 0})

        return

    batch_prepare_draft.short_description = "更新草稿"

@xadmin.sites.register(CsOrderDetail)
class CsOrderDetailAdmin(object):
    list_display = ['csorder', 'lightin_sku', 'handle','sellable','quantity', 'skuattr', "photo",]
    list_editable = ["quantity", ]

    search_fields = []

    ordering = []
    list_filter = ()

    actions = [ ]

    def photo(self, obj):
        # 如果sku有属性图片则用属性图片，否则用spu图片的第一张
        image = None
        sku = obj.lightin_sku
        if sku.image:
            image = sku.image
            print("sku 图片")
        else:

            spu = sku.lightin_spu
            if spu.images_dict:
                image = json.loads(spu.images_dict).values()
                if image and len(image) > 0:
                    a = "/"
                    image_split = list(image)[0].split(a)

                    image_split[4] = '800x800'
                    image = a.join(image_split)
                    print("spu 图片", spu, image)

        img = '<a><img src="%s" width="200px"></a>' % (image)

        return mark_safe(img)

    photo.short_description = "product photo"

    def skuattr(self,obj):
        return  obj.lightin_sku.skuattr

    skuattr.short_description = "skuattr"

    def sellable(self, obj):
        return obj.lightin_sku.o_sellable

    sellable.short_description = "sellable"

    def handle(self, obj):
        return obj.lightin_sku.lightin_spu.handle

    handle.short_description = "handle"

@xadmin.sites.register(Customer)
class CustomerAdmin(object):
    list_display = ['name', 'receiver_name', 'country_code','city','address1', 'address2', "address3",
                    'city','phone_1', 'phone_2', "comments","conversation",]
    list_editable = [ ]

    search_fields = []

    ordering = []
    list_filter = ()

    actions = [ ]
'''