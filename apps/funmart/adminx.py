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


@xadmin.sites.register(FunmartOrder)
class FunmartOrderAdmin(object):


    list_display = ["order_no", "track_code", "ship_method","upload_date", ]
    list_editable = []

    search_fields = ["order_no",'track_code', ]
    list_filter = ( "ship_method","upload_date", )
    ordering = []

    actions = [ ]


@xadmin.sites.register(FunmartOrderItem)
class FunmartOrderItemAdmin(object):
    list_display = ["order_no", "sku", "quantity", "price","ship_method",  ]
    list_editable = []

    search_fields = ["order_no", 'sku', ]
    list_filter = ( )
    ordering = []

    actions = []

