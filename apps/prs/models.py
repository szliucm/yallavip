from django.db import models
from fb.models import MyPage,MyPhoto,MyFeed,MyAd,MyAlbum
from shop.models import ShopifyProduct
from commodity.models import SelectionRule

from datetime import datetime


# Create your models here.

class MyCategory(models.Model):
    """
    商品类别
    """
    super_cate = models.ForeignKey('self', blank=True,null=True, on_delete=models.CASCADE,
                                 verbose_name="父品类")
    super_name = models.CharField(u'父品类名', default='', max_length=100, null=True, blank=True)
    name = models.CharField(u'品类名', default='', max_length=100, null=True, blank=True)
    level = models.BigIntegerField(u'层级', default=0, null=True, blank=True)
    tags = models.CharField(u'tags', default='', max_length=500, null=True, blank=True)

    active = models.BooleanField(default=True, verbose_name="可用")
    published = models.BooleanField(default=False, verbose_name="已发布")

    collcetion_no = models.CharField(u'collcetion_no', default='', max_length=500, null=True, blank=True)
    publishe_error = models.CharField(u'publishe_error', default='', max_length=500, null=True, blank=True)

    '''
    cate_1 = models.CharField(u'cate_1', default='', max_length=256, null=True, blank=True)
    cate_2 = models.CharField(u'cate_2', default='', max_length=256, null=True, blank=True)
    cate_3 = models.CharField(u'cate_3', default='', max_length=256, null=True, blank=True)
    '''

    class Meta:
        verbose_name = "商品品类"
        verbose_name_plural = verbose_name

        app_label = 'prs'

    def __str__(self):
        return self.name

class MyCategorySize(models.Model):
    """
    商品类别
    """
    cate = models.ForeignKey(MyCategory, blank=True,null=True, on_delete=models.CASCADE,
                                 related_name="cate_size", verbose_name="品类")
    size = models.CharField(u'规格', default='', max_length=100, null=True, blank=True)
    sku_quantity = models.BigIntegerField(u'SKU数量', default=0, null=True, blank=True)

    class Meta:
        verbose_name = "商品尺码"
        verbose_name_plural = verbose_name


    def __str__(self):
        return self.size

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
    #myproductcate = models.ForeignKey('MyProductCategory', null=True, blank=False, verbose_name="产品类目",
     #                             related_name="ali_productcate", on_delete=models.CASCADE)
    vendor_no = models.CharField(default='unknow', max_length=200,  null=True, blank=True, verbose_name="供应商编号")


    url = models.CharField(default='',max_length=300, null=True, blank=True, verbose_name="1688链接")

    listing = models.BooleanField(default=False, verbose_name="获取1688产品信息")
    posted_mainshop = models.BooleanField(default=False, verbose_name="上架到主站")
    product_no = models.CharField(default='',max_length=300, null=True, blank=True, verbose_name="product_no")
    handle = models.CharField(default='', max_length=300, null=True, blank=True, verbose_name="货号")
    post_error = models.BooleanField(default=False, verbose_name="错误信息")


    active  = models.BooleanField(default=True, verbose_name="可用")

    created_time = models.DateTimeField(null=True, blank=True, verbose_name="上传时间")
    staff = models.CharField(u'运营经理', default='', max_length=100, null=True, blank=True)

    class Meta:
        verbose_name = "1688产品"
        verbose_name_plural = verbose_name


    def __str__(self):
        return  self.url.partition(".html")[0].rpartition("/")[2]

class MyProductAliShop(models.Model):

    vendor_name = models.CharField(max_length=200,  null=False, blank=False, verbose_name="供应商")

    url = models.CharField(default='',max_length=300, null=True,  verbose_name="1688店铺链接")

    updated = models.BooleanField(default=False, verbose_name="已更新")

    class Meta:
        verbose_name = "1688店铺"
        verbose_name_plural = verbose_name

    def __str__(self):
        return  self.url.partition(".html")[0].rpartition("/")[2]


