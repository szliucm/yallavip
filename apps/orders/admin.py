from django.contrib import admin
from django.shortcuts import get_object_or_404, get_list_or_404, render
from import_export import resources, fields
from import_export.widgets import ForeignKeyWidget
from .models import Order, Verify, OrderConversation,ClientService
from conversations.models import Conversation
from django.db import models
from yunpian_python_sdk.model import constant as YC
from yunpian_python_sdk.ypclient import YunpianClient
from datetime import datetime
import urllib
import random
from django.db.models import Q
from django.utils.safestring import mark_safe
from django import forms
from django.contrib import admin, messages
from django.http import HttpResponseRedirect
from django.template import RequestContext

# Register your models here.
# -*- coding: utf-8 -*-


admin.site.disable_action('delete_selected')

def valid_phone(x):
    x = str(x)
    x = x.replace(' ', '')
    x = x.replace('o', '')
    x = x.replace('O', '')

    if x.find('966') > -1:
        a = x.find('966') + 3
        x = x[a:]
    x = x.lstrip('0')

    return x


class OrderResource(resources.ModelResource):
    order_no = fields.Field(attribute='order_no', column_name='订单号')
    order_status = fields.Field(attribute='order_status', column_name='订单状态')

    buyer_name = fields.Field(attribute='buyer_name', column_name='买家姓名')
    '''
    order = fields.Field(
        column_name='order',
        attribute='order',
        widget=ForeignKeyWidget(Order, 'order_no'))
    '''

    product_quantity = fields.Field(attribute='product_quantity', column_name='产品数量')
    order_amount = fields.Field(attribute='order_amount', column_name='订单金额')

    order_comment = fields.Field(attribute='order_comment', column_name='订单备注')
    warhouse_comment = fields.Field(attribute='warhouse_comment', column_name='拣货备注')
    cs_comment = fields.Field(attribute='cs_comment', column_name='客服备注')

    receiver_name = fields.Field(attribute='receiver_name', column_name='收货人姓名')
    receiver_addr1 = fields.Field(attribute='receiver_addr1', column_name='地址1')
    receiver_addr2 = fields.Field(attribute='receiver_addr2', column_name='地址2')
    receiver_city = fields.Field(attribute='receiver_city', column_name='收货人城市')
    receiver_country = fields.Field(attribute='receiver_country', column_name='收货人国家')
    receiver_phone = fields.Field(attribute='receiver_phone', column_name='收货人电话')

    package_no = fields.Field(attribute='package_no', column_name='包裹号')
    logistic_no = fields.Field(attribute='logistic_no', column_name='物流追踪号')
    logistic_type = fields.Field(attribute='logistic_type', column_name='物流方式')

    order_time = fields.Field(attribute='order_time', column_name='下单时间')
    sales = models.CharField(u'销售客服', max_length=20, null=True)

    class Meta:
        model = Order
        skip_unchanged = True
        report_skipped = True
        import_id_fields = ('order_no',)
        fields = ('order_no', 'order_status', 'buyer_name', 'product_quantity', 'order_amount', 'order_comment',
                  'warhouse_comment', 'cs_comment', 'receiver_name', 'receiver_addr1', 'receiver_addr2',
                  'receiver_city', 'receiver_country', 'receiver_phone', 'package_no', 'logistic_no', 'logistic_type',
                  'order_time')
        # exclude = ()



