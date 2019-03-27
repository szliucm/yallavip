from django.db import models

from prs.models import  Lightin_SKU

# Create your models here.


class Customer(models.Model):
    name = models.CharField(u'客户姓名', default='', max_length=100, blank=False,null=False)

    handles = models.TextField(u'货号', blank=True, null=True)

    #本次订单信息
    receiver = models.ForeignKey('Receiver', related_name='receiver_customer', null=False, on_delete=models.CASCADE,
                                 verbose_name="Receiver")

    discount = models.CharField(u'discount', default='0', max_length=100, blank=True)
    order_amount = models.IntegerField(u'COD金额', default=0, blank=True, null=True)

    sales = models.CharField(u'Sales', default='', max_length=50, blank=True,null=True)

    class Meta:
        verbose_name = "客户"
        verbose_name_plural = verbose_name


    def __str__(self):
        return self.name

class Receiver(models.Model):
    customer = models.ForeignKey(Customer, related_name='customer_receiver', null=False, on_delete=models.CASCADE,
                                 verbose_name="Customer")

    name = models.CharField(u'收件人姓名', default='', max_length=100, blank=False,null=False)
    COUNTRIES = (
        ("SA", "SA"),

    )
    country_code = models.CharField(u'country_code', choices=COUNTRIES, default='SA', max_length=10, blank=False,
                                    null=False)

    CITIES = (
        ("riyadh", "Riyadh"),
        ("jeddah", "Jeddah"),
        ("dammam", "Dammam"),
        ("al khobar", "Al Khobar"),
        ("hofuf", "Hofuf"),
        ("jubail", "Jubail"),
        ("dhahran", "Dhahran"),
        ("tabuk", "Tabuk"),
        ("buraydah", "Buraydah"),
        ("al hassa", "Al Hassa"),
        ("jizan", "Jizan"),
        ("qatif", "Qatif"),
    )

    city = models.CharField(u'city', choices=CITIES, default='', max_length=20, blank=False, null=False)
    address1 = models.CharField(u'address1', default='', max_length=100, blank=False, null=False)
    address2 = models.CharField(u'address2', default='', max_length=100, blank=True)
    address3 = models.CharField(u'address3', default='', max_length=100, blank=True)
    phone_1 = models.CharField(u'phone_1', default='', max_length=100, blank=False, null=False)
    phone_2 = models.CharField(u'phone_1', default='', max_length=100, blank=True)

    comments = models.TextField(u'备注', blank=True, null=True)
    class Meta:
        verbose_name = "收件人"
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.name

class Conversation(models.Model):
    customer = models.ForeignKey(Customer, related_name='customer_conversation', null=False, on_delete=models.CASCADE,
                                 verbose_name="Customer")

    name = models.CharField(u'Facebook名字', default='', max_length=100, blank=False,null=False)


    coversation = models.CharField(u'聊天链接', default='', max_length=100, blank=False, null=False)
    comments = models.TextField(u'备注', blank=True, null=True)

    class Meta:
        verbose_name = "Facebook会话"
        verbose_name_plural = verbose_name


    def __str__(self):
        return self.name

class Draft(models.Model):
    customer = models.ForeignKey(Customer, related_name='customer_draft', null=False, on_delete=models.CASCADE,
                                 verbose_name="Customer")

    lightin_sku = models.ForeignKey(Lightin_SKU, related_name='lightin_sku_draft', null=False, on_delete=models.CASCADE,
                                verbose_name="lightin_sku")

    price = models.CharField(u'单价', default='', max_length=50, blank=False,null=False)
    quantity = models.IntegerField(u'数量', default=0, blank=False, null=False)


    class Meta:
        verbose_name = "客户草稿"
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.lightin_sku.SKU

class DealLog(models.Model):

    customer = models.ForeignKey(Customer, related_name='customer_deallog', null=False, on_delete=models.CASCADE,
                                 verbose_name="Customer")
    deal_action = models.CharField(u'操作', default='', max_length=100, blank=False,null=False)
    deal_staff = models.CharField(u'操作员', default='', max_length=50, blank=True,null=True)
    deal_time = models.DateTimeField(u'操作时间', auto_now=True, null=True, blank=True)

    class Meta:
        verbose_name = "操作日志"
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.deal_staff
