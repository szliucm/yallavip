# -*- coding: utf-8 -*-
__author__ = 'bobby'

import traceback

import numpy as np, re
import xadmin
from xadmin.layout import Main, Side, Fieldset, Row, AppendedText
from django.shortcuts import get_object_or_404, get_list_or_404, render
from import_export import resources, fields
from import_export.widgets import ForeignKeyWidget
from .models import Shop,ShopifyProduct,ShopifyVariant,ShopifyImage, ShopifyCustomer,ShopifyAddress
import  shopify
import requests
import json


from django.db import models

import datetime
import urllib
import random
from django.db.models import Q
from django.utils.safestring import mark_safe
from django import forms
from django.contrib import admin, messages
from django.http import HttpResponseRedirect
from django.template import RequestContext
from xadmin.filters import manager as filter_manager, FILTER_PREFIX, SEARCH_VAR, DateFieldListFilter, \
    RelatedFieldSearchFilter
from django.utils.html import format_html



@xadmin.sites.register(Shop)
class ShopAdmin(object):

    list_display = [ 'shop_name','apikey','password',"product_updated_time","customer_updated_time" ]
     #'sku_name','img',

    search_fields = ["shop_name",]
    #list_filter = ['supply_status','update_time' ]
    #list_editable = ["supply_status"]
    actions = ['download_product','download_customer','create_product',]

    def create_product(self, request, queryset):
        for shop in queryset:
            shop_obj = Shop.objects.get(shop_name=shop.shop_name)
            shop_url = "https://%s:%s@%s.myshopify.com" % (shop_obj.apikey, shop_obj.password, shop_obj.shop_name)

            shopify.ShopifyResource.set_site(shop_url)

            # Get the current shop
            shop = shopify.Shop.current()

            print("shop is ", shop)

            # Get a specific product
            # product = shopify.Product.find(179761209)

            # Create a new product

            url = shop_url + "/admin/products.json"
            params = {
                "product": {
                    "title": "Burton Custom Freestyle 151",
                    "body_html": "<strong>Good snowboard!</strong>",
                    "vendor": "Burton",
                    "product_type": "Snowboard",
                    "images": [
                        {
                            "src": "https://nodei.co/npm/shopify-node-api.png?downloads=true&downloadRank=true&stars=true"
                        }
                    ]
                  }
            }
            headers = {
                "Content-Type": "application/json",
                "charset": "utf-8",

            }
            r = requests.post(url, headers=headers, data = json.dumps(params))
            data = json.loads(r.text)

            print("product  is ", data["product"]["id"])

            '''
            new_product = shopify.Product()
            new_product.title = "Burton Custom Freestyle 151"
            new_product.id
            success = new_product.save()  # returns false if the record is invalid
            # or
            if new_product.errors:
                # something went wrong, see new_product.errors.full_messages() for example
                print(new_product.errors.full_messages())
            '''
            shopify.ShopifyResource.clear_session()


    create_product.short_description = "发布产品"

    def download_product(self, request, queryset):
        # 定义actions函数
        for shop in queryset:

            shop_obj = Shop.objects.get(shop_name=shop.shop_name)
            now = datetime.datetime.now()+datetime.timedelta(hours=-4)

            shop_url = "https://%s:%s@%s.myshopify.com" % (shop_obj.apikey, shop_obj.password,shop_obj.shop_name)
            #shop_url = "https://12222a833afcad263c5cc593eca7af10:47aea3fe8f4b9430b1bac56c886c9bae@yallasale-com.myshopify.com/admin"
            #shopify.ShopifyResource.set_site(shop_url)


            url = shop_url + "/admin/products/count.json"
            params = {
                #"updated_at_min": shop.product_updated_time
            }

            r = requests.get(url, params)
            data = json.loads(r.text)

            print("product count is ",data["count"])

            total_count = data["count"]

            i=0
            limit = 100
            product_list = []
            variant_list = []
            image_list = []
            while True:
                try:

                    if(i*limit > total_count):
                        break

                    i = i + 1
                    print("page is ", i)
                    #products = shopify.Product.find(page=i,limit=limit,updated_at_min=shop.updated_time)
                    url = shop_url + "/admin/products.json"
                    params = {
                        "page":i,
                        "limit":limit,
                        #"updated_at_min": shop.product_updated_time,
                        "field" : "product_id,handle,created_at,published_at,updated_attags,vendor",
                    }


                    r = requests.get(url, params)
                    products = json.loads(r.text)["products"]
                    #print("range(len(products)", range(len(products)))

                    for j in range(len(products)):
                        row =  products[j]
                        print("row is ",row)

                        product = ShopifyProduct(
                            shop_name = shop.shop_name,
                            product_no=row["id"],
                            handle=row["handle"],
                            created_at=row["created_at"].split('+')[0],
                            #published_at=row["published_at"].split('+')[0],
                            updated_at=row["updated_at"].split('+')[0],
                            tags=row["tags"],
                            vendor=row["vendor"],


                        )
                        product_list.append(product)


                        try:

                            for j in range(len(row["variants"])):
                                variant_row = row["variants"][j]

                                variant = ShopifyVariant(
                                    variant_no=variant_row["id"],
                                    product_no=variant_row["product_id"],
                                    created_at=variant_row["created_at"].split('+')[0],
                                    updated_at=variant_row["updated_at"].split('+')[0],
                                    sku=variant_row["sku"],
                                    image_no=variant_row["image_id"],
                                    title=variant_row["title"],
                                    price=variant_row["price"],
                                    option1=variant_row["option1"],
                                    option2=variant_row["option2"],
                                    option3=variant_row["option3"],

                                )
                                variant_list.append(variant)
                                #print(" variant_list  is ", variant_list)
                        except KeyError:
                            print("no variant ".format(row.shop_name))
                            break

                        try:

                            for k in range(len(row["images"])):
                                image_row = row["images"][k]

                                image = ShopifyImage(
                                    image_no=image_row["id"],
                                    product_no=image_row["product_id"],
                                    created_at=image_row["created_at"].split('+')[0],
                                    updated_at=image_row["updated_at"].split('+')[0],
                                    position=image_row["position"],
                                    width=image_row["width"],
                                    height=image_row["height"],
                                    src=image_row["src"],


                                )
                                image_list.append(image)
                                #print(" variant_list  is ", variant_list)
                        except KeyError:
                            print("no image ".format(row.shop_name))
                            break


                except KeyError:
                    print("products for the shop {} completed".format(row.shop_name))
                    break

            ShopifyProduct.objects.bulk_create(product_list)
            ShopifyVariant.objects.bulk_create(variant_list)
            ShopifyImage.objects.bulk_create(image_list)
            Shop.objects.filter(shop_name=shop.shop_name).update(product_updated_time=now)

        #shopify.ShopifyResource.clear_session()

    download_product.short_description = "下载产品"

    def download_customer(self, request, queryset):
        # 定义actions函数
        for shop in queryset:

            shop_obj = Shop.objects.get(shop_name=shop.shop_name)
            now = datetime.datetime.now()+datetime.timedelta(hours=-4)

            shop_url = "https://%s:%s@%s.myshopify.com" % (shop_obj.apikey, shop_obj.password,shop_obj.shop_name)
            #shop_url = "https://12222a833afcad263c5cc593eca7af10:47aea3fe8f4b9430b1bac56c886c9bae@yallasale-com.myshopify.com/admin"
            #shopify.ShopifyResource.set_site(shop_url)


            url = shop_url + "/admin/customers/count.json"
            params = {
                "updated_at_min": shop.customer_updated_time
            }

            r = requests.get(url, params)
            data = json.loads(r.text)

            print("customers count is ",data["count"])
            #total_count = data["count"]
            #total_count = data["count"]
            total_count = 10
            i=0
            limit = 100
            customer_list = []
            while True:
                try:

                    if(i*limit > total_count):
                        break

                    i = i + 1
                    print("page is ", i)

                    url = shop_url + "/admin/customers.json"
                    params = {
                        "page":i,
                        "limit":limit,
                        #debug "updated_at_min": shop.customer_updated_time,
                        #"field" : "",
                    }


                    r = requests.get(url, params)
                    customers = json.loads(r.text)["customers"]
                    #print("customers", customers)

                    for j in range(len(customers)):
                        row =  customers[j]

                        customer = ShopifyCustomer(
                            shop_name=shop.shop_name,
                            customer_no=row["id"],
                            email=row["email"],
                            accepts_marketing=row["accepts_marketing"],
                            created_at=row["created_at"].split('+')[0],
                            updated_at=row["updated_at"].split('+')[0],
                            first_name=row["first_name"],

                            last_name=row["last_name"],
                            orders_count=row["orders_count"],
                            state=row["state"],
                            total_spent=row["total_spent"],


                            note=row["note"],
                            verified_email=row["verified_email"],
                            #multipass_noentifier=row["multipass_noentifier"],
                            tax_exempt=row["tax_exempt"],
                            phone=row["phone"],
                            tags=row["tags"],
                            #last_order_no=row["last_order_no"],
                            #last_order_name=row["last_order_name"],


                        )
                        print("customer is ", customer.first_name)

                        customer_list.append(customer)



                        addresses = row["addresses"]

                        address_list = []
                        for k in range(len(addresses)):
                            row_address = addresses[k]
                            address = ShopifyAddress(
                                address_no=row_address["id"],
                                customer_no=row_address["customer_id"],
                                first_name=row_address["first_name"],
                                last_name=row_address["last_name"],
                                company=row_address["company"],

                                address1=row_address["address1"],
                                address2=row_address["address2"],
                                city=row_address["city"],
                                province=row_address["province"],

                                country=row_address["country"],
                                zip=row_address["zip"],
                                # multipass_noentifier=row["multipass_noentifier"],
                                phone=row_address["phone"],

                                name=row_address["name"],
                                province_code=row_address["province_code"],
                                country_code=row_address["country_code"],
                                country_name=row_address["country_name"],
                                default=row_address["default"],

                            )

                            address_list.append(address)

                        ShopifyAddress.objects.bulk_create(address_list)


                        #for variant in product.variants:
                         #   print(" variant  is ", variant.sku)

                except KeyError as e:
                    print('traceback.print_exc():', traceback.print_exc())
                    print("customers for the shop {} completed".format(shop.shop_name))
                    break


            ShopifyCustomer.objects.bulk_create(customer_list)

            Shop.objects.filter(shop_name=shop.shop_name).update(customer_updated_time=now)



    download_customer.short_description = "下载客户信息"