class OrderAdmin(admin.ModelAdmin):

    def verify_status(self, obj):
        verify = Verify.objects.get(order=obj.id)
        return verify.get_verify_status_display()

    verify_status.short_description = "审核状态"



    def show_conversation(self, obj):
        conversation = OrderConversation.objects.get(order=obj.id).conversation

        return mark_safe(
            u'<a href="http://business.facebook.com%s" target="view_window">%s</a>' % (conversation.link, u'会话'))

    show_conversation.allow_tags = True

    show_conversation.short_description = "会话"

    import_export_args = {"import_resource_class": OrderResource, "export_resource_class": OrderResource}

    list_display = ["order_no", "order_status", "verify_time", "show_conversation","verify_status"]
    # list_display_links = ["show_conversation"]
    search_fields = ["order_no", ]
    list_filter = ("sales", "order_status", "receiver_city","verify_time",)

    actions = ['start_verify','batch_copy']

    def start_verify(self, request, queryset):
        # 定义actions函数

        #qsList = list(queryset)
        #VerifyList = []
        for row in queryset:
            #order = Order.objects.get(id=row.id),
            v = Verify(

                    #order_ptr = order,

                    #order_nos=row.order_no,
                order = Order.objects.get(id=row.id),

                verify_status="PROCESSING",
                phone_1=valid_phone(row.receiver_phone),
                sms_status="未发送",
                start_time=datetime.now(),

                final_time=datetime.now(),
                )

            v.save()


        rows_updated = queryset.update(verify_time=datetime.now(), )

        #rows_updated = len(rows_updated)
        if rows_updated == 1:
            message_bit = '1 story wa'
        else:
            message_bit = "%s stories were" % rows_updated
        self.message_user(request, "%s successfully marked as verified." % message_bit)

    start_verify.short_description = "批量开始审核"

    def batch_copy(self, request, queryset):
        # 定义actions函数
        qsList = list(queryset)
        orderList = []
        for row in qsList:
            # orderList.append(row.order_no)
            orderList.append(row.order_no)

        message_bit = ','.join(orderList)

        # self.message_user(request, "[ %s ] successfully copied." %message_bit)
        self.message_user("[ %s ] successfully copied." % message_bit)
        return

    batch_copy.short_description = "复制所选单号"

    # def get_search_results(self, request, queryset, search_term):
    def get_search(self, request, queryset, search_term):
        """批量查询订单号"""
        queryset, use_distinct = super().get_search_results(request, queryset, search_term)
        print("hello")
        print(queryset)
        print(search_term)
        if (len(search_term) > 0):
            queryset |= self.model.objects.filter(order_no__in=search_term.split(","))

        return queryset, use_distinct


