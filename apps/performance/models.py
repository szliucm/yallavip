from django.db import models

# Create your models here.
class Sales(models.Model):
    order_date = models.DateField(u'订单日期', auto_now=False, null=True, blank=True)
    #type = models.CharField(u'类型', default='', max_length=200, blank=True)
    #count = models.IntegerField(u'数量', default=0, blank=True, null=True)
    conversation_count = models.IntegerField(u'会话数', default=0, blank=True, null=True)
    message_count = models.IntegerField(u'消息数', default=0, blank=True, null=True)

    open = models.IntegerField(u'审核中数量', default=0, blank=True, null=True)
    open_amount = models.IntegerField(u'审核中金额', default=0, blank=True, null=True)
    transit = models.IntegerField(u'已交运数量', default=0, blank=True, null=True)
    transit_amount = models.IntegerField(u'已交运金额', default=0, blank=True, null=True)
    delivered  = models.IntegerField(u'delivered数量', default=0, blank=True, null=True)
    delivered_amount = models.IntegerField(u'delivered金额', default=0, blank=True, null=True)
    refused = models.IntegerField(u'refused数量', default=0, blank=True, null=True)
    refused_amount = models.IntegerField(u'refused金额', default=0, blank=True, null=True)
    cancelled = models.IntegerField(u'取消数量', default=0, blank=True, null=True)
    cancelled_amount = models.IntegerField(u'取消金额', default=0, blank=True, null=True)
    #delivered_rate = models.IntegerField(u'签收率', default=0, blank=True, null=True)
    def cal_delivered_rate(self):

        total = self.transit + self.delivered+ self.refused
        if total>0:
            return   "{:.0%}".format( self.delivered/ total )
        else:
            return  0


    cal_delivered_rate.short_description = "签收率"
    delivered_rate = property(cal_delivered_rate)

    class Meta:
        verbose_name = "整体业绩"
        verbose_name_plural = verbose_name

    def __str__(self):
        return str(self.order_date)

'''
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
'''

class StaffTrack(models.Model):
    order_date = models.DateField(u'订单日期', auto_now=False, null=True, blank=True)
    staff = models.CharField(u'客服', default='', max_length=200, blank=True)
    open = models.IntegerField(u'审核中数量', default=0, blank=True, null=True)
    open_amount = models.IntegerField(u'审核中金额', default=0, blank=True, null=True)
    transit = models.IntegerField(u'已交运数量', default=0, blank=True, null=True)
    transit_amount = models.IntegerField(u'已交运金额', default=0, blank=True, null=True)
    delivered = models.IntegerField(u'delivered数量', default=0, blank=True, null=True)
    delivered_amount = models.IntegerField(u'delivered金额', default=0, blank=True, null=True)
    refused = models.IntegerField(u'refused数量', default=0, blank=True, null=True)
    refused_amount = models.IntegerField(u'refused金额', default=0, blank=True, null=True)
    cancelled = models.IntegerField(u'取消数量', default=0, blank=True, null=True)
    cancelled_amount = models.IntegerField(u'取消金额', default=0, blank=True, null=True)
    #delivered_reate = models.IntegerField(u'签收率', default=0, blank=True, null=True)
    def cal_delivered_rate(self):

        total = self.transit + self.delivered+ self.refused
        if total>0:
            return   "{:.0%}".format( self.delivered/ total )
        else:
            return  0


    cal_delivered_rate.short_description = "签收率"
    delivered_rate = property(cal_delivered_rate)

    class Meta:
        verbose_name = "客服业绩"
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.order_date

class PageTrack(models.Model):
    order_date = models.DateField(u'订单日期', auto_now=False, null=True, blank=True)
    page_no = models.CharField(u'page_no', default='', max_length=200, blank=True)
    open = models.IntegerField(u'审核中数量', default=0, blank=True, null=True)
    open_amount = models.IntegerField(u'审核中金额', default=0, blank=True, null=True)
    transit = models.IntegerField(u'已交运数量', default=0, blank=True, null=True)
    transit_amount = models.IntegerField(u'已交运金额', default=0, blank=True, null=True)
    delivered = models.IntegerField(u'delivered数量', default=0, blank=True, null=True)
    delivered_amount = models.IntegerField(u'delivered金额', default=0, blank=True, null=True)
    refused = models.IntegerField(u'refused数量', default=0, blank=True, null=True)
    refused_amount = models.IntegerField(u'refused金额', default=0, blank=True, null=True)
    cancelled = models.IntegerField(u'取消数量', default=0, blank=True, null=True)
    cancelled_amount = models.IntegerField(u'取消金额', default=0, blank=True, null=True)
    def cal_delivered_rate(self):

        total = self.transit + self.delivered+ self.refused
        if total>0:
            return   "{:.0%}".format( self.delivered/ total )
        else:
            return  0


    cal_delivered_rate.short_description = "签收率"
    delivered_rate = property(cal_delivered_rate)
    class Meta:
        verbose_name = "Page业绩"
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.order_date