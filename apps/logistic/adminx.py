# -*- coding: utf-8 -*-
__author__ = 'bobby'

import requests
import json
import time
import base64
import operator

from django.utils import timezone as dt

from io import BytesIO

# 图片的基本参数获取
try:
    from PIL import Image, ImageDraw, ImageFont, ImageEnhance
    import csv
    import math
except ImportError:
    import Image, ImageDraw, ImageFont, ImageEnhance

from . import watermark

import numpy as np, re
import xadmin
from django.shortcuts import get_object_or_404, get_list_or_404, render
from import_export import resources, fields
from import_export.widgets import ForeignKeyWidget
from .models import Package, LogisticSupplier,LogisticCustomerService,OverseaPackage,Resell,\
        LogisticBalance,Overtime,ToBalance,LogisticManagerConfirm,LogisticResendTrail,Reminder, MultiPackage,DealTrail
from orders.models import Order,OrderConversation,OrderDetail
from product.models import Product
from django.db import models

from datetime import datetime,timedelta
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
from django.utils import timezone as dt


def create_product(dest_shop, queryset ):
    '''

    handle_init = ShopifyProduct.objects.filter(shop_name=dest_shop).order_by('-product_no').first()

    handle_i = handle_init.handle

    handle_i = int(handle_i[1:])

    print(" now let's start create_product ", handle_i)
    '''

    for order in queryset:

        # 初始化SDK
        shop_obj = Shop.objects.get(shop_name=dest_shop)

        shop_url = "https://%s:%s@%s.myshopify.com" % (shop_obj.apikey, shop_obj.password, shop_obj.shop_name)

        url = shop_url + "/admin/products.json"


        #每100个订单创建一个海外仓商品，订单作为变体存放。，否则创建新的

        order_no = order.order_no
        handle_i = int(int(order_no.split('-')[1]) /100)
        handle_new = "O"+ str(handle_i).zfill(5)

        #所以先检测商品是否存在
        url = shop_url + "/admin/products/%s.json"%(handle_new)
        r = requests.post(url, headers=headers, data=json.dumps(params))

        print("handl_new is ", handle_new)
        print("r is ", r)
        return

        '''
        params = {
            "product": {
                "handle": handle_new,
                "title": product.title,
                "body_html": product.body_html,
                "vendor": product.vendor,
                "product_type": product.product_type,
                "tags": product.tags,

                # "variants": variants_list,
                # "options": option_list
            }
        }
        headers = {
            "Content-Type": "application/json",
            "charset": "utf-8",

        }

        r = requests.post(url, headers=headers, data=json.dumps(params))
        data = json.loads(r.text)
        new_product = data.get("product")
        if new_product is None:
            print("data is ", data)
            continue

        new_product_no = new_product.get("id")

        # 增加变体

        # image
        image_dict = {}
        for k_img in range(len(new_product["images"])):
            image_row = new_product["images"][k_img]
            new_image_no = image_row["id"]
            # new_image_list.append(image_no)
            old_image_no = imgs_list[k_img]["image_no"]

            image_dict[old_image_no] = new_image_no
            # print("old image %s new image %s"%(old_image_no, new_image_no ))

        # option
        option_list = []

        options = ShopifyOptions.objects.filter(product_no=product.product_no).values('name', 'values')
        for row in options:
            option = {
                "name": row["name"],
                "values": re.split('[.]', row["values"])
            }
            option_list.append(option)

        # variant
        variants_list = []

        variants = ShopifyVariant.objects.filter(product_no=product.product_no).values()

        for variant in variants:
            old_image_no = variant.get("image_no")
            new_image_no = image_dict.get(old_image_no)
            print("image dict  %s %s " % (old_image_no, new_image_no))

            sku = handle_new
            option1 = variant.get("option1")
            option2 = variant.get("option2")
            option3 = variant.get("option3")

            if option1:
                sku = sku + "-" + option1.replace("&", '').replace('-', '').replace('.', '').replace(' ', '')
                if option2:
                    sku = sku + "_" + option2.replace("&", '').replace('-', '').replace('.', '').replace(' ', '')
                    if option3:
                        sku = sku + "_" + option3.replace("&", '').replace('-', '').replace('.', '').replace(' ', '')

            variant_item = {
                "option1": option1,
                "option2": option2,
                "option3": option3,
                "price": int(float(variant.get("price")) * 2.8),
                "compare_at_price": int(float(variant.get("price")) * 2.8 * random.uniform(2, 3)),
                "sku": sku,
                "position": variant.get("position"),
                "image_id": new_image_no,
                "grams": variant.get("grams"),
                "title": variant.get("title"),
                "taxable": "true",
                "inventory_management": "shopify",
                "fulfillment_service": "manual",
                "inventory_policy": "continue",

                "inventory_quantity": 10000,
                "requires_shipping": "true",
                "weight": 0.5,
                "weight_unit": "kg",

            }
            # print("variant_item", variant_item)
            variants_list.append(variant_item)

        params = {
            "product": {
                "variants": variants_list,
                "options": option_list,

            }
        }
        headers = {
            "Content-Type": "application/json",
            "charset": "utf-8",

        }

        # print("upload data is ",json.dumps(params))

        url = shop_url + "/admin/products/%s.json" % (new_product_no)
        r = requests.put(url, headers=headers, data=json.dumps(params))
        data = json.loads(r.text)

        new_product = data.get("product")
        if new_product is None:
            print("data is ", data)
            continue

        product_list = []
        product_list.append(new_product)
        insert_product(dest_shop, product_list)

        print("new_product_no is", new_product.get("id"))

        # shopify.ShopifyResource.clear_session()

    queryset.update(listed=True, )
    '''






# 裁剪压缩图片
def clipResizeImg_new(im, dst_w, dst_h, qua=95):
    '''''
        先按照一个比例对图片剪裁，然后在压缩到指定尺寸
        一个图片 16:5 ，压缩为 2:1 并且宽为200，就要先把图片裁剪成 10:5,然后在等比压缩
    '''
    ori_w, ori_h = im.size

    dst_scale = float(dst_w) / dst_h  # 目标高宽比
    ori_scale = float(ori_w) / ori_h  # 原高宽比

    if ori_scale <= dst_scale:
        # 过高
        width = ori_w
        height = int(width / dst_scale)

        x = 0
        y = (ori_h - height) / 2

    else:
        # 过宽
        height = ori_h
        width = int(height * dst_scale)

        x = (ori_w - width) / 2
        y = 0

        # 裁剪
    box = (x, y, width + x, height + y)
    # 这里的参数可以这么认为：从某图的(x,y)坐标开始截，截到(width+x,height+y)坐标
    # 所包围的图像，crop方法与php中的imagecopy方法大为不一样
    newIm = im.crop(box)
    im = None

    # 压缩
    ratio = float(dst_w) / width
    newWidth = int(width * ratio)
    newHeight = int(height * ratio)
    #newIm.resize((newWidth, newHeight), Image.ANTIALIAS).save("test6.jpg", "JPEG", quality=95)
    return newIm.resize((newWidth, newHeight), Image.ANTIALIAS)

    print
    "old size  %s  %s" % (ori_w, ori_h)
    print
    "new size %s %s" % (newWidth, newHeight)
    print
    u"剪裁后等比压缩完成"


