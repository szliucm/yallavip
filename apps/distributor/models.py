from django.db import models
from prs.models import Lightin_SPU, Lightin_SKU

# Create your models here.
'''
class Yallavip_SPU(Lightin_SPU):
    class Meta:
        proxy = True

        verbose_name = "SPU"
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.SPU


class Yallavip_SKU(Lightin_SKU):
    class Meta:
        proxy = True

        verbose_name = "SKU"
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.SKU

class Cart(models.Model):
    distributor = models.CharField(default='', max_length=300, null=True, blank=True, verbose_name="分销商")
    create_time = models.DateTimeField(u'创建时间', auto_now=False, null=True, blank=True)

    checked = models.BooleanField(u"订单确认状态", default=False)
    checked_time = models.DateTimeField(u'确认时间', auto_now=False, null=True, blank=True)



    class Meta:
        verbose_name = "购物车"
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.distributor


class CartDetail(models.Model):

    cart = models.ForeignKey(Cart, related_name='cart_detail', null=False, on_delete=models.CASCADE,
                              verbose_name="Cart")

    sku = models.ForeignKey(Yallavip_SKU, related_name='sku_detail', null=False, on_delete=models.CASCADE,
                              verbose_name="SKU")

    price = models.IntegerField(verbose_name="供方价(CNY)", default=0,blank=True, null=True)
    quantity = models.IntegerField(u'数量',default=0,blank=True, null=True)

    def cal_amount(self):
        return self.price * self.quantity

    cal_amount.short_description = "金额小计(CNY)"
    amount = property(cal_amount)


    class Meta:
        verbose_name = "购物车明细"
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.sku.SKU
'''