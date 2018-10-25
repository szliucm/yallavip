from django.db import models
from django.utils.html import format_html
from conversations.models import Conversation


# Create your models here.
class Order(models.Model):
    LOGISTIC_STATUS = (
        ("ARRANGE CRRGOS ON WAREHOUSE", "ARRANGE CRRGOS ON WAREHOUSE"),
        ("case closed", "case closed"),
        ("CONSIGNMENT RECEIVED AT TRANSIT POINT", "CONSIGNMENT RECEIVED AT TRANSIT POINT"),
        ("Consignment Received At Transit Point", "Consignment Received At Transit Point"),
        ("DELIVERY INFO INCORRECT/INCOMPLETE/MISSING", "DELIVERY INFO INCORRECT/INCOMPLETE/MISSING"),
        ("Flight arrived", "Flight arrived"),
        ("IN TRANSIT", "IN TRANSIT"),
        ("In Transit", "In Transit"),
        ("NOT DELIVERED", "NOT DELIVERED"),
        ("out for delivery", "out for delivery"),
        ("RECEIVER UNABLE TO BE CONNECTED", "RECEIVER UNABLE TO BE CONNECTED"),
        ("Receiver was not in when delivery attempt", "Receiver was not in when delivery attempt"),
        ("RETURNED TO DEPOT", "RETURNED TO DEPOT"),
        ("Shipment arrived at XX Distribution center", "Shipment arrived at XX Distribution center"),
        ("Shipment under processing at Distribution center", "Shipment under processing at Distribution center"),
        ("shipment was returned", "shipment was returned"),
        (None, "未处理"),
        ("START SITE TRANSPORT SHIPMENT", "启运"),
        ("Delivered", "已签收"),
        ("receiver refused to accept the shipment", "拒签"),
    )
    '''
    DELIVER_STATUS = (
        ("WAITING", "待处理"),
        ("DELIVERING", "派送中"),
        ("DELIVERED", "签收"),
        ("PROBLEM", "问题件"),
        ("REFUSED", "拒签"),
        ("RETURNING", "退仓中"),
        ("RETURNED", "已退仓"),

    )
    '''
    RESPONSE = (
        ("NONE", "待定"),
        ("DELIVER", "派送员"),
        ("CUSTOMER", "客户"),
        ("YALLAVIP", "YallaVIP"),
    )

    DEAL = (
        ("NONE", "待定"),

        ("LOST", "丢件"),

        ("DELIVERED", "已签收"),

        ("WAITING", "沟通中"),
        ("RE_DELIVER", "重新派送"),
        ("RE_DELIVERING", "重新派送中"),

        ("REFUSED", "拒签"),
        ("RETURNING", "退仓中"),
        ("RETURNED", "已退到仓库"),
    )

    SETTLETYPE = (
        ("COD", "COD"),
        ("FEE", "运费"),
    )



    order_no = models.CharField(u'订单号', default='', max_length=50, blank=True)

    order_status = models.CharField(u'订单状态', max_length=30, default='未知', blank=True)

    buyer_name = models.CharField(u'买家姓名', default='', max_length=500, blank=True)

    # product_quantity = models.CharField(u'产品数量', default='', max_length=50, blank=True)
    order_amount = models.CharField(u'订单金额', default='', max_length=50, blank=True)

    order_comment = models.CharField(u'订单备注', max_length=500, default='', null=True, blank=True)
    warhouse_comment = models.CharField(u'拣货备注', max_length=500, default='', null=True, blank=True)
    cs_comment = models.CharField(u'客服备注', max_length=500, default='', null=True, blank=True)

    receiver_name = models.CharField(u'收货人姓名', default='', max_length=500, blank=True)
    receiver_addr1 = models.CharField(u'地址1', default='', max_length=500, blank=True)
    receiver_addr2 = models.CharField(u'地址2', default='', max_length=500, blank=True)
    receiver_city = models.CharField(u'收货人城市', default='', max_length=500, blank=True)
    receiver_country = models.CharField(u'收货人国家', default='', max_length=500, blank=True)
    receiver_phone = models.CharField(u'收货人电话', default='', max_length=500, blank=True)

    package_no = models.CharField(u'包裹号', default='', max_length=100, blank=True)
    logistic_no = models.CharField(u'物流追踪号', default='', max_length=100, blank=True)

    logistic_type = models.CharField(u'物流方式', default='', max_length=100, blank=True)
    weight = models.CharField(u'称重重量', default='', max_length=100, blank=True)
    order_time = models.DateTimeField(u'下单时间', auto_now=False, null=True, blank=True)
    send_time = models.DateTimeField(u'发货时间', auto_now=False, blank=True, null=True)

    #物流更新
    '''
    refer_no = models.CharField(u'参考号', max_length=50, null=True, blank=True)
    shipping_time = models.DateTimeField(u'出货时间', auto_now=False, null=True, blank=True)
    tracking_no = models.CharField(u'转单号', max_length=50, null=True, blank=True)
    real_weight = models.CharField(u'实重', max_length=100, null=True, blank=True)
    size_weight = models.CharField(u'体积重', max_length=100, null=True, blank=True)
    charge_weight = models.CharField(u'计费重', max_length=100, null=True, blank=True)
    '''

    logistic_update_date = models.DateField(u'物流更新时间', auto_now=False, null=True, blank=True)
    logistic_update_locate = models.CharField(u'物流更新地点', max_length=100, null=True, blank=True)
    #logistic_update_status = models.CharField(u'物流状态 ', max_length=100, null=True, blank=True)
    logistic_update_status = models.CharField(choices=LOGISTIC_STATUS, verbose_name='物流状态', max_length=100, null=True, blank=True)




    #人工更新
    verify_time = models.DateTimeField(u'提交审核时间', auto_now=False, null=True, blank=True)



    #问题件
    problem_type = models.CharField(u'问题类型', max_length=200, null=True, blank=True)
    response = models.CharField(choices=RESPONSE, max_length=20, default='NONE', verbose_name="责任")
    feedback = models.CharField(verbose_name="反馈原因", max_length=100, null=True, blank=True)
    feedback_time = models.DateTimeField(u'反馈时间', auto_now=False, null=True, blank=True)
    deal = models.CharField(choices=DEAL, max_length=50, default='NONE', verbose_name="处理办法", blank=True)

    #财务
    SETTLE_STATUS = (
        ("COD", "COD"),
        ("FEE", "运费"),
        ("COMPENSATE", "赔偿"),
    )
    settle_status  = models.CharField(choices=SETTLE_STATUS, max_length=50, default='NONE', verbose_name="财务结算", blank=True)

    PACKAGE_STATUS = (
        ("NONE", "待处理"),
        ("START", "交运"),
        ("DELIVERED", "妥投"),
        ("TEMPORARY", "暂存站点"),
        ("RETURNED", "海外仓"),
        ("LOST", "丢失"),
        ("DELIVERING", "运输中"),
        ("RETURNING", "退仓中"),

        ("RESELLOUT", "二次售罄"),
    )

    package_status = models.CharField(choices=PACKAGE_STATUS, max_length=50, default='NONE', verbose_name="包裹状态", blank=True)

    CUSTOMER_STATUS = (
        ("WELLDONE", "签收"),
        ("RETURNED", "拒签"),
        ("LOST", "失联"),
    )
    customer_status = models.CharField(choices=CUSTOMER_STATUS, max_length=50, default='NONE', verbose_name="客户状态", blank=True)

    POSTSALE_STTUS = (
        ("QUANLITY", "质量问题"),
        ("RETURNED", "少发"),
        ("LOST", "发错"),
        ("DELIVERING", "多收钱"),

    )
    postsale_status = models.CharField(choices=POSTSALE_STTUS, max_length=50, default='NONE', verbose_name="售后状态", blank=True)

    FILE_STTUS = (
        ("OPEN", "开放"),
        ("CLOSED", "归档"),

    )
    file_status = models.CharField(choices=FILE_STTUS, max_length=50, default='OPEN', verbose_name="归档状态",
                                       blank=True)

    RESELL_STTUS = (
        ("LISTING", "上架中"),
        ("UNLISTING", "下架中"),
        ("SELLOUT", "二次售罄"),
        ("DESTROYED", "销毁"),


    )
    resell_status = models.CharField(choices=RESELL_STTUS, max_length=50, default='UNLISTING', verbose_name="二次销售状态",
                                   blank=True)




    class Meta:
        verbose_name = "订单"
        verbose_name_plural = verbose_name


    def __str__(self):
        return self.order_no


