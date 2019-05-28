# -*- coding: utf-8 -*-
from django.db import models

# Create your models here.
class FunmartOrder(models.Model):
    order_no = models.CharField(u'order_no', default='', max_length=50, blank=True)
    track_code = models.CharField(u'track_code', default='', max_length=50, blank=True)
    ship_method = models.CharField(u'ship_method', default='', max_length=50, blank=True)
    upload_date = models.DateField(u'扫描日期', auto_now=True, null=True, blank=True)
    downloaded =  models.BooleanField(u"已下载", default=False)

    class Meta:
        verbose_name = "Funmart 订单"
        verbose_name_plural = verbose_name


    def __str__(self):
        return self.order_no

class FunmartOrderItem(models.Model):
    order = models.ForeignKey(FunmartOrder, related_name='funmartorder_orderitem', null=False, on_delete=models.CASCADE,
                              verbose_name="Order")
    order_no = models.CharField(u'order_no', default='', max_length=50, blank=True)
    sku = models.CharField(u'sku', default='', max_length=50, blank=True)

    quantity = models.IntegerField(u'数量', default=0, blank=True, null=True)
    price = models.CharField(u'Price', default='', max_length=50, blank=True)



    class Meta:
        verbose_name = "Funmart 订单明细"
        verbose_name_plural = verbose_name


    def __str__(self):
        return self.order_no
