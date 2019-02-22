from django.db import models
from fb.models import MyPhoto,MyFeed,MyAd,MyAlbum

from datetime import datetime


# Create your models here.

class MyCategory(models.Model):
    """
    商品类别
    """
    super_cate = models.ForeignKey('self', blank=True,null=True, on_delete=models.CASCADE,
                                 verbose_name="父品类")
    code = models.CharField(u'code', default='', max_length=256, null=True, blank=True)
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

    got = models.BooleanField(default=False, verbose_name="获取状态")
    got_error = models.CharField(default='无', max_length=100, null=True, blank=True, verbose_name="获取错误")
    got_time = models.DateTimeField(null=True, blank=True, verbose_name="更新时间")

    shopify_price = models.FloatField(u'shopify售价', default=0, blank=True, null=True)

    published = models.BooleanField(default=False, verbose_name="发布到shopify状态")
    publish_error = models.CharField(default='无', max_length=100, null=True, blank=True, verbose_name="发布错误")
    published_time = models.DateTimeField(null=True, blank=True, verbose_name="发布时间")

    product_no = models.CharField(default='', max_length=300, null=True, blank=True, verbose_name="shopify product_no")
    handle = models.CharField(default='', max_length=300, null=True, blank=True, verbose_name="handle")

    class Meta:
        verbose_name = "兰亭SPU"
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.SPU

class Lightin_SKU(models.Model):
    lightin_spu = models.ForeignKey(Lightin_SPU, null=True, blank=True, verbose_name="SPU外键",
                                    related_name="spu_sku", on_delete=models.CASCADE)

    SPU = models.CharField(default='',max_length=300, null=True, blank=True, verbose_name="SPU")

    SKU = models.CharField(default='',max_length=300, null=True, blank=True, verbose_name="SKU")
    barcode = models.CharField(u'barcode', default='', max_length=100, blank=True)

    quantity = models.IntegerField(u'数量', default=0, blank=True, null=True)

    vendor_sale_price = models.FloatField(verbose_name="供方销售价",default=0)
    vendor_supply_price = models.FloatField(verbose_name="供方采购价", default=0)



    weight = models.FloatField(verbose_name="weight", default=0)
    length = models.FloatField(verbose_name="length", default=0)
    width = models.FloatField(verbose_name="width", default=0)
    height = models.FloatField(verbose_name="height", default=0)

    skuattr = models.TextField(default='', null=True, blank=True, verbose_name="skuattr")

    class Meta:
        verbose_name = "兰亭SKU"
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.SPU

class LightinAlbum(models.Model):

    lightin_spu = models.ForeignKey(Lightin_SPU, null=True, blank=True, verbose_name="SPU",
                                related_name="myfb_product", on_delete=models.CASCADE)


    myalbum = models.ForeignKey('fb.MyAlbum', null=True, blank=True, verbose_name="相册",
                                  related_name="lightin_myalbum", on_delete=models.SET_NULL)

    fb_id = models.CharField(default='',max_length=100, null=True, blank=True, verbose_name="接触点代码")

    batch_no = models.IntegerField(u'批次号', default=0, blank=True, null=True)
    name  = models.TextField(default='', null=True, blank=True, verbose_name="文案")
    image_marked = models.CharField(default='',max_length=100, null=True, blank=True, verbose_name="水印图")

    material =  models.BooleanField(default=False, verbose_name="素材准备")
    material_error = models.CharField(default='无',max_length=256, null=True, blank=True, verbose_name="素材错误")

    published = models.BooleanField(default=False, verbose_name="发布状态")
    publish_error = models.CharField(default='无',max_length=256, null=True, blank=True, verbose_name="发布错误(或图片数量)")
    published_time = models.DateTimeField(null=True, blank=True, verbose_name="发布时间")

    class Meta:
        verbose_name = "Lightin 相册"
        verbose_name_plural = verbose_name

    def __str__(self):

        return  self.lightin_spu.SPU