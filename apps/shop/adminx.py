# -*- coding: utf-8 -*-
__author__ = 'bobby'

import numpy as np, re
import xadmin
from django.shortcuts import get_object_or_404, get_list_or_404, render
from import_export import resources, fields
from import_export.widgets import ForeignKeyWidget
from .models import Shop
import  shopify

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




class ShopAdmin(object):

    list_display = [ 'shop_name','apikey','password', ]
     #'sku_name','img',

    search_fields = ["shop_name",]
    #list_filter = ['supply_status','update_time' ]
    #list_editable = ["supply_status"]
    actions = ['update_orders',]

    def update_orders(self, request, queryset):
        # 定义actions函数
        for row in queryset:

            shop_obj = Shop.objects.get(shop_name=row.shop_name)
            shop_url = "https://%s:%s@%s.myshopify.com/admin" % (shop_obj.apikey, shop_obj.password,shop_obj.shop_name)
            #shop_url = "https://12222a833afcad263c5cc593eca7af10:47aea3fe8f4b9430b1bac56c886c9bae@yallasale-com.myshopify.com/admin"
            shopify.ShopifyResource.set_site(shop_url)

            # Get the current shop
            #shop = shopify.Shop.current()
            #print("shop is : ", shop)
            # Get a specific product
            #product = shopify.Product.find()
            #print(("product is ", product))

            orders = shopify.Order.find()
            print("orders order_number   is ",orders[2].order_number  )


        #rows_updated = queryset.update(verify_status='PROCESSING', cancel=None, error_money=None, error_contact=None,
        #                               error_address=None, error_cod=None, error_note=None)


    update_orders.short_description = "更新订单"


xadmin.site.register(Shop, ShopAdmin)