class MyProductShopify(MyProduct):

    product_no = models.BigIntegerField(u'产品编号', default=0, null=True, blank=True)

    #myproductcate = models.ForeignKey('MyProductCategory', null=True, blank=False, verbose_name="产品类目",
     #                                 related_name="shopify_productcate", on_delete=models.CASCADE)
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
    publish_error = models.CharField(default='', max_length=500, null=True, blank=True, verbose_name="发布错误")

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


class MyFbProduct(models.Model):
    OBJ_TYPE = (
        ("PHOTO", "相册"),
        ("FEED", "帖子"),
        ("AD", "广告"),
        ("GROUP", "社群"),

    )
    myproduct = models.ForeignKey('shop.ShopifyProduct', null=True, blank=True, verbose_name="产品",
                                related_name="myfb_product", on_delete=models.SET_NULL)
    myaliproduct = models.ForeignKey('AliProduct', null=True, blank=True, verbose_name="1688产品",
                                  related_name="myfb_aliproduct", on_delete=models.SET_NULL)
    mypage = models.ForeignKey('fb.MyPage', null=True, blank=True, verbose_name="主页",
                                  related_name="myfb_page", on_delete=models.SET_NULL)
    obj_type = models.CharField(choices=OBJ_TYPE,default='PHOTO',max_length=30, null=True, blank=True, verbose_name="接触点类型")

    #myresource = models.ForeignKey('MyProductResources', null=True, blank=True, verbose_name="创意",
     #                        related_name="myfb_resource", on_delete=models.SET_NULL)

    fb_id = models.CharField(default='',max_length=100, null=True, blank=True, verbose_name="接触点代码")
    cate_code = models.CharField(default='', max_length=100, null=True, blank=True, verbose_name="品类代码")
    album_name = models.CharField(default='', max_length=100, null=True, blank=True, verbose_name="相册")
    album_no = models.CharField(default='', max_length=100, null=True, blank=True, verbose_name="相册编码")

    published = models.BooleanField(default=False, verbose_name="发布状态")
    publish_error = models.CharField(default='',max_length=256, null=True, blank=True, verbose_name="发布错误(或图片数量)")
    published_time = models.DateTimeField(null=True, blank=True, verbose_name="发布时间")

    class Meta:
        verbose_name = "FB接触点(新)"
        verbose_name_plural = verbose_name

    def __str__(self):

        return  self.myaliproduct.handle

