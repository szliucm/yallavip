from django.db import models

# Create your models here.
class Package(models.Model):
    logistic_no = models.CharField(u'物流追踪号', default='', max_length=100, blank=True)
    refer_no = models.CharField(u'包裹号', max_length=50, null=True, blank=True)
    tracking_no = models.CharField(u'转单号', max_length=50, null=True, blank=True)
    send_time = models.DateTimeField(u'发货时间', auto_now=False, blank=True, null=True)

    real_weight = models.CharField(u'实重', max_length=100, null=True, blank=True)
    size_weight = models.CharField(u'体积重', max_length=100, null=True, blank=True)
    charge_weight = models.CharField(u'计费重', max_length=100, null=True, blank=True)
    logistic_start_date = models.DateField(u'物流收货时间', auto_now=False, null=True, blank=True)
    logistic_update_date = models.DateField(u'物流更新时间', auto_now=False, null=True, blank=True)
    logistic_update_status = models.CharField(verbose_name='物流状态', max_length=100, null=True,
                                              blank=True)
    logistic_update_locate = models.CharField(u'物流更新地点', max_length=100, null=True, blank=True)

    # 问题件
    problem_type = models.CharField(u'问题类型', max_length=200, null=True, blank=True)
    RESPONSE = (
        ("NONE", "待定"),
        ("DELIVER", "派送员"),
        ("CUSTOMER", "客户"),
        ("YALLAVIP", "YallaVIP"),
    )
    response = models.CharField(choices=RESPONSE, max_length=20, default='NONE', verbose_name="责任")
    feedback = models.CharField(verbose_name="反馈原因", max_length=100, null=True, blank=True)
    feedback_time = models.DateTimeField(u'反馈时间', auto_now=False, null=True, blank=True)

    DEAL = (
        ("NONE", "待定"),

        ("LOST", "丢件"),

        ("DELIVERED", "已签收"),

        ("WAITING", "沟通中"),
        ("RE_DELIVER", "重新派送"),
        ("RE_DELIVERING", "重新派送中"),

        ("REFUSED", "拒签"),
        #("RETURNING", "退仓中"),
        #("RETURNED", "已退到仓库"),
    )
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
        ("LOST", "丢失"),
        ("PROBLEM", "问题件"),

        ("TEMPORARY", "暂存站点"),
        ("RETURNED", "海外仓"),
        ("RETURNING", "退仓中"),

        ("REDELIVERING", "二次销售派送中"),
        ("RESELLOUT", "二次售罄"),
    )

    package_status = models.CharField(choices=PACKAGE_STATUS, max_length=50, default='NONE', verbose_name="物流公司包裹状态", blank=True)

    yallavip_package_status = models.CharField(choices=PACKAGE_STATUS, max_length=50, default='NONE', verbose_name="中仪包裹状态",
                                      blank=True)

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

    RESELL_STATUS = (
        ("NONE", "未处理"),
        ("LISTING", "上架中"),
        ("UNLISTING", "下架中"),
        ("REDELIVERING", "二次销售派送中"),
        ("SELLOUT", "二次售罄"),
        ("DESTROYED", "销毁"),


    )
    resell_status = models.CharField(choices=RESELL_STATUS, max_length=50, default='UNLISTING', verbose_name="二次销售状态",
                                   blank=True)

    sec_logistic_no = models.CharField(u'二次物流追踪号', default='', max_length=100, blank=True)

    class Meta:
        verbose_name = "包裹追踪"
        verbose_name_plural = verbose_name


    def __str__(self):
        return self.logistic_no

class LogisticSupplier(Package):
    class Meta:
        proxy = True

        verbose_name = "物流公司更新数据"
        verbose_name_plural = verbose_name


    def __str__(self):
        return self.logistic_no

class LogisticCustomerService(Package):
    class Meta:
        proxy = True

        verbose_name = "客服物流跟踪"
        verbose_name_plural = verbose_name


    def __str__(self):
        return self.logistic_no

class OverseaPackage(Package):
    class Meta:
        proxy = True

        verbose_name = "海外包裹跟踪"
        verbose_name_plural = verbose_name


    def __str__(self):
        return self.logistic_no


class Resell(Package):
    class Meta:
        proxy = True

        verbose_name = "海外仓销售"
        verbose_name_plural = verbose_name


    def __str__(self):
        return self.logistic_no

class LogisticTrail(models.Model):
    waybillnumber = models.CharField(u'物流追踪号', default='', max_length=100, blank=True)
    trail_status  = models.CharField(u'发生状态', default='', max_length=500, blank=True)
    trail_statuscnname = models.CharField(u'发生状态_zh', default='', max_length=500, blank=True)
    trail_time = models.DateTimeField(u'发生时间', auto_now=False, blank=True, null=True)
    trail_locaiton= models.CharField(u'发生地点', default='', max_length=100, blank=True)


    class Meta:
        verbose_name = "物流轨迹"
        verbose_name_plural = verbose_name


    def __str__(self):
        return self.waybillnumber + "_" + self.trail_status

class LogisticBalance(models.Model):
    package = models.ForeignKey(Package, related_name='package_balance', null=True, on_delete=models.SET_NULL,
                              verbose_name="包裹")
    waybillnumber = models.CharField(u'物流追踪号', default='', max_length=100, blank=True)

    BALANCE_TYPE = (
        ("COD",    "COD收款"),
        ("RETURN", "退仓"),
        ("RESEND", "重派"),
        ("COMPANSATE", "赔偿"),


    )
    balance_type =  models.CharField(choices=BALANCE_TYPE, default='COD', max_length=30, null=True, blank=True,
                                verbose_name="对账类型")
    batch = models.CharField(u'批次', default='', max_length=100, blank=True)
    charge_weight = models.CharField(u'计费重', default='', max_length=100, blank=True)
    cod = models.CharField(u'代收货款', default='', max_length=100, blank=True, null=True)
    money = models.CharField(u'币种', default='', max_length=100, blank=True, null=True)
    exchange = models.CharField(u'汇率', default='', max_length=100, blank=True, null=True)
    cod_base = models.CharField(u'本位币金额', default='', max_length=100, blank=True, null=True)
    freight = models.CharField(u'运费', default='', max_length=100, blank=True, null=True)
    cod_fee = models.CharField(u'代收款手续费', default='', max_length=100, blank=True, null=True)
    vat = models.CharField(u'VAT', default='', max_length=100, blank=True, null=True)
    re_deliver = models.CharField(u'重派费', default='', max_length=100, blank=True, null=True)
    print_fee = models.CharField(u'打单费', default='', max_length=100, blank=True, null=True)
    other_fee = models.CharField(u'其他杂费', default='', max_length=100, blank=True, null=True)
    comment = models.CharField(u'备注', default='', max_length=100, blank=True, null=True)

    receivable = models.CharField(u'应收金额', default='', max_length=100, blank=True, null=False)
    refunded = models.CharField(u'应退金额', default='', max_length=100, blank=True, null=False)


    upload_time = models.DateTimeField(u'上传时间', auto_now=True, blank=True, null=True)



    class Meta:
        verbose_name = "物流对账"
        verbose_name_plural = verbose_name


    def __str__(self):
        return self.waybillnumber + "_" + self.balance_type + "_" + self.batch