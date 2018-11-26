# -*- coding: utf-8 -*-
__author__ = 'bobby'

import numpy as np, re
import xadmin
from django.shortcuts import get_object_or_404, get_list_or_404, render
from import_export import resources, fields
from import_export.widgets import ForeignKeyWidget
from .models import Product

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

from orders.models import OrderDetail


class ProductResource(resources.ModelResource):

    product = fields.Field(attribute='product', column_name='商品')
    sku = fields.Field(attribute='sku', column_name='sku')
    sku_name = fields.Field(attribute='sku_name', column_name='商品名称')
    ref_price = fields.Field(attribute='ref_price', column_name='购买参考价（RMB）')
    img = fields.Field(attribute='img', column_name='图片URL')
    weight = fields.Field(attribute='weight', column_name='实际重量（g）')
    source_url = fields.Field(attribute='source_url', column_name='来源url（超始值为：http://）')
    alternative = fields.Field(attribute='alternative', column_name='替代产品')


    class Meta:
        model = Product
        skip_unchanged = True
        report_skipped = True
        import_id_fields = ('sku',)
        fields = ('product', 'sku', 'sku_name', 'ref_price', 'img','weight','source_url','alternative', )
        # exclude = ()


class ProductAdmin(object):



    import_export_args = {"import_resource_class": ProductResource, "export_resource_class": ProductResource}

    list_display = [ 'product','sku','supply_status','supply_comments','ref_orders', 'alternative','developer','update_time', 'weight','source_url']
     #'sku_name','img',

    search_fields = ["sku",'product']
    list_filter = ['supply_status','update_time' ,'developer']
    list_editable = ["alternative","supply_comments",]
    actions = ['batch_delay','batch_stop','batch_normal',]

    def ref_orders(self, obj):

        query_set = OrderDetail.objects.filter(Q(sku=obj.sku) & Q(order__order_status = "待打单（缺货）"))
        return  query_set.distinct("order").count()
        '''
        orders = []
        for row in query_set:
            order = row.order
            if order not in orders:
                orders.append(order)
        return len(orders)
        '''
    ref_orders.short_description = "关联订单"

    def batch_ref_orders(self, request, queryset):
        # 定义actions函数


        for row in queryset:
            #OrderDetail.objects.filter(Q(sku=row.sku) & Q(row.order__order_status="待打单（缺货）"))
            order_set = OrderDetail.objects.filter(Q(sku=row.sku) & Q(order__order_status="待打单（缺货）"))
            orders = []
            for row in order_set:
                order = row.order
                if order not in orders:
                    orders.append(order)
            Product.objects.filter(sku=row.sku).update(ref_orders = len(orders))

        return

    batch_ref_orders.short_description = "批量关联订单"


    def ref_orders(self, obj):

        query_set = OrderDetail.objects.filter(Q(sku=obj.sku) & Q(order__order_status = "待打单（缺货）"))

        orders = []
        for row in query_set:
            order = row.order
            if order not in orders:
                orders.append(order)

        return len(orders)

    ref_orders.short_description = "关联订单"


    def batch_stop(self, request, queryset):
        # 定义actions函数
        rows_updated = queryset.update(supply_status='STOP',update_time=datetime.now() )

        if rows_updated == 1:
            message_bit = '1 story was'
        else:
            message_bit = "%s stories were" % rows_updated
        self.message_user(request, "%s successfully marked as error." % message_bit)

    batch_stop.short_description = "批量断货"

    def batch_delay(self, request, queryset):
        # 定义actions函数
        rows_updated = queryset.update(supply_status='DELAY',update_time=datetime.now() )

        if rows_updated == 1:
            message_bit = '1 story was'
        else:
            message_bit = "%s stories were" % rows_updated
        self.message_user(request, "%s successfully marked as error." % message_bit)

    batch_delay.short_description = "批量延迟"

    '''
    def batch_pause(self, request, queryset):
        # 定义actions函数
        rows_updated = queryset.update(supply_status='PAUSE',update_time=datetime.now() )


        if rows_updated == 1:
            message_bit = '1 story was'
        else:
            message_bit = "%s stories were" % rows_updated
        self.message_user(request, "%s successfully marked as error." % message_bit)

    batch_pause.short_description = "批量缺货"
    '''

    def batch_normal(self, request, queryset):
        # 定义actions函数
        rows_updated = queryset.update(supply_status='NORMAL',update_time=datetime.now() )
        if rows_updated == 1:
            message_bit = '1 story was'
        else:
            message_bit = "%s stories were" % rows_updated
        self.message_user(request, "%s successfully marked as error." % message_bit)

    batch_normal.short_description = "批量正常"


    def get_list_queryset(self):
        """xadmin 有效的批量查询订单号"""
        queryset = super().get_list_queryset()

        query = self.request.GET.get(SEARCH_VAR, '')

        if (len(query) > 0):
            queryset |= self.model.objects.filter(product__in=query.split(","))

        if (len(query) > 0):
            queryset |= self.model.objects.filter(sku__in=query.split(","))

        return queryset
    '''
    def get_search_results(self, request, queryset, search_term):
        """批量查询sku号"""
        queryset, use_distinct = super().get_search_results(request, queryset, search_term)

        if (len(search_term) > 0):
            queryset |= self.model.objects.filter(product__in=search_term.split(","))

        if (len(search_term) > 0):
            queryset |= self.model.objects.filter(sku__in=search_term.split(","))
        return queryset, use_distinct
    '''
xadmin.site.register(Product, ProductAdmin)

'''
class ProductCategoryResource(resources.ModelResource):
    name = fields.Field(attribute='name', column_name='类别名')
    code = fields.Field(attribute='code', column_name='类别code')
    parent_category = fields.Field(attribute='parent_category', column_name='父类目级别')

    desc = fields.Field(attribute='desc', column_name='类别描述')
    category_type = fields.Field(attribute='category_type', column_name='类目级别')
    is_tab = fields.Field(attribute='is_tab', column_name='是否导航')
    add_time = fields.Field(attribute='add_time', column_name='添加时间')


    class Meta:
        model = ProductCategory
        skip_unchanged = True
        report_skipped = True
        import_id_fields = ('code',)
        fields = ('name', 'code', 'parent_category', 'desc', 'category_type', 'is_tab','add_time',)
        # exclude = ()

@xadmin.sites.register(ProductCategory)
class ProductCategoryAdmin(object):



    import_export_args = {"import_resource_class": ProductCategoryResource, "export_resource_class": ProductCategoryResource}

    list_display = [ 'name', 'code', 'parent_category', 'desc', 'category_type', 'is_tab','add_time',]


    search_fields = ["name",]
    list_filter = ['category_type',]
    list_editable = []
    actions = []

@xadmin.sites.register(ProductCategoryMypage)
class ProductCategoryMypageAdmin(object):


    list_display = [ 'mypage', 'productcategory',]


    search_fields = ["mypage__page",'productcategory__name']
    list_filter = ['mypage__page', 'productcategory__category_type',]
    list_editable = []
    actions = []
'''