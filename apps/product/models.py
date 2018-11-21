from django.db import models
from fb.models import MyPage

# Create your models here.
class Product(models.Model):
    SUPPLY_STATUS = (
        ("NORMAL", "正常"),
        ("DELAY", "供货延迟"),
        ("STOP", "断货"),
        #("PAUSE", "缺货"),
    )
    product = models.CharField(u'商品',default='',  max_length=50,  blank=True)
    sku = models.CharField(u'SKU',default='',  max_length=50,  blank=True)
    sku_name = models.CharField(u'商品名称', default='', max_length=500, blank=True)
    img = models.CharField(u'图片URL', max_length=300, default='', blank=True)
    ref_price = models.CharField(u'购买参考价', default='', max_length=200, blank=True)
    weight = models.CharField(u'实际重量', default='', max_length=200, blank=True)
    source_url = models.CharField(u'来源url', default='', max_length=500, blank=True)
    supply_status = models.CharField(u'供应状态',choices= SUPPLY_STATUS,max_length=50, default='NORMAL', blank=True)
    supply_comments = models.CharField(u'供应备注', max_length=500, default='', blank=True)
    update_time = models.DateTimeField(u'更新时间', auto_now=False, null=True, blank=True)

    alternative = models.CharField(u'替代产品',max_length=50, default='', blank=True)
    developer  = models.CharField(u'开发者',max_length=50, default='', blank=True)

    class Meta:
        verbose_name = "商品"
        verbose_name_plural = verbose_name
    def __str__(self):
        return  self.sku

class ProductCategory(models.Model):
    """
    商品类别
    """
    CATEGORY_TYPE = (
        (1, "一级类目"),
        (2, "二级类目"),
        (3, "三级类目"),
    )

    name = models.CharField(default="", max_length=30, verbose_name="类别名", help_text="类别名")
    code = models.CharField(default="", max_length=30, verbose_name="类别code", help_text="类别code")
    desc = models.TextField(default="", verbose_name="类别描述", help_text="类别描述")
    category_type = models.IntegerField(choices=CATEGORY_TYPE, verbose_name="类目级别", help_text="类目级别")
    parent_category = models.CharField(default="",  null=True, blank=True,max_length=30, verbose_name="父类目级别", help_text="父类目级别")
    #parent_category = models.ForeignKey("self", null=True, blank=True, verbose_name="父类目级别", help_text="父目录",
     #                                   related_name="sub_cat",on_delete=models.CASCADE)
    is_tab = models.BooleanField(default=False, verbose_name="是否导航", help_text="是否导航")
    add_time = models.DateTimeField(auto_now=False, null=True, blank=True, verbose_name="添加时间")

    class Meta:
        verbose_name = "商品类别"
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.name

class ProductCategoryMypage(models.Model):
    mypage = models.ForeignKey(MyPage, null=True, blank=True, verbose_name="主页", help_text="主页",
                                        related_name="category_page",on_delete=models.CASCADE)
    productcategory = models.ForeignKey(ProductCategory, null=True, blank=True, verbose_name="产品类别", help_text="产品类别",
                               related_name="page_category", on_delete=models.CASCADE)


    class Meta:
        verbose_name = "品类对应主页"
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.productcategory.name