class VerifyAdmin(admin.ModelAdmin):
    # import_export_args = {'import_resource_class': MessageResource, 'export_resource_class': MessageResource}
    def order_no(self, obj):
        #return obj.order.order_no
        return obj.order.order_no

    order_no.short_description = "订单号"

    def order_status(self, obj):
        return obj.order.order_status

    order_status.short_description = "订单状态"

    #readonly_fields = ('order', 'order_time',)
    list_display = ('order', 'order_status','colored_verify_status', \
                    'colored_sms_status', 'cancel', 'error_money', 'error_contact', \
                  'error_address', 'error_cod', 'error_note')

    search_fields = ['order__order_no', ]
    list_filter = ('verify_status', 'sms_status', 'error_money','order__order_status','order__order_time')

    actions = ['batch_copy', 'batch_verify','batch_error_money', \
               'batch_error_contact', 'batch_error_address', 'batch_error_cod', \
               'batch_error_note', 'batch_submit', 'batch_sms', 'batch_confirmSMS', 'batch_cancel','batch_notstart', 'batch_restart', 'set_type_action']



    #自定义django的admin后台action

    def batch_submit(self, request, queryset):
        # 定义actions函数
        rows_updated = queryset.filter(error_money=True, error_contact=True,
                                       error_address=True, error_cod=True, error_note=True).update(verify_status='SUCCESS')

        rows_updated += queryset.filter(Q(error_money=False) | Q(error_contact=False) |
                                        Q(error_address=False) | Q(error_cod=False) | Q(error_note=False)).update(
            verify_status='WAIT')

        rows_updated = queryset.filter(cancel=False).update(verify_status='CLOSED')

        # rows_updated += Verify.objects.filter(error_money=False).update(verify_status='问题单')

        if rows_updated == 1:
            message_bit = '1 story was'
        else:
            message_bit = "%s stories were" % rows_updated
        self.message_user(request, "%s successfully marked as verified." % message_bit)

    batch_submit.short_description = "批量提交"

    def batch_verify(self, request, queryset):
        # 定义actions函数
        rows_updated = queryset.update(verify_status='SUCCESS', error_money=True, error_contact=True,
                                       error_address=True, error_cod=True, error_note=True)
        if rows_updated == 1:
            message_bit = '1 story was'
        else:
            message_bit = "%s stories were" % rows_updated
        self.message_user(request, "%s successfully marked as confirmed." % message_bit)

    batch_verify.short_description = "批量通过审核"

    def batch_notstart(self, request, queryset):
        # 定义actions函数
        rows_updated = queryset.update(verify_status='NOSTART', error_money=False, error_contact=False,
                                       error_address=False, error_cod=False, error_note=False)
        if rows_updated == 1:
            message_bit = '1 story was'
        else:
            message_bit = "%s stories were" % rows_updated
        self.message_user(request, "%s successfully marked as confirmed." % message_bit)

    batch_notstart.short_description = "批量搁置审核"

    def batch_restart(self, request, queryset):
        # 定义actions函数
        rows_updated = queryset.update(verify_status='PROCESSING', cancel=None, error_money=None, error_contact=None,
                                       error_address=None, error_cod=None, error_note=None)
        if rows_updated == 1:
            message_bit = '1 story was'
        else:
            message_bit = "%s stories were" % rows_updated
        self.message_user(request, "%s successfully marked as confirmed." % message_bit)

    batch_restart.short_description = "批量重新审核"

    def batch_sms(self, request, queryset):
        # 定义actions函数
        # qsList = list(queryset)
        orderList = []

        for row in queryset:

            #orderList.append(row.order_no)

            if (row.phone_1 != None):
                code = 'Y' + str(random.randint(100000, 999999))
                param = {YC.MOBILE: '+966' + row.phone_1,
                         # YC.TEXT: '【YallaVIP】Please send  YallaVIP\'s shopping code#%s# to us by facebook messanger. We will deliver your order when we get your code.'%row[1]}
                         YC.TEXT: '【YallaVip】Please send  YallaVIP\'s shopping code#%s# to us by facebook messanger. We will deliver your order when we get your code.' % code}
                print(param)
                print(urllib.parse.urlencode(param))
                # r = clnt.sms().single_send(param)

            if (row.phone_2 != None):
                code = 'Y' + str(random.randint(100000, 999999))
                param = {YC.MOBILE: '+966' + row.phone_2,
                         # YC.TEXT: '【YallaVIP】Please send  YallaVIP\'s shopping code#%s# to us by facebook messanger. We will deliver your order when we get your code.'%row[1]}
                         YC.TEXT: '【YallaVip】Please send  YallaVIP\'s shopping code#%s# to us by facebook messanger. We will deliver your order when we get your code.' % code}
                print(param)
                print(urllib.parse.urlencode(param))
                # r = clnt.sms().single_send(param)
            if (row.phone_3 != None):
                code = 'Y' + str(random.randint(100000, 999999))
                param = {YC.MOBILE: '+966' + row.phone_3,
                         # YC.TEXT: '【YallaVIP】Please send  YallaVIP\'s shopping code#%s# to us by facebook messanger. We will deliver your order when we get your code.'%row[1]}
                         YC.TEXT: '【YallaVip】Please send  YallaVIP\'s shopping code#%s# to us by facebook messanger. We will deliver your order when we get your code.' % code}
                print(param)
                print(urllib.parse.urlencode(param))
                # r = clnt.sms().single_send(param)

            # r = clnt.sms().single_send(param)

        rows_updated = queryset.update(sms_status='已发送')

        # message_bit = ','.join(orderList)
        self.message_user(request, "[ %s ] orders successfully send sms code." % rows_updated)

        """
        if rows_updated == 1:
            message_bit = '1 story was'
        else:
            message_bit = "%s stories were" %rows_updated
        self.message_user(request,"%s successfully marked as send." %message_bit)
        """

    batch_sms.short_description = "批量发送验证码"

    def batch_confirmSMS(self, request, queryset):
        # 定义actions函数
        rows_updated = queryset.update(sms_status='已确认')
        if rows_updated == 1:
            message_bit = '1 story was'
        else:
            message_bit = "%s stories were" % rows_updated
        self.message_user(request, "%s successfully marked as confirmed." % message_bit)

    batch_confirmSMS.short_description = "批量确认验证码"

    def batch_error_money(self, request, queryset):
        # 定义actions函数
        rows_updated = queryset.update(error_money=False)
        if rows_updated == 1:
            message_bit = '1 story was'
        else:
            message_bit = "%s stories were" % rows_updated
        self.message_user(request, "%s successfully marked as error." % message_bit)

    batch_error_money.short_description = "批量价格问题"

    def batch_error_contact(self, request, queryset):
        # 定义actions函数
        rows_updated = queryset.update(error_contact=False)
        if rows_updated == 1:
            message_bit = '1 story was'
        else:
            message_bit = "%s stories were" % rows_updated
        self.message_user(request, "%s successfully marked as error." % message_bit)

    batch_error_contact.short_description = "批量电话问题"

    def batch_error_address(self, request, queryset):
        # 定义actions函数
        rows_updated = queryset.update(error_address=False)
        if rows_updated == 1:
            message_bit = '1 story was'
        else:
            message_bit = "%s stories were" % rows_updated
        self.message_user(request, "%s successfully marked as error." % message_bit)

    batch_error_address.short_description = "批量地址问题"

    def batch_error_cod(self, request, queryset):
        # 定义actions函数
        rows_updated = queryset.update(error_cod=False)
        if rows_updated == 1:
            message_bit = '1 story was'
        else:
            message_bit = "%s stories were" % rows_updated
        self.message_user(request, "%s successfully marked as error." % message_bit)

    batch_error_cod.short_description = "批量COD问题"

    def batch_error_note(self, request, queryset):
        # 定义actions函数
        rows_updated = queryset.update(error_note=False)
        if rows_updated == 1:
            message_bit = '1 story was'
        else:
            message_bit = "%s stories were" % rows_updated
        self.message_user(request, "%s successfully marked as error." % message_bit)

    batch_error_note.short_description = "批量备注问题"

    def batch_cancel(self, request, queryset):
        # 定义actions函数
        rows_updated = queryset.update(cancel=False, verify_status = 'CLOSED')
        if rows_updated == 1:
            message_bit = '1 story was'
        else:
            message_bit = "%s stories were" % rows_updated
        self.message_user(request, "%s successfully marked as error." % message_bit)

    batch_cancel.short_description = "批量关闭订单"

    def batch_copy(self, request, queryset):
        # 定义actions函数
        qsList = list(queryset)
        orderList = []
        for row in qsList:
            # orderList.append(row.order_no)
            orderList.append(row.order.order_no)

        message_bit = ','.join(orderList)

        # self.message_user(request, "[ %s ] successfully copied." %message_bit)
        self.message_user("[ %s ] successfully copied." % message_bit)
        return

    batch_copy.short_description = "复制所选单号"

    def get_search_results(self, request, queryset, search_term):
        """批量查询订单号"""
        queryset, use_distinct = super().get_search_results(request, queryset, search_term)
        print("hello")
        print(queryset)
        print(search_term)
        if (len(search_term) > 0):
            queryset |= self.model.objects.filter(order__order_no__in=search_term.split(","))
        return queryset, use_distinct


class ClientServiceAdmin(admin.ModelAdmin):

    def show_conversation(self, obj):
        conversation = OrderConversation.objects.get(order=obj.id).conversation

        return mark_safe(
            u'<a href="http://business.facebook.com%s" target="view_window">%s</a>' % (conversation.link, u'会话'))

    show_conversation.allow_tags = True

    show_conversation.short_description = "会话"

    list_display = ["order", "cs_reply","show_conversation"]
    search_fields = ['order', ]

    '''
    def get_queryset(self, request):
        qs = super().get_queryset(request)

        return qs.filter(verify_status='PROCESSING')
    '''


#admin.site.register(Order, OrderAdmin)
admin.site.register(Verify, VerifyAdmin)
admin.site.register(ClientService, ClientServiceAdmin)