from django.db import models
from django.utils.html import format_html
#from conversations.models import Conversation
from prs.models import  Lightin_SPU, Lightin_SKU,Lightin_barcode
from customer.models import  Customer,  CITY
from conversations.models import FbConversation

from django.contrib.auth import get_user_model

User = get_user_model()

# Create your models here.
class Order(models.Model):

    #新的以客户为中心的模型
    customer = models.ForeignKey(Customer, related_name='customer_order', null=True, on_delete=models.CASCADE,verbose_name="Customer")

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
    order_id = models.CharField(u'订单id', default='', max_length=100, blank=True, null=True)
    order_no = models.CharField(u'订单号', default='', max_length=50, unique=True, blank=True, null=True)
    updated = models.BooleanField(u'更新状态', default=False)
    #inventory_status  = models.CharField(u'库存状态', default='', max_length=50, blank=True)

    #不锁定条码
    def cal_stock(self):
        if not self.status == 'open' or self.wms_status == 'W':
            return  "已处理"

        items = self.order_orderdetail.all()
        if not items:
            return "没找到明细"

        outstock_skus = 0
        #outstock_quantity = 0
        #outstock_amount = 0

        busystock_skus = 0
        none_skus = 0
        stock_list =[]


        for item in items:
            stock_list.append(item.stock)

        if "没有产品" in stock_list:
            return  "没有产品"
        elif "缺货" in stock_list:
            return "缺货"

        elif "紧张" in stock_list:
            return "紧张"
        elif "充足" in stock_list:
            return "充足"

        '''    
            if item.stock == "缺货":
                outstock_skus += 1
                #outstock_quantity += item.outstock
                #outstock_amount += item.outstock * float(item.price)
            elif item.stock == "紧张":
                busystock_skus += 1
            elif item.stock == "没有产品":
                none_skus += 1

        stock = "共 %s个sku " %(items.count())

        if busystock_skus > 0:
            stock = stock + " %s 个sku紧张 " %( busystock_skus)

        if outstock_skus >0:
            stock = stock + " %s 个sku缺货 " % (outstock_skus)

        if none_skus >0:
            stock = stock + " %s 个sku没有产品 " % (none_skus)

        if busystock_skus ==0 and outstock_skus == 0 and none_skus == 0:
            stock = stock + "库存充足"
        '''


    cal_stock.short_description = "库存"
    stock = property(cal_stock)

    #锁定条码
    def cal_inventory_status(self):
        items = self.order_orderdetail.all()
        outstock_skus = 0
        outstock_quantity = 0
        outstock_amount = 0

        for item in items:

            if item.inventory_status == "缺货":
                outstock_skus += 1
                outstock_quantity += item.outstock
                outstock_amount += item.outstock * float(item.price)

        if outstock_skus == 0:
            return "库存锁定"
        else:
            return "共 %s个sku 缺货: %s 个sku %s 件  %s SAR" %(items.count(), outstock_skus,outstock_quantity,int(outstock_amount))

    cal_inventory_status.short_description = "库存状态"
    inventory_status = property(cal_inventory_status)


    #o_status = models.CharField(u'oms_订单状态', max_length=30, default='', blank=True)

    #shopify 订单状态

    status = models.CharField(u'shopify订单状态', max_length=30, default='paid', blank=True)
    financial_status = models.CharField(u'shopify订单支付状态', max_length=30, default='',null=True, blank=True)
    fulfillment_status = models.CharField(u'shopify订单仓配状态', max_length=100, default='',null=True, blank=True)

    #wms 订单处理状态， C:待发货审核 W:待发货 D:已发货 H:暂存 N:异常订单 P:问题件 X:废弃
    fulfill_error = models.CharField(u'wms发货错误', max_length=500, default='', blank=True)
    wms_status = models.CharField(u'wms订单状态', max_length=30, default='', blank=True)
    track_status = models.CharField(u'wms派送状态', max_length=30, default='', blank=True)
    #totalFee = models.DecimalField(verbose_name="费用小计",)

    order_status = models.CharField(u'订单状态', max_length=30, default='未知', blank=True)

    buyer_name = models.CharField(u'买家姓名', default='', max_length=500, blank=True)

    # product_quantity = models.CharField(u'产品数量', default='', max_length=50, blank=True)
    order_amount = models.CharField(u'订单金额', default='', max_length=50, blank=True)

    def cal_real_amount(self):
        if self.verify.real_amount == "":
            return  self.order_amount
        else:
            return  self.verify.real_amount

    cal_real_amount.short_description = "实收金额"
    real_amount = property(cal_real_amount)


    order_comment = models.CharField(u'订单备注', max_length=500, default='', null=True, blank=True)
    warhouse_comment = models.CharField(u'拣货备注', max_length=500, default='', null=True, blank=True)
    cs_comment = models.CharField(u'客服备注', max_length=500, default='', null=True, blank=True)

    receiver_name = models.CharField(u'收货人姓名', default='', max_length=500, null=True,blank=True)
    receiver_addr1 = models.CharField(u'地址1', default='', max_length=500, null=True,blank=True)
    receiver_addr2 = models.CharField(u'地址2', default='', max_length=500, null=True,blank=True)
    receiver_city = models.CharField(u'城市', choices=CITY,max_length=100, default= 'None',null=True, blank=True)

    receiver_country = models.CharField(u'收货人国家', default='', max_length=500, null=True,blank=True)
    receiver_phone = models.CharField(u'收货人电话', default='', max_length=500, null=True,blank=True)
    receiver_phone_2 = models.CharField(u'收货人电话_2', default='', max_length=500, null=True, blank=True)

    package_no = models.CharField(u'包裹号', default='', max_length=100, blank=True)
    logistic_no = models.CharField(u'物流追踪号', default='', max_length=100, blank=True)
    waybillnumber = models.CharField(u'佳成单号', default='', max_length=100, blank=True)

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
        ("SELLING", "二次售出"),
        ("SELLOUT", "二次售罄"),
        ("DESTROYED", "销毁"),



    )
    resell_status = models.CharField(choices=RESELL_STTUS, max_length=50, default='UNLISTING', verbose_name="二次销售状态",
                                   blank=True)

    conversation = models.ForeignKey(FbConversation,  blank=True, null=True,on_delete=models.CASCADE, verbose_name="客户会话")
    user = models.ForeignKey(User, blank=True, null=True, verbose_name='用户', help_text='用户', on_delete=models.CASCADE, related_name='user_order')
    add_time = models.DateTimeField(auto_now_add=True, verbose_name='添加时间', null=True, blank=True)


    class Meta:
        verbose_name = "订单"
        verbose_name_plural = verbose_name


    def __str__(self):
        return self.order_no

