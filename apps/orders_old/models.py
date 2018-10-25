from django.db import models
from django.utils.html import format_html
from conversations.models import Conversation

# Create your models here.
class Order(models.Model):

    order_no = models.CharField(u'订单号',default='', unique=True, max_length=50,  blank=True)
    order_status = models.CharField(u'订单状态',max_length=30, default='未知', blank=True)

    buyer_name = models.CharField(u'买家姓名',default='',  max_length=50,  blank=True)

    product_quantity = models.CharField(u'产品数量', default='', max_length=50, blank=True)
    order_amount = models.CharField(u'订单金额',default='',  max_length=50,  blank=True)

    order_comment =  models.CharField(u'订单备注',max_length=300, default='' , null=True, blank=True)
    warhouse_comment = models.CharField(u'拣货备注', max_length=300, default='', null=True, blank=True)
    cs_comment = models.CharField(u'客服备注', max_length=300, default='', null=True, blank=True)

    receiver_name = models.CharField(u'收货人姓名',default='',  max_length=100,  blank=True)
    receiver_addr1 = models.CharField(u'地址1', default='', max_length=300, blank=True)
    receiver_addr2 = models.CharField(u'地址2', default='', max_length=300, blank=True)
    receiver_city = models.CharField(u'收货人城市', default='', max_length=50, blank=True)
    receiver_country = models.CharField(u'收货人国家', default='', max_length=50, blank=True)
    receiver_phone = models.CharField(u'收货人电话', default='', max_length=300, blank=True)

    package_no = models.CharField(u'包裹号', default='', max_length=100, blank=True)
    logistic_no = models.CharField(u'物流追踪号', default='', max_length=100, blank=True)
    logistic_type = models.CharField(u'物流方式', default='', max_length=100, blank=True)


    order_time = models.DateTimeField(u'下单时间', auto_now=False, null=True,blank=True)
    verify_time = models.DateTimeField(u'提交审核时间', auto_now=False, null=True,blank=True)
    sales = models.CharField(u'销售客服', max_length=100, null=True, blank=True)

    class Meta:
        verbose_name = "订单"
        verbose_name_plural = verbose_name
    def __str__(self):
        return  self.order_no

class OrderConversation(models.Model):

    order = models.ForeignKey(Order, related_name='order2conversation', null=True, blank=True,
                                     verbose_name="订单", on_delete=models.CASCADE)

    conversation = models.ForeignKey(Conversation, related_name='conversation2order', null=True, blank=True,
                                     verbose_name="会话", on_delete=models.CASCADE)


    class Meta:
        verbose_name = "订单_会话"
        verbose_name_plural = verbose_name
    def __str__(self):
        return  self.order.order_no

class Verify(models.Model):

    VERIFY_STATUS = (
        ("NOSTART", "未启动"),
        ("PROCESSING", "审核中"),
        ("SUCCESS", "通过"),
        ("WAIT", "问题单"),
        ("CLOSED", "关闭"),

    )


    #order = models.ForeignKey(Order, related_name='order', null=True, blank=True,
    #                                 verbose_name="订单", on_delete=models.CASCADE)
    order = models.OneToOneField(Order, on_delete=models.CASCADE,  verbose_name="订单")

    verify_status = models.CharField(choices=VERIFY_STATUS, default="NOSTART",max_length=30,  verbose_name="审单状态")

    order_no = models.CharField(u'订单号', max_length=20, null=True)
    order_time = models.DateTimeField(u'下单时间', auto_now=False, null=True)
    sales = models.CharField(u'销售客服', max_length=20, null=True)

    ori_phone = models.CharField(u'客户电话', max_length=100, null=True)
    phone_1 = models.CharField(u'电话_1', max_length=50, null=True)
    phone_2 = models.CharField(u'电话_2', max_length=20, null=True, blank=True)
    phone_3 = models.CharField(u'电话_3', max_length=20, null=True, blank=True)


    sms_status = models.CharField(u'验证码状态', max_length=20, default='未发送')

    error_money = models.BooleanField(u'价格问题', default=False)
    error_contact = models.BooleanField(u'联系方式问题', default=False)
    error_address = models.BooleanField(u'地址问题', default=False)
    error_cod = models.BooleanField(u'COD问题', default=False)
    error_note = models.BooleanField(u'备注问题', default=False)
    # err_code =  models.IntegerField(u'审核代码',default='',blank=True, null=True)

    cancel = models.BooleanField(u'取消订单', default=False)

    cs_reply = models.CharField(u'客服回复', max_length=200, default='', blank=True)
    cs = models.CharField(u'客服', max_length=50, default='')
    reply_time = models.CharField(u'回复时间', max_length=50, default='')

    start_time = models.DateTimeField(u'开始审核时间', auto_now=True, null=True)
    start_staff = models.CharField(u'开始审核人', max_length=50, null=True)
    final_time = models.DateTimeField(u'最后审核时间', null=True)
    final_staff = models.CharField(u'最后审核人', max_length=256, null=True)


    class Meta:
        verbose_name = "审单"
        verbose_name_plural = verbose_name
    def __str__(self):
        return  self.verify_status

    def colored_verify_status(self):

        #if ( self.error_money and self.error_contact and  self.error_address
        #        and self.error_cod   and self.error_note):
        #    self.verify_status = '已审核'
        if( self.verify_status == 'SUCCESS' ):

            color_code = 'green'
        elif (self.verify_status == 'WAIT'):
             color_code = 'red'
        else:
            color_code = 'blue'

        return format_html(
            '<span style="color:{};">{}</span>',
            color_code,
            self.get_verify_status_display(),
        )

    colored_verify_status.short_description = u"审单状态"

    def colored_sms_status(self):
        if self.sms_status == '已发送':
            color_code = 'red'
        elif self.sms_status == '已确认':
            color_code = 'green'
        else:
            color_code = 'blue'
        return format_html(
            '<span style="color:{};">{}</span>',
            color_code,
            self.sms_status,
        )

    colored_sms_status.short_description = u"验证码状态"