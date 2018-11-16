# -*- coding: utf-8 -*-
__author__ = 'bobby'
from xadmin.views import BaseAdminPlugin, ListAdminView

from facebook_business.api import FacebookAdsApi
from facebook_business.exceptions import FacebookRequestError
from facebook_business.adobjects.systemuser import SystemUser
from facebook_business.adobjects.page import Page
from facebook_business.adobjects.pagepost import PagePost
from facebook_business.adobjects.album import Album
from facebook_business.adobjects.photo import Photo
from facebook_business.adobjects.adaccount import AdAccount
from facebook_business.adobjects.campaign import Campaign
from facebook_business.adobjects.adset import AdSet
from facebook_business.adobjects.ad import Ad
from facebook_business.adobjects.adsinsights import AdsInsights


import traceback

import numpy as np, re
import xadmin
from xadmin.layout import Main, Side, Fieldset, Row, AppendedText
from django.shortcuts import get_object_or_404, get_list_or_404, render
from import_export import resources, fields
from import_export.widgets import ForeignKeyWidget
from .models import Shop,ShopifyProduct,ShopifyVariant,ShopifyImage,ShopifyOptions, ShopifyCustomer,ShopifyAddress
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
import random
DEBUG = False

my_app_id = "562741177444068"
my_app_secret = "e6df363351fb5ce4b7f0080adad08a4d"
my_access_token = "EAAHZCz2P7ZAuQBABHO6LywLswkIwvScVqBP2eF5CrUt4wErhesp8fJUQVqRli9MxspKRYYA4JVihu7s5TL3LfyA0ZACBaKZAfZCMoFDx7Tc57DLWj38uwTopJH4aeDpLdYoEF4JVXHf5Ei06p7soWmpih8BBzadiPUAEM8Fw4DuW5q8ZAkSc07PrAX4pGZA4zbSU70ZCqLZAMTQZDZD"
def get_token(target_page):

    url = "https://graph.facebook.com/v3.2/{}?fields=access_token".format(target_page)
    param = dict()
    param["access_token"] = my_access_token

    r = requests.get(url, param)

    data = json.loads(r.text)

    #print("request response is ", data["access_token"])
    return data["access_token"]


def insert_product( shop_name, products):


    for j in range(len(products)):
        product_list = []
        variant_list = []
        image_list = []
        option_list = []

        row = products[j]

        if j == 1:
            print("row is ", row)

        product = ShopifyProduct(
            shop_name= shop_name,
            product_no=row["id"],
            handle=row["handle"],
            body_html=row["body_html"],
            title=row["title"],
            created_at=row["created_at"].split('+')[0],

            updated_at=row["updated_at"].split('+')[0],
            tags=row["tags"],
            vendor=row["vendor"],
            product_type=row["product_type"],

        )
        product_list.append(product)

        try:

            for k in range(len(row["variants"])):
                variant_row = row["variants"][k]

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

        except KeyError:
            print("no variant ".format(row.shop_name))
            break

        try:

            for m in range(len(row["images"])):
                image_row = row["images"][m]

                image = ShopifyImage(
                    image_no=image_row["id"],
                    product_no=image_row["product_id"],
                    created_at=image_row["created_at"].split('+')[0],
                    updated_at=image_row["updated_at"].split('+')[0],
                    position=image_row["position"],
                    width=image_row["width"],
                    height=image_row["height"],
                    src=image_row["src"],
                    # variant_ids

                )
                image_list.append(image)
                # print(" variant_list  is ", variant_list)
        except KeyError:
            print("no image ".format(row.shop_name))
            break

        try:

            for n in range(len(row["options"])):
                option_row = row["options"][n]
                values = ','.join(option_row["values"])

                # print(" %s length of values %s "%(option_row["product_id"], len(values)))

                option = ShopifyOptions(
                    product_no=option_row["product_id"],
                    name=option_row["name"],

                    values=values
                )

                option_list.append(option)
                # print(" variant_list  is ", variant_list)
        except KeyError:
            print("no option ".format(row.shop_name))
            break

        # print(product_list)

        ShopifyProduct.objects.bulk_create(product_list)
        ShopifyVariant.objects.bulk_create(variant_list)
        ShopifyImage.objects.bulk_create(image_list)
        ShopifyOptions.objects.bulk_create(option_list)