class OrderDetail(models.Model):
    order = models.ForeignKey(Order, related_name='order_orderdetail', null=False, on_delete=models.CASCADE,
                              verbose_name="Order")

    F_SKU = models.ForeignKey(Lightin_SKU, related_name='sku_orderdetail', null=False, on_delete=models.CASCADE,
                              verbose_name="SKU")

    sku = models.CharField(u'SKU', default='', max_length=100, null=True, blank=True)
    # product = models.CharField(u'产品名称',default='',  max_length=500,  blank=True)
    product_quantity = models.CharField(u'Quantity', default='', max_length=50, blank=True)
    # money_type = models.CharField(u'币种缩写', default='', max_length=50, blank=True)
    price = models.CharField(u'Unit Price', default='', max_length=50, blank=True)

    #inventory_status = models.CharField(u'库存状态', default='', max_length=50, blank=True)

    def cal_stock(self):
        if not self.order.status == 'open':
            return  self.order.status

        sku_list = ["13531030880298", "price gap", "COD link", "price gap 2", ]
        if self.sku in sku_list:
            return "充足"

        items = Lightin_SKU.objects.filter(SKU=self.sku)

        if items:
            item = items[0]
            if   item.o_sellable >=0:
                return "充足"
            elif (item.o_quantity - item.o_locked)>= int(float(self.product_quantity)):
                return  "紧张"
            else:
                return  "缺货"
        else:
            return "没有产品"

    cal_stock.short_description = "库存状态"
    stock = property(cal_stock)


    class Meta:
        verbose_name = "订单明细"
        verbose_name_plural = verbose_name
        # unique_together = (("order", "sku"),)


    def __str__(self):
        return self.sku

class OrderDetail_lightin(models.Model):
    order = models.ForeignKey(Order, related_name='order_orderdetail_lightin', null=False, on_delete=models.CASCADE,
                              verbose_name="Order")

    SKU = models.CharField(u'SKU', default='', max_length=100, null=True, blank=True)


    #barcode = models.CharField(u'barcode', default='', max_length=100, blank=True)
    barcode = models.ForeignKey(Lightin_barcode, related_name='barcode_orderdetail_lightin', null=False, on_delete=models.CASCADE,
                              verbose_name="barcode")

    quantity = models.IntegerField(u'数量', default=0, blank=True, null=True)
    price = models.CharField(u'Unit Price', default='', max_length=50, blank=True)

    class Meta:
        verbose_name = "订单明细_lightin"
        verbose_name_plural = verbose_name



    def __str__(self):
        return self.barcode.barcode


