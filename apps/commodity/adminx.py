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

    actions = [ "batch_update_yallavip_album","batch_prepare_yallavip_photoes",
                "batch_prepare_yallavip_album_source","batch_prepare_yallavip_album_material",
                "batch_sync_yallavip_album",]
    list_display = ('mypage', 'rules','active',)
    list_editable = []
    search_fields = []
    list_filter = ("mypage","active",)
    filter_horizontal = ('rules',)
    style_fields = {'rules':'m2m_transfer'}

    exclude = [ 'update_time', 'staff',]
    ordering = ["mypage"]

    def batch_update_yallavip_album(self, request, queryset):
        from prs.tasks import update_yallavip_album

        for row in queryset:
            update_yallavip_album(page_no=row.mypage.page_no)

    batch_update_yallavip_album.short_description = "批量创建相册"

    def batch_prepare_yallavip_photoes(self, request, queryset):
        from prs.tasks import prepare_yallavip_photoes

        for row in queryset:
            prepare_yallavip_photoes(page_no=row.mypage.page_no)

    batch_prepare_yallavip_photoes.short_description = "批量创建基础信息"

    def batch_prepare_yallavip_album_source(self, request, queryset):
        from prs.tasks import prepare_yallavip_album_source

        for row in queryset:
            prepare_yallavip_album_source(page_no=row.mypage.page_no)

    batch_prepare_yallavip_album_source.short_description = "批量创建预览图片"

    def batch_prepare_yallavip_album_material(self, request, queryset):
        from prs.tasks import prepare_yallavip_album_material

        for row in queryset:
            prepare_yallavip_album_material(page_no=row.mypage.page_no)

    batch_prepare_yallavip_album_material.short_description = "批量创建水印图片"

    def batch_sync_yallavip_album(self, request, queryset):
        from prs.tasks import sync_yallavip_album

        for row in queryset:
            sync_yallavip_album(page_no=row.mypage.page_no)

    batch_sync_yallavip_album.short_description = "批量发布到相册"