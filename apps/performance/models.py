from django.db import models

# Create your models here.
class Sales(models.Model):
    order_date = models.DateField(u'订单日期', auto_now=False, null=True, blank=True)
    type = models.CharField(u'类型', default='', max_length=200, blank=True)
    count = models.IntegerField(u'数量', default=0, blank=True, null=True)


    class Meta:
        verbose_name = "销售业绩"
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.order_date

class StaffPerformace(models.Model):
    order_date = models.DateField(u'订单日期', auto_now=False, null=True, blank=True)
    staff = models.CharField(u'客服', default='', max_length=200, blank=True)
    order_status = models.CharField(u'订单状态', default='', max_length=200, blank=True)
    count = models.IntegerField(u'数量', default=0, blank=True, null=True)


    class Meta:
        verbose_name = "客服业绩"
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.order_date