class OrderDetail(models.Model):
    order = models.ForeignKey(Order, related_name='orderdetail', null=False, on_delete=models.CASCADE,
                              verbose_name="订单")


    sku = models.CharField(u'SKU', default='', max_length=100, blank=True)
    # product = models.CharField(u'产品名称',default='',  max_length=500,  blank=True)
    product_quantity = models.CharField(u'产品数量', default='', max_length=50, blank=True)
    # money_type = models.CharField(u'币种缩写', default='', max_length=50, blank=True)
    price = models.CharField(u'产品售价', default='', max_length=50, blank=True)


    # pic_url = models.CharField(u'图片网址', default='', max_length=200, blank=True)

    class Meta:
        verbose_name = "订单明细"
        verbose_name_plural = verbose_name
        # unique_together = (("order", "sku"),)


    def __str__(self):
        return self.order.order_no


class OrderConversation(models.Model):

    order = models.ForeignKey(Order, related_name='order2conversation', null=False,
                              verbose_name="订单", on_delete=models.CASCADE)

    conversation = models.ForeignKey(Conversation, related_name='conversation2order', null=False,
                                     verbose_name="会话", on_delete=models.CASCADE)


    class Meta:
        verbose_name = "订单_会话"
        verbose_name_plural = verbose_name


    def __str__(self):
        return self.order.order_no


