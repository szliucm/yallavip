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
from fb.models import  MyPage
import requests
import json


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

    datasrc = forms.ModelMultipleChoiceField(widget=forms.CheckboxSelectMultiple, queryset=None)

    def __init__(self, queryset,  *args, **kwargs):
        super(select_form, self).__init__(*args, **kwargs)

        self.fields["datasrc"].queryset = queryset


class ChoosePage(BaseActionView):

    # 这个是执行函数名
    action_name = "chooase_page"
    # 这个是显示的名字
    description = "选择目标page"

    model_perm = 'change'
    icon = 'fa fa-times'

    @filter_hook
    # 对数据的操作
    def do_models(self, queryset,form_selected):

        print("start do something to the model ")
        print("queryset is ", queryset)
        print("form_selected is ", form_selected)
        #需要进行的操作

        for creative in queryset:
            for page in form_selected:
                obj, created = MyProductFb.objects.update_or_create(
                    myresource=creative, mypage= page,
                                defaults={
                                    'myproduct': creative.myproduct,
                                    'obj_type': "FEED"

                                },

                            )




        ##############################
        return

    @filter_hook
    #捕捉操作
    def do_action(self, queryset):
        ##############需要选择的对象
        form_queryset = MyPage.objects.filter(active=True)
        ############################

        form = select_form(form_queryset, self.request.POST )
        if form.is_valid():
            #print("form is ", form)
            form_selected = form.cleaned_data["datasrc"]
            # 执行动作
            self.do_models(queryset,form_selected)
            return HttpResponseRedirect(self.request.get_full_path())
        else:
            form = select_form(form_queryset, self.request.POST)

        context = self.get_context()
        context.update({
            'queryset': queryset,
            'form': form,
            "opts": self.opts,
            "app_label": self.app_label,
            "form_action": self.action_name ,
            'action_checkbox_name': ACTION_CHECKBOX_NAME,
        })

        return TemplateResponse(self.request,
                                'select_form.html', context)