def batch_updatelogistic_trail(self, request, queryset):
    # 定义actions函数
    requrl = "http://api.jcex.com/JcexJson/api/notify/sendmsg"
    '''
    #登录
    param_login = dict()
    param_login["service"] = 'login'

    param_login_data = dict()
    param_login_data["username"] = "2b6365bbe56bac825491703334bf71fe"
    param_login_data["password"] = "db713ce28c137b3b29af05f8d678d742db713ce28c137b3b29af05f8d678d742"


    login_data_body = base64.b64encode(json.dumps(param_login_data).encode('utf-8'))
    param_login["data_body"] = login_data_body
    res_login = requests.post(requrl, params=param_login)

    data_login = json.loads(res_login.text)
    print("url", requrl)
    print("param befor b64encode for login", json.dumps(param_login_data).encode('utf-8'))
    print("param for login", param_login)
    print("data_login",data_login)
    '''

    # 货物跟踪信息
    param = dict()
    param["service"] = 'track'

    param_data = dict()
    param_data["customerid"] = -1
    param_data["isdisplaydetail"] = "true"

    # data_body =base64.b64encode(json.dumps(param_data).encode('utf-8'))
    #  base64.b64encode()

    # 转单号查询
    param_2 = dict()
    param_2["service"] = 'turns'

    param_data_2 = dict()
    param_data_2["customerid"] = -1

    print("I'm here")

    for row in queryset:

        param_data["waybillnumber"] = row.logistic_no
        data_body = base64.b64encode(json.dumps(param_data).encode('utf-8'))
        param["data_body"] = data_body

        print("start fetch logistic info ", param)
        res = requests.post(requrl, params=param)

        data = json.loads(res.text)

        print("data is ", data)

        waybillnumber = data["waybillnumber"]
        # recipientcountry = data["recipientcountry"]

        statusdetail = data["displaydetail"][0]["statusdetail"]
        if (len(statusdetail) == 0):
            continue

        # 最新状态
        if (len(statusdetail) > 0):
            status_d = statusdetail[len(statusdetail) - 1]
            update_date = datetime.strptime(status_d["time"].split(" ")[0], '%Y-%m-%d').date()
            logistic_start_date = datetime.strptime(statusdetail[0]["time"].split(" ")[0], '%Y-%m-%d').date()
            Package.objects.filter(logistic_no=waybillnumber).update(

                logistic_update_status=status_d["status"],

                logistic_update_date=update_date,

                logistic_update_locate=status_d["locate"],
                logistic_start_date=logistic_start_date,
            )
        '''
        #获取转单号
        if(row.tracking_no is None):

            param_data_2["waybillnumber"] = row.logistic_no
            data_body_2 = base64.b64encode(json.dumps(param_data).encode('utf-8'))

            print(json.dumps(param_data).encode('utf-8'))
            param_2["data_body"] = data_body_2
            res = requests.post(requrl, params=param_2)

            data_2 = json.loads(res.text)
            print("data_2 is ", data_2)

            #tracking_no = data_2["transfernumber"]
            #Package.objects.filter(logistic_no=waybillnumber).update(
             #   tracking_no=tracking_no,

            #)
        '''
    return


batch_updatelogistic_trail.short_description = "更新物流轨迹"


class PackageResource(resources.ModelResource):
    logistic_no = fields.Field(attribute='logistic_no', column_name='单号')
    refer_no = fields.Field(attribute='refer_no', column_name='参考号')
    tracking_no = fields.Field(attribute='tracking_no', column_name='转单号')
    logistic_update_status = fields.Field(attribute='logistic_update_status', column_name='订单状态1')
    logistic_update_date = fields.Field(attribute='logistic_update_date', column_name='更新时间')
    problem_type = fields.Field(attribute='problem_type', column_name='异常说明')

    package_status = fields.Field(attribute='package_status', column_name='包裹状态')



    class Meta:
        model = Package
        skip_unchanged = True
        report_skipped = True
        import_id_fields = ('logistic_no',)
        fields = ('logistic_no', 'refer_no','tracking_no','logistic_update_status','logistic_update_date','problem_type',
                  'package_status',)


class PackageAdmin(object):
    import_export_args = {"import_resource_class": PackageResource,
                          "export_resource_class": PackageResource}



    actions = [
               'batch_response',
               'batch_deliver_response', 'batch_customer_response', 'batch_yallavip_response',

                'batch_type',
               'batch_contact', 'batch_refuse', 'batch_info_error','batch_lost',

               'batch_deal',
               'batch_delivered','batch_wait','batch_redeliver', 'batch_redelivering',
               'batch_refused', 'batch_returning', 'batch_returned',
               "batch_updatelogistic_trail",]


    list_display = ( 'logistic_no','package_status','yallavip_package_status',
                    'logistic_update_date', 'logistic_update_status', 'logistic_update_locate',
                    'problem_type','tracking_no')
    list_editable = [ ]
    search_fields = ['logistic_no', ]
    list_filter = ("package_status","logistic_update_status",)
    ordering = []


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
            #print("data is ", data)
            waybillnumber = data["waybillnumber"]
            #recipientcountry = data["recipientcountry"]

            statusdetail = data["displaydetail"][0]["statusdetail"]
            if(len(statusdetail) == 0):
                continue
            #最新状态
            if (len(statusdetail) > 0):
                status_d = statusdetail[len(statusdetail)-1]
                update_date = datetime.strptime(status_d["time"].split(" ")[0], '%Y-%m-%d').date()

                Package.objects.filter(logistic_no=waybillnumber).update(

                    logistic_update_status=status_d["status"],

                    logistic_update_date=update_date,

                    logistic_update_locate=status_d["locate"]
                )
                #else:
                 #   print("order 无可更新")

        return

    batch_updatelogistic_trail.short_description = "更新物流轨迹"






    def get_list_queryset(self):
        """批量查询订单号"""
        queryset = super().get_list_queryset()

        query = self.request.GET.get(SEARCH_VAR, '')


        if (len(query) > 0):
            queryset |= self.model.objects.filter(logistic_no__in=query.split(","))
        return queryset

