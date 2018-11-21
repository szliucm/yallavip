import xadmin
from django.shortcuts import render,render_to_response
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

from .models import Txh
from shop.models import Shop

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


# 继承基本动作模板
from xadmin.plugins.actions import BaseActionView

class MySelectedAction(BaseActionView):

    # 这个是执行函数名
    action_name = "update_selected"
    # 这个是显示的名字
    description = "更新所選項"

    model_perm = 'change'
    icon = 'fa fa-times'

    class data_src_form(forms.forms.Form):
        SHOP = Shop.objects.all()
        _selected_action = forms.CharField(widget=forms.MultipleHiddenInput)
        shop = forms.ModelChoiceField(queryset=SHOP, empty_label='请选择店铺')

        shops = forms.ModelMultipleChoiceField(widget=forms.CheckboxSelectMultiple, queryset=SHOP)

    @filter_hook
    # 对数据的操作
    def update_models(self, queryset):

        print("update models ")
        print(self.request.POST.get('waiter_id'))
        print(self.request.POST.get('post'))
        print(type(queryset))
        print(queryset)
        n = queryset.count()
        for case in queryset:
           print("case is ", case)
        '''
        if n:
            if self.delete_models_batch:
                self.log('update', _('Batch delete %(count)d %(items)s.') % {"count": n, "items": model_ngettext(self.opts, n)})
                queryset.update(waiter_id=self.request.POST.get('waiter_id'))
            else:
                for obj in queryset:
                    self.log('update', '', obj)
                    obj.update(waiter_id=self.request.POST.get('waiter_id'))
            self.message_user(_("?????Successfully deleted %(count)d %(items)s.") % {
                "count": n, "items": model_ngettext(self.opts, n)
            }, 'success')
            '''

    @filter_hook
    def do_action(self, queryset):
        form = None

        print("I'm here ",self.request)
        print("method ", self.request.method)
        print("post ", self.request.POST)

        if 'dream' in self.request.POST:
            print("haha I get you")
            form = self.data_src_form(self.request.POST)
            if form.is_valid():
                print("form is ", form)
                shop = form.cleaned_data["shop"]
                shops = form.cleaned_data["shops"]
                #for case in queryset:
                #    case.data_src = data_src
                print("type shop ", type(shop),shop)
                print("*************")
                print("shops ", shops)
                self.update_models(queryset)
                mess ="do it"

                self.message_user(_("Successfully. %s")%(mess) , 'success')
                return  HttpResponseRedirect(self.request.get_full_path())
            else:
                self.messages.warning(self.request,u"please to choose ")
                form = None
        else:
            print("what's wrong")

        if not form:
            form = self.data_src_form()
        context = self.get_context()

        path = self.request.get_full_path()
        #print("context is ", context)
        print("path is ", path)
        print("queryset is ", queryset)


        context = self.get_context()
        context.update({

            'queryset': queryset,
            'form': form,
            "opts": self.opts,
            "app_label": self.app_label,
            'action_checkbox_name': ACTION_CHECKBOX_NAME,
        })

        return TemplateResponse(self.request,
                                'batch_update.html', context)
        '''
        if self.request.POST.get('post'):
            # 这里输出yes
            print("wei ",self.request.POST.get('post'))

            # Return None to display the change list page again.
            return None
        else:

            print("not get post ",self.request.POST)


        context = self.get_context()

        # 展现到页面的内容
        path = self.request.get_full_path()
        print(type(queryset))

        print(queryset)
        print("path is ", path)
        #print("self path is ", self.get_url())
        context.update({
            'path': path,
            'action': 'update_selected',
            'queryset': queryset,
            "app_label": self.app_label,
            'action_checkbox_name': ACTION_CHECKBOX_NAME,
        })

        # Display the confirmation page
        # 确认页的相关参数
        return TemplateResponse(self.request, self.delete_selected_confirmation_template or
                                'batch_update.html', context)

        '''

