# -*- coding: utf-8 -*-
__author__ = 'Aaron'

import  json
import xadmin
from xadmin.layout import Main, Side, Fieldset, Row, AppendedText

from import_export import resources, fields
from import_export.widgets import ForeignKeyWidget
from django.db.models import Count
import  re
from django.utils.safestring import mark_safe
from xadmin.filters import manager as filter_manager, FILTER_PREFIX, SEARCH_VAR, DateFieldListFilter, \
    RelatedFieldSearchFilter

from .models import *
from fb.models import MyPage,MyAlbum
from shop.models import Shop,ShopifyProduct, ShopifyImage,ShopifyVariant,ShopifyOptions
from .choose_target import ChoosePage
from prs.tasks import create_abs_label

import os,requests

from django.conf import settings
from apps.fb.fb_dev import get_token

from .cate_action import SelectCategory


class MyCategoryResource(resources.ModelResource):
    super_cate = fields.Field(
        column_name='super_cate',
        attribute='super_cate',
        widget=ForeignKeyWidget(MyCategory, 'code'))
    code = fields.Field(attribute='code', column_name='code')

    class Meta:
        model = MyCategory
        skip_unchanged = True
        report_skipped = True
        import_id_fields = ('code',)
        fields = ('code',)
        # exclude = ()




class Lightin_SPUResource(resources.ModelResource):
    '''
    SPU = fields.Field(attribute='SPU', column_name='SPU')
    en_name = fields.Field(attribute='en_name', column_name='SPU')
    cn_name = fields.Field(attribute='cn_name', column_name='cn_name')
    cate_1 = fields.Field(attribute='cate_1', column_name='SPU')
    cate_2 = fields.Field(attribute='cate_2', column_name='SPU')
    cate_3 = fields.Field(attribute='cate_3', column_name='SPU')
    vendor_sale_price = fields.Field(attribute='vendor_sale_price', column_name='SPU')
    vendor_supply_price = fields.Field(attribute='vendor_supply_price', column_name='SPU')
    link = fields.Field(attribute='link', column_name='SPU')
    '''



    class Meta:
        model = Lightin_SPU
        skip_unchanged = True
        report_skipped = True
        import_id_fields = ('SPU',)
        fields = ("SPU", "en_name","cn_name", "cate_1","cate_2","cate_3","vendor_sale_price","vendor_supply_price","vendor" ,"link",)
        # exclude = ()

@xadmin.sites.register(Lightin_SPU)
class Lightin_SPUAdmin(object):

    def photo(self, obj):
        if obj.images is not None and len(obj.images)>0 :
            photos = json.loads(obj.images)
            img = ''

            for photo in photos:
                try:
                    img = img + '<a><img src="%s" width="100px"></a>' % (photo)
                except Exception as e:
                    print("获取图片出错", e)

            return mark_safe(img)

        else:
            photos = "no photo"
            return photos

    photo.short_description = "图片"

    import_export_args = {"import_resource_class": Lightin_SPUResource,
                          "export_resource_class": Lightin_SPUResource}

    list_display = [ "SPU","handle", "sellable","free_shipping",  "yallavip_price","free_shipping_price", "en_name","cn_name", "photo","vendor","link", ]
    # 'sku_name','img',

    search_fields = ["SPU","handle","breadcrumb", ]
    list_filter = ["vendor","free_shipping", ]
    list_editable = []
    readonly_fields = ()
    actions = []

class Lightin_SKUResource(resources.ModelResource):

    class Meta:
        model = Lightin_SKU
        skip_unchanged = True
        report_skipped = True
        import_id_fields = ('SKU',)
        fields = ("SPU", "SKU","barcode","quantity", "vendor_sale_price","vendor_supply_price","weight", "length","width","height","skuattr","image",)
        # exclude = ()




