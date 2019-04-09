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