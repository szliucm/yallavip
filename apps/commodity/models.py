from django.db import models
from fb.models import MyPage

# Create your models here.
#选品规则
class SelectionRule(models.Model):
    name = models.CharField(u'选品规则', default='', max_length=200, blank=True)

    cates = models.CharField(max_length=300,null=True, blank=True, verbose_name="关联品类",help_text="多个品类用逗号隔开")
    prices = models.CharField(max_length=300, null=True, blank=True, verbose_name="价格区间",help_text="最低价最高价，用逗号隔开")
    attrs = models.CharField(max_length=300, null=True, blank=True, verbose_name="规格",help_text="多个规格用逗号隔开")

    class Meta:
        verbose_name = "选品规则"
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.name

#套装规则
class ComboRule(models.Model):
    selection_rule = models.ForeignKey(SelectionRule, related_name='selection_combo', null=True, blank=True,
                                     verbose_name="选品规则", on_delete=models.CASCADE)

    name = models.CharField(u'套装规则', default='', max_length=200, blank=True)
    items_count = models.CharField(max_length=300, null=True, blank=True, verbose_name="数量区间",help_text="用逗号隔开")
    items_amount = models.CharField(max_length=300, null=True, blank=True, verbose_name="金额区间", help_text="用逗号隔开")

    class Meta:
        verbose_name = "套装规则"
        verbose_name_plural = verbose_name


    def __str__(self):
        return self.name


#调价规则
class PriceRule(models.Model):
    selection_rule = models.ForeignKey(SelectionRule, related_name='selection_price', null=True, blank=True,
                                     verbose_name="选品规则", on_delete=models.CASCADE)

    name = models.CharField(u'调价规则', default='', max_length=200, blank=True)
    TYPE = (
        ("取整","取整"),
        ("倍数", "倍数"),
    )



    type = models.CharField(u'类型', choices=TYPE,default='', max_length=200, blank=True)
    rules = models.CharField(max_length=300, null=True, blank=True, verbose_name="定价规则")

    commit = models.BooleanField(u'是否提交', default=False)

    class Meta:
        verbose_name = "调价规则"
        verbose_name_plural = verbose_name


    def __str__(self):
        return self.name

#page选品规则
class PageRule(models.Model):

    mypage = models.OneToOneField(MyPage, on_delete=models.CASCADE,  verbose_name="Page")

    rules  = models.ManyToManyField(SelectionRule, blank=False, verbose_name="Rules",
                                 related_name="page_selection")
    #selectionrule = models.ForeignKey(SelectionRule, null=False, blank=False, verbose_name="SelectionRule",
     #                          related_name="page_selection", on_delete=models.CASCADE)

    active = models.BooleanField(default=True, verbose_name="可用")

    update_time = models.DateTimeField(null=True, blank=True, verbose_name="更新时间")
    staff = models.CharField(u'运营', default='', max_length=100, null=True, blank=True)

    class Meta:
        verbose_name = "page选品规则"
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.mypage.page



# breadcrumb
class Breadcrumb(models.Model):
    breadcrumb = models.CharField(u'breadcrumb', default='', max_length=200)
    spus_count = models.IntegerField(u'数量', default=0, blank=True, null=True)

    class Meta:
        verbose_name = "breadcrumb"
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.breadcrumb


#page 主推 breadcrumb
class PagePromoteCate(models.Model):

    mypage = models.OneToOneField(MyPage, on_delete=models.CASCADE,  verbose_name="Page")

    breadcrumb  = models.ManyToManyField(Breadcrumb, blank=False, verbose_name="breadcrumb",
                                 related_name="breadcrumb_promote")


    class Meta:
        verbose_name = "page主推breadcrumb"
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.mypage.page
