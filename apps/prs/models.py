from commodity.models import SelectionRule
from datetime import datetime
from django.db import models
from fb.models import MyPage, MyPhoto, MyFeed, MyAd, MyAlbum
from shop.models import ShopifyProduct


# Create your models here.

class MyCategory(models.Model):
    """
    商品类别
    """
    super_cate = models.ForeignKey('self', blank=True, null=True, on_delete=models.CASCADE,
                                   verbose_name="父品类")
    super_name = models.CharField(u'父品类名', default='', max_length=100, null=True, blank=True)
    name = models.CharField(u'品类名', default='', max_length=100, null=True, blank=True)
    level = models.BigIntegerField(u'层级', default=0, null=True, blank=True)
    tags = models.CharField(u'tags', default='', max_length=500, null=True, blank=True)
    vendor = models.CharField(u'vendor', default='', max_length=500, null=True, blank=True)

    active = models.BooleanField(default=True, verbose_name="可用")
    published = models.BooleanField(default=False, verbose_name="已发布")

    collcetion_no = models.CharField(u'collcetion_no', default='', max_length=500, null=True, blank=True)
    publishe_error = models.CharField(u'publishe_error', default='', max_length=500, null=True, blank=True)
    sellable_gt = models.IntegerField(u'最低库存', default=0, blank=True, null=True)
    '''
    cate_1 = models.CharField(u'cate_1', default='', max_length=256, null=True, blank=True)
    cate_2 = models.CharField(u'cate_2', default='', max_length=256, null=True, blank=True)
    cate_3 = models.CharField(u'cate_3', default='', max_length=256, null=True, blank=True)
    '''

    class Meta:
        verbose_name = "商品品类"
        verbose_name_plural = verbose_name

        app_label = 'prs'
        ordering = ['name']

    def __str__(self):
        # return self.tags
        return self.super_name + '-'+ str(self.level) + '-' + self.name


class Lightin_SPU(models.Model):
    mycategory = models.ForeignKey(MyCategory, null=True, blank=True, verbose_name="品类",
                                   related_name="cate_spu", on_delete=models.CASCADE)

    SPU = models.CharField(default='', max_length=300, null=True, blank=True, verbose_name="SPU")

    vendor = models.CharField(default='', max_length=20, null=True, blank=True, verbose_name="Vendor")

    en_name = models.CharField(default='', max_length=300, null=True, blank=True, verbose_name="en_name")
    cn_name = models.CharField(default='', max_length=300, null=True, blank=True, verbose_name="cn_name")
    cate_1 = models.CharField(u'cate_1', default='', max_length=256, null=True, blank=True)
    cate_2 = models.CharField(u'cate_2', default='', max_length=256, null=True, blank=True)
    cate_3 = models.CharField(u'cate_3', default='', max_length=256, null=True, blank=True)

    vendor_sale_price = models.FloatField(verbose_name="供方销售价", default=0)
    vendor_supply_price = models.FloatField(verbose_name="供方采购价", default=0)
    link = models.CharField(default='', max_length=300, null=True, blank=True, verbose_name="link")

    title = models.CharField(default='', max_length=300, null=True, blank=True, verbose_name="title")
    breadcrumb = models.CharField(default='', max_length=300, null=True, blank=True, verbose_name="breadcrumb")

    currency = models.CharField(default='', max_length=300, null=True, blank=True, verbose_name="currency")

    sale_price = models.FloatField(verbose_name="供方实际销售价", default=0)
    images = models.TextField(default='', null=True, blank=True, verbose_name="图片")
    images_dict = models.TextField(default='', null=True, blank=True, verbose_name="图片字典")
    attr_image_dict = models.TextField(default='', null=True, blank=True, verbose_name="属性图片字典")

    got = models.BooleanField(default=False, verbose_name="获取状态", null=True, blank=True, )
    got_error = models.CharField(default='', max_length=100, null=True, blank=True, verbose_name="获取错误")
    got_time = models.DateTimeField(null=True, blank=True, verbose_name="更新时间")

    yallavip_price = models.FloatField(u'yallavip售价', default=0, blank=True, null=True)
    free_shipping_price = models.FloatField(u'yallavip包邮价', default=0, blank=True, null=True)

    shopify_price = models.FloatField(u'shopify售价', default=0, blank=True, null=True)

    published = models.BooleanField(default=False, verbose_name="发布到shopify状态")
    shopify_published = models.BooleanField(default=False, verbose_name="shopify发布状态")

    image_published = models.BooleanField(default=False, verbose_name="图片发布到shopify状态")
    images_shopify = models.TextField(default='', null=True, blank=True, verbose_name="shopify图片字典")
    publish_error = models.CharField(default='无', max_length=100, null=True, blank=True, verbose_name="发布错误")
    published_time = models.DateTimeField(null=True, blank=True, verbose_name="发布时间")

    # shopify_product = models.ForeignKey(ShopifyProduct, null=True, blank=True, verbose_name="shopify产品",
    #                               related_name="shopify_spu", on_delete=models.CASCADE)

    product_no = models.CharField(default='', max_length=300, null=True, blank=True, verbose_name="shopify product_no")
    handle = models.CharField(default='', max_length=300, null=True, blank=True, verbose_name="handle")

    updated = models.BooleanField(default=False, verbose_name="更新状态")
    update_error = models.CharField(default='', max_length=500, null=True, blank=True, verbose_name="更新错误")

    quantity = models.IntegerField(u'数量', default=0, blank=True, null=True)

    sellable = models.IntegerField(u'oms_可售数量', default=0, blank=True, null=True)

    aded = models.BooleanField(default=False, verbose_name="广告状态")
    ad_error = models.CharField(default='', max_length=100, null=True, blank=True, verbose_name="发布错误")

    active = models.BooleanField(default=True, verbose_name="有效性")
    promoted = models.BooleanField(default=False, verbose_name="促销状态")
    free_shipping = models.BooleanField(default=False, verbose_name="包邮状态")

    longaded = models.BooleanField(default=False, verbose_name="长期广告状态")
    size_count = models.IntegerField(u'size数量', default=0, blank=True, null=True)
    one_size = models.BooleanField(default=False, verbose_name="均码")

    class Meta:
        verbose_name = "兰亭SPU"
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.SPU