class OrderConversation(models.Model):

    order = models.ForeignKey(Order, related_name='order2conversation', null=False,
                              verbose_name="订单", on_delete=models.CASCADE)

    #conversation = models.ForeignKey(Conversation, related_name='conversation2order', null=False,
     #                                verbose_name="会话", on_delete=models.CASCADE)


    class Meta:
        verbose_name = "订单_会话"
        verbose_name_plural = verbose_name


    def __str__(self):
        return self.order.order_no


class Verification(models.Model):
    #conversation = models.ForeignKey(Conversation, related_name='verification2conversation', null=True, blank=True,
     #                                verbose_name="会话", on_delete=models.CASCADE)


    # order_no = order_no = models.CharField(u'订单号',default='',  max_length=50,  blank=True)
    verify_code = models.CharField(u'验证码', default='', null=False, max_length=50, blank=True)
    verify_time = models.DateTimeField(u'验证时间', auto_now=False, null=True, blank=True)
    message_content = models.CharField(u'消息正文', default='', null=False, max_length=500, blank=True)

    valid = models.BooleanField(u'有效会话', default=False, null=True)


    class Meta:
        verbose_name = "会话-验证码"
        verbose_name_plural = verbose_name
        #unique_together = (("conversation", "verify_code"),)


    def __str__(self):
        return self.conversation.conversation_no


