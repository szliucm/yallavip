from django.db import models

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