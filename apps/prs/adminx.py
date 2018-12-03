# -*- coding: utf-8 -*-
__author__ = 'Aaron'

import xadmin
from .models import *

@xadmin.sites.register(MyProduct)
class MyProductAliAdmin(object):
    list_display = ['product_no', 'vendor_no', ]


    search_fields = ["product_no","vendor_no", ]
    list_filter = [ ]
    list_editable = []
    readonly_fields = ()
    actions = []

@xadmin.sites.register(MyProductAli)
class MyProductAliAdmin(object):
    list_display = ['myproduct', 'vendor_no', 'url',]
    # 'sku_name','img',

    search_fields = ["myproduct","url","myproductcate", ]
    list_filter = ["myproductcate", ]
    list_editable = []
    readonly_fields = ("myproduct","vendor_no",)
    actions = []

@xadmin.sites.register(MyProductAliShop)
class MyProductAliShopAdmin(object):
    list_display = ['vendor_nname', 'updated', 'url',]
    # 'sku_name','img',

    search_fields = ["vendor_nname","url","updated", ]
    list_filter = ["updated", ]
    list_editable = ["updated",]
    #readonly_fields = ("myproduct","vendor_no",)
    actions = []

@xadmin.sites.register(MyProductResources)
class MyProductResourcesAdmin(object):
    list_display = ['myproduct', "myproductali", 'name',"resource_cate","resource_type", ]
    # 'sku_name','img',

    search_fields = ["myproduct","resource" ]
    list_filter = ["resource_cate","resource_type" ,]
    list_editable = []
    readonly_fields = ()
    actions = []

@xadmin.sites.register(MyProductShopify)
class MyProductShopifyAdmin(object):
    list_display = [ 'myproduct',"myproductali","shopifyproduct", 'shopifyvariant',"obj_type", ]


    search_fields = ["myproduct","myproductali","shopifyproduct" ,'shopifyvariant',]
    list_filter = ["obj_type",]
    list_editable = []
    readonly_fields = ("shopifyproduct", 'shopifyvariant',)
    actions = []

@xadmin.sites.register(MyProductFb)
class MyProductFbAdmin(object):
    list_display = [ "mypage", "myresource", 'myproduct',"myphoto", 'myfeed',"myad","obj_type", ]
    # 'sku_name','img',

    search_fields = ["myproduct","myresource" ]
    list_filter = ["myproduct","obj_type","mypage"]
    list_editable = []
    readonly_fields = ("myphoto", 'myfeed',"myad",)
    actions = []