# -*- coding: utf-8 -*-
__author__ = 'bobby'

import numpy as np, re
import xadmin
from django.shortcuts import get_object_or_404, get_list_or_404, render
from import_export import resources, fields
from import_export.widgets import ForeignKeyWidget
from .models import Purchase,PurchaseDetail, Stock
from sysadmin.models import ActionLog

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


class PurchaseResource(resources.ModelResource):
    purchase_no = fields.Field(attribute='purchase_no', column_name='采购单号')
    logistic_fee = fields.Field(attribute='logistic_fee', column_name='运费')
    other_fee = fields.Field(attribute='other_fee', column_name='其它费用')
    discount = fields.Field(attribute='discount', column_name='采购单折扣金额')
    need_pay = fields.Field(attribute='need_pay', column_name='采购单应付总额')
    warehouse = fields.Field(attribute='warehouse', column_name='库位')
    supplier = fields.Field(attribute='supplier', column_name='供货商名称')
    contacter = fields.Field(attribute='contacter', column_name='联系人')
    logistic_no = fields.Field(attribute='logistic_no', column_name='运单号')
    ali_no = fields.Field(attribute='ali_no', column_name='1688订单号')
    purchase_time = fields.Field(attribute='purchase_time', column_name='创建时间')
    receive_time = fields.Field(attribute='receive_time', column_name='到货时间')
    receive_status = fields.Field(attribute='receive_status', column_name='到货状态')
    comment = fields.Field(attribute='comment', column_name='备注')


    class Meta:
        model = Purchase
        skip_unchanged = True
        report_skipped = True
        import_id_fields = ('purchase_no',)
        fields = ('purchase_no', 'logistic_fee', 'other_fee', 'discount', 'need_pay', 'warehouse',
                  'supplier', 'contacter', 'logistic_no', 'ali_no', 'purchase_time',
                  'receive_time', 'receive_status', 'comment')
        # exclude = ()


class PurchaseAdmin(object):

    import_export_args = {"import_resource_class": PurchaseResource, "export_resource_class": PurchaseResource}

    list_display = ['purchase_no','receive_status','logistic_status', 'response','deal','logistic_fee', 'other_fee', 'discount', 'need_pay', 'warehouse',
                  'supplier', 'contacter', 'logistic_no', 'ali_no', 'purchase_time',
                  'receive_time',  'comment']


    search_fields = ["purchase_no"]
    list_filter = ['receive_status','logistic_status' ]
    list_editable = ["logistic_status",'response','deal',]
    ordering = ['-purchase_no']
    actions = ['batch_received', 'batch_lost', 'batch_miss', ]

    def batch_received(self, request, queryset):
        # 定义actions函数
        rows_updated = queryset.update(logistic_status='RECEIVED')
        if rows_updated == 1:
            message_bit = '1 story was'
        else:
            message_bit = "%s stories were" % rows_updated
        self.message_user(request, "%s successfully marked as error." % message_bit)

    batch_received.short_description = "批量显示签收"

    def batch_lost(self, request, queryset):
        # 定义actions函数
        rows_updated = queryset.update(logistic_status='LOST')
        if rows_updated == 1:
            message_bit = '1 story was'
        else:
            message_bit = "%s stories were" % rows_updated
        self.message_user(request, "%s successfully marked as error." % message_bit)

    batch_lost.short_description = "批量物流丢件"

    def batch_miss(self, request, queryset):
        # 定义actions函数
        rows_updated = queryset.update(logistic_status='MISS')
        if rows_updated == 1:
            message_bit = '1 story was'
        else:
            message_bit = "%s stories were" % rows_updated
        self.message_user(request, "%s successfully marked as error." % message_bit)

    batch_miss.short_description = "批量供应商漏发"



class PurchaseDetailResource(resources.ModelResource):
    purchase = fields.Field(
        column_name='采购单号',
        attribute='purchase',
        widget=ForeignKeyWidget(Purchase, 'purchase_no'))

    product_name = fields.Field(attribute='product_name', column_name='商品名称')
    sku = fields.Field(attribute='sku', column_name='商品SKU')
    price = fields.Field(attribute='price', column_name='单价（CNY）')
    quantity = fields.Field(attribute='quantity', column_name='采购数量')
    receive_quantity = fields.Field(attribute='receive_quantity', column_name='到货数量')
    amount = fields.Field(attribute='amount', column_name='商品总金额')


    class Meta:
        model = PurchaseDetail
        skip_unchanged = True
        report_skipped = True
        import_id_fields = ('purchase','sku')
        fields = ('purchase', 'product_name', 'sku', 'price', 'quantity', 'receive_quantity','amount')
        # exclude = ()




class PurchaseDetailAdmin(object):

    import_export_args = {"import_resource_class": PurchaseDetailResource, "export_resource_class": PurchaseDetailResource}

    list_display = ['purchase', 'product_name', 'sku', 'price', 'quantity', 'receive_quantity','amount']

    search_fields = ["purchase__purchase_no", ]

    ordering = ['-purchase']

    actions = []


class StockResource(resources.ModelResource):


    sku = fields.Field(attribute='sku', column_name='sku(必填)')

    warehouse = fields.Field(attribute='warehouse', column_name='库位')
    stock_quantity = fields.Field(attribute='stock_quantity', column_name='库存量（数字）')
    transit_quantity = fields.Field(attribute='transit_quantity', column_name='采购在途')
    plateform_sku = fields.Field(attribute='plateform_sku', column_name='平台SKU')


    class Meta:
        model = Stock
        skip_unchanged = True
        report_skipped = True
        import_id_fields = ( 'sku','warehouse')
        fields = ('sku', 'warehouse','stock_quantity', 'transit_quantity', 'plateform_sku',)
        # exclude = ()




class StockAdmin(object):

    import_export_args = {"import_resource_class": StockResource, "export_resource_class": StockResource}

    list_display = ['sku', 'warehouse','stock_quantity', 'transit_quantity', 'plateform_sku']


    search_fields = ["sku", ]






xadmin.site.register(Purchase, PurchaseAdmin)
xadmin.site.register(PurchaseDetail, PurchaseDetailAdmin)

xadmin.site.register(Stock, StockAdmin)