@xadmin.sites.register(Shop)
class ShopAdmin(object):

    list_display = [ 'shop_name','apikey','password',"product_updated_time","customer_updated_time" ]
     #'sku_name','img',

    search_fields = ["shop_name",]
    #list_filter = ['supply_status','update_time' ]
    #list_editable = ["supply_status"]
    actions = ['download_product','download_customer',]




    def download_product(self, request, queryset):
        # 定义actions函数


        for shop in queryset:

            shop_obj = Shop.objects.get(shop_name=shop.shop_name)
            if DEBUG:
                max_product_no = "1774563229738"
            else:

                product = ShopifyProduct.objects.filter(shop_name = shop.shop_name ).order_by('product_no').last()
                if product is None:
                    max_product_no = "0"
                else:
                    max_product_no = product.product_no



            shop_url = "https://%s:%s@%s.myshopify.com" % (shop_obj.apikey, shop_obj.password,shop_obj.shop_name)
            #shop_url = "https://12222a833afcad263c5cc593eca7af10:47aea3fe8f4b9430b1bac56c886c9bae@yallasale-com.myshopify.com/admin"
            #shopify.ShopifyResource.set_site(shop_url)



            url = shop_url + "/admin/products/count.json"
            params = {
                "since_id":  max_product_no
            }
            #print("url %s params %s"%(url, params))
            r = requests.get(url, params)
            data = json.loads(r.text)

            if DEBUG:
                print("product count is ",data["count"])

            total_count = data["count"]

            i=0
            limit = 100

            while True:
                try:

                    if(i*limit > total_count):
                        break

                    i = i + 1


                    if DEBUG and i > 1 :
                        print("i %s max_product_no %s"%(i, max_product_no))


                        break


                    #products = shopify.Product.find(page=i,limit=limit,updated_at_min=shop.updated_time)
                    url = shop_url + "/admin/products.json"
                    params = {
                        "page":i,
                        "limit":limit,
                        "since_id":  max_product_no,
                        "fields" : "id,handle,body_html,title,product_type,created_at,published_at,"
                                   "updated_at,tags,vendor,variants,images,options",
                        #"fields": "product_id",
                    }
                    #print(("params is ", params))

                    r = requests.get(url, params)
                    products = json.loads(r.text)["products"]
                    #print("range(len(products)", range(len(products)))
                    '''
                    for j in range(len(products)):
                        product_list = []
                        variant_list = []
                        image_list = []
                        option_list = []

                        row =  products[j]

                        if j==1:
                            print("row is ",row)


                        product = ShopifyProduct(
                            shop_name = shop.shop_name,
                            product_no=row["id"],
                            handle=row["handle"],
                            body_html=row["body_html"],
                            title=row["title"],
                            created_at=row["created_at"].split('+')[0],

                            updated_at=row["updated_at"].split('+')[0],
                            tags=row["tags"],
                            vendor=row["vendor"],
                            product_type=row["product_type"],


                        )
                        product_list.append(product)


                        try:

                            for k in range(len(row["variants"])):
                                variant_row = row["variants"][k]

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

                        except KeyError:
                            print("no variant ".format(row.shop_name))
                            break

                        try:

                            for m in range(len(row["images"])):
                                image_row = row["images"][m]

                                image = ShopifyImage(
                                    image_no=image_row["id"],
                                    product_no=image_row["product_id"],
                                    created_at=image_row["created_at"].split('+')[0],
                                    updated_at=image_row["updated_at"].split('+')[0],
                                    position=image_row["position"],
                                    width=image_row["width"],
                                    height=image_row["height"],
                                    src=image_row["src"],
                                    #variant_ids

                                )
                                image_list.append(image)
                                #print(" variant_list  is ", variant_list)
                        except KeyError:
                            print("no image ".format(row.shop_name))
                            break

                        try:

                            for n in range(len(row["options"])):
                                option_row = row["options"][n]
                                values = ','.join(option_row["values"])

                                #print(" %s length of values %s "%(option_row["product_id"], len(values)))

                                option = ShopifyOptions(
                                    product_no = option_row["product_id"],
                                    name=option_row["name"],

                                    values = values
                                )

                                option_list.append(option)
                                #print(" variant_list  is ", variant_list)
                        except KeyError:
                            print("no option ".format(row.shop_name))
                            break

                        #print(product_list)

                        ShopifyProduct.objects.bulk_create(product_list)
                        ShopifyVariant.objects.bulk_create(variant_list)
                        ShopifyImage.objects.bulk_create(image_list)
                        ShopifyOptions.objects.bulk_create(option_list)
                '''
                    insert_product(shop.shop_name, products)


                except KeyError:
                    print("products for the shop {} completed".format(shop.shop_name))
                    break


            #Shop.objects.filter(shop_name=shop.shop_name).update(product_updated_time=now)

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

    list_display = ['shop_name',  'product_no','handle','created_at', "updated_at","listed","title"]
     #'sku_name','img',

    search_fields = ["handle","product_no"]
    list_filter = ['shop_name','listed',"created_at", ]
    #list_editable = ["supply_status"]
    actions = ["create_product","post_product","post_photo"]
    #inlines = [VariantInline, ]
    ordering = ['-product_no']


    def create_product(self, request, queryset):
        dest_shop = "yallasale-com"

        handle_init = ShopifyProduct.objects.filter(shop_name = dest_shop ).order_by('-product_no').first()

        handle_i = handle_init.handle

        handle_i = int(handle_i[1:])


        print(" now let's start create_product ", handle_i)


        for product in queryset:
            handle_i = handle_i+1
            handle_new = "A" + str(handle_i)

            shop_obj = Shop.objects.get(shop_name=dest_shop)
            #初始化SDK
            shop_url = "https://%s:%s@%s.myshopify.com" % (shop_obj.apikey, shop_obj.password, shop_obj.shop_name)
            #shopify.ShopifyResource.set_site(shop_url)

            # Get the current shop
            #shop = shopify.Shop.current()
            # Get a specific product
            # product = shopify.Product.find(179761209)

            # Create a new product

            url = shop_url + "/admin/products.json"

            imgs_list = []

            imgs = ShopifyImage.objects.filter(product_no=product.product_no).values('image_no','src').order_by('position')


            for img in imgs:

                image = {
                    "src": img["src"],
                    "image_no": img["image_no"]
                         }
                imgs_list.append(image)
            '''
            option_list = []

            options = ShopifyOptions.objects.filter(product_no=product.product_no).values('name', 'values')
            for row in options:
                option = {
                    "name": row["name"],
                    "values": re.split('[.]', row["values"])
                }
                option_list.append(option)

            #变体
            variants_list = []

            variants = ShopifyVariant.objects.filter(product_no=product.product_no).values()

            for variant in variants:
                #old_image_no = variant.get("image_no")
                #new_image_no = image_dict[old_image_no]
                #print("image dict  %s %s " % (old_image_no, new_image_no))

                sku = "A" + str(handle_i)
                option1 = variant.get("option1")
                option2 = variant.get("option2")
                option3 = variant.get("option3")

                if option1:
                    sku = sku + "-" + option1.replace("&", '').replace('-', '').replace('.', '').replace(' ', '')
                    if option2:
                        sku = sku + "_" + option2.replace("&", '').replace('-', '').replace('.', '').replace(' ', '')
                        if option3:
                            sku = sku + "_" + option3.replace("&", '').replace('-', '').replace('.', '').replace(' ',
                                                                                                                 '')

                variant_item = {
                    "option1": option1,
                    "option2": option2,
                    "option3": option3,
                    "price": int(float(variant.get("price")) * 3),
                    "compare_at_price": int(float(variant.get("price")) * 3 * random.uniform(2, 3)),
                    "sku": sku,
                    "position": variant.get("position"),
                    #"image_id": new_image_no,
                    "grams": variant.get("grams"),
                    "title": variant.get("title"),
                    "taxable": "true",
                    "inventory_management": "shopify",
                    "fulfillment_service": "manual",
                    "inventory_policy": "continue",

                    "inventory_quantity": 10000,
                    "requires_shipping": "true",
                    "weight": 0.5,
                    "weight_unit": "kg",

                }
                # print("variant_item", variant_item)
                variants_list.append(variant_item)

            print("variants_list is ", len(variants_list))
            '''

            params = {
                "product": {
                    "handle": handle_new,
                    "title": product.title,
                    "body_html": product.body_html,
                    "vendor": product.vendor,
                    "product_type":product.product_type,
                    "tags": product.tags,
                    "images": imgs_list,
                    #"variants": variants_list,
                    #"options": option_list
                  }
            }
            headers = {
                "Content-Type": "application/json",
                "charset": "utf-8",

            }

            r = requests.post(url, headers=headers, data = json.dumps(params))
            data = json.loads(r.text)
            new_product = data.get("product")
            if new_product is None:
                print("data is ", data)
                continue

            new_product_no = new_product.get("id")



            #增加变体

            #image
            image_dict = {}
            for k_img in range(len(new_product["images"])):
                image_row = new_product["images"][k_img]
                new_image_no = image_row["id"]
                #new_image_list.append(image_no)
                old_image_no = imgs_list[k_img]["image_no"]

                image_dict[old_image_no] = new_image_no
                #print("old image %s new image %s"%(old_image_no, new_image_no ))

            #option
            option_list = []

            options = ShopifyOptions.objects.filter(product_no=product.product_no).values('name', 'values')
            for row in options:
                option = {
                    "name": row["name"],
                    "values": re.split('[.]', row["values"])
                }
                option_list.append(option)

            #variant
            variants_list = []

            variants = ShopifyVariant.objects.filter(product_no=product.product_no).values()

            for variant in variants:
                old_image_no = variant.get("image_no")
                new_image_no = image_dict.get(old_image_no)
                print("image dict  %s %s "%(old_image_no, new_image_no)  )



                sku = handle_new
                option1 = variant.get("option1")
                option2 = variant.get("option2")
                option3 = variant.get("option3")

                if option1 :
                    sku = sku + "-" + option1.replace("&",'').replace('-','').replace('.','').replace(' ','')
                    if option2:
                        sku = sku + "_" + option2.replace("&",'').replace('-','').replace('.','').replace(' ','')
                        if option3:
                            sku = sku + "_" + option3.replace("&",'').replace('-','').replace('.','').replace(' ','')



                variant_item = {
                    "option1": option1,
                    "option2": option2,
                    "option3": option3,
                    "price": int (float(variant.get("price"))*2.8),
                    "compare_at_price": int (float(variant.get("price"))*2.8 *random.uniform(2,3)),
                    "sku": sku,
                    "position": variant.get("position"),
                    "image_id": new_image_no,
                    "grams": variant.get("grams"),
                    "title": variant.get("title"),
                    "taxable": "true",
                    "inventory_management": "shopify",
                    "fulfillment_service": "manual",
                    "inventory_policy": "continue",

                    "inventory_quantity": 10000,
                    "requires_shipping": "true",
                    "weight": 0.5,
                    "weight_unit": "kg",

                }
                #print("variant_item", variant_item)
                variants_list.append(variant_item)

            params = {
                "product": {
                    "variants": variants_list,
                    "options": option_list,

                }
            }
            headers = {
                "Content-Type": "application/json",
                "charset": "utf-8",

            }

            #print("upload data is ",json.dumps(params))

            url = shop_url + "/admin/products/%s.json"%(new_product_no)
            r = requests.put(url, headers=headers, data=json.dumps(params))
            data = json.loads(r.text)
            
            new_product = data.get("product")
            if new_product is None:
                print("data is ", data)
                continue

            product_list = []
            product_list.append(new_product)
            insert_product(dest_shop, product_list)

            print("new_product_no is", new_product.get("id"))



            #shopify.ShopifyResource.clear_session()

        queryset.update(listed=True, )

    create_product.short_description = "发布到主店铺"

    def post_product(self, request, queryset):

        for product in queryset:
            imgs = ShopifyImage.objects.filter(product_no=product.product_no).values( 'src').\
                                    order_by( 'position').first()
            if imgs is None:
                print("no image")
                continue
            image = imgs.get("src")

            print("type of %s is  %s %s" % (imgs, type(imgs), image))

            # 发图片post
            page_id = "358078964734730"
            token = get_token(page_id)
            FacebookAdsApi.init(access_token=token)
            fields = [
            ]
            params = {
                'url': image,
                'published': 'false',
            }
            photo_to_be_post = Page(page_id).create_photo(
                fields=fields,
                params=params,
            )
            photo_to_be_post_id = photo_to_be_post.get_id()
            fields = [
                'object_id',
            ]
            params = {
                'message': 'I have something good for you!',
                'attached_media': [{'media_fbid': photo_to_be_post_id}],
            }
            feed_post_with_image = Page(page_id).create_feed(
                fields=fields,
                params=params,
            )
            feed_post_with_image_id = feed_post_with_image.get_id()
            '''
            fields = [
            ]
            params = {
            }
            PagePost(feed_post_with_image_id).api_delete(
                fields=fields,
                params=params,
            )
            '''
            print("Wow ",feed_post_with_image_id )


    post_product.short_description = "发布到facebook"

    def post_photo(self, request, queryset):
        page_id = "358078964734730"
        album_no = "364220710787222"
        token = get_token(page_id)
        #token = "EAAHZCz2P7ZAuQBAE9FEXmxUZCmISP6of8BCpvHYcgbicLOFAZAZB014FZARgDfxvx5AKRbPFSMqlzllrDHAFOtbty8x9eSzKJqbD5CAVRHJdH4kejAyv1B4MYDnwW9Qr5ZCwYG6q8Gk7Ok3ZBpfZC5OoovyjZCwaqebeVoXrXeGFkrk8ifZC9hyWX7cZCIqkopgZCIketETbWEqs4u4rGxbgsXttQJ0AF9iiQpoAZD"

        adobjects = FacebookAdsApi.init(my_app_id, my_app_secret,access_token=token, debug=True)

        for product in queryset:
            imgs = ShopifyImage.objects.filter(product_no=product.product_no).values('src'). \
                order_by('position').first()
            if imgs is None:
                print("no image")
                continue
            image = imgs.get("src")

            print("type of %s is  %s %s" % (imgs, type(imgs), image))


            fields = [
                      ]
            params = {
                "url": image,
            }
            photos = Album(album_no).create_photo(
                fields=fields,
                params=params,
            )

            print("photos is ", photos)
    post_photo.short_description = "发布到相册"

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