'''
class LogisticSupplierResource(resources.ModelResource):
    logistic_no = fields.Field(attribute='logistic_no', column_name='单号')
    tracking_no = fields.Field(attribute='tracking_no', column_name='转单号')
    logistic_update_status = fields.Field(attribute='logistic_update_status', column_name='订单状态')
    logistic_update_date = fields.Field(attribute='logistic_update_date', column_name='更新时间')
    problem_type = fields.Field(attribute='problem_type', column_name='异常说明')

    charge_weight = fields.Field(attribute='charge_weight', column_name='计费重量')
    package_status = fields.Field(attribute='package_status', column_name='包裹状态')



    class Meta:
        model = Package
        skip_unchanged = True
        report_skipped = True
        import_id_fields = ('logistic_no',)
        fields = ('logistic_no', 'tracking_no','logistic_update_status','logistic_update_date','problem_type',
                  'charge_weight','package_status',)




class LogisticSupplierAdmin(object):
    import_export_args = {"import_resource_class": LogisticSupplierResource,
                          "export_resource_class": LogisticSupplierResource}

    actions = ['yallavip_package_start',]


    def weight(self, obj):
        orders = Order.objects.filter(logistic_no=obj.logistic_no)
        order_nos = ''
        for order in orders:
            if (order == None):
                continue
            order_nos = str(order_nos) +str(order.weight)+  str(',')
        return order_nos

    weight.short_description = "称重重量"


    list_display = ( 'logistic_no','tracking_no','send_time','logistic_start_date','weight','charge_weight','package_status','yallavip_package_status',
                    'logistic_update_date', 'logistic_update_status', 'logistic_update_locate',
                    'problem_type')
    list_editable = [ ]
    search_fields = ['logistic_no', ]
    list_filter = ("package_status","yallavip_package_status","logistic_update_status",'send_time','logistic_start_date',)
    ordering = []

    
    def yallavip_package_start(self, request, queryset):
        # 定义actions函数
        rows_updated = queryset.update(yallavip_package_status="START")

    yallavip_package_start.short_description = "中仪包裹状态-发运"



    def get_list_queryset(self):
        """批量查询订单号"""
        queryset = super().get_list_queryset()

        query = self.request.GET.get(SEARCH_VAR, '')


        if (len(query) > 0):
            queryset |= self.model.objects.filter(logistic_no__in=query.split(","))
        return queryset


class OverseaPackageAdmin(object):
    def logistic_type(self, obj):
        order = Order.objects.filter(logistic_no=obj.logistic_no).first()

        return order.logistic_type

    logistic_type.short_description = "物流公司"

    actions = ['batch_updatelogistic_trail','batch_start', 'batch_delivered', 'batch_problem','batch_lost', 'batch_temporary', 'batch_returned',
               'batch_returning', 'batch_destroyed',
               ]

    list_display = (
    'logistic_no', 'logistic_type', 'refer_no', 'send_time', 'package_status', 'yallavip_package_status',
    'resell_status',
    'logistic_update_date', 'logistic_update_status', 'logistic_update_locate',
    'sec_logistic_no',
    )
    list_editable = ['sec_logistic_no']
    search_fields = ['logistic_no']
    list_filter = ('send_time','logistic_update_date', 'logistic_update_status', 'deal', 'package_status',
                   'yallavip_package_status',)
    ordering = ['-send_time']

    def batch_start(self, request, queryset):
        queryset.update(yallavip_package_status="START")
        return

    batch_start.short_description = "交运中"

    def batch_delivered(self, request, queryset):
        queryset.update(yallavip_package_status="DELIVERED")
        return

    batch_delivered.short_description = "妥投"

    def batch_problem(self, request, queryset):
        queryset.update(yallavip_package_status="PROBLEM")
        return

    batch_problem.short_description = "问题件"

    def batch_temporary(self, request, queryset):
        queryset.update(yallavip_package_status="TEMPORARY")
        return

    batch_temporary.short_description = "暂存站点"

    def batch_lost(self, request, queryset):
        queryset.update(yallavip_package_status="LOST")
        return

    batch_lost.short_description = "丢件"

    def batch_returned(self, request, queryset):
        queryset.update(yallavip_package_status="RETURNED")
        return

    batch_returned.short_description = "海外仓"

    def batch_returning(self, request, queryset):
        queryset.update(yallavip_package_status="TRANSIT")
        return

    batch_returning.short_description = "退仓中"

    def batch_destroyed(self, request, queryset):
        queryset.update(resell_status="DESTROYED", yallavip_package_status="DESTROYED")
        return

    batch_destroyed.short_description = "批量销毁"

    def batch_updatelogistic_trail(self, request, queryset):
        # 定义actions函数
        requrl = "http://api.jcex.com/JcexJson/api/notify/sendmsg"

       
        #货物跟踪信息
        param = dict()
        param["service"] = 'track'

        param_data = dict()
        param_data["customerid"] = "3c917d0c-6290-11e8-a277-6c92bf623ff2"
        param_data["isdisplaydetail"] = "true"

        # data_body =base64.b64encode(json.dumps(param_data).encode('utf-8'))
        #  base64.b64encode()


        #转单号查询
        param_2 = dict()
        param_2["service"] = 'turns'

        param_data_2 = dict()
        param_data_2["customerid"] = "3c917d0c-6290-11e8-a277-6c92bf623ff2"



        for row in queryset:

            param_data["waybillnumber"] = row.logistic_no
            data_body = base64.b64encode(json.dumps(param_data).encode('utf-8'))
            param["data_body"] = data_body

            print("start update track requrl is %s param is %s "%(requrl,param))

            res = requests.post(requrl, params=param)


            if res.status_code != 200:
                print("error !!!!!! response is ", res)
                continue

            data = json.loads(res.text)
            print("data",data)

            waybillnumber = data.get('waybillnumber','none')

            if(waybillnumber == 'none'):
                continue

            # recipientcountry = data["recipientcountry"]

            statusdetail = data["displaydetail"][0]["statusdetail"]
            if (len(statusdetail) == 0):
                continue

            real_weight = data["displaydetail"][0]["totalweight"]
            charge_weight = data["displaydetail"][0]["chargeweight"]
            size_weight = data["displaydetail"][0]["checkinvolumeweight"]



            # 最新状态
            if (len(statusdetail) > 0):
                status_d = statusdetail[len(statusdetail) - 1]
                update_date = datetime.strptime(status_d["time"].split(" ")[0], '%Y-%m-%d').date()
                logistic_start_date = datetime.strptime(statusdetail[0]["time"].split(" ")[0], '%Y-%m-%d').date()
                Package.objects.filter(logistic_no=waybillnumber).update(

                    logistic_update_status=status_d["status"],

                    logistic_update_date=update_date,

                    logistic_update_locate=status_d["locate"],
                    logistic_start_date=logistic_start_date,
                    real_weight=data["displaydetail"][0]["totalweight"],
                    charge_weight = data["displaydetail"][0]["chargeweight"],
                    size_weight = data["displaydetail"][0]["checkinvolumeweight"],
                )

            totalweight=  data["displaydetail"][0]["totalweight"]
            chargeweight = data["displaydetail"][0]["chargeweight"]
            checkinvolumeweight = data["displaydetail"][0]["checkinvolumeweight"]

            #获取转单号
            if(row.tracking_no is None):

                param_data_2["waybillnumber"] = row.logistic_no
                data_body_2 = base64.b64encode(json.dumps(param_data).encode('utf-8'))

                print(json.dumps(param_data).encode('utf-8'))
                param_2["data_body"] = data_body_2
                res = requests.post(requrl, params=param_2)

                data_2 = json.loads(res.text)
                print("data_2 is ", data_2)

                #tracking_no = data_2["transfernumber"]
                #Package.objects.filter(logistic_no=waybillnumber).update(
                 #   tracking_no=tracking_no,

                #)

        return

    batch_updatelogistic_trail.short_description = "更新物流轨迹"

    def get_list_queryset(self):
        """批量查询订单号"""
        queryset = super().get_list_queryset()

        query = self.request.GET.get(SEARCH_VAR, '')

        if (len(query) > 0):
            queryset |= self.model.objects.filter(logistic_no__in=query.split(","))
        return queryset
'''

