from django.db import models
from django.utils.html import format_html
from pytz import timezone
from datetime import  datetime
from django.utils import timezone as dt


# Create your models here.
class Package(models.Model):
    super_package = models.ForeignKey('self', null=True, on_delete=models.CASCADE,
                                 verbose_name="父包裹")

    logistic_no = models.CharField(u'物流追踪号', default='', max_length=100, blank=True)
    refer_no = models.CharField(u'包裹号', max_length=50, null=True, blank=True)
    tracking_no = models.CharField(u'转单号', max_length=50, null=True, blank=True)
    send_time = models.DateTimeField(u'发货时间', auto_now=False, blank=True, null=True)

    logistic_supplier = models.CharField(u'物流供应商', max_length=50, null=True, blank=True)
    real_weight = models.CharField(u'实重', max_length=100, null=True, blank=True)
    size_weight = models.CharField(u'体积重', max_length=100, null=True, blank=True)
    charge_weight = models.CharField(u'计费重', max_length=100, null=True, blank=True)
    logistic_start_date = models.DateField(u'物流收货时间', auto_now=False, null=True, blank=True)
    logistic_update_date = models.DateField(u'物流更新时间', auto_now=False, null=True, blank=True)
    logistic_update_status = models.CharField(verbose_name='物流状态', max_length=100, null=True,
                                              blank=True)
    logistic_update_locate = models.CharField(u'物流更新地点', max_length=100, null=True, blank=True)

    update_trail_time = models.DateTimeField(u'轨迹更新时间', auto_now=False, blank=True, null=True)
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
    resend_start_time = models.DateTimeField(u'重派启动时间', auto_now=False, null=True, blank=True)


    DEAL = (
        ("NONE", "待定"),
        ("WAITING", "沟通中"),


        ("DELIVERED", "已签收"),
        ("REFUSED", "拒签"),
        ("RE_DELIVER", "重新派送"),
        ("LOSTCONNECT", "无法联系"),

        ("LOST", "丢件"),
        ("RE_DELIVERING", "重新派送中"),



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
    wait_status = models.BooleanField(default=False, verbose_name="等待确认")

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

    WAREHOUSE_CHECK_STATUS = (
        ("NONE", "未处理"),
        ("DISCARD", "废弃订单"),
        ("MULTIPACKAGE", "多包裹"),
        ("TOCLEAR", "状态不明待确认"),
        ("TOREFUND", "签收待确认"),
        ("TORETURN", "退仓待确认"),
        ("TOLOST", "丢件待确认"),
        ("BALANCED", "已对账"),

    )

    warehouse_check = models.CharField(choices=WAREHOUSE_CHECK_STATUS, max_length=50, default='NONE', verbose_name="仓库核实状态",blank=True)
    warehouse_check_comments = models.CharField(u'仓库核实说明', default='', max_length=200, blank=True)
    child_packages =  models.CharField(max_length=200, default='NONE', verbose_name="子包裹",blank=True)
    warehouse_checktime = models.DateTimeField(u'仓库核实时间', auto_now=False, blank=True, null=True)
    warehouse_check_manager = models.CharField(u'仓库核实负责人', default='', max_length=200, blank=True)

    def cal_total_date(self):
        cst_tz = timezone('Asia/Shanghai')

        if self.file_status =="OPEN":
            if self.send_time is not None:
                now = datetime.now().replace(tzinfo=cst_tz)
                return (now - self.send_time).days
            else:
                return "没有发货信息"
        else:
            if self.logistic_update_date is not None and self.send_time is not None:
                return (self.logistic_update_date - self.send_time.date()).days
            else:
                return "没有轨迹信息"

    cal_total_date.short_description = "累计交运时间(天)"
    total_date = property(cal_total_date)

    def cal_total_trans_date(self):
        cst_tz = timezone('Asia/Shanghai')

        if self.file_status =="OPEN":
            if self.logistic_start_date is not None:
                now = datetime.now().replace(tzinfo=cst_tz)
                days = (now.date() - self.logistic_start_date).days

                if days > 40:
                    color_code = 'red'
                    days = days + " (超时了！)"
                else:
                    color_code = 'greed'

                return format_html(
                    '<span style="color:{};">{}</span>',
                    color_code,
                    days,
                )
            else:
                return "没有轨迹信息"
        else:
            if self.logistic_update_date is not None and self.logistic_start_date is not None:
                return (self.logistic_update_date - self.logistic_start_date).days
            else:
                return "没有轨迹信息"

    cal_total_trans_date.short_description = "累计运输时间(天)"
    total_trans_date = property(cal_total_trans_date)

    def cal_lost_date(self):
        cst_tz = timezone('Asia/Shanghai')

        if self.file_status =="OPEN":
            if self.logistic_update_date is not None:
                now = datetime.now().replace(tzinfo=cst_tz)
                return (now.date() - self.logistic_update_date).days
            else:
                return "没有轨迹信息"
        else:
            return 0

    cal_lost_date.short_description = "最后更新时间(天)"
    lost_date = property(cal_lost_date)

    '''
    def save(self, *args, **kwargs):
        cst_tz = timezone('Asia/Shanghai')
        now = datetime.now().replace(tzinfo=cst_tz)

        self.feedback_time = now
        print("@@@@@@@@@@@@@")
        super().save(*args, **kwargs)
    '''

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
    def cal_waite_date(self):
        cst_tz = timezone('Asia/Shanghai')



        if self.file_status =="OPEN":
            if self.feedback_time is not None:
                now = datetime.now().replace(tzinfo=cst_tz)
                days = (now - self.feedback_time).days
                if days >= 3:
                    color_code = 'red'
                    days =  str(days) +"  (超时!)"

                else:
                    color_code = 'greed'

                return format_html(
                    '<span style="color:{};">{}</span>',
                    color_code,

                    days,
                )
            else:
                return format_html(
                    '<span style="color:{};">{}</span>',
                    'red',
                    "没有沟通",
                )

        else:
           return "已关闭"

    cal_waite_date.short_description = "沟通时间(天)"
    waite_date = property(cal_waite_date)

    class Meta:
        proxy = True

        verbose_name = "客服物流跟踪"
        verbose_name_plural = verbose_name


    def __str__(self):
        return self.logistic_no

class LogisticManagerConfirm(Package):
    class Meta:
        proxy = True

        verbose_name = "客服主管审核"
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.logistic_no

class LogisticResendTrail(Package):

    def cal_resend_date(self):
        cst_tz = timezone('Asia/Shanghai')

        if self.file_status =="OPEN":
            if self.feedback_time is not None:
                now = datetime.now().replace(tzinfo=cst_tz)
                return (now - self.feedback_time).days
            else:
                return "没有时间信息"
        else:
            if self.logistic_update_date is not None and self.feedback_time is not None:
                return (self.logistic_update_date - self.feedback_time.date()).days
            else:
                return "没有时间信息"

    cal_resend_date.short_description = "反馈重派时间(天)"
    resend_date = property(cal_resend_date)

    def cal_resend_stat(self):
        cst_tz = timezone('Asia/Shanghai')

        if self.file_status =="OPEN":
            if self.feedback_time is not None and self.logistic_update_date is not None:
                days = (self.logistic_update_date - self.feedback_time.date()).days

                if days <0 :
                    color_code = 'red'
                    days = "还没开始重派"
                else:
                    color_code = 'green'
                    days = str(days) + " 物流有更新"

                return format_html(
                    '<span style="color:{};">{}</span>',
                    color_code,
                    days,
                )

            else:
                return "没有时间信息"
        else:
            if self.logistic_update_date is not None and self.feedback_time is not None:
                return (self.logistic_update_date - self.feedback_time.date()).days
            else:
                return "没有时间信息"

    cal_resend_stat.short_description = "重派动态"
    resend_stat = property(cal_resend_stat)

    class Meta:
        proxy = True

        verbose_name = "客服物流重派跟踪"
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
    money = models.CharField(u'币种', default='SAR', max_length=100, blank=True, null=True)
    exchange = models.CharField(u'汇率', default='1.78', max_length=100, blank=True, null=True)
    cod_base = models.CharField(u'本位币金额', default='', max_length=100, blank=True, null=True)
    freight = models.CharField(u'运费', default='', max_length=100, blank=True, null=True)
    cod_fee = models.CharField(u'代收款手续费', default='', max_length=100, blank=True, null=True)
    vat = models.CharField(u'VAT', default='', max_length=100, blank=True, null=True)
    re_deliver = models.CharField(u'重派费', default='', max_length=100, blank=True, null=True)
    print_fee = models.CharField(u'打单费', default='', max_length=100, blank=True, null=True)
    other_fee = models.CharField(u'其他杂费', default='', max_length=100, blank=True, null=True)
    comment = models.CharField(u'备注', default='', max_length=100, blank=True, null=True)

    receivable = models.CharField(u'应收金额', default='', max_length=100, blank=True, null=True)
    refunded = models.CharField(u'应退金额', default='', max_length=100, blank=True, null=True)


    upload_time = models.DateTimeField(u'上传时间', auto_now=True, blank=True, null=True)



    class Meta:
        verbose_name = "物流对账"
        verbose_name_plural = verbose_name


    def __str__(self):
        return str(self.waybillnumber) + "_" + self.balance_type + "_" + self.batch

class Overtime(Package):
    class Meta:
        proxy = True

        verbose_name = "超时订单"
        verbose_name_plural = verbose_name


    def __str__(self):
        return self.logistic_no

class Reminder(Package):
    class Meta:
        proxy = True

        verbose_name = "物流催单"
        verbose_name_plural = verbose_name


    def __str__(self):
        return self.logistic_no

class MultiPackage(Package):
    class Meta:
        proxy = True

        verbose_name = "待处理多包裹"
        verbose_name_plural = verbose_name


    def __str__(self):
        return self.logistic_no

class ToBalance(Package):
    class Meta:
        proxy = True

        verbose_name = "待对账"
        verbose_name_plural = verbose_name


    def __str__(self):
        return self.logistic_no



class DealTrail(models.Model):
    package = models.ForeignKey(Package, related_name='package_dealtrail', null=True, on_delete=models.SET_NULL,
                              verbose_name="包裹")

    waybillnumber = models.CharField(u'物流追踪号', default='', max_length=100, blank=True)
    deal_type  = models.CharField(u'处理类型', default='', max_length=500, blank=True)
    deal_staff = models.CharField(u'处理人', default='', max_length=500, blank=True)
    deal_time = models.DateTimeField(u'处理时间', auto_now=True, blank=True, null=True)
    deal_action = models.CharField(u'处理动作', default='', max_length=100, blank=True)
    deal_comments= models.CharField(u'处理备注', default='', max_length=100, blank=True,null=True)


    class Meta:
        verbose_name = "处理日志"
        verbose_name_plural = verbose_name


    def __str__(self):
        return self.waybillnumber + "_" + self.deal_comments