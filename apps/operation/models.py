from django.db import models


class Op_Product(models.Model):
    product = models.CharField(u'产品', default='', max_length=100, blank=True)
    order_count = models.CharField(u'订单数', default='', max_length=100,blank=True)
    order_quantity = models.CharField(u'销售数量', default='', max_length=100, blank=True)
    like_count = models.CharField(u'点赞数', default='', max_length=100, blank=True)
    comment_count = models.CharField(u'评论数', default='', max_length=100, blank=True)
    post_count = models.CharField(u'post数', default='', max_length=100, blank=True)
    conversion = models.CharField (u'转化率', default='', max_length=100, blank=True)
    cluster = models.CharField(u'cluster', default='', max_length=100, blank=True)
    #product = models.CharField(u'评论数', default='', max_length=100, blank=True)

    OPTIMIZATIION = (
        ("NONE", "待定"),
        ("COPY", "优化图文"),
        ("PROMOTE", "改进促销"),
        ("COMBINATION", "尝试组合"),

    )
    '''
    OPTIMIZATIION = (
        ("cluster_0", "加大推广"),
        ("cluster_1", "自然销售中"),
        ("cluster_2", "潜力款"),
        ("cluster_3", "图文优化"),
        ("cluster_4", "图文优化（优先）"),

    )
     '''
    optimization = models.CharField (u'优化建议',choices=OPTIMIZATIION, default='', max_length=100, blank=True)
    challenger = models.CharField(u'企划', default='', max_length=100, blank=True)
    challenger_comment = models.CharField(u'企划备注', default='', max_length=100, blank=True)
    challenge_start_time = models.DateTimeField(u'开始企划时间', auto_now=False, null=True, blank=True)

    ENHANCE =(
        ("NONE", "待定"),
        ("POST", "增加post"),
        ("AD", "投放广告"),
        ("DOWN", "减少投放"),

    )

    enhance =  models.CharField(u'运营要求', choices=ENHANCE,default='', max_length=100, blank=True)
    operator = models.CharField(u'运营者', default='', max_length=100, blank=True)
    operator_comment = models.CharField(u'运营者备注', default='', max_length=100, blank=True)
    operate_start_time = models.DateTimeField(u'开始运营时间', auto_now=False, null=True, blank=True)
    # combination = models.CharField(u'建议组合', default='', max_length=100, blank=True)
    # similar = models.CharField(u'相似产品', default='', max_length=100, blank=True)



    class Meta:
        verbose_name = "热销产品管理"
        verbose_name_plural = verbose_name


    def __str__(self):
        return self.product

class Op_Supplier(models.Model):
    supplier = models.CharField(u'供应商', default='', max_length=100, blank=True)
    product_count = models.CharField(u'产品数', max_length=100, default='', blank=True)
    sku_count = models.CharField(u'sku数',  default='',max_length=100, blank=True)
    purchase_amount = models.CharField(u'采购金额',  max_length=10, default='',  blank=True)
    avg_time = models.CharField(u'平均到货时间', default='', max_length=100, blank=True)
    purchase_count = models.CharField(u'采购次数', default='', max_length=100,  blank=True)
    error_count = models.CharField(u'出错次数', default='', max_length=100, blank=True)
    error_ratio = models.CharField (u'差错率', default='', max_length=100, blank=True)
    cluster = models.CharField(u'cluster', default='', max_length=100, blank=True)

    OPTIMIZATIION = (
        ("NONE", "待定"),
        ("ACCOUNT", "深入合作"),
        ("ERROR", "改善合作"),
        ("REPLACE", "汰换供应商"),

    )
    '''
    OPTIMIZATIION = (
        ("cluster_0", "加大力度推广"),
        ("cluster_1", "汰换供应商(优先)"),
        ("cluster_2", "优化合作"),
        ("cluster_3", "潜力供应商"),
        ("cluster_4", "汰换供应商"),

    )
 '''
    optimization = models.CharField(u'优化建议',choices=OPTIMIZATIION, default='', max_length=100, blank=True)
    challenger = models.CharField(u'供应商管理', default='', max_length=100, blank=True)
    challenger_comment = models.CharField(u'供应商管理备注', default='', max_length=100, blank=True)
    challenge_start_time = models.DateTimeField(u'开始供管时间', auto_now=False, null=True, blank=True)

    ENHANCE = (
        ("NONE", "待定"),
        ("MORENEW", "加大上新"),
        ("MOREPROMOTE", "加大推广"),
        ("CUT", "精简产品"),

    )
    enhance = models.CharField(u'运营要求',choices=ENHANCE, default='', max_length=100, blank=True)
    operator = models.CharField(u'运营者', default='', max_length=100, blank=True)
    operator_comment = models.CharField(u'运营者备注', default='', max_length=100, blank=True)
    operate_start_time = models.DateTimeField(u'开始运营时间', auto_now=False, null=True, blank=True)



    class Meta:
        verbose_name = "供应商管理"
        verbose_name_plural = verbose_name


    def __str__(self):
        return self.supplier

class Planning(Op_Product):
    class Meta:
        proxy = True

        verbose_name = "企划"
        verbose_name_plural = verbose_name


    def __str__(self):
        return self.product