class Lightin_SKU(models.Model):
    lightin_spu = models.ForeignKey(Lightin_SPU, null=True, blank=True, verbose_name="SPU外键",
                                    related_name="spu_sku", on_delete=models.CASCADE)

    SPU = models.CharField(default='', max_length=300, null=True, blank=True, verbose_name="SPU")
    SKU = models.CharField(default='', max_length=100, null=True, blank=True, verbose_name="SKU")

    # barcode = models.CharField(u'barcode', default='', max_length=100, blank=True)

    o_quantity = models.IntegerField(u'oms_可用数量', default=0, blank=True, null=True)
    o_locked = models.IntegerField(u'oms_锁定数量', default=0, blank=True, null=True)
    o_reserved = models.IntegerField(u'oms_保留数量', default=0, blank=True, null=True)
    o_sellable = models.IntegerField(u'oms_可售数量', default=0, blank=True, null=True)

    vendor_sale_price = models.FloatField(verbose_name="供方销售价", default=0, blank=True, null=True)
    vendor_supply_price = models.FloatField(verbose_name="供方采购价", default=0, blank=True, null=True)

    weight = models.FloatField(verbose_name="weight", default=0, blank=True, null=True)
    length = models.FloatField(verbose_name="length", default=0, blank=True, null=True)
    width = models.FloatField(verbose_name="width", default=0, blank=True, null=True)
    height = models.FloatField(verbose_name="height", default=0, blank=True, null=True)

    skuattr = models.TextField(default='', null=True, blank=True, verbose_name="skuattr")
    size = models.CharField(default='', max_length=100, null=True, blank=True, verbose_name="size")

    # image = models.ImageField(u'组合图', upload_to='combo/', default="", null=True, blank=True)
    image = models.TextField(default='', null=True, blank=True, verbose_name="sku图")
    image_marked = models.CharField(default='', max_length=100, null=True, blank=True, verbose_name="组合水印图")

    comboed = models.BooleanField(u'是否组合商品', default=False, null=True)
    checked = models.BooleanField(u'是否审核', default=False, null=True)
    locked = models.BooleanField(u'库存锁定', default=False, null=True)
    imaged = models.BooleanField(u'图片已生成', default=False, null=True)
    listed = models.BooleanField(u'已发布到主站', default=False, null=True)
    published = models.BooleanField(u'已发布到Facebook', default=False, null=True)

    combo_error = models.CharField(default='', max_length=100, null=True, blank=True, verbose_name="组合错误")
    sku_price = models.IntegerField(u'sku售价', default=0, blank=True, null=True)
    free_shipping_price = models.FloatField(u'yallavip包邮价', default=0, blank=True, null=True)

    # listing_status = models.BooleanField(u'发布到Facebook', default=False)

    # y_sellable = models.IntegerField(u'wms_可售数量', default=0, blank=True, null=True)
    # y_reserved = models.IntegerField(u'wms_待出库数量', default=0, blank=True, null=True)

    class Meta:
        verbose_name = "兰亭SKU"
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.SKU


