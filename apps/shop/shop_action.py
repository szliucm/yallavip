# 继承基本动作模板
from xadmin.plugins.actions import BaseActionView

from django.http import HttpResponse, HttpResponseRedirect
from django.template.context import RequestContext

from xadmin import views
from .models import *
# 自定义动作所需
from django import forms, VERSION as django_version
from django.core.exceptions import PermissionDenied
from django.db import router
from django.template.response import TemplateResponse
from django.utils.encoding import force_text
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext as _
from django.contrib.admin.utils import get_deleted_objects
from xadmin.util import model_ngettext
from xadmin.views.base import filter_hook
from shop.models import ProductCategory,ProductCategoryMypage
from fb.models import  MyPage,MyAlbum,MyPhoto



from facebook_business.api import FacebookAdsApi
from facebook_business.exceptions import FacebookRequestError
from facebook_business.adobjects.systemuser import SystemUser
from facebook_business.adobjects.page import Page
from facebook_business.adobjects.pagepost import PagePost
from facebook_business.adobjects.album import Album
from facebook_business.adobjects.photo import Photo
#from facebookads.adobjects.adimage import AdImage
from facebook_business.adobjects.adaccount import AdAccount
from facebook_business.adobjects.campaign import Campaign
from facebook_business.adobjects.adset import AdSet
from facebook_business.adobjects.ad import Ad
from facebook_business.adobjects.adsinsights import AdsInsights

import  random

import time
import datetime

from .photo_mark import  photo_mark


my_app_id = "562741177444068"
my_app_secret = "e6df363351fb5ce4b7f0080adad08a4d"
my_access_token = "EAAHZCz2P7ZAuQBABHO6LywLswkIwvScVqBP2eF5CrUt4wErhesp8fJUQVqRli9MxspKRYYA4JVihu7s5TL3LfyA0ZACBaKZAfZCMoFDx7Tc57DLWj38uwTopJH4aeDpLdYoEF4JVXHf5Ei06p7soWmpih8BBzadiPUAEM8Fw4DuW5q8ZAkSc07PrAX4pGZA4zbSU70ZCqLZAMTQZDZD"


my_app_id_dev = "1976935359278305"
my_app_secret_dev = "f4ee797596ed236c0bc74d33f52e6a54"
my_access_token_dev = "EAAcGAyHVbOEBAAL2mne8lmKC55lbDMndPYEVR2TRmOWf9ePUN97SiZCqwCd3KOZBrEkC57rVt3ZClhXi6oxxf1i0hRCK50QALuAQOCs60U30FjNYimeP97xLjfl7wZAAjThdkXPJujsWcAXOwkTNKvKlmP6tZBPUtSYb3i4i1vUs40MZAUOzNIG9v7HNjnyyIZD"

second_app_id = "437855903410360"
second_token = "EAAGOOkWV6LgBAIGWTMe3IRKJQNp5ld7nxmiafOdWwlPn8BksJxFUsCiAqzMQ1ZC1LJipR2tcHXZBO949i0ZB5xOOfHbut2hk7sIP3YZB5MfuqjFtm9LGq3J7xrBtUFPLZBT9pe2UcUTXann8DXhwMPQOlIBANiNJE6RA11vNrZC0fGijUsDJds"

import requests
import json

def get_token(target_page,token=None):


    url = "https://graph.facebook.com/v3.2/{}?fields=access_token".format(target_page)
    param = dict()
    if token is None:
        param["access_token"] = my_access_token
    else:
        param["access_token"] = token

    r = requests.get(url, param)

    data = json.loads(r.text)

    # print("request response is ", data["access_token"])
    return data["access_token"]
'''
def create_new_album(page_no , new_albums ):
    # 建相册要用开发账号

    adobjects = FacebookAdsApi.init(access_token=get_token(page_no, my_access_token_dev), debug=True)
    new_album_list = []
    #print("new_albums",new_albums )
    for new_album in new_albums:
        fields = ["created_time", "description", "id",
                  "name", "count", "updated_time", "link",
                  "likes.summary(true)", "comments.summary(true)"
                  ]
        params = {
                'name': new_album,
                'location': 'Riyadh Region, Saudi Arabia',
                #'privacy': 'everyone',
                'place': '111953658894021',
                'message':"Yallavip's most fashion "+ new_album,

                    }
        album = Page(page_no).create_album(
                                fields=fields,
                                params=params,
                            )
        #插入到待返回的相册列表中
        new_album_list.append(album.get("id"))
        #保存到数据库中
        obj, created = MyAlbum.objects.update_or_create(album_no=album["id"],
                                                        defaults={'page_no': page_no,
                                                                  'created_time': album["created_time"].split('+')[0],
                                                                  'updated_time': album["updated_time"].split('+')[0],

                                                                  'name': album["name"],
                                                                  'count': album["count"],
                                                                  'like_count': album["likes"]["summary"][
                                                                      "total_count"],
                                                                  'comment_count': album["comments"]["summary"][
                                                                      "total_count"],
                                                                  'link': album["link"],

                                                                  }
                                                        )



        #print("created albums ", album)
    return  new_album_list
'''

