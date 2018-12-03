from django.db import models
from fb.models import MyPhoto,MyFeed,MyAd


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

    def __str__(self):
        return self.code

class MyProduct(models.Model):
    product_no = models.CharField(default='', max_length=100, null=True, blank=True,verbose_name="产品编号")
    vendor_no = models.CharField(default='', max_length=100, null=True, blank=True, verbose_name="供应商编号")

    class Meta:
        verbose_name = "基础产品"
        verbose_name_plural = verbose_name
    def __str__(self):

        return  self.product_no

class MyProductAli(models.Model):

    myproduct = models.ForeignKey('MyProduct', null=True, blank=True, verbose_name="产品",
                                related_name="ali_product", on_delete=models.CASCADE)
    myproductcate = models.ForeignKey('MyProductCategory', null=False, blank=False, verbose_name="产品类目",
                                  related_name="ali_productcate", on_delete=models.CASCADE)
    vendor_no = models.CharField(default='unknow', max_length=200,  null=True, blank=True, verbose_name="供应商编号")

    url = models.CharField(default='',max_length=300, null=True, blank=True, verbose_name="1688链接")

    listing = models.BooleanField(default=False, verbose_name="已上架")

    class Meta:
        verbose_name = "1688产品"
        verbose_name_plural = verbose_name

    def __str__(self):
        if self.vendor_no:
            return  self.vendor_no
        else:
            return "unknow"

class MyProductAliShop(models.Model):

    vendor_nname = models.CharField(max_length=200,  null=False, blank=False, verbose_name="供应商")

    url = models.CharField(default='',max_length=300, null=True,  verbose_name="1688店铺链接")

    updated = models.BooleanField(default=False, verbose_name="已更新")

    class Meta:
        verbose_name = "1688店铺"
        verbose_name_plural = verbose_name

    def __str__(self):
        return  self.vendor_nname


class MyProductShopify(models.Model):
    OBJ_TYPE = (
        ("PRODUCT", "单品"),
        ("OVERSEAS", "海外仓包裹"),

    )
    myproduct = models.ForeignKey('MyProduct', null=True, blank=True, verbose_name="产品",
                                  related_name="shop_product", on_delete=models.CASCADE)
    myproductali = models.ForeignKey('MyProductAli', null=True, blank=True, verbose_name="货源",
                                  related_name="shop_ali", on_delete=models.CASCADE)
    obj_type = models.CharField(choices=OBJ_TYPE, default='PRODUCT', max_length=30, null=True, blank=True,
                                verbose_name="产品类型")

    shopifyproduct = models.ForeignKey('shop.ShopifyProduct', null=True, blank=True, verbose_name="shopify产品",
                                related_name="shop_product", on_delete=models.CASCADE)
    shopifyvariant = models.ForeignKey('shop.ShopifyVariant', null=True, blank=True, verbose_name="shopify变体",
                               related_name="shop_variant", on_delete=models.CASCADE)


    def product_shopify_no(self):  # 计算字段要显示在修改页面中只能定义在只读字段中(否则不显示):readonly_fields = ('sc',)
        if self.obj_type == "PRODUCT" and self.shopifyproduct:
            return self.shopifyproduct.product_no
        elif self.obj_type == "OVERSEAS" and self.shopifyvariant:
            return self.shopifyvariant.sku
        else:
            return "none"

    product_shopify_no.short_description = '产品shopify_id'  # 用于显示时的名字 , 没有这个,字段标题将显示'name'

    class Meta:
        verbose_name = "shopify商品"
        verbose_name_plural = verbose_name

    def __str__(self):

        return self.product_shopify_no()

class MyProductFb(models.Model):
    OBJ_TYPE = (
        ("PHOTO", "相册"),
        ("FEED", "帖子"),
        ("AD", "广告"),

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

        return  self.product_fb_no()




class MyProductResources(models.Model):
    myproduct = models.ForeignKey('MyProduct', null=True, blank=True, verbose_name="产品",
                                  related_name="resource_product", on_delete=models.CASCADE)
    myproductali = models.ForeignKey('MyProductAli', null=True, blank=True, verbose_name="1688信息",
                                  related_name="resource_ali", on_delete=models.CASCADE)

    name = models.CharField( default='', max_length=100, null=True, blank=True, verbose_name="资源名")
    resource = models.FileField(u'资源', upload_to='resource/', default="", null=True, blank=True)

    RESOURCE_CATE = (
        ("IMAGE", "图片"),
        ("VIDEO", "视频"),
    )
    resource_cate = models.CharField(choices=RESOURCE_CATE, default='IMAGE', max_length=30, null=True, blank=True,
                                     verbose_name="资源性质")

    RESOURCE_TYPE = (
        #("SKU", "sku自带"),
        #("AUTO", "自带生成"),
        ("RAW", "素材"),
        ("PS", "成品"),
    )
    resource_type = models.CharField(choices=RESOURCE_TYPE, default='RAW', max_length=30, null=True, blank=True,
                                verbose_name="资源类型")



    created_time = models.DateTimeField(null=True, blank=True, verbose_name="上传时间")
    staff = models.CharField(u'上传人', default='', max_length=100, null=True,blank=True)


    class Meta:
        verbose_name = "创意"
        verbose_name_plural = verbose_name
    def __str__(self):
        return self.name