class YallavipAlbum(models.Model):
    page = models.ForeignKey(MyPage, null=True, blank=True, verbose_name="Page",
                             related_name="page_album", on_delete=models.CASCADE)

    cate = models.ForeignKey(MyCategory, null=True, blank=True, verbose_name="MyCategory",
                             related_name="cate_album", on_delete=models.CASCADE)
    # catesize = models.ForeignKey(MyCategorySize, null=True, blank=True, verbose_name="MyCategorySize",
    #                               related_name="catesize_album", on_delete=models.CASCADE)

    # rule = models.ForeignKey(SelectionRule, null=True, blank=True, verbose_name="SelectionRule",
    #                               related_name="rule_album", on_delete=models.CASCADE)

    album = models.ForeignKey(MyAlbum, null=True, blank=True, verbose_name="fb相册",
                              related_name="myalbum_album", on_delete=models.SET_NULL)

    published = models.BooleanField(default=False, verbose_name="发布状态")
    publish_error = models.CharField(default='无', max_length=256, null=True, blank=True, verbose_name="发布错误(或图片数量)")
    published_time = models.DateTimeField(null=True, blank=True, verbose_name="发布时间")

    deleted = models.BooleanField(default=False, verbose_name="删除状态")
    delete_error = models.CharField(default='无', max_length=256, null=True, blank=True, verbose_name="删除结果")
    deleted_time = models.DateTimeField(null=True, blank=True, verbose_name="删除时间")

    active = models.BooleanField(default=False, verbose_name="有效性")

    class Meta:
        verbose_name = "Yallavip 相册"
        verbose_name_plural = verbose_name

    def __str__(self):
        if self.cate:
            return self.cate.name
        elif self.catesize:
            return self.catesize.size.name + " " + self.catesize.size


class LightinAlbum(models.Model):
    lightin_spu = models.ForeignKey(Lightin_SPU, null=True, blank=True, verbose_name="SPU",
                                    related_name="myfb_product", on_delete=models.CASCADE)

    lightin_sku = models.ForeignKey(Lightin_SKU, null=True, blank=True, verbose_name="SKU",
                                    related_name="myfb_sku", on_delete=models.CASCADE)

    # myalbum = models.ForeignKey('fb.MyAlbum', null=True, blank=True, verbose_name="相册",
    #                             related_name="lightin_myalbum", on_delete=models.SET_NULL)

    yallavip_album = models.ForeignKey(YallavipAlbum, null=True, blank=True, verbose_name="yallavip相册",
                                       related_name="yallavip_album", on_delete=models.SET_NULL)

    fb_id = models.CharField(default='', max_length=100, null=True, blank=True, verbose_name="接触点代码")

    batch_no = models.IntegerField(u'批次号', default=0, blank=True, null=True)
    name = models.TextField(default='', null=True, blank=True, verbose_name="文案")
    image_pure = models.CharField(default='', max_length=100, null=True, blank=True, verbose_name="无logo水印图")
    image_marked = models.CharField(default='', max_length=100, null=True, blank=True, verbose_name="水印图")

    sourced = models.BooleanField(default=False, verbose_name="资源准备")
    source_error = models.CharField(default='', max_length=256, null=True, blank=True, verbose_name="资源错误")
    source_image = models.CharField(default='', max_length=100, null=True, blank=True, verbose_name="资源图")

    material = models.BooleanField(default=False, verbose_name="素材准备")
    material_error = models.CharField(default='无', max_length=256, null=True, blank=True, verbose_name="素材错误")

    published = models.BooleanField(default=False, verbose_name="发布状态")
    publish_error = models.CharField(default='无', max_length=256, null=True, blank=True, verbose_name="发布错误(或图片数量)")
    published_time = models.DateTimeField(null=True, blank=True, verbose_name="发布时间")

    todelete = models.BooleanField(default=False, verbose_name="待删除")
    deleted = models.BooleanField(default=False, verbose_name="删除状态")
    delete_error = models.CharField(default='无', max_length=256, null=True, blank=True, verbose_name="删除结果")
    deleted_time = models.DateTimeField(null=True, blank=True, verbose_name="删除时间")

    aded = models.BooleanField(default=False, verbose_name="广告状态")
    free_shipping = models.BooleanField(default=False, verbose_name="包邮状态")

    class Meta:
        verbose_name = "相册图片"
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.name


