from django.db import models
from prs.models import Lightin_SPU, Lightin_SKU

# Create your models here.
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
    update_time = models.DateTimeField(u'更新时间', auto_now=False, null=True, blank=True)


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

    price = models.IntegerField(verbose_name="供方价", default=0,blank=True, null=True)
    quantity = models.IntegerField(u'数量',default=0,blank=True, null=True)

    amount = models.IntegerField(verbose_name="小计", default=0,blank=True, null=True)

    class Meta:
        verbose_name = "购物车明细"
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.sku