@xadmin.sites.register(Lightin_SKU)
class Lightin_SKUAdmin(object):


    import_export_args = {"import_resource_class": Lightin_SKUResource,
                          "export_resource_class": Lightin_SKUResource}

    def photo(self, obj):
        if obj.lightin_spu.images is not None and len(obj.lightin_spu.images)>0 :
            photos = json.loads(obj.lightin_spu.images)
            img = ''

            for photo in photos:
                try:
                    img = img + '<a><img src="%s" width="384px"></a>' % (photo)
                except Exception as e:
                    img = "获取图片出错 "+ e

        else:
            img = "no photo"

        return mark_safe(img)

    photo.short_description = "spu图片"

    def sku_photo(self, obj):
        if obj.image is not None and len(obj.image)>0 :
           img = '<a><img src="%s" width="100px"></a>' % (obj.image)
        else:
            img = "no photo"

        return mark_safe(img)

    sku_photo.short_description = "sku图片"

    def shopify_price(self, obj):
        return obj.lightin_spu.shopify_price

    shopify_price.short_description = "price"

    def cn_name(self, obj):
        return obj.lightin_spu.cn_name

    cn_name.short_description = "cn_name"

    def handle(self, obj):
        return obj.lightin_spu.handle

    handle.short_description = "handle"

    list_display = ["SKU", "SPU", 'cn_name', "o_sellable","sku_photo", "handle","sku_price","free_shipping_price", "photo","skuattr",]

    # 'sku_name','img',
    search_fields = ["SPU", "SKU","lightin_spu__handle",]
    list_filter = ["skuattr", "SPU","lightin_spu__breadcrumb","lightin_spu__vendor",]
    list_editable = []
    readonly_fields = ()
    actions = []
    ordering = ["-o_sellable"]




class Lightin_barcodeResource(resources.ModelResource):

    class Meta:
        model = Lightin_barcode
        skip_unchanged = True
        report_skipped = True
        import_id_fields = ('barcode',)
        fields = ( "SKU","barcode","quantity")
        # exclude = ()

@xadmin.sites.register(Lightin_barcode)
class Lightin_barcodeAdmin(object):

    import_export_args = {"import_resource_class": Lightin_barcodeResource,
                          "export_resource_class": Lightin_barcodeResource}

    list_display = ["SKU","barcode","occupied", "sellable", "o_quantity","o_sellable","o_reserved","o_shipped","y_sellable","y_reserved","y_shipped",]


    search_fields = ["SKU","barcode",]
    list_filter = ["SKU"]
    list_editable = []
    readonly_fields = ()
    actions = []

@xadmin.sites.register(YallavipAlbum)
class YallavipAlbumAdmin(object):

    def free_shipping_count(self, obj):
        return LightinAlbum.objects.filter(yallavip_album=obj,lightin_spu__free_shipping=True ).count()

    free_shipping_count.short_description = "包邮数量"

    def published_count(self, obj):
        return LightinAlbum.objects.filter(yallavip_album=obj, published=True).count()

    published_count.short_description = "已发布图片数量"

    def readypublish_count(self, obj):
        return LightinAlbum.objects.filter(yallavip_album=obj, published=False, material=True,lightin_spu__sellable__gt=0).count()

    readypublish_count.short_description = "待发布图片数量"

    def topublish_count(self, obj):
        return LightinAlbum.objects.filter(yallavip_album=obj, material=False,lightin_spu__sellable__gt=0).count()

    topublish_count.short_description = "可发布图片数量"

    def sellable(self, obj):
        return  obj.lightin_spu.sellable

    sellable.short_description = "sellable"

    list_display = ["page","rule",  "album","free_shipping_count","published","published_count","readypublish_count", "topublish_count", "deleted", "active",]
    # 'sku_name','img',

    search_fields = ["album__name",]
    list_filter = [ "page","rule", "published", "deleted", "active",]
    list_editable = []
    readonly_fields = ()
    actions = ["prepare_yallavip_ad",]

    def prepare_yallavip_ad(self, request, queryset):
        from prs.fb_action import  prepare_yallavip_ad_album
        lightinalbums_all = LightinAlbum.objects.filter(lightin_spu__sellable__gt=0, lightin_spu__SPU__istartswith="s",
                                                        lightin_spu__shopify_price__gt=30,
                                                        # lightin_spu__shopify_price__lt=50,
                                                        aded=False,
                                                        yallavip_album__page__active=True,
                                                        yallavip_album__page__is_published=True,
                                                        published=True).distinct()
        for yallavip_album in queryset:
            prepare_yallavip_ad_album(yallavip_album.pk, lightinalbums_all)