class LogisticCustomerServiceResource(resources.ModelResource):


    class Meta:
        model = LogisticCustomerService
        skip_unchanged = True
        report_skipped = True
        import_id_fields = ('logistic_no',)
        fields = ('logistic_no','comments','deal', 'feedback','response')

class LogisticCustomerServiceAdmin(object):
    import_export_args = {"import_resource_class": LogisticCustomerServiceResource,
                          "export_resource_class": LogisticCustomerServiceResource}

    def deal_trail(self,queryset,deal):
        for row in queryset:
            DealTrail.objects.create(
                package = row,
                waybillnumber = row.logistic_no,
                deal_type = "客服",
                deal_staff = str(self.request.user),
                deal_time = dt.now(),
                deal_action = deal,
                deal_comments = row.feedback
            )

    def order_no(self, obj):
        orders = Order.objects.filter(logistic_no=obj.logistic_no)
        order_nos = ''
        for order in orders:
            if (order == None):
                continue
            order_nos = str(order_nos) +str(order.order_no)+  str(',')
        return order_nos

    order_no.short_description = "订单号"

    def logistic_type(self, obj):
        order = Order.objects.filter(logistic_no=obj.logistic_no).first()

        return order.logistic_type

    logistic_type.short_description = "物流公司"

    def show_conversation(self, obj):
        # print('orderconversation')
        # print('orderconversation')
        orders = Order.objects.filter(logistic_no=obj.logistic_no)

        links = ''
        for order in orders:

            if (order == None):
                continue

            orderconversation = OrderConversation.objects.filter(order=order)
            for item in orderconversation:
                conversation = item.conversation

                if (conversation != None):
                    link = mark_safe(
                        u'<a href="http://business.facebook.com%s" target="view_window">%s</a>' % (
                            conversation.link, u'  ' + order.order_no))
                    links = links + link
        return (links)
    show_conversation.allow_tags = True
    show_conversation.short_description = "会话"

    def order_comment(self, obj):
        orders = Order.objects.filter(logistic_no=obj.logistic_no)
        comments = ''
        for order in orders:
            if (order == None):
                continue
            comments = str(comments) + str(order.order_comment)+ str(',')
        return comments

    order_comment.short_description = "订单备注"




    def receiver_phone(self, obj):
        order = Order.objects.filter(logistic_no=obj.logistic_no).last

        return order.receiver_phone

    receiver_phone.short_description = "收货人电话"




    actions = [
       # 'batch_updatelogistic_trail',
       # 'batch_response',
       # 'batch_deliver_response', 'batch_customer_response', 'batch_yallavip_response',

        #'batch_type',
        #'batch_contact', 'batch_refuse', 'batch_info_error', 'batch_lost',

        #'batch_deal',
         'batch_wait','batch_delivered', 'batch_redeliver','batch_refused','batch_lostconnect',

        #'batch_redelivering', 'batch_returning', 'batch_returned',

       ]

    list_display = ('logistic_no','send_time','logistic_start_date',
                    #'yallavip_package_status','problem_type', 'response',

                    'logistic_update_date', 'logistic_update_status', 'logistic_update_locate',
                    'problem_date','problem_trail',
                     'feedback', 'deal', 'feedback_time',
                    "total_date", "lost_date","waite_date",

                     'order_no','order_comment', 'receiver_phone',

                    'show_conversation')
    list_editable = ['feedback',  ]

    search_fields = [ 'logistic_no' ]
    list_filter = ('logistic_start_date','logistic_update_date', 'logistic_update_status', 'deal','package_status','yallavip_package_status',)
    ordering = ['send_time']


    def batch_updatelogistic_trail(self, request, queryset):
        # 定义actions函数
        requrl = "http://api.jcex.com/JcexJson/api/notify/sendmsg"


        param_data = dict()
        param_data["customerid"] = -1
        # param_data["waybillnumber"] = "989384782"
        param_data["isdisplaydetail"] = "true"


        # data_body =base64.b64encode(json.dumps(param_data).encode('utf-8'))
        #  base64.b64encode()

        param = dict()
        param["service"] = 'track'
        # param["data_body"] = data_body

        res = requests.post(requrl, params=param)

        for row in queryset:

            param_data["waybillnumber"] = row.logistic_no
            data_body = base64.b64encode(json.dumps(param_data).encode('utf-8'))
            param["data_body"] = data_body
            res = requests.post(requrl, params=param)

            data = json.loads(res.text)

            waybillnumber = data["waybillnumber"]
            # recipientcountry = data["recipientcountry"]

            statusdetail = data["displaydetail"][0]["statusdetail"]
            if (len(statusdetail) == 0):
                continue

            # 最新状态
            if (len(statusdetail) > 0):
                status_d = statusdetail[len(statusdetail) - 1]
                update_date = datetime.strptime(status_d["time"].split(" ")[0], '%Y-%m-%d').date()
                logistic_start_date = datetime.strptime(statusdetail[0]["time"].split(" ")[0], '%Y-%m-%d').date()
                # print("logistic_start_date", logistic_start_date)

                Package.objects.filter(logistic_no=waybillnumber).update(

                    logistic_update_status=status_d["status"],

                    logistic_update_date=update_date,

                    logistic_update_locate=status_d["locate"],
                    logistic_start_date=logistic_start_date,
                )
                # else:
                #   print("order 无可更新")

        return

    batch_updatelogistic_trail.short_description = "更新物流轨迹"



    # 问题件处理
    # 责任
    def batch_response(self, request, queryset):
        return

    batch_response.short_description = "******责任******"

    def batch_deliver_response(self, request, queryset):
        # 定义actions函数
        rows_updated = queryset.update(response="DELIVER", feedback_time=datetime.now())
        if rows_updated == 1:
            message_bit = '1 story was'
        else:
            message_bit = "%s stories were" % rows_updated
        self.message_user(request, "%s successfully marked as error." % message_bit)

    batch_deliver_response.short_description = "批量派送员责任"

    def batch_customer_response(self, request, queryset):
        # 定义actions函数
        rows_updated = queryset.update(response="CUSTOMER", feedback_time=datetime.now())
        if rows_updated == 1:
            message_bit = '1 story was'
        else:
            message_bit = "%s stories were" % rows_updated
        self.message_user(request, "%s successfully marked as error." % message_bit)

    batch_customer_response.short_description = "批量客户责任"

    def batch_yallavip_response(self, request, queryset):
        # 定义actions函数
        rows_updated = queryset.update(response="YALLAVIP", feedback_time=datetime.now())
        if rows_updated == 1:
            message_bit = '1 story was'
        else:
            message_bit = "%s stories were" % rows_updated
        self.message_user(request, "%s successfully marked as error." % message_bit)

    batch_yallavip_response.short_description = "批量yallavip责任"

    def batch_type(self, request, queryset):
        return

    batch_type.short_description = "******问题类型******"

    def batch_contact(self, request, queryset):
        # 定义actions函数
        rows_updated = queryset.update(problem_type="NORESPONSE", feedback_time=datetime.now())
        if rows_updated == 1:
            message_bit = '1 story was'
        else:
            message_bit = "%s stories were" % rows_updated
        self.message_user(request, "%s successfully marked as error." % message_bit)

    batch_contact.short_description = "联系不到客户"

    def batch_refuse(self, request, queryset):
        # 定义actions函数
        rows_updated = queryset.update(problem_type="REFUSE", feedback_time=datetime.now())
        if rows_updated == 1:
            message_bit = '1 story was'
        else:
            message_bit = "%s stories were" % rows_updated
        self.message_user(request, "%s successfully marked as error." % message_bit)

    batch_refuse.short_description = "拒签"

    def batch_info_error(self, request, queryset):
        # 定义actions函数
        rows_updated = queryset.update(problem_type="INFOERROR", feedback_time=datetime.now())
        if rows_updated == 1:
            message_bit = '1 story was'
        else:
            message_bit = "%s stories were" % rows_updated
        self.message_user(request, "%s successfully marked as error." % message_bit)

    batch_info_error.short_description = "信息错误"

    def batch_lost(self, request, queryset):
        # 定义actions函数
        return queryset.update(deal="LOST", feedback_time=datetime.now())

    batch_lost.short_description = "丢件"

    def batch_deal(self, request, queryset):
        return

    batch_deal.short_description = "******处理******"

    def batch_delivered(self, request, queryset):
        # 定义actions函数
        deal = "DELIVERED"
        self.deal_trail(queryset, deal)

        return queryset.update(deal=deal, yallavip_package_status="DELIVERED",wait_status = True,feedback_time=dt.now())

    batch_delivered.short_description = "已签收"

    def batch_wait(self, request, queryset):
        # 定义actions函数
        deal = "WAITING"
        self.deal_trail(queryset, deal)

        return queryset.update(deal=deal, feedback_time=dt.now())

    batch_wait.short_description = "沟通中"

    def batch_redeliver(self, request, queryset):
        # 定义actions函数
        deal = "RE_DELIVER"
        self.deal_trail(queryset, deal)

        return queryset.update(deal=deal,wait_status=False, feedback_time=dt.now())

    batch_redeliver.short_description = "重新派送"



    def batch_refused(self, request, queryset):
        # 定义actions函数
        deal = "REFUSED"
        self.deal_trail(queryset, deal)

        return queryset.update(deal=deal, feedback_time=dt.now())


    batch_refused.short_description = "拒签"

    def batch_lostconnect(self, request, queryset):
        # 定义actions函数
        deal = "LOSTCONNECT"
        self.deal_trail(queryset, deal)

        return queryset.update(deal=deal, feedback_time=dt.now())
    batch_lostconnect.short_description = "无法联系"

    def get_list_queryset(self):
        """批量查询订单号"""
        queryset = super().get_list_queryset()

        query = self.request.GET.get(SEARCH_VAR, '')


        if (len(query) > 0):
            queryset |= self.model.objects.filter(logistic_no__in=query.split(","))
        return queryset

    def queryset(self):
        qs = super().queryset()

        deal_list= ["NONE",
                     "WAITING",
                     ]

        return qs.filter(file_status="OPEN" , wait_status = False, warehouse_check= "NONE",
                         yallavip_package_status="PROBLEM", deal__in = deal_list)