'''
class ImageInline(object):
    model = ShopifyImage
    extra = 1
    #style = 'tab'
    form_layout = (
            Main(
                Fieldset('',
                        Row( 'image_no', 'src'),
                         ),

            )
        )


class VariantInline(object):
    model = ShopifyVariant
    extra = 1
    #style = 'tab'
    form_layout = (
            Main(
                Fieldset('',
                        Row( 'sku', 'title'),
                         ),
                
            )
        )
    inlines=[ImageInline, ]
'''
@xadmin.sites.register(ShopifyProduct)
class ShopifyProductAdmin(object):

    list_display = ['shop_name',  'product_no','handle','created_at', "updated_at"]
     #'sku_name','img',

    search_fields = ["handle",]
    #list_filter = ['supply_status','update_time' ]
    #list_editable = ["supply_status"]
    actions = ["create_product",]
    #inlines = [VariantInline, ]
    ordering = ['-created_at']


class AddressInline(object):
    model = ShopifyAddress
    extra = 1
    #style = 'tab'
    form_layout = (
        Main(
            Fieldset('customer',
                    Row( 'address_no', 'address1'),
                     ),
        )
    )
@xadmin.sites.register(ShopifyCustomer)
class ShopifyCustomerAdmin(object):

    list_display = [ 'shop_name', 'customer_no','first_name','last_name',"created_at", "updated_at"]
     #'sku_name','img',

    search_fields = ['customer_no', 'first_name','last_name',]
    #list_filter = ['supply_status','update_time' ]
    #list_editable = ["supply_status"]
    actions = []

    form_layout = (
        Main(
            Fieldset('customer_no',
                    Row( 'first_name', 'last_name'),
                     ),

            Fieldset('created_at',
                     'updated_at',

                    # Row(AppendedText('file_size', 'MB'), 'author'),
                    # 'content'
                     ),
        ),
        Side(
            Fieldset('最近订单',
                     'last_order_no', 'last_order_name'
                     ),
        )
    )

    inlines = [AddressInline, ]

@xadmin.sites.register(ShopifyAddress)
class ShopifyAddressAdmin(object):

    list_display = [ 'customer_no','address_no',]
     #'sku_name','img',

    search_fields = ['customer_no','address_no',]
    #list_filter = ['supply_status','update_time' ]
    #list_editable = ["supply_status"]
    actions = []

    form_layout = (
        Main(
            Fieldset('客户',
                     'customer',
                     ),

            Fieldset('地址',
                     'address1',

                     # Row(AppendedText('file_size', 'MB'), 'author'),
                     # 'content'
                     ),
        ),
        Side(
            Fieldset('联系方式',
                     'phone',                     ),
        )
    )