class AliProduct(models.Model):
    offer_id = models.CharField(default='',max_length=300, null=True, blank=True, verbose_name="编号")
    cate_code = models.CharField(default='NONE', max_length=300, null=True, blank=True, verbose_name="品类")

    priority = models.CharField(default='', max_length=300, null=True, blank=True, verbose_name="优先级")



    #为上传shopify而生成的记录
    title = models.CharField(default='',max_length=300, null=True, blank=True, verbose_name="标题")
    #images = models.TextField(default='', null=True, blank=True, verbose_name="图片")
    options = models.TextField(default='', null=True, blank=True, verbose_name="属性")
    options_zh = models.TextField(default='', null=True, blank=True, verbose_name="中文属性")
    image_dict = models.TextField(default='', null=True, blank=True, verbose_name="图片字典")
    price_dict = models.TextField(default='', null=True, blank=True, verbose_name="价格字典")

    maxprice = models.IntegerField(u'价格(price)', default=0, blank=True, null=True)
    price_rate = models.FloatField(u'价格系数',default=0,)


    product_no = models.CharField(default='', max_length=300, null=True, blank=True, verbose_name="product_no")
    handle = models.CharField(default='', max_length=300, null=True, blank=True, verbose_name="货号")

    #系统运行记录
    started = models.BooleanField(default=False, verbose_name="抓取状态")
    started_error = models.CharField(default='', max_length=100, null=True, blank=True, verbose_name="抓取错误")
    started_time = models.DateTimeField(null=True, blank=True, verbose_name="启动时间")

    # 神箭手抓下来的记录
    created = models.BooleanField(default=False, verbose_name="爬取状态")
    created_error = models.CharField(default='', max_length=100, null=True, blank=True, verbose_name="爬取错误")
    created_time = models.DateTimeField(null=True, blank=True, verbose_name="爬取时间")

    title_zh = models.CharField(default='', max_length=300, null=True, blank=True, verbose_name="商品名称(name)")
    price_range = models.CharField(default='', max_length=300, null=True, blank=True, verbose_name="价格(price)")

    trade_info =models.TextField(default='', null=True, blank=True, verbose_name="批发信息(trade_info)")
    sales_count = models.IntegerField(u'总销量(sales_count)', default=0, blank=True, null=True)

    sku_info = models.TextField(default='', null=True, blank=True, verbose_name="商品规格(sku)")
    sku_detail = models.TextField(default='', null=True, blank=True, verbose_name="规格详情(sku_detail)")
    params = models.TextField(default='', null=True, blank=True, verbose_name="商品参数(params)")
    images = models.TextField(default='', null=True, blank=True, verbose_name="商品图片(images)")
    shipping_from = models.TextField(default='', null=True, blank=True, verbose_name="发货地(shipping_from)")
    score = models.CharField(default='', max_length=100,null=True, blank=True, verbose_name="商品评分(score)")
    comments_count = models.CharField(default='',max_length=100, null=True, blank=True, verbose_name="评价数(comments_count)")

    sid = models.CharField(default='', max_length=100, null=True, blank=True, verbose_name="店铺ID(sid)")
    company_name = models.CharField(default='', max_length=100, null=True, blank=True, verbose_name="公司名称(company_name)")

    #发布到shopify，便于下单
    published = models.BooleanField(default=False, verbose_name="发布状态")
    publish_error = models.CharField(default='', max_length=100, null=True, blank=True, verbose_name="发布错误(或图片数量)")
    published_time = models.DateTimeField(null=True, blank=True, verbose_name="发布时间")

    stopped = models.BooleanField(default=False, verbose_name="停用状态")
    class Meta:
        verbose_name = "ali产品信息"
        verbose_name_plural = verbose_name

    def __str__(self):

        return  self.offer_id

class MyFbAlbumCate(models.Model):
    mypage = models.ForeignKey('fb.MyPage', null=True, blank=True, verbose_name="主页",
                               related_name="myfbalbum_page", on_delete=models.CASCADE)

    myalbum = models.ForeignKey('fb.MyAlbum', null=False, blank=False, verbose_name="相册",
                               related_name="myfbalbum_album", on_delete=models.CASCADE)


    mycategory = models.ForeignKey(MyCategory, null=False, blank=False, verbose_name="品类",
                               related_name="myfbalbum_cate", on_delete=models.CASCADE)

    #cate_code = models.CharField(default='', max_length=100, null=True, blank=True, verbose_name="品类代码")
    #album_name = models.CharField(default='', max_length=100, null=True, blank=True, verbose_name="相册")
    #album_no = models.CharField(default='', max_length=100, null=True, blank=True, verbose_name="相册编码")

    #published = models.BooleanField(default=False, verbose_name="发布状态")
    #publish_error = models.CharField(default='',max_length=256, null=True, blank=True, verbose_name="发布错误(或图片数量)")
    #published_time = models.DateTimeField(null=True, blank=True, verbose_name="发布时间")

    cate_active = models.BooleanField(default=True, verbose_name="品类活跃状态")

    class Meta:
        verbose_name = "相册品类关联"
        verbose_name_plural = verbose_name

    def __str__(self):

        return  self.myalbum.name


class Proxy(models.Model):
    ip = models.CharField(default='',max_length=300, null=True, blank=True, verbose_name="ip")
    active = models.BooleanField(default=False,null=True, blank=True,verbose_name="有效性")

    class Meta:
        verbose_name = "代理服务器"
        verbose_name_plural = verbose_name

    def __str__(self):
        return str(self.ip)

