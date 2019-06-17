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

    yallavip_images = models.TextField(default='', null=True, blank=True, verbose_name="images")
    image_downloaded = models.BooleanField(u"image_downloaded", default=False)
    SALE_TYPE = (
        ("hot", "hot"),
        ("normal", "normal"),
        ("drug", "drug"),

    )

    sale_type = models.CharField(choices=SALE_TYPE, default='', max_length=30, null=True, blank=True, verbose_name="sale_type")

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
    name = models.CharField(default='', max_length=300, null=True, blank=True, verbose_name="name")
    cn_name = models.CharField(default='', max_length=300, null=True, blank=True, verbose_name="cn_name")
    skuattr = models.TextField(default='', null=True, blank=True, verbose_name="skuattr")

    images = models.TextField(default='', null=True, blank=True, verbose_name="images")
    sale_price = models.FloatField(verbose_name="sale_price", default=0)

    pack_height =models.CharField(default='', max_length=100, null=True, blank=True, verbose_name="pack_height")
    pack_length = models.CharField(default='', max_length=100, null=True, blank=True, verbose_name="pack_length")
    pack_weight = models.CharField(default='', max_length=100, null=True, blank=True, verbose_name="pack_weight")
    pack_width = models.CharField(default='', max_length=100, null=True, blank=True, verbose_name="pack_width")



    downloaded = models.BooleanField(u"downloaded", default=False)  # 从erp下载sku信息
    download_error = models.CharField(default='', max_length=300, null=True, blank=True, verbose_name="download_error")
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


    download_error = models.CharField(default='', max_length=300, null=True, blank=True, verbose_name="download_error")
    class Meta:
        verbose_name = "FunmartBarcode"
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.barcode

class YallavipBarcode(models.Model):
    funmart_sku = models.ForeignKey(FunmartSKU, null=True, blank=True, verbose_name="SKU",
                                    related_name="funmartsku_yallavipbarcode", on_delete=models.CASCADE)
    SKU = models.CharField(default='',max_length=300, null=True, blank=True, verbose_name="SKU")
    barcode = models.CharField(u'barcode', default='', max_length=100, blank=True)

    class Meta:
        verbose_name = "YallavipBarcode"
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.barcode


class FunmartOrder(models.Model):
    track_code = models.CharField(u'track_code', default='', max_length=50, blank=True, unique=True)
    order_no = models.CharField(u'order_no', default='', max_length=50, blank=True)
    order_ref = models.CharField(u'order_ref', default='', max_length=50, blank=True)
    ret_track_code = models.CharField(u'ret_track_code', default='', max_length=50, blank=True)


    order_date = models.DateTimeField(auto_now=False, null=True, blank=True,verbose_name="order_date")
    ship_method = models.CharField(u'ship_method', default='', max_length=50, blank=True)

    quantity = models.IntegerField(u'quantity', default=0, blank=True, null=True)
    scanned_quantity = models.IntegerField(u'scanned_quantity', default=0, blank=True, null=True)

    scanner = models.CharField(u'scanner', default='', max_length=50, blank=True)
    scan_time = models.DateTimeField(u'scan_time', auto_now=False, null=True, blank=True)

    batch_no = models.IntegerField(u'batch_no', default=0, blank=True, null=True)
    scanned = models.BooleanField(u"scanned", default=False)
    upload_date = models.DateField(u'upload_date',  null=True, blank=True)
    downloaded = models.BooleanField(u"downloaded", default=False)
    dealed = models.BooleanField(u"dealed", default=False)

    class Meta:
        verbose_name = "FunmartOrder"
        verbose_name_plural = verbose_name

        unique_together = (('track_code', 'order_ref', 'ret_track_code'),)

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
    scanned_quantity = models.IntegerField(u'scanned_quantity', default=0, blank=True, null=True)
    scanner = models.CharField(u'scanner', default='', max_length=50, blank=True)
    scan_time = models.DateTimeField(u'scan_time', auto_now=False, null=True, blank=True)

    price = models.CharField(u'Price', default='', max_length=50, blank=True)

    category_cn = models.CharField(u'category_cn', default='', max_length=500, blank=True)
    category_en = models.CharField(u'category_en', default='', max_length=500, blank=True)
    name = models.CharField(u'name', default='', max_length=500, blank=True)

    item_code = models.CharField(u'item_code', default='', max_length=50, blank=True)
    barcode = models.CharField(u'barcode', default='', max_length=50, blank=True)
    action = models.CharField(u'action', default='', max_length=50, blank=True)
    batch_no = models.IntegerField(u'batch_no', default=0, blank=True, null=True)
    bag_no = models.IntegerField(u'bag_no', default=0, blank=True, null=True)


    class Meta:
        verbose_name = "FunmartOrderItem"
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.order_no + '_' + self.sku













