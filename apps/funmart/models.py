# -*- coding: utf-8 -*-
from django.db import models

# Create your models here.
class FunmartSPU(models.Model):
    SPU = models.CharField(default='',max_length=300, null=True, blank=True, verbose_name="SPU")

    cate_1 = models.CharField(u'cate_1', default='', max_length=256, null=True, blank=True)
    cate_2 = models.CharField(u'cate_2', default='', max_length=256, null=True, blank=True)
    cate_3 = models.CharField(u'cate_3', default='', max_length=256, null=True, blank=True)

    en_name = models.CharField(default='', max_length=300, null=True, blank=True, verbose_name="en_name")

    skuattr = models.TextField(default='', null=True, blank=True, verbose_name="skuattr")
    description = models.TextField(default='', null=True, blank=True, verbose_name="description")
    images = models.TextField(default='', null=True, blank=True, verbose_name="images")
    link = models.CharField(default='', max_length=300, null=True, blank=True, verbose_name="link")
    sale_price = models.FloatField(verbose_name="sale_price", default=0)
    skuList = models.TextField(default='', null=True, blank=True, verbose_name="skuList")
    downloaded = models.BooleanField(u"downloaded", default=False)

    sale_type = models.CharField(default='', max_length=30, null=True, blank=True, verbose_name="sale_type")

    class Meta:
        verbose_name = "Funmart SPU"
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.SPU

class FunmartSKU(models.Model):
    funmart_spu = models.ForeignKey(FunmartSPU, null=True, blank=True, verbose_name="funmart_spu",
                                    related_name="funmartspu_sku", on_delete=models.CASCADE)
    SPU = models.CharField(default='',max_length=300, null=True, blank=True, verbose_name="SPU")
    SKU = models.CharField(default='', max_length=100, null=True, blank=True, verbose_name="SKU")

    skuattr = models.TextField(default='', null=True, blank=True, verbose_name="skuattr")

    images = models.TextField(default='', null=True, blank=True, verbose_name="images")
    sale_price = models.FloatField(verbose_name="sale_price", default=0)
    downloaded = models.BooleanField(u"downloaded", default=False)

    class Meta:
        verbose_name = "Funmart SKU"
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.SKU

class FunmartOrder(models.Model):
    order_no = models.CharField(u'order_no', default='', max_length=50, blank=True)
    track_code = models.CharField(u'track_code', default='', max_length=50, blank=True)
    ship_method = models.CharField(u'ship_method', default='', max_length=50, blank=True)
    upload_date = models.DateField(u'upload_date', auto_now=True, null=True, blank=True)
    downloaded =  models.BooleanField(u"downloaded", default=False)
    dealed = models.BooleanField(u"dealed", default=False)
    batch_no = models.IntegerField(u'batch_no', default=0, blank=True, null=True)

    class Meta:
        verbose_name = "FunmartOrder"
        verbose_name_plural = verbose_name


    def __str__(self):
        return self.order_no

class FunmartOrderItem(models.Model):
    order = models.ForeignKey(FunmartOrder, related_name='funmartorder_orderitem', null=False, on_delete=models.CASCADE,
                              verbose_name="Order")
    funmart_sku = models.ForeignKey(FunmartSKU, null=True, blank=True, verbose_name="funmart_sku",
                                    related_name="funmartsku_order", on_delete=models.CASCADE)

    order_no = models.CharField(u'order_no', default='', max_length=50, blank=True)
    sku = models.CharField(u'sku', default='', max_length=50, blank=True)

    quantity = models.IntegerField(u'quantity', default=0, blank=True, null=True)
    price = models.CharField(u'Price', default='', max_length=50, blank=True)



    class Meta:
        verbose_name = "FunmartOrderItem"
        verbose_name_plural = verbose_name


    def __str__(self):
        return self.order_no + '_' + self.sku