#单独抓取ali链接上新
class AliProduct_vendor(models.Model):

    ali_url = models.CharField(default='',max_length=300, null=True, blank=True, verbose_name="产品链接")
    #priority = models.CharField(default='',max_length=300, null=True, blank=True, verbose_name="优先级")
    vendor = models.CharField(default='',max_length=300, null=True, blank=True, verbose_name="供应商")
    cate_code = models.CharField(default='', max_length=300, null=True, blank=True, verbose_name="品类")
    got = models.BooleanField(default=False, null=True, blank=True, verbose_name="已抓取")

    class Meta:
        verbose_name = "供应商上新链接"
        verbose_name_plural = verbose_name

    def __str__(self):
        return str(self.ali_url)


class Lightin_SPU(models.Model):
    SPU = models.CharField(default='',max_length=300, null=True, blank=True, verbose_name="SPU")

    vendor = models.CharField(default='',max_length=20, null=True, blank=True, verbose_name="Vendor")

    en_name = models.CharField(default='',max_length=300, null=True, blank=True, verbose_name="en_name")
    cn_name = models.CharField(default='', max_length=300, null=True, blank=True, verbose_name="cn_name")
    cate_1 = models.CharField(u'cate_1', default='', max_length=256, null=True, blank=True)
    cate_2 = models.CharField(u'cate_2', default='', max_length=256, null=True, blank=True)
    cate_3 = models.CharField(u'cate_3', default='', max_length=256, null=True, blank=True)

    vendor_sale_price = models.FloatField(verbose_name="供方销售价",default=0)
    vendor_supply_price = models.FloatField(verbose_name="供方采购价", default=0)
    link = models.CharField(default='', max_length=300, null=True, blank=True, verbose_name="link")

    title = models.CharField(default='', max_length=300, null=True, blank=True, verbose_name="title")
    breadcrumb = models.CharField(default='', max_length=300, null=True, blank=True, verbose_name="breadcrumb")

    currency = models.CharField(default='', max_length=300, null=True, blank=True, verbose_name="currency")

    sale_price = models.FloatField(verbose_name="供方实际销售价", default=0)
    images = models.TextField(default='', null=True, blank=True, verbose_name="图片")
    images_dict = models.TextField(default='', null=True, blank=True, verbose_name="图片字典")
    attr_image_dict = models.TextField(default='', null=True, blank=True, verbose_name="属性图片字典")

    got = models.BooleanField(default=False, verbose_name="获取状态",null=True, blank=True,)
    got_error = models.CharField(default='', max_length=100, null=True, blank=True, verbose_name="获取错误")
    got_time = models.DateTimeField(null=True, blank=True, verbose_name="更新时间")

    yallavip_price = models.FloatField(u'yallavip售价', default=0, blank=True, null=True)
    shopify_price = models.FloatField(u'shopify售价', default=0, blank=True, null=True)

    published = models.BooleanField(default=False, verbose_name="发布到shopify状态")
    shopify_published = models.BooleanField(default=False, verbose_name="shopify发布状态")

    image_published = models.BooleanField(default=False, verbose_name="图片发布到shopify状态")
    images_shopify =  models.TextField(default='', null=True, blank=True, verbose_name="shopify图片字典")
    publish_error = models.CharField(default='无', max_length=100, null=True, blank=True, verbose_name="发布错误")
    published_time = models.DateTimeField(null=True, blank=True, verbose_name="发布时间")

    shopify_product = models.ForeignKey(ShopifyProduct, null=True, blank=True, verbose_name="shopify产品",
                                    related_name="shopify_spu", on_delete=models.CASCADE)

    product_no = models.CharField(default='', max_length=300, null=True, blank=True, verbose_name="shopify product_no")
    handle = models.CharField(default='', max_length=300, null=True, blank=True, verbose_name="handle")

    updated = models.BooleanField(default=False, verbose_name="更新状态")
    update_error = models.CharField(default='', max_length=500, null=True, blank=True, verbose_name="更新错误")

    quantity = models.IntegerField(u'数量', default=0, blank=True, null=True)

    sellable = models.IntegerField(u'oms_可售数量', default=0, blank=True, null=True)
    aded = models.BooleanField(default=False, verbose_name="广告状态")
    ad_error = models.CharField(default='', max_length=100, null=True, blank=True, verbose_name="发布错误")

    class Meta:
        verbose_name = "兰亭SPU"
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.SPU