@xadmin.sites.register(LogisticManagerConfirm)
class LogisticManagerConfirmAdmin(object):
    actions = [
        'batch_returning',
        'batch_redeal',
    ]
    def deal_trail(self,queryset,deal):
        for row in queryset:
            DealTrail.objects.create(
                package= row,
                waybillnumber = row.logistic_no,
                deal_type = "客服",
                deal_staff = str(self.request.user),
                deal_time = dt.now(),
                deal_action = deal,
                deal_comments = row.feedback
            )

    def batch_returning(self, request, queryset):
        # 定义actions函数
        deal = "RETURNING"
        self.deal_trail(queryset,deal)
        return queryset.update(deal=deal, feedback_time=dt.now(), warehouse_check ="TORETURN" )

    batch_returning.short_description = "退仓中"

    def batch_redeal(self, request, queryset):
        # 定义actions函数
        deal = "WAITING"
        self.deal_trail(queryset, deal)
        return queryset.update(deal=deal, feedback_time=dt.now())

    batch_redeal.short_description = "重新沟通"

    list_display = ('logistic_no', 'send_time', 'logistic_start_date', 'yallavip_package_status',

                    'logistic_update_date', 'logistic_update_status', 'logistic_update_locate',

                    'problem_type', 'response', 'feedback', 'deal', 'feedback_time',
                    'order_no', 'order_comment', 'receiver_phone',
                    'show_conversation')
    list_editable = ['feedback', ]

    search_fields = ['logistic_no']
    list_filter = ('logistic_start_date', 'logistic_update_date', 'logistic_update_status', 'deal', 'package_status',
                   'yallavip_package_status',)
    ordering = ['send_time']

    def order_no(self, obj):
        orders = Order.objects.filter(logistic_no=obj.logistic_no)
        order_nos = ''
        for order in orders:
            if (order == None):
                continue
            order_nos = str(order_nos) + str(order.order_no) + str(',')
        return order_nos

    order_no.short_description = "订单号"

    def logistic_type(self, obj):
        order = Order.objects.filter(logistic_no=obj.logistic_no).first()

        return order.logistic_type

    logistic_type.short_description = "物流公司"

    def show_conversation(self, obj):
        # print('orderconversation')
        # print('orderconversation')
        orders = Order.objects.filter(logistic_no=obj.logistic_no)

        links = ''
        for order in orders:

            if (order == None):
                continue

            orderconversation = OrderConversation.objects.filter(order=order)
            for item in orderconversation:
                conversation = item.conversation

                if (conversation != None):
                    link = mark_safe(
                        u'<a href="http://business.facebook.com%s" target="view_window">%s</a>' % (
                            conversation.link, u'  ' + order.order_no))
                    links = links + link
        return (links)

    show_conversation.allow_tags = True
    show_conversation.short_description = "会话"

    def order_comment(self, obj):
        orders = Order.objects.filter(logistic_no=obj.logistic_no)
        comments = ''
        for order in orders:
            if (order == None):
                continue
            comments = str(comments) + str(order.order_comment) + str(',')
        return comments

    order_comment.short_description = "订单备注"

    def receiver_phone(self, obj):
        order = Order.objects.filter(logistic_no=obj.logistic_no).last

        return order.receiver_phone

    receiver_phone.short_description = "收货人电话"


    def get_list_queryset(self):
        """批量查询订单号"""
        queryset = super().get_list_queryset()

        query = self.request.GET.get(SEARCH_VAR, '')

        if (len(query) > 0):
            queryset |= self.model.objects.filter(logistic_no__in=query.split(","))
        return queryset

    def queryset(self):
        qs = super().queryset()
        deal_list = ["LOST",
                     "REFUSED",
                     "LOSTCONNECT",

                     ]
        return qs.filter(logistic_supplier='佳成', file_status="OPEN", wait_status=False, warehouse_check="NONE",
                         deal__in=deal_list)