def post_photo_to_album(targer_page,album_no,product ):
    from django.db.models import Max
    # 检查产品是否已经在相册中了，如果不存在，就发布新图片
    #myphotos = MyPhoto.objects.filter(name=product.handle , album_no=album_no )

    page_no = targer_page.page_no
    myphotos = MyPhoto.objects.filter(name__icontains=product.handle, album_no=album_no)
    #print("args is  %s %s %s"%(page_no,album_no , product.handle ))
    if myphotos:
        print("photo exist")
        return False
    else:
        print("now we need to create new photos for %s"%(product.handle))


    adobjects = FacebookAdsApi.init(my_app_id, my_app_secret, access_token=get_token(page_no), debug=True)


    #print("product.product_no ", product.product_no)
    ori_images = ShopifyImage.objects.filter(product_no=product.product_no).order_by('position')
    if not ori_images :

        print("no image %s"%(product.product_no))
        return False

    ori_image = random.choice(ori_images)

    #print("position is ", ori_image.position)



    name = product.title + "  [" + product.handle+"]"
    options = ShopifyOptions.objects.filter(product_no=product.product_no).values()
    for option in options:
        name = name + "\n\n   " + option.get("name") + " : " + option.get("values")

    max_price = ShopifyVariant.objects.filter(product_no=product.product_no).aggregate(Max("price")).get("price__max")
    name = name + "\n\nPrice:  " + str(int(max_price)) + "SAR"

    #打标
    price1 = int(max_price)
    price2 = int(price1 *  random.uniform(2, 3))

    image, iamge_url = photo_mark(ori_image ,product,str(price1), str(price2),  targer_page, type="album" )
    if not image:
        print("打水印失败")
        return False

    #print("after photo mark", iamge_url)

    fields = ["id","name","created_time", "updated_time","picture","link",
                      "likes.summary(true)","comments.summary(true)"
    ]
    params = {
        "published": "true",

        "url": iamge_url,
        "name": name,
        "qn":product.handle

    }
    photo = Album(album_no).create_photo(
        fields=fields,
        params=params,
    )

    obj, created = MyPhoto.objects.update_or_create(photo_no=photo["id"],
                                                    defaults={
                                                            'page_no': page_no,
                                                                'album_no': album_no,
                                                              "product_no": product.product_no,
                                                                'listing_status':True,
                                                              'created_time':
                                                                  photo["created_time"],#.split('+')[0],
                                                              'updated_time':
                                                                  photo["updated_time"],#.split('+')[0],

                                                              'name': photo.get("name"),
                                                              'picture': photo["picture"],
                                                              'link': photo["link"],
                                                              'like_count': photo["likes"]["summary"]["total_count"],
                                                              'comment_count': photo["comments"]["summary"][
                                                                  "total_count"]

                                                              }
                                                    )
    obj, created = ShopifyProduct.objects.filter(product_no=product.product_no).update(

                                                        listing_status=True,

                                                    )

    #print("new_photo saved ", obj, created)
    return  True




ACTION_CHECKBOX_NAME = '_selected_action'
checkbox = forms.CheckboxInput({'class': 'action-select'}, lambda value: False)
#print(checkbox)

def action_checkbox(obj):
    return checkbox.render(ACTION_CHECKBOX_NAME, force_text(obj.pk))


action_checkbox.short_description = mark_safe(
    '<input type="checkbox" id="action-toggle" />')
action_checkbox.allow_tags = True
action_checkbox.allow_export = False
action_checkbox.is_column = False


class select_form(forms.Form, ):
    _selected_action = forms.CharField(widget=forms.MultipleHiddenInput)
    # album = forms.ModelChoiceField(queryset=myalbum, empty_label='请选择相册')
    datasrc = forms.ModelMultipleChoiceField(widget=forms.CheckboxSelectMultiple, queryset=None)

    def __init__(self, queryset,  *args, **kwargs):
        super(select_form, self).__init__(*args, **kwargs)

        self.fields["datasrc"].queryset = queryset