@xadmin.sites.register(LightinAlbum)
class LightinAlbumAdmin(object):

    def photo(self, obj):
        if obj.image_marked is not None and len(obj.image_marked)>0 :
            photo = obj.image_marked
            try:
                img = '<a><img src="%s" width="100px"></a>' % (photo)
            except Exception as e:
                print("获取图片出错", e)
                img = "no photo"

            return mark_safe(img)

        else:
            return  "no photo"

    photo.short_description = "图片"

    def source_photo(self, obj):

        try:
            img = '<a><img src="%s" width="100px"></a>' % (obj.source_image)
        except Exception as e:
            print("获取图片出错", e)
            img = "no photo"

        return mark_safe(img)



    source_photo.short_description = "源图片"

    def page(self, obj):
        return  obj.myalbum.mypage

    page.short_description = "page"

    def sellable(self, obj):
        return  obj.lightin_spu.sellable

    sellable.short_description = "sellable"

    def spu_onesize(self, obj):

        return  obj.lightin_spu.one_size

    spu_onesize.short_description = "均码的SPU数量"

    list_display = ["lightin_spu","sellable", "spu_onesize",  "yallavip_album","photo","batch_no","name","source_photo", "fb_id", "published","publish_error","published_time",]
    # 'sku_name','img',

    search_fields = ["lightin_spu__SPU","yallavip_album__album__name","name",]
    list_filter = [ "published","yallavip_album__page","yallavip_album","material","batch_no","deleted","sourced" ]
    list_editable = []
    readonly_fields = ()
    actions = []




@xadmin.sites.register(YallavipAd)
class YallavipAdAdmin(object):
    def show_promote(self, obj):

        try:
            img = mark_safe('<img src="%s" width="100px" />' % (obj.image_marked_url))
        except Exception as e:
            img = ''
        print (img)

        return img

    show_promote.short_description = '广告图片'
    show_promote.allow_tags = True


    def page(self, obj):
        return  obj.yallavip_album.page.page

    def like_count(self, obj):
        return  obj.fb_feed.like_count

    like_count.short_description = "like_count"

    '''
    def sellable(self, obj):
        handle_list = obj.spus_name.split(",")
        sellable = Lightin_SPU.objects.filter(handle__in=handle_list).values("handle","sellable")
        return  list(sellable)


    sellable.short_description = "sellable"
    '''

    list_display = ["spus_name", "yallavip_album", "page", 'sellable', 'like_count', 'show_promote',"active", "published","engagement_aded", "message_aded",]

    # 'sku_name','img',
    search_fields = ["spus_name","yallavip_album__album__name", ]
    list_filter = ["yallavip_album__page", "active","published","engagement_aded","message_aded", "long_ad","page_no",]
    list_editable = []
    readonly_fields = ()
    actions = []
    ordering = []



@xadmin.sites.register(PagePromoteCate)
class PagePromoteCateAdmin(object):


    actions = [ ]
    list_display = ('mypage', 'cate', 'promote_cate',)
    list_editable = []
    search_fields = ['mypage__page', 'cate__name','promote_cate__name' ]
    list_filter = ('cate',)
    filter_horizontal = ('cate','promote_cate')
    style_fields = {'cate': 'm2m_transfer',
                    'promote_cate': 'm2m_transfer'
                    }

    exclude = []
    ordering = []