class Lightin_SKU(models.Model):

    lightin_spu = models.ForeignKey(Lightin_SPU, null=True, blank=True, verbose_name="SPU外键",
                                    related_name="spu_sku", on_delete=models.CASCADE)

    SPU = models.CharField(default='',max_length=300, null=True, blank=True, verbose_name="SPU")
    SKU = models.CharField(default='', max_length=100, null=True, blank=True, verbose_name="SKU")

    #barcode = models.CharField(u'barcode', default='', max_length=100, blank=True)

    o_quantity = models.IntegerField(u'oms_可用数量', default=0, blank=True, null=True)
    o_locked = models.IntegerField(u'oms_锁定数量', default=0, blank=True, null=True)
    o_reserved = models.IntegerField(u'oms_保留数量', default=0, blank=True, null=True)
    o_sellable = models.IntegerField(u'oms_可售数量', default=0, blank=True, null=True)


    vendor_sale_price = models.FloatField(verbose_name="供方销售价",default=0, blank=True, null=True)
    vendor_supply_price = models.FloatField(verbose_name="供方采购价", default=0, blank=True, null=True)



    weight = models.FloatField(verbose_name="weight", default=0, blank=True, null=True)
    length = models.FloatField(verbose_name="length", default=0, blank=True, null=True)
    width = models.FloatField(verbose_name="width", default=0, blank=True, null=True)
    height = models.FloatField(verbose_name="height", default=0, blank=True, null=True)

    skuattr = models.TextField(default='', null=True, blank=True, verbose_name="skuattr")

    #image = models.ImageField(u'组合图', upload_to='combo/', default="", null=True, blank=True)
    image = models.CharField(default='', max_length=200, null=True, blank=True, verbose_name="sku图")
    image_marked = models.CharField(default='', max_length=100, null=True, blank=True, verbose_name="组合水印图")

    comboed = models.BooleanField(u'是否组合商品', default=False, null=True)
    checked = models.BooleanField(u'是否审核', default=False, null=True)
    locked = models.BooleanField(u'库存锁定', default=False, null=True)
    imaged = models.BooleanField(u'图片已生成', default=False, null=True)
    listed = models.BooleanField(u'已发布到主站', default=False, null=True)
    published = models.BooleanField(u'已发布到Facebook', default=False, null=True)

    combo_error = models.CharField(default='', max_length=100, null=True, blank=True, verbose_name="组合错误")
    sku_price = models.IntegerField(u'sku售价', default=0, blank=True, null=True)

    #listing_status = models.BooleanField(u'发布到Facebook', default=False)

    #y_sellable = models.IntegerField(u'wms_可售数量', default=0, blank=True, null=True)
    #y_reserved = models.IntegerField(u'wms_待出库数量', default=0, blank=True, null=True)

    class Meta:
        verbose_name = "兰亭SKU"
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.SKU



class YallavipAlbum(models.Model):

    page = models.ForeignKey(MyPage, null=True, blank=True, verbose_name="Page",
                                related_name="page_album", on_delete=models.CASCADE)


    rule = models.ForeignKey(SelectionRule, null=True, blank=True, verbose_name="SelectionRule",
                                    related_name="rule_album", on_delete=models.CASCADE)

    album = models.ForeignKey(MyAlbum, null=True, blank=True, verbose_name="fb相册",
                                  related_name="myalbum_album", on_delete=models.SET_NULL)

    published = models.BooleanField(default=False, verbose_name="发布状态")
    publish_error = models.CharField(default='无',max_length=256, null=True, blank=True, verbose_name="发布错误(或图片数量)")
    published_time = models.DateTimeField(null=True, blank=True, verbose_name="发布时间")

    deleted = models.BooleanField(default=False, verbose_name="删除状态")
    delete_error = models.CharField(default='无', max_length=256, null=True, blank=True, verbose_name="删除结果")
    deleted_time = models.DateTimeField(null=True, blank=True, verbose_name="删除时间")

    active = models.BooleanField(default=False, verbose_name="有效性")

    class Meta:
        verbose_name = "Yallavip 相册"
        verbose_name_plural = verbose_name

    def __str__(self):

        return  self.rule.name


