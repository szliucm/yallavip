# -*- coding: utf-8 -*-
__author__ = 'bobby'

import requests
import json
import time
from datetime import datetime, timedelta, timezone
import base64
from django.db.models import Sum
import numpy as np, re
import xadmin
from xadmin.layout import Main, Side, Fieldset, Row, AppendedText
from django.shortcuts import get_object_or_404, get_list_or_404, render
from import_export import resources, fields
from import_export.widgets import ForeignKeyWidget
from .models import *
from django.utils.safestring import mark_safe
from django.utils.html import format_html

from .views import testView


'''
class ScanOrderResource(resources.ModelResource):

    class Meta:
        model = ScanOrder
        skip_unchanged = True
        report_skipped = True
        import_id_fields = ('track_code','batch_no',)
        fields = ('track_code','batch_no',)
        # exclude = ()


@xadmin.sites.register(ScanOrder)
class ScanOrderAdmin(object):
    import_export_args = {'import_resource_class': ScanOrderResource, 'export_resource_class': ScanOrderResource}



    list_display = ["track_code", "order_no", "batch_no", "shelfed",  "quantity", "scanned_quantity",]
    list_editable = []

    search_fields = ['track_code', "order_no",]
    list_filter = ( "batch_no","downloaded",  )
    ordering = []

    actions = [ ]

@xadmin.sites.register(ScanOrderItem)
class ScanOrderItemAdmin(object):
    list_display = ["track_code", "shelfed",  "quantity", "scanned_quantity",]
    list_editable = []

    search_fields = ['track_code', ]
    list_filter = ( "shelfed", )
    ordering = []

    actions = [ ]
'''

class FunmartOrderResource(resources.ModelResource):

    class Meta:
        model = FunmartOrder
        skip_unchanged = True
        report_skipped = True
        import_id_fields = ('track_code',)
        fields = ('track_code','batch_no',)
        # exclude = ()

@xadmin.sites.register(FunmartOrder)
class FunmartOrderAdmin(object):
    import_export_args = {'import_resource_class': FunmartOrderResource, 'export_resource_class': FunmartOrderResource}



    list_display = ["track_code", "order_no","quantity",  "ship_method", "upload_date", ]
    list_editable = []

    search_fields = ["order_no",'track_code', ]
    list_filter = ( "ship_method","upload_date","batch_no",   )
    ordering = []

    actions = [ ]

    def update_funmart_orders(self, request, queryset):
        from funmart.tasks import  download_funmart_orders

        download_funmart_orders()
        return

    update_funmart_orders.short_description = "update funmart orders"

@xadmin.sites.register(FunmartOrderItem)
class FunmartOrderItemAdmin(object):
    list_display = ["sku", "item_code","barcode", "quantity", "scanned_quantity", "price", "action","track_code","batch_no",]
    list_editable = []

    search_fields = ["track_code", 'sku', ]
    list_filter = ( "action","batch_no", )
    ordering = []

    actions = []

@xadmin.sites.register(FunmartSPU)
class FunmartSPUAdmin(object):
    list_display = ["SPU", "cate_1", "cate_2", "cate_3", "en_name", "skuattr", "images", "link","sale_price", "skuList", ]
    list_editable = []

    search_fields = ["SPU", ]
    list_filter = ("cate_1", "cate_2", "cate_3", )
    ordering = []

    actions = []

@xadmin.sites.register(FunmartSKU)
class FunmartSKUAdmin(object):
    def show_photo(self, obj):

        try:
            photos = json.loads(obj.images)
            img = mark_safe('<img src="%s" width="100px" />' % (photos[0]))
            print(img)
        except Exception as e:
            img = ''
        return img

    show_photo.short_description = 'photo'
    show_photo.allow_tags = True

    list_display = ["SKU", "SPU", "skuattr",  "sale_price" ,"show_photo",]
    list_editable = []

    search_fields = ["SKU", 'SPU', ]
    list_filter = ("downloaded", "uploaded", )
    ordering = []

    actions = []

