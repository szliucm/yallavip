# -*- coding: utf-8 -*-
from django.db import models


# Create your models here.
class FunmartSPU(models.Model):
    SPU = models.CharField(default='', max_length=300, null=True, blank=True, verbose_name="SPU")

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
    download_error = models.CharField(default='', max_length=300, null=True, blank=True, verbose_name="download_error")

    sale_type = models.CharField(default='', max_length=30, null=True, blank=True, verbose_name="sale_type")

    class Meta:
        verbose_name = "Funmart SPU"
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.SPU


class FunmartSKU(models.Model):
    funmart_spu = models.ForeignKey(FunmartSPU, null=True, blank=True, verbose_name="funmart_spu",
                                    related_name="funmartspu_sku", on_delete=models.CASCADE)
    SPU = models.CharField(default='', max_length=300, null=True, blank=True, verbose_name="SPU")
    SKU = models.CharField(default='', max_length=100, null=True, blank=True, verbose_name="SKU")

    skuattr = models.TextField(default='', null=True, blank=True, verbose_name="skuattr")

    images = models.TextField(default='', null=True, blank=True, verbose_name="images")
    sale_price = models.FloatField(verbose_name="sale_price", default=0)
    downloaded = models.BooleanField(u"downloaded", default=False)  # 从erp下载sku信息
    uploaded = models.BooleanField(u"uploaded", default=False)  # 上传sku信息到wms

    class Meta:
        verbose_name = "Funmart SKU"
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.SKU


class FunmartBarcode(models.Model):
    funmart_sku = models.ForeignKey(FunmartSKU, null=True, blank=True, verbose_name="SKU",
                                    related_name="funmartsku_barcode", on_delete=models.CASCADE)

    SKU = models.CharField(default='',max_length=300, null=True, blank=True, verbose_name="SKU")

    barcode = models.CharField(u'barcode', default='', max_length=100, blank=True)

class ScanOrder(models.Model):
    track_code = models.CharField(u'track_code', default='', max_length=50, blank=True)
    batch_no = models.IntegerField(u'batch_no', default=0, blank=True, null=True)
    downloaded = models.BooleanField(u"downloaded", default=False)
    shelfed = models.BooleanField(u"shelfed", default=False)

    class Meta:
        verbose_name = "ScanOrder"
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.track_code


class BatchSKU(models.Model):
    batch_no = models.IntegerField(u'batch_no', default=0, blank=True, null=True)

    SKU = models.CharField(default='', max_length=100, null=True, blank=True, verbose_name="SKU")
    sale_type = models.CharField(default='', max_length=100, null=True, blank=True, verbose_name="sale_type")

    order_count = models.IntegerField(u'batch_count', default=0, blank=True, null=True)
    quantity = models.IntegerField(u'quantity', default=0, blank=True, null=True)
    uploaded = models.BooleanField(u"uploaded", default=False)  # 上传sku信息到wms

    images = models.TextField(default='', null=True, blank=True, verbose_name="images")
    en_name = models.CharField(default='', max_length=300, null=True, blank=True, verbose_name="en_name")
    skuattr = models.TextField(default='', null=True, blank=True, verbose_name="skuattr")

    ACTION = (
        ("Put Away", "Put Away"),

        ("Normal_Case", "Normal_Case"),
        ("Drug_No_Size", "Drug_No_Size"),
        ("Drug_Size", "Drug_Size"),

    )
    action = models.CharField(choices=ACTION, default='', max_length=100, null=True, blank=True, verbose_name="Action")

    class Meta:
        verbose_name = "BatchSKU"
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.SKU


class FunmartOrder(models.Model):
    order_no = models.CharField(u'order_no', default='', max_length=50, blank=True)
    track_code = models.CharField(u'track_code', default='', max_length=50, blank=True)
    order_date = models.DateTimeField(auto_now=False, null=True, blank=True,verbose_name="order_date")
    ship_method = models.CharField(u'ship_method', default='', max_length=50, blank=True)
    upload_date = models.DateField(u'upload_date', auto_now=True, null=True, blank=True)
    downloaded = models.BooleanField(u"downloaded", default=False)
    dealed = models.BooleanField(u"dealed", default=False)

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
    track_code = models.CharField(u'track_code', default='', max_length=50, blank=True)
    sku = models.CharField(u'sku', default='', max_length=50, blank=True)

    quantity = models.IntegerField(u'quantity', default=0, blank=True, null=True)
    price = models.CharField(u'Price', default='', max_length=50, blank=True)

    category_cn = models.CharField(u'category_cn', default='', max_length=500, blank=True)
    category_en = models.CharField(u'category_en', default='', max_length=500, blank=True)
    name = models.CharField(u'name', default='', max_length=500, blank=True)

    class Meta:
        verbose_name = "FunmartOrderItem"
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.order_no + '_' + self.sku


class Test(models.Model):
    class Meta:
        verbose_name = u"自定义页面"
        verbose_name_plural = verbose_name

    def __unicode__(self):
        return self.Meta.verbose_name
