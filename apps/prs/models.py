from django.db import models
from fb.models import MyPhoto,MyFeed,MyAd

from datetime import datetime


# Create your models here.

class MyProductCategory(models.Model):
    """
    商品类别
    """
    code = models.CharField(u'code', default='', max_length=256, null=True, blank=True)
    cate_1 = models.CharField(u'cate_1', default='', max_length=256, null=True, blank=True)
    cate_2 = models.CharField(u'cate_2', default='', max_length=256, null=True, blank=True)
    cate_3 = models.CharField(u'cate_3', default='', max_length=256, null=True, blank=True)
    album_name = models.CharField(u'相册名', default='', max_length=256, null=True, blank=True)
    class Meta:
        verbose_name = "商品类别"
        verbose_name_plural = verbose_name

        app_label = 'prs'

    def __str__(self):
        return self.code

class MyProduct(models.Model):
    #product_no = models.BigIntegerField(u'产品编号', default=0, null=True, blank=True)
    #vendor_no = models.CharField(default='', max_length=100, null=True, blank=True, verbose_name="供应商编号")

    #handle = models.CharField(u'handle', default='', max_length=256, null=True, blank=True)
    #total_orders = models.IntegerField(u'总订单数', default=0, blank=True, null=True)
    #total_quantity = models.IntegerField(u'总销售数', default=0, blank=True, null=True)
    product_number = models.CharField(u'货号', default='', max_length=256, null=True, blank=True)

    OBJ_TYPE = (
        ("PRODUCT", "单品"),
        ("COMBO", "组合商品"),
        ("OVERSEAS", "海外仓包裹"),

    )

    obj_type = models.CharField(choices=OBJ_TYPE, default='PRODUCT', max_length=30, null=True, blank=True,
                                verbose_name="产品类型")

    created_time = models.DateTimeField(null=True, blank=True, verbose_name="上传时间")
    staff = models.CharField(u'运营经理', default='', max_length=100, null=True, blank=True)


    class Meta:
        verbose_name = "产品基础信息"
        verbose_name_plural = verbose_name

        app_label = 'prs'

    def __str__(self):

        return  self.product_number

class MyProductAli(models.Model):

    #myproduct = models.ForeignKey('MyProduct', null=True, blank=True, verbose_name="产品",
     #                           related_name="ali_product", on_delete=models.CASCADE)
    myproductcate = models.ForeignKey('MyProductCategory', null=True, blank=False, verbose_name="产品类目",
                                  related_name="ali_productcate", on_delete=models.CASCADE)
    vendor_no = models.CharField(default='unknow', max_length=200,  null=True, blank=True, verbose_name="供应商编号")


    url = models.CharField(default='',max_length=300, null=True, blank=True, verbose_name="1688链接")

    listing = models.BooleanField(default=False, verbose_name="已上架")
    posted_mainshop = models.BooleanField(default=False, verbose_name="上架到主站")
    product_no = models.CharField(default='',max_length=300, null=True, blank=True, verbose_name="product_no")
    handle = models.CharField(default='', max_length=300, null=True, blank=True, verbose_name="货号")
    post_error = models.BooleanField(default=False, verbose_name="发布到主站失败")


    active  = models.BooleanField(default=True, verbose_name="可用")

    created_time = models.DateTimeField(null=True, blank=True, verbose_name="上传时间")
    staff = models.CharField(u'运营经理', default='', max_length=100, null=True, blank=True)

    class Meta:
        verbose_name = "1688产品"
        verbose_name_plural = verbose_name


    def __str__(self):
        if self.vendor_no:
            return  self.vendor_no
        else:
            return "unknow"

class MyProductAliShop(models.Model):

    vendor_name = models.CharField(max_length=200,  null=False, blank=False, verbose_name="供应商")

    url = models.CharField(default='',max_length=300, null=True,  verbose_name="1688店铺链接")

    updated = models.BooleanField(default=False, verbose_name="已更新")

    class Meta:
        verbose_name = "1688店铺"
        verbose_name_plural = verbose_name

    def __str__(self):
        return  self.vendor_nname


