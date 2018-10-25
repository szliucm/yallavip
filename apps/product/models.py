from django.db import models

# Create your models here.
class Product(models.Model):
    SUPPLY_STATUS = (
        ("NORMAL", "正常"),
        ("STOP", "断货"),
        ("PAUSE", "缺货"),
    )
    product = models.CharField(u'商品',default='',  max_length=50,  blank=True)
    sku = models.CharField(u'SKU',default='',  max_length=50,  blank=True)
    sku_name = models.CharField(u'商品名称', default='', max_length=500, blank=True)
    img = models.CharField(u'图片URL', max_length=300, default='', blank=True)
    ref_price = models.CharField(u'购买参考价', default='', max_length=200, blank=True)
    weight = models.CharField(u'实际重量', default='', max_length=200, blank=True)
    source_url = models.CharField(u'来源url', default='', max_length=500, blank=True)



    supply_status = models.CharField(u'供应状态',choices= SUPPLY_STATUS,max_length=50, default='NORMAL', blank=True)
    update_time = models.DateTimeField(u'更新时间', auto_now=False, null=True, blank=True)
    class Meta:
        verbose_name = "商品"
        verbose_name_plural = verbose_name
    def __str__(self):
        return  self.sku