class Verify(models.Model):

    VERIFY_STATUS = (
        ("NOSTART", "未启动"),
        ("PROCESSING", "审核中"),
        ("SUCCESS", "已审核"),
        ("OUTRANGE", "超出派送范围"),
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
        ("DELAY", "缺货"),
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
    sms_code = models.CharField( max_length=20, default='', verbose_name="回收的验证码")

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

    OUT_OF_STOCK = (
        ("NONE", "未处理"),
        ("ASKED", "已发送话术"),
        ("AGREE", "同意"),
        ("WAIT", "愿意等货"),
        ("REFUSE", "不同意"),
        ("NOREPLY", "无反应"),
    )
    deal_outofstock = models.CharField(choices=OUT_OF_STOCK, max_length=20, default='NONE', verbose_name="缺货处理")
    real_amount = models.CharField(u'实收金额', default='', max_length=50, blank=True)

    start_time = models.DateTimeField(u'开始审核时间', auto_now=True, null=True)
    start_staff = models.CharField(u'开始审核人', max_length=50, null=True)
    final_time = models.DateTimeField(u'最后审核时间', auto_now=True, null=True)
    final_staff = models.CharField(u'最后审核人', max_length=256, null=True)

    sales = models.CharField(u'销售客服', max_length=100, null=True, blank=True)
    facebook_user_name = models.CharField(u'客户facebook姓名', default='', max_length=500, null=True, blank=True)

    conversation_link = models.CharField(u'会话链接', max_length=500, null=True, blank=True)

    business_id = models.CharField(u'business_id', max_length=500, null=True, blank=True)
    mailbox_id = models.CharField(u'mailbox_id', max_length=500, null=True, blank=True)
    selected_item_id = models.CharField(u'selected_item_id', max_length=500, null=True, blank=True)









    city = models.CharField(u'城市', choices=CITY,max_length=100, default= 'None',null=True, blank=True)
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


class OverseaOrder(Order):
    class Meta:
        proxy = True

        verbose_name = "在海外仓的包裹"
        verbose_name_plural = verbose_name

        ordering = ['order_amount']

    def __str__(self):
        return self.logistic_no

class OverseaSkuRank(models.Model):
    sku = models.CharField(u'SKU', default='', max_length=100, null=True, blank=True)
    orders =  models.IntegerField(u'包裹数量',default=0,blank=True, null=True)

    class Meta:
        verbose_name = "在海外仓的爆款"
        verbose_name_plural = verbose_name

        ordering = ['-orders']

    def __str__(self):
        return self.sku

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

class MyOrder(models.Model):
    buyer_name = models.CharField(u'买家姓名', default='', max_length=500, blank=True)
    class Meta:
        verbose_name = "YallaVIP Order"
        verbose_name_plural = verbose_name


    def __str__(self):
        return self.buyer_name

class MyOrderDetail(models.Model):
    order = models.ForeignKey(MyOrder, related_name='my_order_orderdetail', null=False, on_delete=models.CASCADE,
                              verbose_name="Order")
    '''
    lightin_spu = models.ForeignKey(Lightin_SPU, related_name='lightin_spu_orderdetail', null=True,
                                    on_delete=models.CASCADE,
                                    verbose_name="货号")
    '''
    handle = models.CharField(default='', max_length=300, null=True, blank=True, verbose_name="handle")
    lightin_sku = models.ForeignKey(Lightin_SKU, related_name='lightin_sku_orderdetail', null=True, on_delete=models.CASCADE,
                              verbose_name="sku")
    #sku = models.CharField(u'SKU', default='', max_length=100, null=True, blank=True)
    quantity = models.CharField(u'Quantity', default='', max_length=50, blank=True)
    price = models.CharField(u'Unit Price', default='', max_length=50, blank=True)



    def cal_amount(self):
        return  self.product_quantity * self.price

    cal_amount.short_description = "小计"
    amount = property(cal_amount)


    class Meta:
        verbose_name = "YallaVIP OrderItem"
        verbose_name_plural = verbose_name


    def __str__(self):
        return self.lightin_sku.skuattr
'''
class Customer(models.Model):
    name = models.CharField(u'买家姓名', default='', max_length=100, blank=True,null=False)

    receiver_name = models.CharField(u'收货人姓名', default='', max_length=100, blank=True,null=False)

    COUNTRIES = (
        ("SA", "SA"),

    )
    country_code = models.CharField(u'country_code',choices=COUNTRIES, default='SA', max_length=10, blank=False,null=False)

    CITIES = (
        ("riyadh", "Riyadh"),
        ("jeddah", "Jeddah"),
        ("dammam", "Dammam"),
        ("al khobar", "Al Khobar"),
        ("hofuf", "Hofuf"),
        ("jubail", "Jubail"),
        ("dhahran", "Dhahran"),
        ("tabuk", "Tabuk"),
        ("buraydah", "Buraydah"),
        ("al hassa", "Al Hassa"),
        ("jizan", "Jizan"),
        ("qatif", "Qatif"),
    )

    city = models.CharField(u'city', choices=CITIES, default='', max_length=20, blank=False,null=False)
    address1 = models.CharField(u'address1', default='', max_length=100, blank=False,null=False)
    address2 = models.CharField(u'address2', default='', max_length=100, blank=True)
    address3 = models.CharField(u'address3', default='', max_length=100, blank=True)
    phone_1 = models.CharField(u'phone_1', default='', max_length=100, blank=False,null=False)
    phone_2 = models.CharField(u'phone_1', default='', max_length=100, blank=True)

    comments = models.TextField(u'备注', blank=True, null=True)
    conversation = models.CharField(u'聊天链接', default='', max_length=100, blank=False,null=False)

    class Meta:
        verbose_name = "客户"
        verbose_name_plural = verbose_name


    def __str__(self):
        return self.name + "  " + self.phone_1

class CsOrder(models.Model):

    customer = models.ForeignKey(Customer, related_name='customer_cs_order', null=False, on_delete=models.CASCADE,
                                verbose_name="Customer")



    handles = models.TextField(u'货号',blank=True, null=True)
    discount = models.CharField(u'discount', default='0', max_length=100, blank=True)

    order_amount = models.IntegerField(u'COD金额', default=0, blank=True, null=True)

    sales = models.CharField(u'Sales', default='', max_length=50, blank=True)

    class Meta:
        verbose_name = "客服下单"
        verbose_name_plural = verbose_name


    def __str__(self):
        if self.customer:
            return self.customer.name
        else:
            return  ""

class CsOrderDetail(models.Model):
    csorder = models.ForeignKey(CsOrder, related_name='cs_order_detail', null=False, on_delete=models.CASCADE,
                              verbose_name="CsOrder")

    lightin_sku = models.ForeignKey(Lightin_SKU, related_name='lightin_sku_detail', null=False, on_delete=models.CASCADE,
                                verbose_name="lightin_sku")

    price = models.CharField(u'单价', default='', max_length=50, blank=True)
    quantity = models.IntegerField(u'数量', default=0, blank=True, null=True)


    class Meta:
        verbose_name = "客服下单明细"
        verbose_name_plural = verbose_name


    def __str__(self):
        return self.lightin_sku.SKU


'''



class Order_History(Order):
    class Meta:
        proxy = True

        verbose_name = "历史订单"
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.order_no

class Order_Detail_Real(OrderDetail):
    class Meta:
        proxy = True

        verbose_name = "真实发货订单明细"
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.order.order_no


