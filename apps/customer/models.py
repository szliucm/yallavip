from django.db import models


from prs.models import Lightin_SPU, Lightin_SKU
from conversations.models import FbConversation
from django.contrib.auth import get_user_model

User = get_user_model()


# Create your models here.


CITY = (
    ("None", "暂不支持"),
    ("Other", "人工处理"),
    ("Abu Arish", "Abu Arish"),
    ("Abha", "Abha"),
    ("Abqaiq", "Abqaiq"),
    ("Ain Dar", "Ain Dar"),
    ("Al Hassa", "Al Hassa"),
    ("Al-Jsh", "Al-Jsh"),
    ("Anak", "Anak"),
    ("Arar", "Arar"),
    ("Awamiah", "Awamiah"),
    ("Baha", "Baha"),
    ("Bahara", "Bahara"),
    ("Batha", "Batha"),
    ("Bisha", "Bisha"),
    ("Buraidah", "Buraidah"),
    ("Dammam", "Dammam"),
    ("Dawadmi", "Dawadmi"),
    ("Deraab", "Deraab"),
    ("Dere'iyeh", "Dere'iyeh"),
    ("Dhahran", "Dhahran"),
    ("Dhurma", "Dhurma"),
    ("Dhurma", "Dhurma"),
    ("Dhurma", "Dhurma"),
    ("Gizan", "Gizan"),
    ("Hadeethah", "Hadeethah"),
    ("Hafer Al Batin", "Hafer Al Batin"),
    ("Hail", "Hail"),
    ("Harad", "Harad"),
    ("Haweyah/Dha", "Haweyah/Dha"),
    ("Hofuf", "Hofuf"),
    ("Horaimal", "Horaimal"),
    ("Jafar", "Jafar"),
    ("Jeddah", "Jeddah"),
    ("Jouf", "Jouf"),
    ("Jubail", "Jubail"),
    ("Khafji", "Khafji"),
    ("Khamis Mushait", "Khamis Mushait"),
    ("Kharj", "Kharj"),
    ("Khobar", "Khobar"),
    ("Khodaria", "Khodaria"),
    ("Madinah", "Madinah"),
    ("Majma", "Majma"),
    #("Makkah", "Makkah"),
    ("Mecca", "Mecca"),
    ("Mubaraz", "Mubaraz"),
    ("Mulaija", "Mulaija"),
    ("Muzahmiah", "Muzahmiah"),
    ("Nabiya", "Nabiya"),
    ("Najran", "Najran"),
    ("Noweirieh", "Noweirieh"),
    ("Ojam", "Ojam"),
    ("Onaiza", "Onaiza"),
    ("Othmanyah", "Othmanyah"),
    ("Oyaynah", "Oyaynah"),
    ("Qarah", "Qarah"),
    ("Qariya Al Olaya", "Qariya Al Olaya"),
    ("Qassim", "Qassim"),
    ("Qatif", "Qatif"),
    ("Qunfudah", "Qunfudah"),
    ("Qurayat", "Qurayat"),
    ("Quwei'ieh", "Quwei'ieh"),
    ("Rabigh", "Rabigh"),
    ("Rahima", "Rahima"),
    ("Ras Al Kheir", "Ras Al Kheir"),
    ("Ras Tanura", "Ras Tanura"),
    ("Remah", "Remah"),
    ("Riyadh", "Riyadh"),
    ("Rwaydah", "Rwaydah"),
    ("Safanyah", "Safanyah"),
    ("Safwa", "Safwa"),
    ("Sakaka", "Sakaka"),
    ("Salbookh", "Salbookh"),
    ("Salwa", "Salwa"),
    ("Sarar", "Sarar"),
    ("Satorp (Jubail Ind'l 2)", "Satorp (Jubail Ind'l 2)"),
    ("Seihat", "Seihat"),
    ("Shefa'a", "Shefa'a"),
    ("Shoaiba", "Shoaiba"),
    ("Tabuk", "Tabuk"),
    ("Taif", "Taif"),
    ("Tanjeeb", "Tanjeeb"),
    ("Tarut", "Tarut"),
    ("Tebrak", "Tebrak"),
    ("Thadek", "Thadek"),
    ("Thuqba", "Thuqba"),
    ("Udhaliyah", "Udhaliyah"),
    ("Unayzah", "Unayzah"),
    ("Uyun", "Uyun"),
    ("Wadi El Dwaser", "Wadi El Dwaser"),
    ("Yanbu", "Yanbu"),
    ("Yanbu Al Baher", "Yanbu Al Baher"),
    ("Shaqra", "Shaqra"),



)


class Customer(models.Model):
    name = models.CharField(u'客户姓名', default='', max_length=100, blank=False, null=False)

    handles = models.TextField(u'货号', blank=True, null=True)
    attrs = models.CharField(u'规格', default='', max_length=100, blank=True, null=True)

    # 本次订单信息
    receiver = models.ForeignKey('Receiver', related_name='receiver_customer', on_delete=models.CASCADE,
                                 verbose_name="Receiver", null=True, blank=True)

    discount = models.CharField(u'discount', default='0', max_length=100, blank=True)
    order_amount = models.IntegerField(u'COD金额', default=0, blank=True, null=True)

    sales = models.CharField(u'Sales', default='', max_length=50, blank=True, null=True)
    comments = models.CharField(u'comments', default='', max_length=200, blank=True, null=True)
    active = models.BooleanField(u'活跃客户', default=True, null=False)
    message = models.CharField(u'message', default='', max_length=100, blank=True, null=True)
    update_time = models.DateTimeField(auto_now=True, blank=True, verbose_name="更新时间")
    gift = models.BooleanField(u'gift', default=False, null=False)

    class Meta:
        verbose_name = "客户"
        verbose_name_plural = verbose_name
        app_label = 'customer'

    def __str__(self):
        return self.name