class Lightin_barcode(models.Model):
    lightin_sku = models.ForeignKey(Lightin_SKU, null=True, blank=True, verbose_name="SKU",
                                    related_name="sku_barcode", on_delete=models.CASCADE)

    SKU = models.CharField(default='', max_length=300, null=True, blank=True, verbose_name="SKU")

    barcode = models.CharField(u'barcode', default='', max_length=100, blank=True)
    quantity = models.IntegerField(u'数量', default=0, blank=True, null=True)
    # sellable = models.IntegerField(u'可销售库存', default=0, blank=True, null=True)
    # occupied = models.IntegerField(u'订单占用库存', default=0, blank=True, null=True)
    o_quantity = models.IntegerField(u'oms_可用数量', default=0, blank=True, null=True)
    o_sellable = models.IntegerField(u'oms_可售数量', default=0, blank=True, null=True)
    o_reserved = models.IntegerField(u'oms_待出库数量', default=0, blank=True, null=True)

    o_shipped = models.IntegerField(u'oms_历史出库数量', default=0, blank=True, null=True)

    # unsellable = models.IntegerField(u'不可销售库存(', default=0, blank=True, null=True)
    locked = models.IntegerField(u'锁定库存', default=0, blank=True, null=True)
    # virtual = models.IntegerField(u'虚库存', default=0, blank=True, null=True)
    # transport = models.IntegerField(u'调拨占用库存', default=0, blank=True, null=True)
    # air = models.IntegerField(u'调拨中库存', default=0, blank=True, null=True)

    # wms相关信息：产品，库存
    product_status = models.CharField(u'product_status', default='', max_length=100, blank=True)
    product_title = models.CharField(u'product_title', default='', max_length=100, blank=True)
    product_weight = models.CharField(u'product_weight', default='', max_length=100, blank=True)
    product_add_time = models.DateTimeField(null=True, blank=True, verbose_name="product_add_time")
    product_modify_time = models.DateTimeField(null=True, blank=True, verbose_name="product_modify_time")

    warehouse = models.CharField(u'warehouse', default='', max_length=100, blank=True)
    warehouse_code = models.CharField(u'warehouse_code', default='', max_length=100, blank=True)

    y_onway = models.IntegerField(u'wms_在途数量', default=0, blank=True, null=True)
    y_pending = models.IntegerField(u'wms_待上架数量', default=0, blank=True, null=True)
    y_sellable = models.IntegerField(u'wms_可售数量', default=0, blank=True, null=True)
    y_unsellable = models.IntegerField(u'wms_不合格数量', default=0, blank=True, null=True)
    y_reserved = models.IntegerField(u'wms_待出库数量', default=0, blank=True, null=True)
    y_shipped = models.IntegerField(u'wms_历史出库数量', default=0, blank=True, null=True)

    updated_time = models.DateTimeField(null=True, blank=True, verbose_name="更新时间")
    synced = models.BooleanField(default=False, verbose_name="库存同步状态")

    def cal_occupied(self):
        from orders.models import OrderDetail_lightin
        from django.db.models import Sum

        orderdetail_lightins = OrderDetail_lightin.objects.filter(
            order__financial_status="paid",
            order__fulfillment_status__isnull=True,
            order__status="open",
            order__verify__verify_status="SUCCESS",
            order__verify__sms_status="CHECKED",
            order__wms_status__in=["", "W"],
            barcode__barcode=self.barcode
        )
        if orderdetail_lightins:
            return orderdetail_lightins.aggregate(nums=Sum('quantity')).get("nums")
        else:
            return 0

    cal_occupied.short_description = "占用库存"
    occupied = property(cal_occupied)

    def cal_sellable(self):
        if not self.occupied:
            print("occupied 不存在" )
            return  self.o_sellable


        if self.o_sellable and self.occupied:
            return self.o_sellable - self.occupied
        else:
            return 0

    cal_sellable.short_description = "可售库存"
    sellable = property(cal_sellable)

    def save(self, *args, **kwargs):
        # do_something()
        if self.synced == True:
            self.synced = False
        super().save(*args, **kwargs)  # Call the "real" save() method.
        # do_something_else()

    class Meta:
        verbose_name = "Lightin barcode映射"
        verbose_name_plural = verbose_name

    def __str__(self):

        return self.barcode