class LightinAlbum(models.Model):

    lightin_spu = models.ForeignKey(Lightin_SPU, null=True, blank=True, verbose_name="SPU",
                                related_name="myfb_product", on_delete=models.CASCADE)

    lightin_sku = models.ForeignKey(Lightin_SKU, null=True, blank=True, verbose_name="SKU",
                                    related_name="myfb_sku", on_delete=models.CASCADE)

    myalbum = models.ForeignKey('fb.MyAlbum', null=True, blank=True, verbose_name="相册",
                                  related_name="lightin_myalbum", on_delete=models.SET_NULL)

    yallavip_album = models.ForeignKey(YallavipAlbum, null=True, blank=True, verbose_name="yallavip相册",
                                related_name="yallavip_album", on_delete=models.SET_NULL)

    fb_id = models.CharField(default='',max_length=100, null=True, blank=True, verbose_name="接触点代码")

    batch_no = models.IntegerField(u'批次号', default=0, blank=True, null=True)
    name  = models.TextField(default='', null=True, blank=True, verbose_name="文案")
    image_marked = models.CharField(default='',max_length=100, null=True, blank=True, verbose_name="水印图")

    sourced = models.BooleanField(default=False, verbose_name="资源准备")
    source_error = models.CharField(default='', max_length=256, null=True, blank=True, verbose_name="资源错误")
    source_image = models.CharField(default='', max_length=100, null=True, blank=True, verbose_name="资源图")

    material =  models.BooleanField(default=False, verbose_name="素材准备")
    material_error = models.CharField(default='无',max_length=256, null=True, blank=True, verbose_name="素材错误")



    published = models.BooleanField(default=False, verbose_name="发布状态")
    publish_error = models.CharField(default='无',max_length=256, null=True, blank=True, verbose_name="发布错误(或图片数量)")
    published_time = models.DateTimeField(null=True, blank=True, verbose_name="发布时间")

    deleted = models.BooleanField(default=False, verbose_name="删除状态")
    delete_error = models.CharField(default='无', max_length=256, null=True, blank=True, verbose_name="删除结果")
    deleted_time = models.DateTimeField(null=True, blank=True, verbose_name="删除时间")

    aded = models.BooleanField(default=False, verbose_name="广告状态")

    class Meta:
        verbose_name = "相册图片"
        verbose_name_plural = verbose_name

    def __str__(self):

        return  self.name

