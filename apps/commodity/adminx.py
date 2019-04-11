# -*- coding: utf-8 -*-
__author__ = 'Aaron'

import  json
import xadmin
from .models import *

@xadmin.sites.register(SelectionRule)
class SelectionRuleAdmin(object):

    actions = [ ]
    list_display = ('name', 'cates','prices', 'attrs',)
    list_editable = ['name', 'cates','prices', 'attrs',]
    search_fields = ['name', 'cates','prices', 'attrs', ]
    list_filter = ()

    exclude = []
    ordering = []


@xadmin.sites.register(PageRule)
class PageRuleAdmin(object):

    actions = [ ]
    list_display = ('mypage', 'selectionrule','active', 'update_time', 'staff',)
    list_editable = []
    search_fields = []
    list_filter = ("mypage","active",)

    exclude = []
    ordering = ["mypage"]