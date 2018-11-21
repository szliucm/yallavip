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
from fb.models import MyAlbum,MyPage



from facebook_business.api import FacebookAdsApi
from facebook_business.exceptions import FacebookRequestError
from facebook_business.adobjects.systemuser import SystemUser
from facebook_business.adobjects.page import Page
from facebook_business.adobjects.pagepost import PagePost
from facebook_business.adobjects.album import Album
from facebook_business.adobjects.photo import Photo
from facebookads.adobjects.adimage import AdImage
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


class select_album_form(forms.Form, ):


    _selected_action = forms.CharField(widget=forms.MultipleHiddenInput)
    # album = forms.ModelChoiceField(queryset=myalbum, empty_label='请选择相册')
    albums = forms.ModelMultipleChoiceField(widget=forms.CheckboxSelectMultiple, queryset=None)

    def __init__(self,album,  *args, **kwargs):
        super(select_album_form, self).__init__(*args, **kwargs)

        self.fields["albums"].queryset = album

class select_page_form(forms.Form, ):

    mypages = MyPage.objects.all()
    _selected_action = forms.CharField(widget=forms.MultipleHiddenInput)
    pages = forms.ModelChoiceField(queryset=mypages, empty_label='请选择page')
    #pages = forms.ModelMultipleChoiceField(widget=forms.CheckboxSelectMultiple, queryset=mypages)





class post_to_album(BaseActionView):

    # 这个是执行函数名
    action_name = "to_album"
    # 这个是显示的名字
    description = "发布到相册"

    model_perm = 'change'
    icon = 'fa fa-times'
    page_no = "358078964734730"

    page_selected = False
    album_selected = False






    @filter_hook
    # 对数据的操作
    def do_album(self, queryset,albums):
        page_no = None


        token = get_token(self.page_no)
        # token = "EAAHZCz2P7ZAuQBAE9FEXmxUZCmISP6of8BCpvHYcgbicLOFAZAZB014FZARgDfxvx5AKRbPFSMqlzllrDHAFOtbty8x9eSzKJqbD5CAVRHJdH4kejAyv1B4MYDnwW9Qr5ZCwYG6q8Gk7Ok3ZBpfZC5OoovyjZCwaqebeVoXrXeGFkrk8ifZC9hyWX7cZCIqkopgZCIketETbWEqs4u4rGxbgsXttQJ0AF9iiQpoAZD"

        adobjects = FacebookAdsApi.init(my_app_id, my_app_secret, access_token=token, debug=True)

        for product in queryset:
            print("product.product_no ", product.product_no)
            imgs = ShopifyImage.objects.filter(product_no=product.product_no).values('src'). \
                order_by('position').first()
            if imgs is None:
                print("no image")
                continue
            image = imgs.get("src")


            fields = [
            ]
            params = {
                "url": image,
            }
            print(albums)
            for album in albums:


                photos = Album(album.album_no).create_photo(
                    fields=fields,
                    params=params,
                )

                print("photos is ", photos)


    @filter_hook
    def do_action(self, queryset):

        albums = MyAlbum.objects.filter(page_no=self.page_no)
        print(("type albums", type(albums), albums))

        form = select_page_form(self.request.POST, )
        # form = self.data_src_form(self.request.POST)

        if form.is_valid():
            print("form is ", form)

            albums = form.cleaned_data["albums"]
            # 执行动作
            self.do_album(queryset, albums)
            return HttpResponseRedirect(self.request.get_full_path())
        else:
            form = select_album_form(albums, self.request.POST)

        context = self.get_context()
        context.update({
            'queryset': queryset,
            'form': form,
            "opts": self.opts,
            "app_label": self.app_label,
            'action_checkbox_name': ACTION_CHECKBOX_NAME,
        })

        return TemplateResponse(self.request,
                                'select_album.html', context)