# -*- coding: utf-8 -*-
__author__ = 'bobby'
import xadmin
from .models import ActionLog

class ActionLogAdmin(object):
    list_display = ('issue', 'action_time', 'action', 'staff', )
    list_editable = []
    #search_fields = ['logistic_no', ]
    list_filter = ("action","issue","action_time" )
    ordering = ['-action_time']


xadmin.site.register(ActionLog,ActionLogAdmin)