class Verification(models.Model):
    conversation = models.ForeignKey(Conversation, related_name='verification2conversation', null=True, blank=True,
                                     verbose_name="会话", on_delete=models.CASCADE)


    # order_no = order_no = models.CharField(u'订单号',default='',  max_length=50,  blank=True)
    verify_code = models.CharField(u'验证码', default='', null=False, max_length=50, blank=True)
    verify_time = models.DateTimeField(u'验证时间', auto_now=False, null=True, blank=True)
    message_content = models.CharField(u'消息正文', default='', null=False, max_length=500, blank=True)

    valid = models.BooleanField(u'有效会话', default=False, null=True)


    class Meta:
        verbose_name = "会话-验证码"
        verbose_name_plural = verbose_name
        unique_together = (("conversation", "verify_code"),)


    def __str__(self):
        return self.conversation.conversation_no


class Verify(models.Model):

    VERIFY_STATUS = (
        ("NOSTART", "未启动"),
        ("PROCESSING", "审核中"),
        ("SUCCESS", "已审核"),
        ("SIMPLE", "简单问题"),
        ("COMPLEX", "复杂问题"),
        ("CLOSED", "关闭"),
        ("CUSTOMERCLOSED", "客户要求关闭"),
        ("CSCLOSED", "客服关闭"),
        ("TIMEOUTCLOSED", "超时关闭"),

    )
    SMS_STATUS = (
        ("NOSTART", "未发送"),
        ("CLOSED", "关闭"),
        ("WAIT", "待确认"),
        ("CHECKED", "已确认"),
        ("TIMEOUT", "超时"),
    )

    WAIT_STATUS = (
        ("NOSTART", "未启动"),
        ("CANCEL", "取消"),
        ("WAITREPLY", "等待回复"),
        ("NEEDPHONE", "待电话联系"),
        ("RESEND", "重发验证码"),
        ("VERIFY", "验证码已确认"),

    )

    SUPPLY_STATUS = (
        ("NORMAL", "正常"),
        ("STOP", "断货"),
        ("PAUSE", "缺货"),
    )



    # order = models.CharField(u'订单号', default='', max_length=50, blank=True)
    order = models.OneToOneField(Order, on_delete=models.CASCADE, primary_key=True, verbose_name="订单")

    # order = models.ForeignKey(Order, related_name='order', null=True, blank=True,
    #                                 verbose_name="订单", on_delete=models.CASCADE)
    # order = models.OneToOneField(Order, on_delete=models.CASCADE,  verbose_name="订单")

    verify_status = models.CharField(choices=VERIFY_STATUS, default="NOSTART", max_length=30, verbose_name="审单状态")

    # order_ids = models.CharField(u'订单号', max_length=20, null=True)
    # order_time = models.DateTimeField(u'下单时间', auto_now=False, null=True)
    # sales = models.CharField(u'销售客服', max_length=20, null=True)

    # ori_phone = models.CharField(u'客户电话', max_length=100, null=True)
    phone_1 = models.CharField(u'电话_1', max_length=50, null=True)
    phone_2 = models.CharField(u'电话_2', max_length=20, null=True, blank=True)
    phone_3 = models.CharField(u'电话_3', max_length=20, null=True, blank=True)

    sms_status = models.CharField(choices=SMS_STATUS, max_length=20, default='NOSEND', verbose_name="验证码状态")

    error_money = models.BooleanField(u'价格', default=None, null=True)
    error_contact = models.BooleanField(u'电话', default=None, null=True)
    error_address = models.BooleanField(u'地址', default=None, null=True)
    error_cod = models.BooleanField(u'COD', default=None, null=True)
    error_note = models.BooleanField(u'备注', default=None, null=True)
    error_timeout = models.BooleanField(u'超时', default=None, null=True)
    # err_code =  models.IntegerField(u'审核代码',default='',blank=True, null=True)

    supply_status = models.CharField(choices=SUPPLY_STATUS, max_length=20, default='NORMAL', verbose_name="供货状态")

    cancel = models.BooleanField(u'关闭', default=None, null=True)

    verify_comments = models.CharField(u'审单备注', max_length=200, default='', blank=True)
    verify_time = models.DateTimeField(u'审核时间', auto_now=True, null=True)
    cs_reply = models.CharField(u'客服回复', max_length=200, default='', blank=True)
    wait_status = models.CharField(choices=WAIT_STATUS, max_length=20, default='NOSTART', verbose_name="处理状态")
    cs = models.CharField(u'客服', max_length=50, default='')
    reply_time = models.CharField(u'回复时间', max_length=50, default='', null=True)

    start_time = models.DateTimeField(u'开始审核时间', auto_now=True, null=True)
    start_staff = models.CharField(u'开始审核人', max_length=50, null=True)
    final_time = models.DateTimeField(u'最后审核时间', auto_now=True, null=True)
    final_staff = models.CharField(u'最后审核人', max_length=256, null=True)

    sales = models.CharField(u'销售客服', max_length=100, null=True, blank=True)
    facebook_user_name = models.CharField(u'客户facebook姓名', default='', max_length=500, null=True, blank=True)

    conversation_link = models.CharField(u'会话链接', max_length=200, null=True, blank=True)


    class Meta:
        verbose_name = "审单"
        verbose_name_plural = verbose_name


    def __str__(self):
        return self.verify_status


    def colored_phone_1(self):
        # if ( self.error_money and self.error_contact and  self.error_address
        #        and self.error_cod   and self.error_note):
        #    self.verify_status = '已审核'
        if (len(self.phone_1) == 9):
            color_code = 'green'
        else:
            color_code = 'red'

        return format_html(
            '<span style="color:{};">{}</span>',
            color_code,
            self.phone_1,
        )


    colored_phone_1.short_description = u"电话1"


    def colored_verify_status(self):
        # if ( self.error_money and self.error_contact and  self.error_address
        #        and self.error_cod   and self.error_note):
        #    self.verify_status = '已审核'
        if (self.verify_status == 'SUCCESS'):

            color_code = 'green'
        elif (self.verify_status == 'COMPLEX' or self.verify_status == 'SIMPLE'):
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
        if self.sms_status == 'TIMEOUT':
            color_code = 'red'
        elif self.sms_status == 'CHECKED':
            color_code = 'green'
        else:
            color_code = 'blue'
        return format_html(
            '<span style="color:{};">{}</span>',
            color_code,
            self.get_sms_status_display(),
        )


    colored_sms_status.short_description = u"验证码状态"