@xadmin.sites.register(LogisticResendTrail)
class LogisticResendTrailAdmin(object):
    actions = [
        'batch_redelivering','batch_fail','batch_success','batch_nodo',
    ]
    def deal_trail(self,queryset,deal):
        for row in queryset:
            DealTrail.objects.create(
                package = row,
                waybillnumber = row.logistic_no,
                deal_type = "物流重派跟踪",
                deal_staff = str(self.request.user),
                deal_time = dt.now(),
                deal_action = deal,
                deal_comments = row.resend_commnet
            )

    def batch_redelivering(self, request, queryset):
        # 定义actions函数
        deal = "RE_DELIVERING"
        self.deal_trail(queryset, deal)
        return queryset.update(deal=deal, resend_start_time=dt.now())


    batch_redelivering.short_description = "已通知物流重派"

    def batch_fail(self, request, queryset):
        # 定义actions函数
        deal = "RE_FAIL"
        self.deal_trail(queryset, deal)
        return queryset.update(deal=deal,  wait_status = True)

    batch_fail.short_description = "重派失败"

    def batch_success(self, request, queryset):
        # 定义actions函数
        deal = "RE_SUCCESS"
        self.deal_trail(queryset, deal)
        return queryset.update(deal=deal, wait_status = True)

    batch_success.short_description = "重派成功"

    def batch_nodo(self, request, queryset):
        # 定义actions函数
        deal = "RE_NODO"
        self.deal_trail(queryset, deal)
        return queryset.update(deal=deal, wait_status = True)

    batch_nodo.short_description = "没有重派"

    list_display = ('logistic_no', 'send_time',

                    'logistic_update_date', 'logistic_update_status', 'logistic_update_locate',
                    "problem_date",
                    #'feedback', 'deal', 'feedback_time',
                    "resend_start_time","resend_commnet",'resend_date',"resend_stat",
                    'order_no', 'order_comment',
                    # 'receiver_phone',
                    'show_conversation')
    list_editable = ['resend_commnet']

    search_fields = ['logistic_no']
    list_filter = ('logistic_start_date', 'logistic_update_date', 'logistic_update_status', 'deal', 'package_status',
                   'yallavip_package_status',)
    ordering = ['send_time']

    def order_no(self, obj):
        orders = Order.objects.filter(logistic_no=obj.logistic_no)
        order_nos = ''
        for order in orders:
            if (order == None):
                continue
            order_nos = str(order_nos) + str(order.order_no) + str(',')
        return order_nos

    order_no.short_description = "订单号"

    def logistic_type(self, obj):
        order = Order.objects.filter(logistic_no=obj.logistic_no).first()

        return order.logistic_type

    logistic_type.short_description = "物流公司"

    def show_conversation(self, obj):
        # print('orderconversation')
        # print('orderconversation')
        orders = Order.objects.filter(logistic_no=obj.logistic_no)

        links = ''
        for order in orders:

            if (order == None):
                continue

            orderconversation = OrderConversation.objects.filter(order=order)
            for item in orderconversation:
                conversation = item.conversation

                if (conversation != None):
                    link = mark_safe(
                        u'<a href="http://business.facebook.com%s" target="view_window">%s</a>' % (
                            conversation.link, u'  ' + order.order_no))
                    links = links + link
        return (links)

    show_conversation.allow_tags = True
    show_conversation.short_description = "会话"

    def order_comment(self, obj):
        orders = Order.objects.filter(logistic_no=obj.logistic_no)
        comments = ''
        for order in orders:
            if (order == None):
                continue
            comments = str(comments) + str(order.order_comment) + str(',')
        return comments

    order_comment.short_description = "订单备注"

    def receiver_phone(self, obj):
        order = Order.objects.filter(logistic_no=obj.logistic_no).last

        return order.receiver_phone

    receiver_phone.short_description = "收货人电话"

    def get_list_queryset(self):
        """批量查询订单号"""
        queryset = super().get_list_queryset()

        query = self.request.GET.get(SEARCH_VAR, '')

        if (len(query) > 0):
            queryset |= self.model.objects.filter(logistic_no__in=query.split(","))
        return queryset

    def queryset(self):
        qs = super().queryset()
        deal_list = ["RE_DELIVER",
                     "RE_DELIVERING",
                     ]
        return qs.filter( file_status="OPEN", wait_status=False, #warehouse_check="NONE",
                         deal__in=deal_list)



