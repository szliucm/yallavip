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


class ProductResource(resources.ModelResource):

    product = fields.Field(attribute='product', column_name='商品')
    sku = fields.Field(attribute='sku', column_name='sku')
    sku_name = fields.Field(attribute='sku_name', column_name='商品名称')
    ref_price = fields.Field(attribute='ref_price', column_name='购买参考价（RMB）')
    img = fields.Field(attribute='img', column_name='图片URL')
    weight = fields.Field(attribute='weight', column_name='实际重量（g）')
    source_url = fields.Field(attribute='source_url', column_name='来源url（超始值为：http://）')


    class Meta:
        model = Product
        skip_unchanged = True
        report_skipped = True
        import_id_fields = ('sku',)
        fields = ('product', 'sku', 'sku_name', 'ref_price', 'img','weight','source_url' )
        # exclude = ()


class ProductAdmin(object):



    import_export_args = {"import_resource_class": ProductResource, "export_resource_class": ProductResource}

    list_display = [ 'product','sku','supply_status', 'update_time','ref_price', 'weight','source_url']
     #'sku_name','img',

    search_fields = ["sku",'product']
    list_filter = ['supply_status','update_time' ]
    #list_editable = ["supply_status"]
    actions = ['batch_stop','batch_pause','batch_normal',]

    def batch_stop(self, request, queryset):
        # 定义actions函数
        rows_updated = queryset.update(supply_status='STOP',update_time=datetime.now() )



        if rows_updated == 1:
            message_bit = '1 story was'
        else:
            message_bit = "%s stories were" % rows_updated
        self.message_user(request, "%s successfully marked as error." % message_bit)

    batch_stop.short_description = "批量断货"

    def batch_pause(self, request, queryset):
        # 定义actions函数
        rows_updated = queryset.update(supply_status='PAUSE',update_time=datetime.now() )


        if rows_updated == 1:
            message_bit = '1 story was'
        else:
            message_bit = "%s stories were" % rows_updated
        self.message_user(request, "%s successfully marked as error." % message_bit)

    batch_pause.short_description = "批量缺货"

    def batch_normal(self, request, queryset):
        # 定义actions函数
        rows_updated = queryset.update(supply_status='NORMAL',update_time=datetime.now() )
        if rows_updated == 1:
            message_bit = '1 story was'
        else:
            message_bit = "%s stories were" % rows_updated
        self.message_user(request, "%s successfully marked as error." % message_bit)

    batch_normal.short_description = "批量正常"




    def get_search_results(self, request, queryset, search_term):
        """批量查询sku号"""
        queryset, use_distinct = super().get_search_results(request, queryset, search_term)

        if (len(search_term) > 0):
            queryset |= self.model.objects.filter(product__in=search_term.split(","))
        return queryset, use_distinct

xadmin.site.register(Product, ProductAdmin)

