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
from import_export import resources, fields
from import_export.widgets import ForeignKeyWidget
from .models import *

class FunmartOrderResource(resources.ModelResource):

    class Meta:
        model = FunmartOrder
        skip_unchanged = True
        report_skipped = True
        import_id_fields = ('track_code',)
        fields = ('track_code',)
        # exclude = ()

@xadmin.sites.register(FunmartOrder)
class FunmartOrderAdmin(object):
    import_export_args = {'import_resource_class': FunmartOrderResource, 'export_resource_class': FunmartOrderResource}

    def item_count(self, obj):

        return  obj.funmartorder_orderitem.aggregate(Sum("quantity"))["quantity__sum"]

    item_count.short_description = "item_count"

    list_display = ["track_code", "order_no","item_count",  "ship_method", "upload_date", ]
    list_editable = []

    search_fields = ["order_no",'track_code', ]
    list_filter = ( "ship_method","upload_date", )
    ordering = []

    actions = [ ]


@xadmin.sites.register(FunmartOrderItem)
class FunmartOrderItemAdmin(object):
    list_display = ["order_no", "sku", "quantity", "price",  ]
    list_editable = []

    search_fields = ["order_no", 'sku', ]
    list_filter = ( )
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
    list_display = ["SKU", "SPU", "skuattr", "images", "sale_price" ]
    list_editable = []

    search_fields = ["SKU", 'SPU', ]
    list_filter = ( )
    ordering = []

    actions = []