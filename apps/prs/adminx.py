# -*- coding: utf-8 -*-
__author__ = 'Aaron'

import xadmin
from import_export import resources, fields
from django.db.models import Count
import  re
from django.utils.safestring import mark_safe

from .models import *
from shop.models import ShopifyImage
from .choose_target import ChoosePage

import os

from django.conf import settings

@xadmin.sites.register(MyProduct)
class MyProductAdmin(object):
    list_display = [ ]
    # 'sku_name','img',

    search_fields = [ ]
    list_filter = [ ]
    list_editable = []
    readonly_fields = ()
    actions = []

    def save_models(self):
        obj = self.new_obj
        obj.staff = str(self.request.user)
        obj.created_time = datetime.now()

        obj.save()


class MyProductShopifyResource(resources.ModelResource):
    #product_no = fields.Field(attribute='product_no', column_name='product_no')
    #total_orders = fields.Field(attribute='total_orders', column_name='total_orders')
    #total_quantity = fields.Field(attribute='total_quantity', column_name='total_quantity')

    class Meta:
        model = MyProductShopify
        skip_unchanged = True
        report_skipped = True
        import_id_fields = ('product_no',)
        fields = ('product_no','handle','total_orders', 'total_quantity',"week_orders","week_quantity", )
        # exclude = ()

@xadmin.sites.register(MyProductShopify)
class MyProductShopifyAdmin(object):
    import_export_args = {"import_resource_class": MyProductShopifyResource,
                          "export_resource_class": MyProductShopifyResource}

    def show_resource(self, obj):

        resource = obj.resource_product.values_list('resource_target').annotate(Count('id'))
        #resource = str(resource)
        resource = re.split(r"\[|\]", str(resource))

        #return  re.split(r"\[|\]", resource)
        if len(resource)>1:

            return resource[1]
        else:
            return ''

    show_resource.short_description = "创意统计"

    def show_fb(self, obj):

        fb = obj.fb_product.values_list('obj_type','mypage__page').annotate(Count('id'))

        fb = re.split(r"\[|\]", str(fb))


        if len(fb) > 1:

            return fb[1]
        else:
            return ''

    show_fb.short_description = "接触点统计"

    def show_image(self, obj):

        try:
            #img = mark_safe('<img src="%s" width="100px" />' % (obj.logo.url,))

            img = mark_safe(
                '<a href="%s" target="view_window"><img src="%s" width="100px"></a>' % (
                    "https://www.yallavip.com/products/"+obj.handle,
                    ShopifyImage.objects.get(product_no=obj.product_no,position=1).src,
                    ))

        except Exception as e:
            img = ''
        return img

    show_image.short_description = "产品图"

    def show_link(self, obj):

        try:
            #img = mark_safe('<img src="%s" width="100px" />' % (obj.logo.url,))
            link = mark_safe(
                u'<a href="https://yallasale-com.myshopify.com/admin/products/%s" target="view_window">%s</a>' % (
                    obj.product_no,
                    str(obj.product_no)

                    ))
            '''
            return mark_safe(
                u'<a href="http://business.facebook.com%s" target="view_window">%s</a>' % (
                obj.conversation.link, u'会话'))
            '''


        except Exception as e:
            link = ''

        return link

    show_link.short_description = "管理产品"



    list_display = [ "handle","category_code", "show_image","obj_type", "week_orders","week_quantity","total_orders", 'total_quantity','show_resource','show_fb',]


    search_fields = ["handle",]
    list_filter = ["obj_type","category_code", ]
    list_editable = []
    readonly_fields = ("shopifyproduct",)
    ordering = ['-week_orders']
    actions = ["reset_count",]

    def reset_count(self, request, queryset):
        MyProductShopify.objects.all().update(total_orders=0,total_quantity=0,week_orders=0,week_quantity=0)
        return

    reset_count.short_description = "重置统计信息"


@xadmin.sites.register(MyProductAli)
class MyProductAliAdmin(object):
    list_display = [ "myproductcate",'vendor_no', 'url','listing',"created_time","staff","active",]

    # 'sku_name','img',

    search_fields = ["url","myproductcate", ]
    list_filter = ["myproductcate","created_time","staff", ]
    list_editable = ["active",]
    readonly_fields = ("vendor_no","created_time","staff",)
    actions = []

    def save_models(self):
        obj = self.new_obj
        obj.staff = str(self.request.user)
        obj.created_time = datetime.now()
        obj.vendor_no = obj.url.partition(".html")[0].rpartition("/")[1]

        obj.save()

'''
@xadmin.sites.register(MyProductAliShop)
class MyProductAliShopAdmin(object):
    list_display = ['vendor_nname', 'updated', 'url',]
    # 'sku_name','img',

    search_fields = ["vendor_nname","url","updated", ]
    list_filter = ["updated", ]
    list_editable = ["updated",]
    #readonly_fields = ("myproduct","vendor_no",)
    actions = []
'''

@xadmin.sites.register(MyProductResources)
class MyProductResourcesAdmin(object):
    def show_resource(self, obj):
        DEV = False
        if DEV:
            domain = "http://dev.yallavip.com:8000"
        else:
            domain = "http://admin.yallavip.com"
        resource = str(obj.resource)
        destination_url = domain + os.path.join(settings.MEDIA_URL, resource)
        try:
            img = mark_safe('<img src="%s" width="100px" />' % (destination_url))
        except Exception as e:
            img = ''
        return img

    show_resource.short_description = '创意图'

    list_display = ['myproduct','show_resource', "myproductali", 'name',"message", "resource_target","resource_cate","resource_type","created_time","staff", ]
    # 'sku_name','img',

    search_fields = ["myproduct","resource" ]
    list_filter = ["resource_target","resource_cate","resource_type" ,"created_time","staff", ]
    list_editable = []
    readonly_fields = ("created_time","staff", )
    actions = [ChoosePage,]

    def save_models(self):
        obj = self.new_obj
        obj.staff = str(self.request.user)
        obj.created_time = datetime.now()
        obj.save()


@xadmin.sites.register(MyProductPackage)
class MyProductPackageAdmin(object):
    list_display = [ "shopifyvariant","order_no",  ]


    search_fields = ["shopifyvariant","order_no" ,]
    list_filter = []
    list_editable = []
    readonly_fields = ("shopifyvariant",)
    actions = []


@xadmin.sites.register(MyProductFb)
class MyProductFbAdmin(object):
    def show_handle(self, obj):

        return obj.myproduct.handle

    show_handle.short_description = '货号'

    list_display = [ "mypage", "myresource", 'myproduct',"myphoto", 'myfeed',"myad","obj_type", ]
    # 'sku_name','img',

    search_fields = ["myproduct","myresource" ]
    list_filter = ["myproduct","obj_type","mypage"]
    list_editable = []
    readonly_fields = ("myphoto", 'myfeed',"myad",)
    actions = []



class MyProductCategoryResource(resources.ModelResource):


    class Meta:
        model = MyProductCategory
        skip_unchanged = True
        report_skipped = True
        import_id_fields = ('code',)
        fields = ('code','cate_1', 'cate_2', 'cate_3', 'album_name',)
        # exclude = ()

@xadmin.sites.register(MyProductCategory)
class MyProductCategoryAdmin(object):



    import_export_args = {"import_resource_class": MyProductCategoryResource, "export_resource_class": MyProductCategoryResource}

    list_display = [ 'code','cate_1', 'cate_2', 'cate_3', 'album_name',]


    search_fields = ["album_name",]
    list_filter = ['cate_1', 'cate_2', 'cate_3',]
    list_editable = []
    actions = []