class Post_to_Album(BaseActionView):
    model_perm = 'change'
    icon = 'fa fa-times'

    ###############################################
    # 这个是执行函数名
    action_name = "Post_to_Album"
    # 这个是显示的名字
    description = "发布产品到相册"
    # 这是要选择的对象
    form_queryset = MyPage.objects.all()



    @filter_hook
    # 对数据的操作
    def do_models(self, queryset, form_selected):

        #print("start do something to the model ")
        #print("queryset is ", queryset)
        #print("form_selected is ", form_selected)
        # 需要进行的操作


        for page in form_selected:
            #主页的品类
            categories_list = []
            categories = page.category_page.all()
            for category in categories:
                #print("category", category)
                subcategories = ProductCategory.objects.filter(parent_category=category.productcategory.name)

                for subcategorie in subcategories:
                    #print("subcategorie", subcategorie)
                    categories_list.append(subcategorie.name)

            #print("categories_list", categories_list)
            #主页已有的相册

            album_list = []
            album_dict = {}
            albums = MyAlbum.objects.filter(page_no = page.page_no)
            for album in albums:
                album_list.append(album.name)
                album_dict[album.name] = album.album_no
            #print("主页已有相册",album_list )
            #print("主页已有相册", album_dict)

            #产品的tags
            for product in queryset:
                tmp_tags = product.tags.split(',')
                tags = [i.strip() for i in tmp_tags]
                #print("tags is ", tags)
                #print("type of product ", type(product), product)



                #目标相册
                #产品tag 和page的品类 交集就是目标相册
                target_albums = list((set(categories_list).union(set(tags)))^(set(categories_list)^set(tags)))
                #print("target_album is ", target_albums)

                #目标相册是否已经存在
                #目标相册和已有相册交集为空，就是不存在，需要新建相册
                #new_albums = list((set(album_list).union(set(target_albums))) ^ (set(album_list) ^ set(target_albums)))
                new_albums = list(set(target_albums) - set(album_list))
                #print("album ",new_albums )

                new_album_list =  create_new_album(page.page_no, new_albums)

                for target_album in target_albums:
                    new_album_list.append(album_dict.get(target_album))

                #把产品图片发到目标相册中去

                for new_album in new_album_list:
                    #print("new_album is ", new_album)
                    if new_album:
                        post_photo_to_album(page, new_album, product)


                    else:
                        print("album not exist")






        return

        ####################################################

    @filter_hook
    # 捕捉操作
    def do_action(self, queryset):
        form = select_form(self.form_queryset, self.request.POST)
        if form.is_valid():
            # print("form is ", form)
            form_selected = form.cleaned_data["datasrc"]
            # 执行动作
            self.do_models(queryset, form_selected)
            return HttpResponseRedirect(self.request.get_full_path())
        else:
            form = select_form(self.form_queryset, self.request.POST)

        context = self.get_context()
        context.update({
            'queryset': queryset,
            'form': form,
            "opts": self.opts,
            "app_label": self.app_label,
            "form_action": self.action_name,
            'action_checkbox_name': ACTION_CHECKBOX_NAME,
        })

        return TemplateResponse(self.request,
                                'select_form.html', context)


def download_smart_collections():
    # 获取店铺信息
    shop_name = "yallasale-com"
    shop_obj = Shop.objects.get(shop_name=shop_name)
    shop_url = "https://%s:%s@%s.myshopify.com" % (shop_obj.apikey, shop_obj.password, shop_obj.shop_name)

    # 删除所有可能重复的产品信息

    ShopSmartCollection.objects.all().delete()

    # 获取新产品信息
    url = shop_url + "/admin/smart_collections/count.json"
    params = {
    }
    # print("url %s params %s"%(url, params))
    r = requests.get(url, params)
    data = json.loads(r.text)

    print("smart collection count is ", data["count"])

    total_count = data["count"]

    # 更新信息到系统数据库
    i = 0
    limit = 200

    while True:
        try:

            if (i * limit > total_count):
                break

            i = i + 1

            # products = shopify.Product.find(page=i,limit=limit,updated_at_min=shop.updated_time)
            url = shop_url + "/admin/smart_collections.json"
            params = {
                "page": i,
                "limit": limit,
                "fields": "id,title",

            }
            print(("params is ", params))

            r = requests.get(url, params)
            collections = json.loads(r.text)["smart_collections"]
            for collection in collections:
                print (collection["id"], collection["title"])
                obj, created = ShopSmartCollection.objects.update_or_create(collection_id=collection["id"],
                                                           defaults={'title': collection["title"],

                                                                     }
                                                           )



        except KeyError:
            print("smart_collections for the shop {} completed".format(shop))
            break










