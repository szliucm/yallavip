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

    create_time = models.DateTimeField(u'创建时间', auto_now=False, null=True, blank=True)
    update_time = models.DateTimeField(u'更新时间', auto_now=False, null=True, blank=True)


    class Meta:
        verbose_name = "购物车"
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.pk


class CartDetail(models.Model):
    cart = models.ForeignKey(Cart, related_name='cart_detail', null=True, blank=True)

    sku = models.ForeignKey(Yallavip_SKU, related_name='sku_detail', null=True, blank=True)

    amount = models.IntegerField(u'数量',default='',blank=True, null=True)

    class Meta:
        verbose_name = "购物车明细"
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.pk