class ClientService(Verify):
    class Meta:
        proxy = True

        verbose_name = "客服问题单"
        verbose_name_plural = verbose_name


    def __str__(self):
        return self.verify_status


class Logistic_winlink(models.Model):
    LOGISTIC_STATUS = (
        ("PROCESSING", "派送中"),

    )

    RESPONSE = (
        ("NONE", "待定"),
        ("DELIVER", "派送员"),
        ("CUSTOMER", "客户"),
        ("YALLAVIP", "YallaVIP"),
    )

    DEAL = (
        ("NONE", "待定"),
        ("DONE", "处理完成"),
        ("SETTLE", "待对账"),

        ("RETURN", "退仓中"),
        ("RETURNED", "已退到仓库"),
        ("LISTING", "已上架"),

        ("RE_DELIVER", "重新派送"),
        ("SEC_DELIVER", "二次派送中"),
        ("TRI_DELIVER", "三次派送中"),
        ("RECEIVED", "已签收"),
        ("WAIT", "沟通中"),
        ("NORESPONSE", "联系不到客户"),
    )

    # order = models.OneToOneField(Order, on_delete=models.CASCADE, to_field="logistic_no", primary_key=True,  verbose_name="订单")

    logistic_no = models.CharField(u'物流单号', max_length=50, null=True, blank=True)
    order_no = models.CharField(u'原订单号', max_length=100, null=True, blank=True)
    logistic_status = models.CharField(u'派送状态', max_length=50, null=True, blank=True)
    # country = models.CharField(u'国家', max_length=20, null=True, blank=True)
    # city = models.CharField(u'城市', max_length=20, null=True, blank=True)
    # shipping_date = models.DateTimeField(u'发运时间', auto_now=False, null=True, blank=True)
    # issue = models.CharField(u'问题', max_length=20, null=True, blank=True)
    comments = models.CharField(u'物流公司反馈', max_length=200, null=True, blank=True)
    his_comments = models.CharField(u'物流全部反馈', max_length=500, null=True, blank=True)
    logistic_update = models.DateTimeField(u'物流更新时间', auto_now=False, null=True, blank=True)

    response = models.CharField(choices=RESPONSE, max_length=20, default='NONE', verbose_name="责任")
    feedback = models.CharField(verbose_name="反馈原因", max_length=100, null=True, blank=True)
    feedback_time = models.DateTimeField(u'反馈时间', auto_now=False, null=True, blank=True)
    deal = models.CharField(choices=DEAL, max_length=50, default='NONE', verbose_name="处理办法", blank=True)
    img = models.ImageField(verbose_name='证据', upload_to='facebook/', null=True, blank=True)

    class Meta:
        verbose_name = "合联问题单"
        verbose_name_plural = verbose_name

    def image_tag(self):
        return u'<img width=50px src="%s" />' % (self.img)

    image_tag.short_description = '证据图片'
    image_tag.allow_tags = True

    def __str__(self):
        return self.logistic_no