class WmsOriOrder(models.Model):
    order_id = models.CharField(u'订单id', default='', max_length=100, blank=True)
    order_no = models.CharField(u'订单号', default='', max_length=50, blank=True)
    tracking_no = models.CharField(u'跟踪号', default='', max_length=50, blank=True)
    status = models.CharField(u'订单状态', max_length=30, default='', blank=True)
    # track_status = models.CharField(u'派送状态', max_length=30, default='', blank=True)
    created_at = models.DateTimeField(u'创建时间', auto_now=False, blank=True, null=True)
    order_json = models.TextField(u'订单json', default='', null=True, blank=True)
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

    object_story_id = models.CharField(default='', max_length=256, null=True, blank=True,
                                       verbose_name="object_story_id")
    fb_feed = models.ForeignKey(MyFeed, null=True, blank=True, verbose_name="fb_feed",
                                related_name="feed_ad", on_delete=models.CASCADE)

    creative_id = models.CharField(u'creative_id', default='', max_length=500, blank=True)

    active = models.BooleanField(default=False, verbose_name="有效性")
    published = models.BooleanField(default=False, verbose_name="post发布状态")
    publish_error = models.CharField(default='无', max_length=256, null=True, blank=True, verbose_name="发布错误(或图片数量)")
    published_time = models.DateTimeField(null=True, blank=True, verbose_name="发布时间")

    ad_id = models.CharField(u'ad_id', default='', max_length=500, blank=True)
    ad_status = models.CharField(default='无', max_length=50, null=True, blank=True, verbose_name="广告状态")
    update_error = models.CharField(default='无', max_length=256, null=True, blank=True, verbose_name="更新错误")

    engagement_aded = models.BooleanField(default=False, verbose_name="互动广告状态")
    engagement_ad_id = models.CharField(u'互动广告_id', default='', max_length=500, blank=True)
    engagement_ad_status = models.CharField(default='无', max_length=50, null=True, blank=True, verbose_name="广告状态")
    engagement_ad_published_time = models.DateTimeField(null=True, blank=True, verbose_name="互动广告发布时间")
    engagement_ad_publish_error = models.CharField(default='无', max_length=256, null=True, blank=True,
                                                   verbose_name="互动广告publish_error")

    message_aded = models.BooleanField(default=False, verbose_name="消息广告状态")
    message_ad_id = models.CharField(u'message_ad_id', default='', max_length=500, blank=True)
    message_ad_status = models.CharField(default='无', max_length=50, null=True, blank=True, verbose_name="广告状态")
    message_ad_published_time = models.DateTimeField(null=True, blank=True, verbose_name="message_ad发布时间")
    message_ad_publish_error = models.CharField(default='无', max_length=256, null=True, blank=True,
                                                verbose_name="message_ad_publish_error")

    long_ad = models.BooleanField(default=False, verbose_name="long_ad")
    #cate = models.CharField(default='无', max_length=500, null=True, blank=True, verbose_name="cate_tags")
    cate = models.ForeignKey(MyCategory, null=True, blank=True, verbose_name="Category",
                                       related_name="mycate_ad", on_delete=models.CASCADE)

    def cal_sellable(self):
        handle_list = self.spus_name.split(",")
        sellable = Lightin_SPU.objects.filter(handle__in=handle_list).values("handle", "sellable")
        return list(sellable)

    cal_sellable.short_description = "可售库存"
    sellable = property(cal_sellable)

    free_shipping = models.BooleanField(default=False, verbose_name="包邮状态")

    class Meta:
        verbose_name = "Yallavip 广告"
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.spus_name


# page 主推 cate
class PagePromoteCate(models.Model):
    mypage = models.OneToOneField(MyPage, on_delete=models.CASCADE, verbose_name="Page")

    cate = models.ManyToManyField(MyCategory, blank=False, verbose_name="Cate",
                                  related_name="cate_page")
    cate_active = models.BooleanField(default=False, verbose_name="cate可用")

    promote_cate = models.ManyToManyField(MyCategory, blank=False, verbose_name="Promote Cate",
                                          related_name="cate_promote")
    promote_cate_active = models.BooleanField(default=False, verbose_name="promote_cate可用")

    class Meta:
        verbose_name = "page主推cate"
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.mypage.page