class BatchSKU(models.Model):
    batch_no = models.IntegerField(u'batch_no', default=0, blank=True, null=True)
    funmart_sku = models.ForeignKey(FunmartSKU, related_name='funmartsku_batchsku', null=True, on_delete=models.CASCADE,
                              verbose_name="Order")

    SPU = models.CharField(default='', max_length=300, null=True, blank=True, verbose_name="SPU")
    SKU = models.CharField(default='', max_length=100, null=True, blank=True, verbose_name="SKU")
    sale_type = models.CharField(default='', max_length=100, null=True, blank=True, verbose_name="sale_type")

    order_count = models.IntegerField(u'batch_count', default=0, blank=True, null=True)
    quantity = models.IntegerField(u'quantity', default=0, blank=True, null=True)
    uploaded = models.BooleanField(u"uploaded", default=False)  # 上传sku信息到wms

    images = models.TextField(default='', null=True, blank=True, verbose_name="images")
    en_name = models.CharField(default='', max_length=300, null=True, blank=True, verbose_name="en_name")
    skuattr = models.TextField(default='', null=True, blank=True, verbose_name="skuattr")
    ACTION = (
        ("Put_Away", "Put_Away"),

        ("Normal_Case", "Normal_Case"),
        ("Dead_No_Size", "Dead_No_Size"),
        ("Dead_Size", "Dead_Size"),

    )
    action = models.CharField(choices=ACTION, default='', max_length=100, null=True, blank=True, verbose_name="Action")

    class Meta:
        verbose_name = "BatchSKU"
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.SKU

class ScanOrder(models.Model):
    order = models.OneToOneField(FunmartOrder, on_delete=models.CASCADE, verbose_name="订单", default="")
    track_code = models.CharField(u'track_code', default='', max_length=50, blank=True)
    order_no = models.CharField(u'order_no', default='', max_length=50, blank=True)
    order_ref = models.CharField(u'order_ref', default='', max_length=50, blank=True)

    batch_no = models.IntegerField(u'batch_no', default=0, blank=True, null=True)

    shelfed = models.BooleanField(u"shelfed", default=False)

    quantity = models.IntegerField(u'quantity', default=0, blank=True, null=True)
    scanned_quantity = models.IntegerField(u'scanned_quantity', default=0, blank=True, null=True)

    class Meta:
        verbose_name = "ScanOrder"
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.track_code

class ScanOrderItem(models.Model):
    scanorder = models.ForeignKey(ScanOrder, related_name='scanorder_orderitem', null=True, on_delete=models.CASCADE,
                              verbose_name="Order")

    track_code = models.CharField(u'track_code', default='', max_length=50, blank=True)

    sku = models.CharField(u'sku', default='', max_length=50, blank=True)
    quantity = models.IntegerField(u'quantity', default=0, blank=True, null=True)

    scanned_quantity = models.IntegerField(u'scanned_quantity', default=0, blank=True, null=True)
    shelfed = models.BooleanField(u"shelfed", default=False)

    class Meta:
        verbose_name = "ScanOrderItem"
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.track_code


class ScanPackage(models.Model):
    class Meta:
        verbose_name = u"ScanPackage"
        verbose_name_plural = verbose_name

    def __unicode__(self):
        return self.Meta.verbose_name

class ScanPackageItem(models.Model):
    class Meta:
        verbose_name = u"ScanPackageItem"
        verbose_name_plural = verbose_name

    def __unicode__(self):
        return self.Meta.verbose_name

class PrepareBatch(models.Model):
    class Meta:
        verbose_name = u"PrepareBatch"
        verbose_name_plural = verbose_name

    def __unicode__(self):
        return self.Meta.verbose_name



class FulfillBag(models.Model):
    class Meta:
        verbose_name = u"FulfillBag"
        verbose_name_plural = verbose_name

    def __unicode__(self):
        return self.Meta.verbose_name



class Test(models.Model):
    class Meta:
        verbose_name = u"自定义页面"
        verbose_name_plural = verbose_name

    def __unicode__(self):
        return self.Meta.verbose_name


class FunmartImage(models.Model):
    SPU = models.CharField(default='', max_length=300, null=True, blank=True, verbose_name="SPU")
    image = models.TextField(default='', null=True, blank=True, verbose_name="image")

    downloaded = models.BooleanField(u"downloaded", default=False)
    download_error = models.CharField(default='', max_length=300, null=True, blank=True, verbose_name="download_error")

    class Meta:
        verbose_name = u"FunmartImage"
        verbose_name_plural = verbose_name

    def __unicode__(self):
        return self.Meta.verbose_name





from django.db import models

class student_info(models.Model):
    # 字符
    t_name=models.CharField(max_length=20,default='linhongcun')
    # 数字
    t_age=models.IntegerField(default=21)   # 使用数字长度设置无效
    # 图片
    t_image=models.CharField(max_length=300,default='http://itaem.oss-cn-shenzhen.aliyuncs.com/20180509083509.jpg?Expires=4679469344&OSSAccessKeyId=LTAIATBJKsu6vu4R&Signature=PJkwOp9DVhtYu3Xkka0MnZVfnP0%3D')
