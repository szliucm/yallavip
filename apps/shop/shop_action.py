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
from product.models import ProductCategory,ProductCategoryMypage
from fb.models import  MyPage



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

my_app_id = "562741177444068"
my_app_secret = "e6df363351fb5ce4b7f0080adad08a4d"
my_access_token = "EAAHZCz2P7ZAuQBABHO6LywLswkIwvScVqBP2eF5CrUt4wErhesp8fJUQVqRli9MxspKRYYA4JVihu7s5TL3LfyA0ZACBaKZAfZCMoFDx7Tc57DLWj38uwTopJH4aeDpLdYoEF4JVXHf5Ei06p7soWmpih8BBzadiPUAEM8Fw4DuW5q8ZAkSc07PrAX4pGZA4zbSU70ZCqLZAMTQZDZD"


import requests
import json

def get_token(target_page):
    url = "https://graph.facebook.com/v3.2/{}?fields=access_token".format(target_page)
    param = dict()
    param["access_token"] = my_access_token

    r = requests.get(url, param)

    data = json.loads(r.text)

    # print("request response is ", data["access_token"])
    return data["access_token"]

def create_new_album(page_no , new_album ):
    fields = [
                          ]
    params = {
            'name': new_album,
            'location': 'Riyadh Region, Saudi Arabia',
            'privacy': 'everyone',
            'place': '111953658894021',
            'message':"Yallavip most fashion"+ new_album,

                }
    albums = Page(page_no).get_albums(
                            fields=fields,
                            params=params,
                        )

ACTION_CHECKBOX_NAME = '_selected_action'
checkbox = forms.CheckboxInput({'class': 'action-select'}, lambda value: False)
print(checkbox)

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

        print("start do something to the model ")
        #print("queryset is ", queryset)
        #print("form_selected is ", form_selected)
        # 需要进行的操作


        for page in form_selected:
            #主页的品类
            categories_list = []
            categories = page.category_page.all()
            for category in categories:
                subcategories = ProductCategory.objects.filter(parent_category=category.productcategory.name)
                for subcategorie in subcategories:
                    categories_list.append(subcategorie.name)

            #主页已有的相册
            album_list = []
            albums = page.MyAlbum.filter(page_no = page.page_no)
            for album in albums:
                album_list.append(album.name)


            #产品的tags
            for product in queryset:
                tmp_tags = product.tags.split(',')
                tags = [i.strip() for i in tmp_tags]

                #print("categories_list", categories_list)
                #print("tags is ", tags)

                #目标相册
                #产品tag 和page的品类 交集就是目标相册
                target_albums = list((set(categories_list).union(set(tags)))^(set(categories_list)^set(tags)))
                #print("target_album is ", target_album)

                #目标相册是否已经存在
                #目标相册和已有相册交集为空，就是不存在，需要新建相册
                new_albums = list((set(album_list).union(set(target_albums))) ^ (set(album_list) ^ set(target_albums)))

                for new_album in new_albums:
                    create_new_album(page.page_no, new_album)

                #把产品图片发到目标相册中去
                #检查产品是否已经在相册中了，如果不存在，就发布新图片
                #for target_album in target_albums:
                 #   post_photo_album(target_album)

                continue

            obj, created = ProductCategoryMypage.objects.update_or_create(
                            mypage=page, productcategory= category,
                            defaults={
                               # 'productcategory': category
                            },

                        )

                print("created is ",created)
                print("obj is ", obj)



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




