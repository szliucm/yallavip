# -*- coding: utf-8 -*-
__author__ = 'bobby'

import xadmin
from django.shortcuts import get_object_or_404, get_list_or_404, render
from import_export import resources, fields
from import_export.widgets import ForeignKeyWidget
from .models import Order, Verify, OrderConversation
from conversations.models import Conversation
from django.db import models
from yunpian_python_sdk.model import constant as YC
from yunpian_python_sdk.ypclient import YunpianClient
from django.utils import timezone as datetime
import urllib
import random
from django.db.models import Q
from django.utils.safestring import mark_safe


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

    order = fields.Field(
        column_name='order',
        attribute='order',
        widget=ForeignKeyWidget(Order, 'order_no'))

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


class OrderAdmin(object):

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

    list_display = ["order_no", "order_status", "verify_status", "verify_time", "show_conversation"]
    # list_display_links = ["show_conversation"]
    search_fields = ["order_no", ]
    #list_filter = ("sales", "order_status", "receiver_city","verify_time")

    actions = ['start_verify']

    def start_verify(self, request, queryset):
        # 定义actions函数

        # VerifyList = []
        qs = list(queryset)

        for row in qs:
            obj, created = Verify.objects.update_or_create(
                order=Order.objects.get(order_no=row.order_no),
                defaults=dict(verify_status="PROCESSING",
                              phone_1=valid_phone(row.receiver_phone),
                              sms_status="未发送",
                              start_time=datetime.now(),

                              final_time=datetime.now(),


                              ),
            )

        rows_updated = queryset.update(verify_time=datetime.now(), )

        rows_updated = len(qs)
        if rows_updated == 1:
            message_bit = '1 story wa'
        else:
            message_bit = "%s stories were" % rows_updated
        self.message_user(request, "%s successfully marked as verified." % message_bit)

    start_verify.short_description = "批量开始审核"

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