class Logistic_jiacheng(models.Model):


    LOGISTIC_STATUS = (
        ("PROCESSING", "派送中"),

    )

    RESPONSE = (
        ("NONE", "待定"),
        ("DELIVER", "派送员"),
        ("CUSTOMER", "客户"),
        ("YALLAVIP", "YallaVIP"),
    )

    DEAL = (
        ("NONE", "待定"),
        ("DONE", "处理完成"),
        ("SETTLE", "待对账"),

        ("RETURN", "退仓中"),
        ("RETURNED", "已退到仓库"),
        ("LISTING", "已上架"),
        ("RE_DELIVER", "重新派送"),
        ("RE_DELIVERING", "二次派送中"),
        ("WAIT", "沟通中"),
        ("NORESPONSE", "联系不到客户"),
    )

    # order = models.OneToOneField(Order, on_delete=models.CASCADE, to_field="logistic_no", primary_key=True,  verbose_name="订单")

    logistic_no = models.CharField(u'物流单号', max_length=50, null=True, blank=True)
    order_no = models.CharField(u'原订单号', max_length=100, null=True, blank=True)
    tracking_no = models.CharField(u'转单号', max_length=50, null=True, blank=True)
    country = models.CharField(u'国家', max_length=50, null=True, blank=True)

    in_date = models.DateTimeField(u'签入时间', auto_now=False, null=True, blank=True)
    shipping_date = models.DateTimeField(u'出货时间', auto_now=False, null=True, blank=True)
    # issue = models.CharField(u'问题', max_length=100, null=True, blank=True)
    localphone = models.CharField(u'当地电话 ', max_length=100, null=True, blank=True)
    comments = models.CharField(u'问题件类型', max_length=200, null=True, blank=True)

    response = models.CharField(choices=RESPONSE, max_length=20, default='NONE', verbose_name="责任")
    feedback = models.CharField(verbose_name="反馈原因", max_length=100, null=True, blank=True)
    feedback_time = models.DateTimeField(u'反馈时间', auto_now=False, null=True, blank=True)
    deal = models.CharField(choices=DEAL, max_length=50, default='NONE', verbose_name="处理办法", blank=True)
    img = models.ImageField(verbose_name='证据', upload_to='facebook/', null=True, blank=True)


    class Meta:
        verbose_name = "佳成问题单"
        verbose_name_plural = verbose_name


    def image_tag(self):
        return u'<img width=50px src="%s" />' % (self.img)


    image_tag.short_description = '证据图片'
    image_tag.allow_tags = True


    def __str__(self):
        return self.logistic_no