@xadmin.sites.register(Resell)
class ResellAdmin(object):


    actions = []

    list_display = ('logistic_no',  'yallavip_package_status',
                    "ref_order",
                    "order_amount",
                    "photos",
                    'resell_status',
                    'image_created',

                    )
    list_editable = [ 'image_created',]
    search_fields = ['logistic_no',"ref_order__order_no",]
    list_filter = ('resell_status',"ref_order__order_amount", )
    ordering = ["-ref_order",]

    def queryset(self):
        qs = super().queryset()
        deal_list = ["RETURNED",
                     "REDELIVERING",
                     ]
        return qs.filter( yallavip_package_status__in=deal_list)

    def get_list_queryset(self):
        """批量查询订单号"""
        queryset = super().get_list_queryset()

        query = self.request.GET.get(SEARCH_VAR, '')


        if (len(query) > 0):
            queryset |= self.model.objects.filter(logistic_no__in=query.split(","))
        return queryset


xadmin.site.register(Package,PackageAdmin)
#xadmin.site.register(LogisticSupplier,LogisticSupplierAdmin)
#xadmin.site.register(OverseaPackage,OverseaPackageAdmin)
xadmin.site.register(LogisticCustomerService,LogisticCustomerServiceAdmin)
#xadmin.site.register(Resell,ResellAdmin)


class LogisticBalanceResource(resources.ModelResource):
    '''
    package = fields.Field(
        column_name='客户单号',
        attribute='package',
        widget=ForeignKeyWidget(Package, 'logistic_no'))
    '''

    waybillnumber = fields.Field(attribute='waybillnumber', column_name='客户单号')
    balance_type = fields.Field(attribute='balance_type', column_name='对账类型')

    batch = fields.Field(attribute='batch', column_name='批次')

    charge_weight = fields.Field(attribute='charge_weight', column_name='收货计费重')
    cod = fields.Field(attribute='cod', column_name='代收货款')
    money = fields.Field(attribute='money', column_name='币种')
    exchange = fields.Field(attribute='exchange', column_name='汇率')
    cod_base = fields.Field(attribute='cod_base', column_name='本位币金额')

    freight = fields.Field(attribute='freight', column_name='运费')

    cod_fee = fields.Field(attribute='cod_fee', column_name='代收款手续费')
    vat = fields.Field(attribute='vat', column_name='VAT')
    re_deliver = fields.Field(attribute='re_deliver', column_name='重派费')
    print_fee = fields.Field(attribute='print_fee', column_name='打单费')

    other_fee = fields.Field(attribute='other_fee', column_name='其他杂费')

    comment = fields.Field(attribute='comment', column_name='备注')
    receivable = fields.Field(attribute='receivable', column_name='应收金额')

    refunded = fields.Field(attribute='refunded', column_name='应退金额')



    class Meta:
        model = LogisticBalance
        skip_unchanged = True
        report_skipped = True
        import_id_fields = ('waybillnumber',"balance_type","batch")
        fields = ( 'waybillnumber','balance_type','batch','charge_weight','cod',
                  'money','cod_base','freight','cod_fee','vat','re_deliver',
                  'print_fee', 'other_fee', 'comment', 'receivable', 'refunded',)

@xadmin.sites.register(LogisticBalance)
class LogisticBalanceAdmin(object):
    import_export_args = {"import_resource_class": LogisticBalanceResource,
                          "export_resource_class": LogisticBalanceResource}



    #actions = [ ]


    list_display = (  'waybillnumber','balance_type','batch','charge_weight','cod',
                  'money','cod_base','freight','cod_fee','vat','re_deliver',
                  'print_fee', 'other_fee', 'comment', 'receivable', 'refunded',)
    list_editable = [ ]
    search_fields = ['waybillnumber', ]
    list_filter = ("balance_type","batch",)
    ordering = []

@xadmin.sites.register(Overtime)
class OvertimeAdmin(object):
    list_display = ('logistic_no',
                    "send_time",
                    'logistic_update_date', 'logistic_update_status',
                    "total_date","lost_date",
                    "warehouse_check","warehouse_check_comments",

                    "warehouse_checktime","warehouse_check_manager",

                    )
    list_editable = [ "warehouse_check_comments","child_packages",]
    search_fields = ['logistic_no', 'logistic_update_status',]
    list_filter = ("warehouse_check",'logistic_update_status',)
    ordering = ["send_time"]
    actions = ["batch_discard", "batch_multipackage","batch_toclear", "batch_refund","batch_return",]

    def batch_discard(self, request, queryset):
        queryset.update(warehouse_check="DISCARD",
                        file_status="CLOSED",
                        wait_status=False,
                        warehouse_checktime = dt.now(),
                        warehouse_check_manager = str(self.request.user)
                        )
        return

    batch_discard.short_description = "批量废弃包裹"

    def batch_multipackage(self, request, queryset):
        for row in queryset:
            for logistic_no in row.child_packages.split(','):
                Package.objects.update_or_create(
                    super_package = row,
                    logistic_no = logistic_no,
                    defaults={
                        'send_time' : row.send_time,
                    }
                )
        queryset.update(warehouse_check="MULTIPACKAGE",

                        warehouse_checktime = dt.now(),
                        warehouse_check_manager = str(self.request.user)
                        )
        return

    batch_multipackage.short_description = "批量多包裹"

    def batch_toclear(self, request, queryset):
        queryset.update(warehouse_check="TOCLEAR",
                        wait_status= True,
                        warehouse_checktime = dt.now(),
                        warehouse_check_manager = str(self.request.user)
                        )
        return

    batch_toclear.short_description = "批量状态不明待确认"


    def batch_refund(self, request, queryset):
        queryset.update(warehouse_check="TOREFUND",
                        wait_status= True,
                        warehouse_checktime = dt.now(),
                        warehouse_check_manager = str(self.request.user)
                        )
        return

    batch_refund.short_description = "批量签收待确认"



    def batch_return(self, request, queryset):
        queryset.update(warehouse_check="TORETURN", wait_status= True,
                        warehouse_checktime=dt.now(),
                        warehouse_check_manager=str(self.request.user)
                        )
        return

    batch_return.short_description = "批量退仓待确认"

    '''
    def batch_filed(self, request, queryset):
        queryset.update(file_status="CLOSED", wait_status= False,
                        warehouse_checktime=dt.now(),
                        warehouse_check_manager=str(self.request.user)
                        )

        return

    batch_filed.short_description = "批量归档"
    '''

    #没有物流轨迹，没有发货时间，交运时间超过10天的，最后更新时间超过3天的，都会出现在此
    def queryset(self):
        qs = super().queryset()
        overtime_send = dt.now() - timedelta(days=10)
        overtime_update = dt.now() - timedelta(days=3)

        return qs.filter(Q(send_time__isnull=True)
                             |Q(logistic_update_date__isnull=True)
                             |Q(send_time__lt=overtime_send)
                             |Q(logistic_update_date__lt=overtime_update),
                        warehouse_check = "NONE",
                        file_status="OPEN" , wait_status = False)

    def get_list_queryset(self):
        """批量查询订单号"""
        queryset = super().get_list_queryset()

        query = self.request.GET.get(SEARCH_VAR, '')


        if (len(query) > 0):
            queryset |= self.model.objects.filter(logistic_no__in=query.split(","))
        return queryset

    def save_models(self):
        obj = self.new_obj
        obj.warehouse_check_manager = str(self.request.user)
        obj.warehouse_checktime = dt.now()

        obj.save()