class VerifyAdmin(object):
    # import_export_args = {'import_resource_class': MessageResource, 'export_resource_class': MessageResource}

    def _order_status(self, obj):
        return obj.order.order_status

    def _order_status(self, obj):
        return obj.order.order_status

    def _buyer_name(self, obj):
        return obj.order.buyer_name


    readonly_fields = ('order_no', 'order_time',)
    list_display = ('order', 'colored_verify_status', "city",\
                    'colored_sms_status', 'cancel', 'ori_phone', 'phone_1', 'phone_2', \
                    'error_money', 'error_contact', 'error_address', 'error_cod', 'error_note', \
                    'order_time','_order_status','_buyer_name')
    list_editable = ['phone_1', 'phone_2', 'cs_reply']
    search_fields = ['order__order_no', ]
    #list_filter = ('verify_status', 'sms_status', 'error_money', 'cs')

    actions = ['batch_copy', 'batch_error_money', \
               'batch_error_contact', 'batch_error_address', 'batch_error_cod', \
               'batch_error_note', 'batch_submit', 'batch_sms', 'batch_confirm', 'batch_cancel', 'batch_restart', ]

    def batch_submit(self, request, queryset):
        # 定义actions函数
        rows_updated = queryset.filter(error_money=True, error_contact=True,
                                       error_address=True, error_cod=True, error_note=True).update(verify_status='已审核')

        rows_updated += queryset.filter(Q(error_money=False) | Q(error_contact=False) |
                                        Q(error_address=False) | Q(error_cod=False) | Q(error_note=False)).update(
            verify_status='问题单')

        # rows_updated += Verify.objects.filter(error_money=False).update(verify_status='问题单')

        if rows_updated == 1:
            message_bit = '1 story was'
        else:
            message_bit = "%s stories were" % rows_updated
        self.message_user(request, "%s successfully marked as verified." % message_bit)

    batch_submit.short_description = "批量提交"

    def batch_restart(self, request, queryset):
        # 定义actions函数
        rows_updated = queryset.update(verify_status='审核中', error_money=False, error_contact=False,
                                       error_address=False, error_cod=False, error_note=False)
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

            orderList.append(row.order_no)

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

    def batch_confirm(self, request, queryset):
        # 定义actions函数
        rows_updated = queryset.update(sms_status='已确认')
        if rows_updated == 1:
            message_bit = '1 story was'
        else:
            message_bit = "%s stories were" % rows_updated
        self.message_user(request, "%s successfully marked as confirmed." % message_bit)

    batch_confirm.short_description = "批量确认验证码"

    def batch_error_money(self, request, queryset):
        # 定义actions函数
        rows_updated = queryset.update(error_money=True)
        if rows_updated == 1:
            message_bit = '1 story was'
        else:
            message_bit = "%s stories were" % rows_updated
        self.message_user(request, "%s successfully marked as error." % message_bit)

    batch_error_money.short_description = "批量价格审核"

    def batch_error_contact(self, request, queryset):
        # 定义actions函数
        rows_updated = queryset.update(error_contact=True)
        if rows_updated == 1:
            message_bit = '1 story was'
        else:
            message_bit = "%s stories were" % rows_updated
        self.message_user(request, "%s successfully marked as error." % message_bit)

    batch_error_contact.short_description = "批量电话审核"

    def batch_error_address(self, request, queryset):
        # 定义actions函数
        rows_updated = queryset.update(error_address=True)
        if rows_updated == 1:
            message_bit = '1 story was'
        else:
            message_bit = "%s stories were" % rows_updated
        self.message_user(request, "%s successfully marked as error." % message_bit)

    batch_error_address.short_description = "批量地址审核"

    def batch_error_cod(self, request, queryset):
        # 定义actions函数
        rows_updated = queryset.update(error_cod=True)
        if rows_updated == 1:
            message_bit = '1 story was'
        else:
            message_bit = "%s stories were" % rows_updated
        self.message_user(request, "%s successfully marked as error." % message_bit)

    batch_error_cod.short_description = "批量COD审核"

    def batch_error_note(self, request, queryset):
        # 定义actions函数
        rows_updated = queryset.update(error_note=True)
        if rows_updated == 1:
            message_bit = '1 story was'
        else:
            message_bit = "%s stories were" % rows_updated
        self.message_user(request, "%s successfully marked as error." % message_bit)

    batch_error_note.short_description = "批量备注审核"

    def batch_cancel(self, request, queryset):
        # 定义actions函数
        rows_updated = queryset.update(cancel=True)
        if rows_updated == 1:
            message_bit = '1 story was'
        else:
            message_bit = "%s stories were" % rows_updated
        self.message_user(request, "%s successfully marked as error." % message_bit)

    batch_cancel.short_description = "批量取消订单"

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
            queryset |= self.model.objects.filter(order_no__in=search_term.split(","))
        return queryset, use_distinct


class OrderConverstaionResource(resources.ModelResource):
    order = fields.Field(
        column_name='order',
        attribute='order',
        widget=ForeignKeyWidget(Order, 'order_no'))

    conversation = fields.Field(
        column_name='conversation',
        attribute='conversation',
        widget=ForeignKeyWidget(Conversation, 'conversation_no'))

    class Meta:
        model = OrderConversation
        skip_unchanged = True
        report_skipped = True
        import_id_fields = ('order', 'conversation')
        fields = ('order', 'conversation')
        # exclude = ()


class ServiceAdmin(object):
    # import_export_args = {'import_resource_class': MessageResource, 'export_resource_class': MessageResource}

    readonly_fields = ('order_no', 'order_time',)
    list_display = ('order', 'colored_verify_status', \
                    'colored_sms_status', 'cancel', 'ori_phone', 'phone_1', 'phone_2', \
                    'error_money', 'error_contact', 'error_address', 'error_cod', 'error_note', \
                    'cs_reply', 'cs', 'reply_time', 'sales', 'order_time')
    list_editable = ['phone_1', 'phone_2', 'cs_reply']
    search_fields = ['order__order_no', ]
    list_filter = ('verify_status', 'sms_status')


class OrderConverstaionAdmin(object):
    import_export_args = {'import_resource_class': OrderConverstaionResource,
                          'export_resource_class': OrderConverstaionResource}

    list_display = ["order", "conversation"]
    search_fields = ['order', ]


xadmin.site.register(Order, OrderAdmin)
xadmin.site.register(Verify, VerifyAdmin)
xadmin.site.register(OrderConversation, OrderConverstaionAdmin)
