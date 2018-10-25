# -*- coding: utf-8 -*-
__author__ = 'bobby'

import requests
import json
import time
import base64

import numpy as np, re
import xadmin
from django.shortcuts import get_object_or_404, get_list_or_404, render
from import_export import resources, fields
from import_export.widgets import ForeignKeyWidget
from .models import Package, LogisticSupplier,LogisticCustomerService
from orders.models import Order,OrderConversation
from django.db import models

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


class PackageResource(resources.ModelResource):
    logistic_no = fields.Field(attribute='logistic_no', column_name='单号')
    logistic_update_status = fields.Field(attribute='logistic_update_status', column_name='订单状态1')
    logistic_update_date = fields.Field(attribute='logistic_update_date', column_name='更新时间')
    problem_type = fields.Field(attribute='problem_type', column_name='异常说明')

    package_status = fields.Field(attribute='package_status', column_name='包裹状态')



    class Meta:
        model = Package
        skip_unchanged = True
        report_skipped = True
        import_id_fields = ('logistic_no',)
        fields = ('logistic_no', 'logistic_update_status','logistic_update_date','problem_type',
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
                    'problem_type')
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


class LogisticSupplierResource(resources.ModelResource):
    logistic_no = fields.Field(attribute='logistic_no', column_name='单号')
    logistic_update_status = fields.Field(attribute='logistic_update_status', column_name='订单状态')
    logistic_update_date = fields.Field(attribute='logistic_update_date', column_name='更新时间')
    problem_type = fields.Field(attribute='problem_type', column_name='异常说明')

    package_status = fields.Field(attribute='package_status', column_name='包裹状态')



    class Meta:
        model = Package
        skip_unchanged = True
        report_skipped = True
        import_id_fields = ('logistic_no',)
        fields = ('logistic_no', 'logistic_update_status','logistic_update_date','problem_type',
                  'package_status',)


class LogisticSupplierAdmin(object):
    import_export_args = {"import_resource_class": LogisticSupplierResource,
                          "export_resource_class": LogisticSupplierResource}

    actions = [
               'batch_response',
               'batch_deliver_response', 'batch_customer_response', 'batch_yallavip_response',

                'batch_type',
               'batch_contact', 'batch_refuse', 'batch_info_error','batch_lost',

               'batch_deal',
               'batch_delivered','batch_wait','batch_redeliver', 'batch_redelivering',
               'batch_refused', 'batch_returning', 'batch_returned',
               "batch_updatelogistic_trail",]


    list_display = ( 'logistic_no','logistic_start_date','package_status','yallavip_package_status',
                    'logistic_update_date', 'logistic_update_status', 'logistic_update_locate',
                    'problem_type')
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
                logistic_start_date = datetime.strptime(statusdetail[0]["time"].split(" ")[0], '%Y-%m-%d').date()

                Package.objects.filter(logistic_no=waybillnumber).update(

                    logistic_update_status=status_d["status"],

                    logistic_update_date=update_date,

                    logistic_update_locate=status_d["locate"],
                    logistic_start_date = logistic_start_date,
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


class LogisticCustomerServiceAdmin(object):
    def order_no(self, obj):
        orders = Order.objects.filter(logistic_no=obj.logistic_no)
        order_nos = ''
        for order in orders:
            if (order == None):
                continue
            order_nos = str(order_nos) +str(order.order_no)+  str(',')
        return order_nos

    order_no.short_description = "订单号"

    def order_send_time(self, obj):
        order = Order.objects.filter(logistic_no=obj.logistic_no).first()

        return order.send_time

    order_send_time.short_description = "发货时间"

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


    show_conversation.allow_tags = True
    show_conversation.short_description = "会话"

    actions = [
        'batch_response',
        'batch_deliver_response', 'batch_customer_response', 'batch_yallavip_response',

        'batch_type',
        'batch_contact', 'batch_refuse', 'batch_info_error', 'batch_lost',

        'batch_deal',
        'batch_delivered', 'batch_wait', 'batch_redeliver', 'batch_redelivering',
        'batch_refused', 'batch_returning', 'batch_returned',
        "batch_updatelogistic_trail", ]

    list_display = ('logistic_no','logistic_start_date','package_status','yallavip_package_status',

                    'logistic_update_date', 'logistic_update_status', 'logistic_update_locate',

                    'problem_type', 'response', 'feedback', 'deal', 'feedback_time',
                     'order_no','order_comment', 'receiver_phone',
                    'show_conversation')
    list_editable = ['feedback', ]
    search_fields = [ 'logistic_no' ]
    list_filter = ('logistic_start_date','logistic_update_date', 'logistic_update_status', 'deal','package_status','yallavip_package_status',)
    ordering = ['-logistic_no']

    # 交付状态

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
        return queryset.update(deal="DELIVERED", feedback_time=datetime.now())

    batch_delivered.short_description = "已签收"

    def batch_wait(self, request, queryset):
        # 定义actions函数
        return queryset.update(deal="WAITING", feedback_time=datetime.now())

    batch_wait.short_description = "沟通中"

    def batch_redeliver(self, request, queryset):
        # 定义actions函数
        return queryset.update(deal="RE_DELIVER", feedback_time=datetime.now())

    batch_redeliver.short_description = "重新派送"

    def batch_redelivering(self, request, queryset):
        # 定义actions函数
        return queryset.update(deal="RE_DELIVERING", feedback_time=datetime.now())

    batch_redelivering.short_description = "重新派送中"

    def batch_refused(self, request, queryset):
        # 定义actions函数
        return queryset.update(deal="REFUSED", feedback_time=datetime.now())

    batch_refused.short_description = "拒签"

    def batch_returning(self, request, queryset):
        # 定义actions函数
        return queryset.update(deal="RETURNING", feedback_time=datetime.now())

    batch_returning.short_description = "退仓中"

    def batch_returned(self, request, queryset):
        # 定义actions函数
        return queryset.update(deal="RETURNED", feedback_time=datetime.now())

    batch_returned.short_description = "已退到仓库"

    def get_list_queryset(self):
        """批量查询订单号"""
        queryset = super().get_list_queryset()

        query = self.request.GET.get(SEARCH_VAR, '')


        if (len(query) > 0):
            queryset |= self.model.objects.filter(logistic_no__in=query.split(","))
        return queryset

xadmin.site.register(Package,PackageAdmin)
xadmin.site.register(LogisticSupplier,LogisticSupplierAdmin)
xadmin.site.register(LogisticCustomerService,LogisticCustomerServiceAdmin)