class MyProductShopify(MyProduct):

    product_no = models.BigIntegerField(u'产品编号', default=0, null=True, blank=True)

    myproductcate = models.ForeignKey('MyProductCategory', null=True, blank=False, verbose_name="产品类目",
                                      related_name="shopify_productcate", on_delete=models.CASCADE)
    myproductali = models.ForeignKey('MyProductAli', null=True, blank=True, verbose_name="货源",
                                  related_name="shop_ali", on_delete=models.CASCADE)


    #shopifyproduct = models.ForeignKey('shop.ShopifyProduct', null=True, blank=True, verbose_name="shopify产品",
     #                           related_name="shop_product", on_delete=models.CASCADE)
    #shopifyvariant = models.ForeignKey('shop.ShopifyVariant', null=True, blank=True, verbose_name="shopify变体",
     #                          related_name="shop_variant", on_delete=models.CASCADE)

    vendor_no = models.CharField(default='', max_length=100, null=True, blank=True, verbose_name="供应商编号")
    handle = models.CharField(u'货号', default='', max_length=256, null=True, blank=True)

    listed = models.BooleanField(u'已发布到主站', default=False)

    listing_status = models.BooleanField(u'发布到Facebook', default=False)

    SUPPLY_STATUS = (
        ("NORMAL", "正常"),
        ("DELAY", "供货延迟"),
        ("STOP", "断货"),
        # ("PAUSE", "缺货"),
    )
    supply_status = models.CharField(u'供应状态', choices=SUPPLY_STATUS, max_length=50, default='NORMAL', blank=True)
    supply_comments = models.CharField(u'供应备注', max_length=500, default='', blank=True)

    category_code = models.CharField(u'类目', default='', max_length=100, null=True, blank=True)

    total_orders = models.IntegerField(u'总订单数', default=0, blank=True, null=True)
    total_quantity = models.IntegerField(u'总销售数', default=0, blank=True, null=True)

    week_orders = models.IntegerField(u'最近7天订单数', default=0, blank=True, null=True)
    week_quantity = models.IntegerField(u'最近7天销售数', default=0, blank=True, null=True)

    class Meta:
        verbose_name = "shopify商品"
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.handle


class MyProductPackage(MyProduct):

    #shopifyvariant = models.ForeignKey('shop.ShopifyVariant', null=True, blank=True, verbose_name="shopify变体",
     #                          related_name="variant_pacakge", on_delete=models.CASCADE)
    order_no = models.CharField( default='', max_length=100, null=True, blank=True,
                                verbose_name="原包裹号")
    #skus = models.CharField( default='', max_length=100, null=True, blank=True,
     #                           verbose_name="原包裹号")

    class Meta:
        verbose_name = "海外仓包裹"
        verbose_name_plural = verbose_name

    '''
    def __init__(self):
        self.obj_type = "OVERSEAS"
        super().__init__(**kwargs)
    '''


    def __str__(self):

        return str(self.id)

class MyProductFb(models.Model):
    OBJ_TYPE = (
        ("PHOTO", "相册"),
        ("FEED", "帖子"),
        ("AD", "广告"),
        ("GROUP", "社群"),

    )
    myproduct = models.ForeignKey('MyProduct', null=True, blank=True, verbose_name="产品",
                                related_name="fb_product", on_delete=models.CASCADE)
    mypage = models.ForeignKey('fb.MyPage', null=True, blank=True, verbose_name="主页",
                                  related_name="fb_page", on_delete=models.CASCADE)
    obj_type = models.CharField(choices=OBJ_TYPE,default='PHOTO',max_length=30, null=True, blank=True, verbose_name="接触点类型")

    myphoto = models.ForeignKey('fb.MyPhoto', null=True, blank=True, verbose_name="图片",
                                related_name="fb_photo", on_delete=models.CASCADE)
    myfeed = models.ForeignKey('fb.MyFeed', null=True, blank=True, verbose_name="帖子",
                               related_name="fb_feed", on_delete=models.CASCADE)
    myad = models.ForeignKey('fb.MyAd', null=True, blank=True, verbose_name="广告",
                               related_name="fb_ad", on_delete=models.CASCADE)
    myresource = models.ForeignKey('MyProductResources', null=True, blank=True, verbose_name="创意",
                             related_name="fb_resource", on_delete=models.CASCADE)


    fb_id = models.CharField(default='',max_length=100, null=True, blank=True, verbose_name="接触点代码")


    published = models.BooleanField(default=False, verbose_name="发布状态")
    published_time = models.DateTimeField(null=True, blank=True, verbose_name="发布时间")

    def product_fb_no(self):  # 计算字段要显示在修改页面中只能定义在只读字段中(否则不显示):readonly_fields = ('sc',)

        if self.obj_type == "PHOTO" and  self.myphoto:
            return self.myphoto.photo_no
        elif self.obj_type == "FEED"and  self.myfeed:
            return  self.myfeed.feed_no
        elif self.obj_type == "AD"and  self.myad:
            return  self.myad.ad_no
        else:
            return "none"
    product_fb_no.short_description = '产品接触点id'  # 用于显示时的名字 , 没有这个,字段标题将显示'name'

    class Meta:
        verbose_name = "fb接触点"
        verbose_name_plural = verbose_name

    def __str__(self):

        return  str(self.pk)