class Logistic_status(models.Model):
    logistic_no = models.CharField(u'物流单号', max_length=50, null=True, blank=True)


    refer_no = models.CharField(u'参考号', max_length=50, null=True, blank=True)

    #    order_no = models.CharField(u'原订单号', max_length=100, null=True, blank=True)


    shipping_date = models.DateField(u'出货时间', auto_now=False, null=True, blank=True)
    tracking_no = models.CharField(u'转单号', max_length=50, null=True, blank=True)

    real_weight = models.CharField(u'实重', max_length=100, null=True, blank=True)
    size_weight = models.CharField(u'体积重', max_length=100, null=True, blank=True)
    charge_weight = models.CharField(u'计费重', max_length=100, null=True, blank=True)

    '''
    update_date = models.DateField(u'更新时间', auto_now=False, null=True, blank=True)
    update_place = models.CharField(u'更新地点', max_length=100, null=True, blank=True)
    logistic_status = models.CharField(u'签收状态 ', max_length=100, null=True, blank=True)
    '''


    class Meta:
        verbose_name = "物流信息"
        verbose_name_plural = verbose_name


    def __str__(self):
        return self.logistic_no


class Logistic_trail(models.Model):
    logistic_no = models.CharField(u'物流单号', max_length=50, null=True, blank=True)

    update_time = models.DateTimeField(u'更新时间', auto_now=False, null=True, blank=True)
    update_locate = models.CharField(u'更新地点', max_length=100, null=True, blank=True)
    trail_status = models.CharField(u'最新轨迹 ', max_length=100, null=True, blank=True)

    class Meta:
        verbose_name = "物流轨迹"
        verbose_name_plural = verbose_name
        ordering = ['update_time']

    def __str__(self):
        return self.logistic_no