class CustomerFav(models.Model):
    """
    用户收藏操作
    """
    conversation = models.ForeignKey(FbConversation, on_delete=models.CASCADE, verbose_name="客户会话", blank=True, null=True)

    spu = models.ForeignKey(Lightin_SPU,related_name='fav_spu', on_delete=models.CASCADE, verbose_name="商品", help_text="商品id")

    #sales = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="销售客服")

    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="用户")
    add_time = models.DateTimeField("添加时间",auto_now=True)

    class Meta:
        verbose_name = '客户收藏'
        verbose_name_plural = verbose_name
        unique_together = ("conversation", "spu")

    def __str__(self):
        return self.conversation.customer

class CustomerCart(models.Model):

    conversation = models.ForeignKey(FbConversation, on_delete=models.CASCADE, verbose_name="客户会话",null=True, blank=True)
    sku = models.ForeignKey(Lightin_SKU, related_name='cart_sku', null=False, on_delete=models.CASCADE,
                                    verbose_name="sku")

    price = models.CharField(u'单价', default='', max_length=50, blank=False, null=False)
    quantity = models.IntegerField(u'数量', default=1, blank=False, null=False)

    # sales = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="销售客服")

    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="用户")
    add_time = models.DateTimeField("添加时间", auto_now=True)

    class Meta:
        verbose_name = "客户购物车"
        verbose_name_plural = verbose_name
        unique_together = ("conversation", "sku")

    def __str__(self):
        return self.conversation.customer

class Receiver(models.Model):
    customer = models.ForeignKey(Customer, related_name='customer_receiver', null=True, blank=True, on_delete=models.CASCADE,
                                 verbose_name="Customer")
    #conversation = models.ForeignKey(FbConversation, on_delete=models.CASCADE, verbose_name="客户会话",null=True, blank=True)

    name = models.CharField(u'收件人姓名', default='', max_length=100, blank=False, null=False)
    COUNTRIES = (
        ("SA", "SA"),

    )
    country_code = models.CharField(u'country_code', choices=COUNTRIES, default='SA', max_length=10, blank=False,
                                    null=False)


    city = models.CharField(u'city', choices=CITY, default='', max_length=20, blank=False, null=False)
    address1 = models.CharField(u'address1', default='', max_length=100, blank=False, null=False)
    address2 = models.CharField(u'address2', default='', max_length=100, blank=True)
    address3 = models.CharField(u'address3', default='', max_length=100, blank=True)
    phone_1 = models.CharField(u'phone_1', default='', max_length=100, blank=False, null=False)
    phone_2 = models.CharField(u'phone_1', default='', max_length=100, blank=True)

    comments = models.TextField(u'备注', blank=True, null=True)
    #default = models.BooleanField("缺省收件人", default=False, blank=True, null=True)
    #user = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True, verbose_name="用户")
    #add_time = models.DateTimeField("添加时间",auto_now=True, blank=True, null=True )

    class Meta:
        verbose_name = "收件人"
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.name + "   " + self.phone_1 + "  " + self.address1


class Conversation(models.Model):
    customer = models.ForeignKey(Customer, related_name='customer_conversation', null=False, on_delete=models.CASCADE,
                                 verbose_name="Customer")

    name = models.CharField(u'Facebook名字', default='', max_length=100, blank=False, null=False)

    conversation = models.CharField(u'聊天链接', default='', max_length=500, blank=True, null=True)
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

    price = models.CharField(u'单价', default='', max_length=50, blank=False, null=False)
    quantity = models.IntegerField(u'数量', default=0, blank=False, null=False)

    class Meta:
        verbose_name = "客户草稿"
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.lightin_sku.SKU


class DealLog(models.Model):
    customer = models.ForeignKey(Customer, related_name='customer_deallog', null=False, on_delete=models.CASCADE,
                                 verbose_name="Customer")
    deal_action = models.CharField(u'操作', default='', max_length=100, blank=False, null=False)
    content = models.CharField(u'content', default='', max_length=500, blank=False, null=False)
    deal_staff = models.CharField(u'操作员', default='', max_length=50, blank=True, null=True)
    deal_time = models.DateTimeField(u'操作时间', auto_now=True, null=True, blank=True)

    class Meta:
        verbose_name = "操作日志"
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.deal_staff


'''
class change_into(models.Model):

    class Meta:
        verbose_name = u"转入分析"
        verbose_name_plural = verbose_name
        db_table = 'change_into'

    def __str__(self):
        return self.Meta.verbose_name


class change_out(models.Model):

    class Meta:
        verbose_name = u"转出分析"
        verbose_name_plural = verbose_name
        db_table = 'change_out'

    def __str__(self):
        return self.Meta.verbose_name
'''