class MyProductResources(models.Model):
    myproduct = models.ForeignKey('MyProduct', null=True, blank=True, verbose_name="产品",
                                  related_name="resource_product", on_delete=models.CASCADE)
    myproductali = models.ForeignKey('MyProductAli', null=True, blank=True, verbose_name="1688信息",
                                  related_name="resource_ali", on_delete=models.CASCADE)

    name = models.CharField( default='', max_length=300, verbose_name="创意名",help_text="便于理解和管理的名字")
    title = models.TextField(verbose_name="标题", default='', max_length=512, null=True, blank=True)
    message = models.TextField(verbose_name="文案",default='',max_length=2048,null=True,blank=True)
    resource = models.FileField(u'创意', upload_to='resource/', default="", null=True, blank=True)

    handle = models.CharField( default='', max_length=300, verbose_name="货号", null=True, blank=True)

    RESOURCE_TARGET = (
        ("NEW", "新品"),
        ("HOT", "爆款"),
        ("COMBO", "套装"),
        ("PACKAGE", "包裹"),
        ("INTERACT", "互动"),
        ("LUCK", "抽奖"),
        ("SHOW", "晒单"),

    )
    resource_target = models.CharField(choices=RESOURCE_TARGET, default='NEW', max_length=30,
                                     verbose_name="创意标的")

    RESOURCE_CATE = (
        ("IMAGE", "图片"),
        ("VIDEO", "视频"),
    )
    resource_cate = models.CharField(choices=RESOURCE_CATE, default='', max_length=30,
                                     verbose_name="创意类型")

    RESOURCE_TYPE = (
        #("SKU", "sku自带"),
        #("AUTO", "自带生成"),
        ("RAW", "素材"),
        ("PS", "成品"),
    )

    resource_type = models.CharField(choices=RESOURCE_TYPE, default='', max_length=30,
                                verbose_name="创意性质")

    thumbnail = models.BooleanField(default=False, verbose_name="视频生成缩略图")

    created_time = models.DateTimeField(null=True, blank=True, verbose_name="上传时间")
    staff = models.CharField(u'运营经理', default='', max_length=100, null=True,blank=True)

    '''
    def save(self, *args, **kwargs):
        self.staff = str(self.request.user)
        self.created_time = datetime.now()
        super().save(*args, **kwargs)  # Call the "real" save() method.
    '''

    class Meta:
        verbose_name = "创意管理"
        verbose_name_plural = verbose_name
    def __str__(self):
        return self.name

'''
class MyFbProduct(models.Model):
    OBJ_TYPE = (
        ("PHOTO", "相册"),
        ("FEED", "帖子"),
        ("AD", "广告"),
        ("GROUP", "社群"),

    )
    myproduct = models.ForeignKey('shop.ShopifyProduct', null=True, blank=True, verbose_name="产品",
                                related_name="myfb_product", on_delete=models.SET_NULL)
    mypage = models.ForeignKey('fb.MyPage', null=True, blank=True, verbose_name="主页",
                                  related_name="myfb_page", on_delete=models.SET_NULL)
    obj_type = models.CharField(choices=OBJ_TYPE,default='PHOTO',max_length=30, null=True, blank=True, verbose_name="接触点类型")

    myresource = models.ForeignKey('MyProductResources', null=True, blank=True, verbose_name="创意",
                             related_name="myfb_resource", on_delete=models.SET_NULL)

    fb_id = models.CharField(default='',max_length=100, null=True, blank=True, verbose_name="接触点代码")
    cate_code = models.CharField(default='', max_length=100, null=True, blank=True, verbose_name="品类代码")
    album_name = models.CharField(default='', max_length=100, null=True, blank=True, verbose_name="相册")

    published = models.BooleanField(default=False, verbose_name="发布状态")
    publish_error = models.CharField(default='',max_length=100, null=True, blank=True, verbose_name="发布错误")
    published_time = models.DateTimeField(null=True, blank=True, verbose_name="发布时间")

    class Meta:
        verbose_name = "FB接触点(新)"
        verbose_name_plural = verbose_name

    def __str__(self):

        return  str(self.pk)
'''