class Sms(models.Model):
    send_time = models.DateTimeField(u'发送时间', auto_now=False, null=True, blank=True)
    send_status = models.CharField(u'发送状态', max_length=50, null=True, blank=True)
    content = models.CharField(u'内容', max_length=200, null=True, blank=True)
    phone = models.CharField(u'手机号', max_length=50, null=True, blank=True)
    receive_status = models.CharField(u'接收状态', max_length=50, null=True, blank=True)
    fail_reason = models.CharField(u'失败原因', max_length=50, null=True, blank=True)

    class Meta:
        verbose_name = "短信记录"
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.phone


class Logistic(Order):
    class Meta:
        proxy = True

        verbose_name = "订单物流状态"
        verbose_name_plural = verbose_name

        ordering = ['logistic_update_date']

    def __str__(self):
        return self.logistic_no

class OrderTrack(Order):
    class Meta:
        proxy = True

        verbose_name = "订单追踪"
        verbose_name_plural = verbose_name

        ordering = ['order_time']

    def __str__(self):
        return self.logistic_no

class LogisticAccount(models.Model):
    SETTLETYPE = (
        ("COD", "COD"),
        ("FEE", "运费"),
        ("COMPENSATE", "赔偿"),
    )

    logistic_no = models.CharField(u'物流追踪号', default='', max_length=100, blank=True)
    refer_no = models.CharField(u'参考号', max_length=50, null=True, blank=True)
    shipping_time = models.DateTimeField(u'出货时间', auto_now=False, null=True, blank=True)
    tracking_no = models.CharField(u'转单号', max_length=50, null=True, blank=True)

    real_weight = models.CharField(u'实重', max_length=100, null=True, blank=True)
    size_weight = models.CharField(u'体积重', max_length=100, null=True, blank=True)
    charge_weight = models.CharField(u'计费重', max_length=100, null=True, blank=True)

    COD = models.CharField(verbose_name="代收货款", max_length=100, null=True, blank=True)
    exchange = models.CharField(verbose_name="汇率", max_length=100, null=True, blank=True)
    currency = models.CharField(verbose_name="币种", max_length=100, null=True, blank=True)
    standard_currency = models.CharField(verbose_name="本位币金额", max_length=100, null=True, blank=True)
    fee = models.CharField(verbose_name="运费", max_length=100, null=True, blank=True)
    other_fee = models.CharField(verbose_name="其他杂费", max_length=100, null=True, blank=True)
    total_fee = models.CharField(verbose_name="运杂费", max_length=100, null=True, blank=True)
    refund = models.CharField(verbose_name="应退金额", max_length=100, null=True, blank=True)

    settle_type = models.CharField(choices=SETTLETYPE,verbose_name="结算类型", max_length=100, null=True, blank=True)
    PACKAGE_STATUS = (
        ("DELIVERED", "妥投"),
        ("TEMPORARY", "暂存站点"),
        ("RETURNED", "海外仓"),
        ("LOST", "丢失"),
        ("DELIVERING", "运输中"),
        ("RETURNING", "退仓中"),

        ("RESELLOUT", "二次售罄"),
    )

    package_status = models.CharField(choices=PACKAGE_STATUS, max_length=50, default='NONE', verbose_name="包裹状态",
                                      blank=True)

    class Meta:
        verbose_name = "物流对账"
        verbose_name_plural = verbose_name


    def __str__(self):
        return self.logistic_no