class YallavipBarcodeResource(resources.ModelResource):

    class Meta:
        model = YallavipBarcode
        skip_unchanged = True
        report_skipped = True
        import_id_fields = ('barcode',)
        fields = ( "barcode","SKU","funmart_barcode",)
        # exclude = ()


@xadmin.sites.register(YallavipBarcode)
class YallavipBarcodeAdmin(object):
    import_export_args = {"import_resource_class": YallavipBarcodeResource,
                          "export_resource_class": YallavipBarcodeResource}

    def show_photo(self, obj):

        try:

            photos = json.loads(obj.funmart_sku.images)
            img = mark_safe('<img src="%s" width="100px" />' % (photos[0]))
            print(img)
        except Exception as e:
            img = ''
        return img

    show_photo.short_description = 'photo'
    show_photo.allow_tags = True

    def show_cate(self, obj):
        if obj.funmart_sku.funmart_spu.cate_3 :
            cate = obj.funmart_sku.funmart_spu.cate_3
        elif obj.funmart_sku.funmart_spu.cate_2 :
            cate = obj.funmart_sku.funmart_spu.cate_2
        elif obj.funmart_sku.funmart_spu.cate_1:
            cate = obj.funmart_sku.funmart_spu.cate_1
        else:
            cate = ""
        return  cate

    show_cate.short_description = "Category"

    list_display = ["barcode", "funmart_barcode", "SKU", "show_photo","show_cate",]
    list_editable = []

    search_fields = ["barcode","SKU","funmart_barcode", ]
    list_filter = ("funmart_sku__funmart_spu__sale_type",)
    ordering = ["-barcode"]

    actions = []
    '''
    def queryset(self):
        qs = super().queryset()
        return qs.filter(funmart_sku__funmart_spu__sale_type__in=["hot","normal"])
    '''

@xadmin.sites.register(BatchSKU)
class BatchSKUAdmin(object):
    def show_action(self, obj):
        if obj.action == "Put Away":
            color_code = 'green'
        elif obj.action == "Normal_Case":
            color_code = 'blue'
        elif obj.action == "Dead_No_Size":
            color_code = 'yellow'
        elif obj.action == "Dead_Size":
            color_code = 'red'
        else:
            color_code = 'white'

        return format_html(
            '<span style="background-color:{};">{}</span>',

            color_code,
            obj.action,
        )

    show_action.short_description = u"action"

    list_display = ["SKU", "sale_type", "order_count",  "quantity" ,"uploaded", "show_action",]
    list_editable = []

    search_fields = ["SKU",  ]
    list_filter = ( "batch_no","sale_type","action","uploaded",)
    ordering = []

    actions = ["start_batch", "batch_uploaded"]

    def start_batch(self, request, queryset):

        batch_no = BatchSKU.objects.all().aggregate(Max('batch_no')).get("batch_no__max") + 1
        queryset.update(batch_no=batch_no)

    start_batch.short_description = "start batch"



    def batch_uploaded(self, request, queryset):

        queryset.update(uploaded=True)
        skus_list = queryset.values_list("SKU",flat=True)
        FunmartSKU.objects.filter(SKU__in=skus_list).update(uploaded=True)

    batch_uploaded.short_description = "批量上传到wms"

'''
@xadmin.sites.register(Test)
class TestAdmin(object):
	list_display = []
	object_list_template = "funmart/index.html"
	

    	
'''

@xadmin.sites.register(ScanPackage)
class ScanPackageAdmin(object):
	list_display = []
	object_list_template = "funmart/scanpackage.html"

@xadmin.sites.register(PrepareBatch)
class PrepareBatchAdmin(object):
    list_display = []
    object_list_template = "funmart/preparebatch.html"

@xadmin.sites.register(ScanPackageItem)
class ScanPackageItemAdmin(object):
    list_display = []
    object_list_template = "funmart/scanpackageitem.html"



@xadmin.sites.register(FulfillBag)
class FulfillBagAdmin(object):
    list_display = []
    object_list_template = "funmart/fulfillbag.html"