class Lightin_barcode(models.Model):
    lightin_sku = models.ForeignKey(Lightin_SKU, null=True, blank=True, verbose_name="SKU",
                                    related_name="sku_barcode", on_delete=models.CASCADE)

    SKU = models.CharField(default='',max_length=300, null=True, blank=True, verbose_name="SKU")

    barcode = models.CharField(u'barcode', default='', max_length=100, blank=True)
    quantity = models.IntegerField(u'数量', default=0, blank=True, null=True)
    #sellable = models.IntegerField(u'可销售库存', default=0, blank=True, null=True)
    #occupied = models.IntegerField(u'订单占用库存', default=0, blank=True, null=True)
    o_quantity = models.IntegerField(u'oms_可用数量', default=0, blank=True, null=True)
    o_sellable = models.IntegerField(u'oms_可售数量', default=0, blank=True, null=True)
    o_reserved = models.IntegerField(u'oms_待出库数量', default=0, blank=True, null=True)

    o_shipped = models.IntegerField(u'oms_历史出库数量', default=0, blank=True, null=True)

    #unsellable = models.IntegerField(u'不可销售库存(', default=0, blank=True, null=True)
    locked = models.IntegerField(u'锁定库存', default=0, blank=True, null=True)
    #virtual = models.IntegerField(u'虚库存', default=0, blank=True, null=True)
    #transport = models.IntegerField(u'调拨占用库存', default=0, blank=True, null=True)
    #air = models.IntegerField(u'调拨中库存', default=0, blank=True, null=True)

    #wms相关信息：产品，库存
    product_status = models.CharField(u'product_status', default='', max_length=100, blank=True)
    product_title = models.CharField(u'product_title', default='', max_length=100, blank=True)
    product_weight = models.CharField(u'product_weight', default='', max_length=100, blank=True)

    warehouse = models.CharField(u'warehouse', default='', max_length=100, blank=True)
    warehouse_code = models.CharField(u'warehouse_code', default='', max_length=100, blank=True)

    y_onway = models.IntegerField(u'wms_在途数量', default=0, blank=True, null=True)
    y_pending = models.IntegerField(u'wms_待上架数量', default=0, blank=True, null=True)
    y_sellable = models.IntegerField(u'wms_可售数量', default=0, blank=True, null=True)
    y_unsellable = models.IntegerField(u'wms_不合格数量', default=0, blank=True, null=True)
    y_reserved = models.IntegerField(u'wms_待出库数量', default=0, blank=True, null=True)
    y_shipped = models.IntegerField(u'wms_历史出库数量', default=0, blank=True, null=True)

    updated_time = models.DateTimeField(null=True, blank=True, verbose_name="更新时间")
    def cal_occupied(self):
        from orders.models import  OrderDetail_lightin
        from django.db.models import Sum

        orderdetail_lightins = OrderDetail_lightin.objects.filter(
            order__financial_status="paid" ,
            order__fulfillment_status__isnull = True,
            order__status = "open",
            order__verify__verify_status = "SUCCESS",
            order__verify__sms_status = "CHECKED",
            order__wms_status__in = ["","W"],
            barcode__barcode = self.barcode
                                   )
        if orderdetail_lightins:
            return orderdetail_lightins.aggregate(nums = Sum('quantity')).get("nums")
        else:
            return 0

    cal_occupied.short_description = "占用库存"
    occupied = property(cal_occupied)

    def cal_sellable(self):


        return  self.o_sellable - self.occupied


    cal_sellable.short_description = "可售库存"
    sellable = property(cal_sellable)

    class Meta:
        verbose_name = "Lightin barcode映射"
        verbose_name_plural = verbose_name

    def __str__(self):

        return  self.barcode

class Combo(Lightin_SKU):
    '''
    combo_no = models.CharField(u'Combo', default='', max_length=100, blank=True)

    handle = models.CharField(u'货号', default='', max_length=256, null=True, blank=True)

    listed = models.BooleanField(u'已发布到主站', default=False)
    listing_status = models.BooleanField(u'发布到Facebook', default=False)

    o_quantity = models.IntegerField(u'oms_可用数量', default=1, blank=True, null=True)
    o_sellable = models.IntegerField(u'oms_可售数量', default=0, blank=True, null=True)
    o_reserved = models.IntegerField(u'oms_待出库数量', default=0, blank=True, null=True)

    image = models.ImageField(u'组合图', upload_to='combo/', default="", null=True, blank=True)
    image_marked = models.CharField(default='', max_length=100, null=True, blank=True, verbose_name="组合水印图")

    '''

    def cal_items(self):
        if self.combo_item:
            if self.combo_item:
                #return ",".join(self.combo_item.values_list("lightin_sku__SKU", flat=True))
                return ",".join(self.combo_item.values_list("SKU", flat=True))
            else:
                return ""
        else:
            return ""

    cal_items.short_description = "组合明细"
    items = property(cal_items)

    class Meta:
        proxy = True
        verbose_name = "组合产品"
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.SKU