'''

class MySelectedAction(BaseActionView):

    # 这个是执行函数名
    action_name = "my_do_action"
    # 这个是显示的名字
    description = "选择店铺"
    model_perm = 'change'
    icon = 'fa fa-times'

    class SysConfigForm(forms.Form):
        DatabaseType = forms.ChoiceField(choices=[('sqlserver', 'SQLServer'), ('oracle', 'Oracle')])


    @filter_hook
    # 对数据的操作
    def update_models(self, queryset):
        print(self.request)
        print(queryset)

    @filter_hook
    def do_action(self, queryset):
        print(self.request.POST)
        print(self.request)
        print(self.request.method)
        print(type(queryset))
        print(queryset)

        form = None

        if 'cancel' in self.request.POST:
            print(("hoho"))
            self.message_user(self.request, u'已取消')
            return
        elif 'data_src' in self.request.POST:
            form = self.SysConfigForm(self.request.POST)
            if form.is_valid():
                data_src = form.cleaned_data['data_src']
                for case in queryset:
                    case.data_src = data_src
                    case.save()
                    self.message_user(self.request, "%s successfully updated." % queryset.count())
                return HttpResponseRedirect(self.request.get_full_path())
            else:
                self.warning(self.request, u"请选择数据源")
                form = None
        else:
            print("I'm here")

        if not form:
            print("start form")
            form = self.SysConfigForm(
                initial={'DatabaseType': 'oracle', })

        return render(self.request, 'batch_update.html',
                      {'objs': queryset, 'form': form, 'path': self.request.get_full_path(),
                       'action': 'my_do_action', 'title': u'批量修改数据源为'},
                      # context_instance=RequestContext(self.request)
                      )

        
        if self.request.method == "POST":
            print("000000000")
            form = SysConfigForm(self.request.POST,
                            initial={'DatabaseType': 'oracle',},

                            )
            if form.is_valid():  # 所有验证都通过
                # do something处理业务
                print("ooooooooo")
                return HttpResponse("fffffffffffffff  ")
        else:
            form = SysConfigForm(
                            initial={'DatabaseType': 'oracle',}
                            )
        return render(self.request, 'test.html',
                      {'objs': queryset, 'form': form, 'path': self.request.get_full_path(),
                       'action': 'do_action', 'title': u'批量修改数据源为'},
                      # context_instance=RequestContext(self.request)
                      )





        
        print("self.request", self.request)
        print(self.get_context())
        if self.request.POST.get('POST'):
        #if self.request.method == 'POST':  # 当提交表单时
            form = AddForm(self.request.POST)  # form 包含提交的数据
            print("00000000000000")
            print((form))
            if form.is_valid():  # 如果提交的数据合法
                a = form.cleaned_data['a']
                b = form.cleaned_data['b']
                print("222222222222222222")
                self.message_user(self.request, u'已取消')
                #return HttpResponse("fffffffffffffff  "+str(int(a) + int(b)))

        else:  # 当正常访问时
            form = AddForm()
            print("11111111111111")

        print("3333333333333")
        return render(self.request, 'test.html', {'form': form})


        
        form = UserCreationForm(self.request.POST)
        print("haha")
        print(self.request.POST)


        if 'cancel' in self.request.POST:
            print(("hoho"))
            self.message_user(self.request, u'已取消')
            return
        elif 'data_src' in self.request.POST:
            form = self.data_src_form(self.request.POST)
            if form.is_valid():
                data_src = form.cleaned_data['data_src']
                for case in queryset:
                    case.data_src = data_src
                    case.save()
                    self.message_user(self.request, "%s successfully updated." % queryset.count())
                return HttpResponseRedirect(self.request.get_full_path())
            else:
                self.warning(self.request, u"请选择数据源")
                form = None
        
        if not form:
            form = self.data_src_form(
                initial={'_selected_action': self.request.POST.getlist(ACTION_CHECKBOX_NAME)})
        
   

        return render(self.request, 'batch_update.html',
                                  {'objs': queryset, 'form': form, 'path': self.request.get_full_path(),
                                   'action': 'do_action', 'title': u'批量修改数据源为'},
                                  #context_instance=RequestContext(self.request)
                                  )
'''



class TxhAdmin(object):
    # 搜索项
    search_fields = ['shop_name',]
    # 过滤项
    list_filter=['shop_name']
    # 显示的列
    list_display=('shop_name','apikey','password',)
    actions=[MySelectedAction,]


# 注册使之显示在后台中
xadmin.site.register(Txh,TxhAdmin)