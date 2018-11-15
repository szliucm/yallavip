# -*- coding: utf-8 -*-
__author__ = 'bobby'

import numpy as np, re
import xadmin
from xadmin import views

from django.shortcuts import get_object_or_404, get_list_or_404, render
from import_export import resources, fields
from import_export.widgets import ForeignKeyWidget
from .models import Op_Product,Op_Supplier, Planning
from product.models import Product

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


class Op_ProductResource(resources.ModelResource):
    product = fields.Field(attribute='product', column_name='产品')
    order_count = fields.Field(attribute='order_count', column_name='订单数')

    order_quantity = fields.Field(attribute='order_quantity', column_name='销售数量')

    like_count = fields.Field(attribute='like_count', column_name='点赞数')

    comment_count = fields.Field(attribute='comment_count', column_name='评论数')
    post_count = fields.Field(attribute='post_count', column_name='post数')
    conversion = fields.Field(attribute='conversion', column_name='转化率')
    cluster = fields.Field(attribute='cluster', column_name='cluster')



    class Meta:
        model = Op_Product
        skip_unchanged = True
        report_skipped = True
        import_id_fields = ('product',)
        fields = ( 'product','order_count','order_quantity','like_count', 'comment_count','post_count','conversion','cluster',)
        # exclude = ()


@xadmin.sites.register(Op_Product)
class Op_ProductAdmin(object):
    import_export_args = {"import_resource_class": Op_ProductResource, "export_resource_class": Op_ProductResource}

    list_display = [ 'product','show_supply_status','cluster','optimization','challenger','challenger_comment','challenge_start_time','enhance','operator','operator_comment','operate_start_time', 'order_count','order_quantity','like_count', 'comment_count','post_count','conversion',]


    search_fields = ['product']
    list_filter = ['cluster','optimization','enhance',]
    list_editable = ['optimization','enhance','challenger_comment','operator_comment']
    actions = ["start_challenge", "start_operate",'start_COPY', 'start_POST']
    ordering = ['-order_count']

    def show_supply_status(self, obj):
        products = Product.objects.filter(product=obj.product)
        for product in products:
            if(product.supply_status == 'STOP'):
                return  'STOP'
        return 'NORMAL'

    show_supply_status.short_description = "供应状态"

    def get_search_results(self, request, queryset, search_term):
        """批量查询sku号"""
        queryset, use_distinct = super().get_search_results(request, queryset, search_term)

        if (len(search_term) > 0):
            queryset |= self.model.objects.filter(product__in=search_term.split(","))
        return queryset, use_distinct

    def start_challenge(self, request, queryset):
        # 定义actions函数
        rows_updated = queryset.update(challenger=str(self.user), challenge_start_time=datetime.now())

    start_challenge.short_description = "开始挑战"

    def start_COPY(self, request, queryset):
        # 定义actions函数
        rows_updated = queryset.update(optimization='COPY')

    start_COPY.short_description = "优化图文"

    def start_PROMOTE(self, request, queryset):
        # 定义actions函数
        rows_updated = queryset.update(optimization='PROMOTE')

    start_PROMOTE.short_description = "改进促销"



    def start_operate(self, request, queryset):
        # 定义actions函数
        rows_updated = queryset.update(operator=str(self.user), operate_start_time=datetime.now())

    start_operate.short_description = "启动运营"

    def start_POST(self, request, queryset):
        # 定义actions函数
        rows_updated = queryset.update(enhance='POST')

    start_POST.short_description = "增加post"

class Op_SupplierResource(resources.ModelResource):
    supplier = fields.Field(attribute='supplier', column_name='供应商')
    product_count = fields.Field(attribute='product_count', column_name='产品数')

    sku_count = fields.Field(attribute='sku_count', column_name='sku数')

    purchase_amount = fields.Field(attribute='purchase_amount', column_name='采购金额')

    avg_time = fields.Field(attribute='avg_time', column_name='平均到货时间')
    purchase_count = fields.Field(attribute='purchase_count', column_name='采购次数')
    error_count = fields.Field(attribute='error_count', column_name='出错次数')
    error_ratio = fields.Field(attribute='error_ratio', column_name='差错率')
    cluster = fields.Field(attribute='cluster', column_name='cluster')

    class Meta:
        model = Op_Supplier
        skip_unchanged = True
        report_skipped = True
        import_id_fields = ('supplier',)
        fields = ( 'supplier','product_count','sku_count','purchase_amount', 'avg_time','purchase_count','error_count','error_ratio','cluster',)
        # exclude = ()


@xadmin.sites.register(Op_Supplier)
class Op_SupplierAdmin(object):
    import_export_args = {"import_resource_class": Op_SupplierResource, "export_resource_class": Op_SupplierResource}

    list_display = [ 'supplier','cluster','optimization','challenger','challenger_comment','challenge_start_time','enhance','operator','operator_comment','operate_start_time','product_count','sku_count','purchase_amount', 'avg_time','purchase_count','error_count','error_ratio',]


    search_fields = ['supplier']
    list_filter = ['cluster','optimization','enhance',]
    list_editable = ['optimization','enhance','challenger_comment','operator_comment']
    actions = ["start_challenge","start_ACCOUNT", "start_REPLACE","start_operate",]
    ordering = ['-purchase_count']



    def start_challenge(self, request, queryset):
        # 定义actions函数
        rows_updated = queryset.update(challenger = str(self.user), challenge_start_time=datetime.now())

    start_challenge.short_description = "开始挑战"

    def start_ACCOUNT(self, request, queryset):
        # 定义actions函数
        rows_updated = queryset.update(optimization='ACCOUNT')

    start_ACCOUNT.short_description = "深入合作"

    def start_REPLACE(self, request, queryset):
        # 定义actions函数
        rows_updated = queryset.update(optimization='REPLACE')

    start_REPLACE.short_description = "汰换供应商"

    def start_operate(self, request, queryset):
        # 定义actions函数
        rows_updated = queryset.update(operator = str(self.user), operate_start_time=datetime.now())

    start_operate.short_description = "启动运营"

@xadmin.sites.register(Planning)
class PlanningAdmin(object):


    list_display = [ 'product','show_supply_status','cluster','optimization','challenger','challenger_comment','challenge_start_time', 'order_count','order_quantity','like_count', 'comment_count','post_count','conversion',]


    search_fields = ['product']
    list_filter = ['cluster','optimization']
    list_editable = ['optimization','challenger_comment']
    actions = ["start_challenge", 'start_COPY','start_PROMOTE']
    ordering = ['-order_count']

    def show_supply_status(self, obj):
        products = Product.objects.filter(product=obj.product)
        for product in products:
            if(product.supply_status == 'STOP'):
                return  'STOP'
        return 'NORMAL'

    show_supply_status.short_description = "供应状态"

    def get_search_results(self, request, queryset, search_term):
        """批量查询sku号"""
        queryset, use_distinct = super().get_search_results(request, queryset, search_term)

        if (len(search_term) > 0):
            queryset |= self.model.objects.filter(product__in=search_term.split(","))
        return queryset, use_distinct

    def start_challenge(self, request, queryset):
        # 定义actions函数
        rows_updated = queryset.update(challenger=str(self.user), challenge_start_time=datetime.now())

    start_challenge.short_description = "开始企划"

    def start_COPY(self, request, queryset):
        # 定义actions函数
        rows_updated = queryset.update(optimization='COPY')

    start_COPY.short_description = "优化图文"

    def start_PROMOTE(self, request, queryset):
        # 定义actions函数
        rows_updated = queryset.update(optimization='PROMOTE')

    start_PROMOTE.short_description = "改进促销"