class ComboItem(models.Model):
    combo = models.ForeignKey(Combo, null=True, blank=True, verbose_name="Combo",
                                    related_name="combo_item", on_delete=models.CASCADE)

    lightin_sku = models.ForeignKey(Lightin_SKU, null=True, blank=True, verbose_name="SKU",
                                    related_name="sku_comboitem", on_delete=models.CASCADE)
    SKU = models.CharField(default='', max_length=300, null=True, blank=True, verbose_name="SKU")
    #quantity = models.IntegerField(u'可用数量', default=0, blank=True, null=True)
    #o_sellable = models.IntegerField(u'oms_可售数量', default=0, blank=True, null=True)
    #o_reserved = models.IntegerField(u'oms_待出库数量', default=0, blank=True, null=True)



    class Meta:
        verbose_name = "组合产品明细"
        verbose_name_plural = verbose_name

    def __str__(self):
        if self.lightin_sku:
            return self.lightin_sku.SKU
        else:
            return ""

class WmsOriOrder(models.Model):

    order_id = models.CharField(u'订单id', default='', max_length=100, blank=True)
    order_no = models.CharField(u'订单号', default='', max_length=50, blank=True)
    tracking_no = models.CharField(u'跟踪号', default='', max_length=50, blank=True)
    status = models.CharField(u'订单状态', max_length=30, default='', blank=True)
    #track_status = models.CharField(u'派送状态', max_length=30, default='', blank=True)
    created_at = models.DateTimeField(u'创建时间', auto_now=False, blank=True, null=True)
    order_json  =  models.TextField(u'订单json', default='', null=True, blank=True)
    updated = models.BooleanField(u'更新状态', default=False)

    class Meta:
        verbose_name = "原始订单"
        verbose_name_plural = verbose_name


    def __str__(self):
        return self.order_id

class Token(models.Model):

    user_no = models.CharField(u'用户Facebookid', default='', max_length=100, blank=True)
    user_name = models.CharField(u'用户Facebook名字', default='', max_length=100, blank=True)
    long_token = models.CharField(u'token', default='', max_length=300, blank=True)

    update_at = models.DateTimeField(u'更新时间', auto_now=False, blank=True, null=True)
    active = models.BooleanField(u'客户状态', default=False)
    info = models.CharField(u'token', default='', max_length=300, blank=True)

    page_no = models.CharField(u'page_no', default='', max_length=100, blank=True)

    class Meta:
        verbose_name = "token 管理"
        verbose_name_plural = verbose_name


    def __str__(self):
        return self.user_no


class YallavipAd(models.Model):
    yallavip_album = models.ForeignKey(YallavipAlbum, null=True, blank=True, verbose_name="yallavip_album",
                                    related_name="yallavip_album_ad", on_delete=models.CASCADE)
    page_no = models.CharField(u'page_no', default='', max_length=300, blank=True)

    spus_name = models.CharField(u'spus_name', default='', max_length=300, blank=True)
    image_marked_url = models.CharField(u'image_marked_url', default='', max_length=300, blank=True)
    message = models.CharField(u'message', default='', max_length=500, blank=True)
    adset_no = models.CharField(u'adset_no', default='', max_length=500, blank=True)
    creative_id = models.CharField(u'creative_id', default='', max_length=500, blank=True)
    ad_id = models.CharField(u'ad_id', default='', max_length=500, blank=True)

    active = models.BooleanField(default=False, verbose_name="有效性")
    published = models.BooleanField(default=False, verbose_name="发布状态")
    publish_error = models.CharField(default='无', max_length=256, null=True, blank=True, verbose_name="发布错误(或图片数量)")
    published_time = models.DateTimeField(null=True, blank=True, verbose_name="发布时间")

    ad_status = models.CharField(default='无', max_length=50, null=True, blank=True, verbose_name="广告状态")
    update_error = models.CharField(default='无', max_length=256, null=True, blank=True, verbose_name="更新错误")

    class Meta:
        verbose_name = "Yallavip 广告"
        verbose_name_plural = verbose_name

    def __str__(self):

        return  self.spus_name