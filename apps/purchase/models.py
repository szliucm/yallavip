from django.db import models
from sysadmin.models import ActionLog

# Create your models here.
class Purchase(models.Model):
    LOGISITIC_STATUS = (
        ("NORMAL", "正常"),
        ("RECEIVED", "显示已签收"),
        ("LOST", "物流丢件"),
        ("MISS", "供应商漏发"),
    )
    RESPONSE = (
        ("NONE", "待定"),
        ("WAREHOUSE", "仓库"),
        ("SUPPLIER", "供应商"),
        ("BUYER", "采购"),
        ("DELIVER", "快递员"),
    )

    DEAL = (
        ("NONE", "待定"),
        ("DONE", "处理完成"),

        ("RETURN", "要求退货"),
        ("RETURNED", "已退货"),

        ("REFUND", "要求退款"),
        ("REFUNDED", "已退款"),

    )

    purchase_no = models.CharField(u'采购单号',default='',  max_length=50,  blank=True)
    logistic_fee = models.CharField(u'运费',default='',  max_length=50,  blank=True)
    other_fee = models.CharField(u'其它费用',default='',  max_length=50,  blank=True)
    discount = models.CharField(u'采购单折扣金额', default='', max_length=50, blank=True)
    need_pay = models.CharField(u'采购单应付总额', default='', max_length=50, blank=True)
    warehouse = models.CharField(u'库位', default='', max_length=50, blank=True)
    supplier = models.CharField(u'供货商名称', default='', max_length=100, blank=True)
    contacter = models.CharField(u'联系人', default='', max_length=50, blank=True)
    logistic_no = models.CharField(u'运单号', default='', max_length=500, blank=True)
    ali_no = models.CharField(u'1688订单号', default='', max_length=50, blank=True)
    purchase_time = models.CharField(u'创建时间', default='', max_length=50, blank=True)
    receive_time = models.CharField(u'到货时间', default='', max_length=50, blank=True)
    receive_status = models.CharField(u'到货状态', default='', max_length=50, blank=True)
    comment  = models.CharField(u'备注', default='', max_length=500, blank=True)

    logistic_status = models.CharField(choices=LOGISITIC_STATUS, default="NORMAL",max_length=30,  verbose_name="物流状态")
    response = models.CharField(choices=RESPONSE, max_length=20, default='NONE', verbose_name="责任")
    #deal = models.CharField(choices=DEAL, max_length=50, default='NONE', verbose_name="处理办法", blank=True)
    deal = models.CharField( max_length=50, default='', verbose_name="处理办法", blank=True)
    class Meta:
        verbose_name = "采购单"
        verbose_name_plural = verbose_name
    def __str__(self):
        return  self.purchase_no


class PurchaseDetail(models.Model):
    purchase = models.ForeignKey(Purchase, related_name='purchasedetail', null=False,on_delete=models.CASCADE,  verbose_name="采购单")

    product_name = models.CharField(u'商品名称',default='',  max_length=500,  blank=True)
    sku = models.CharField(u'商品SKU',default='',  max_length=100,  blank=True)
    price = models.CharField(u'单价',default='',  max_length=100,  blank=True)
    quantity = models.CharField(u'采购数量', default='', max_length=100, blank=True)
    receive_quantity = models.CharField(u'到货数量', default='', max_length=100, blank=True)
    amount = models.CharField(u'商品总金额', default='', max_length=100, blank=True)

    class Meta:
        verbose_name = "采购单明细"
        verbose_name_plural = verbose_name
        #unique_together = (("order", "sku"),)
    def __str__(self):
        return  self.purchase.purchase_no

class Stock(models.Model):
    SKU_STATUS = (
        ("NORMAL", "正常"),
        ("WAIT", "缺货"),
        ("STOP", "断货"),


    )
    sku = models.CharField(u'商品SKU',default='',  max_length=100,  blank=True)
    warehouse = models.CharField(u'库位',default='',  max_length=100,  blank=True)
    stock_quantity = models.CharField(u'库存量', default='', max_length=100, blank=True)
    transit_quantity = models.CharField(u'采购在途', default='', max_length=100, blank=True)
    plateform_sku = models.CharField(u'平台SKU', default='', max_length=100, blank=True)



    class Meta:
        verbose_name = "仓库清单"
        verbose_name_plural = verbose_name
        #unique_together = (("order", "sku"),)
    def __str__(self):
        return  str(self.sku)