####################催单
@xadmin.sites.register(Reminder)
class ReminderAdmin(object):
    list_display = ('logistic_no',
                    "send_time",
                    'logistic_update_date', 'logistic_update_status',
                    "total_date","lost_date",
                    "warehouse_check","warehouse_check_comments",
                    #"child_packages",
                    "warehouse_checktime","warehouse_check_manager",

                    )
    list_editable = [ "warehouse_check_comments",]
    search_fields = ['logistic_no', 'logistic_update_status',]
    list_filter = ("warehouse_check",'logistic_update_status',)
    ordering = ["send_time"]
    actions = ["batch_refund","batch_return","batch_lost",]

    def batch_refund(self, request, queryset):
        queryset.update(warehouse_check="TOREFUND",
                        wait_status= True,
                        warehouse_checktime = dt.now(),
                        warehouse_check_manager = str(self.request.user)
                        )
        return

    batch_refund.short_description = "批量签收待确认"



    def batch_return(self, request, queryset):
        queryset.update(warehouse_check="TORETURN", wait_status= True,
                        warehouse_checktime=dt.now(),
                        warehouse_check_manager=str(self.request.user)
                        )
        return

    batch_return.short_description = "批量退仓待确认"

    def batch_lost(self, request, queryset):
        queryset.update(warehouse_check="TOLOST", wait_status= True,
                        warehouse_checktime=dt.now(),
                        warehouse_check_manager=str(self.request.user)
                        )
        return

    batch_lost.short_description = "批量丢件待确认"

    # 状态不明，没有关闭的订单，都会出现在此
    def queryset(self):
        qs = super().queryset()
        return qs.filter(warehouse_check ="TOCLEAR",
                         file_status="OPEN", wait_status=True)

    def get_list_queryset(self):
        """批量查询订单号"""
        queryset = super().get_list_queryset()

        query = self.request.GET.get(SEARCH_VAR, '')

        if (len(query) > 0):
            queryset |= self.model.objects.filter(logistic_no__in=query.split(","))
        return queryset

####################多包裹
@xadmin.sites.register(MultiPackage)
class MultiPackageAdmin(object):
    list_display = ('logistic_no',
                    "send_time",
                    'logistic_update_date', 'logistic_update_status',
                    "total_date","lost_date",
                    "warehouse_check","warehouse_check_comments",
                    "child_packages",
                    "warehouse_checktime","warehouse_check_manager",

                    )
    list_editable = [ "warehouse_check_comments","child_packages",]
    search_fields = ['logistic_no', ]
    list_filter = ("child_packages",)
    ordering = ["send_time"]
    actions = ["batch_multipackage",]

    def batch_multipackage(self, request, queryset):
        for row in queryset:
            for logistic_no in row.child_packages.split(','):
                Package.objects.update_or_create(
                    super_package = row,
                    logistic_no = logistic_no,
                    defaults={
                        'send_time' : row.send_time,
                    }
                )
        queryset.update(warehouse_check="MULTIPACKAGE",
                        #file_status="CLOSED",
                        warehouse_checktime = dt.now(),
                        warehouse_check_manager = str(self.request.user)
                        )
        return

    batch_multipackage.short_description = "批量多包裹"

    # 多包裹，但是没有子单号的，都会出现在此
    def queryset(self):
        qs = super().queryset()
        return qs.filter(warehouse_check ="MULTIPACKAGE",child_packages="NONE")

    def get_list_queryset(self):
        """批量查询订单号"""
        queryset = super().get_list_queryset()

        query = self.request.GET.get(SEARCH_VAR, '')

        if (len(query) > 0):
            queryset |= self.model.objects.filter(logistic_no__in=query.split(","))
        return queryset



@xadmin.sites.register(ToBalance)
class ToBalanceAdmin(object):
    list_display = ('logistic_no',
                    "send_time",
                    'logistic_update_date', 'logistic_update_status',
                    "total_date","lost_date",
                    "resend_commnet",
                    "warehouse_check","warehouse_check_comments","warehouse_checktime","warehouse_check_manager",

                    )
    list_editable = [ ]
    search_fields = ['logistic_no', 'logistic_update_status',]
    list_filter = ("warehouse_check","deal","deal", )
    ordering = ["send_time"]
    actions = ["batch_balanced",]


    def batch_balanced(self, request, queryset):
        queryset.update(warehouse_check="BALANCED", wait_status= False, file_status= "CLOSED")
        return

    batch_balanced.short_description = "批量对账确认"



    def queryset(self):
        qs = super().queryset()
        return qs.filter(file_status="OPEN" , wait_status = True)

    def get_list_queryset(self):
        """批量查询订单号"""
        queryset = super().get_list_queryset()

        query = self.request.GET.get(SEARCH_VAR, '')


        if (len(query) > 0):
            queryset |= self.model.objects.filter(logistic_no__in=query.split(","))
        return queryset

@xadmin.sites.register(DealTrail)
class DealTrailAdmin(object):
    list_display = ('waybillnumber',
                    "deal_type", "deal_staff",
                    'deal_time', 'deal_action',
                    "deal_comments",

                    )
    list_editable = [ ]
    search_fields = ['waybillnumber', ]
    list_filter = ("deal_type","deal_staff",)
    ordering = ["waybillnumber"]
    actions = []



    def get_list_queryset(self):
        """批量查询订单号"""
        queryset = super().get_list_queryset()

        query = self.request.GET.get(SEARCH_VAR, '')

        if (len(query) > 0):
            queryset |= self.model.objects.filter(logistic_no__in=query.split(","))
        return queryset



@xadmin.sites.register(OverseaPackage)
class OverseaPackageAdmin(object):
    list_display = ('logistic_no',
                    )
    list_editable = [ ]
    search_fields = ['logistic_no', ]
    list_filter = ()
    ordering = []
    actions = []



    def get_list_queryset(self):
        """批量查询订单号"""
        queryset = super().get_list_queryset()

        query = self.request.GET.get(SEARCH_VAR, '')

        if (len(query) > 0):
            queryset |= self.model.objects.filter(logistic_no__in=query.split(","))
        return queryset

    def queryset(self):
        qs = super().queryset()
        return qs.filter(file_status="OPEN" , wait_status = False, from_warehouse = "海外仓")