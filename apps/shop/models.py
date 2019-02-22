from django.db import models

from fb.models import MyPage

# Create your models here.
class Shop(models.Model):

    shop_name = models.CharField(u'店铺名', default='', max_length=100, blank=True)
    apikey  =  models.CharField(u'API_KEY', default='', max_length=100, blank=True)
    password =  models.CharField(u'PASSWORD', default='', max_length=100, blank=True)
    #max_product_no = models.CharField(u'max_product_no', default='', max_length=100, blank=True)
    product_updated_time = models.DateTimeField(u'product最后更新时间', auto_now=False, null=True, blank=True)
    customer_updated_time = models.DateTimeField(u'customer最后更新时间', auto_now=False, null=True, blank=True)
    max_id = models.IntegerField(u'max_id', default=0, null=True,blank=True)
    class Meta:
        verbose_name = "店铺"
        verbose_name_plural = verbose_name


    def __str__(self):
        return self.shop_name


class ShopifyProduct(models.Model):
    #myproduct = models.ForeignKey('prs.MyProduct', null=True, blank=True, verbose_name="产品",
     #                             related_name="shop_myproduct", on_delete=models.CASCADE)
    #myproductali = models.ForeignKey('prs.MyProductAli', null=True, blank=True, verbose_name="货源",
     #                                related_name="shop_myali", on_delete=models.CASCADE)


    SUPPLY_STATUS = (
        ("NORMAL", "正常"),
        ("DELAY", "供货延迟"),
        ("STOP", "断货"),
        # ("PAUSE", "缺货"),
    )

    shop = models.ForeignKey(Shop, related_name='shop_product', null=True, on_delete=models.CASCADE,
                                 verbose_name="店铺")
    shop_name = models.CharField(u'店铺名', default='', max_length=100,null=True, blank=True)

    product_no = models.BigIntegerField(u'id', default=0, null=True,blank=True)
    handle  =  models.CharField(u'handle', default='', max_length=256, null=True,blank=True)

    cate_1 = models.CharField(u'cate_1', default='', max_length=256, null=True, blank=True)
    cate_2 = models.CharField(u'cate_2', default='', max_length=256, null=True, blank=True)
    cate_3    = models.CharField(u'cate_3', default='', max_length=256, null=True, blank=True)

    body_html = models.TextField(u'body_html', default='', max_length=1024,null=True, blank=True)
    title = models.CharField(u'产品名', default='', max_length=500, null=True,blank=True)
    created_at =  models.DateTimeField(u'创建时间', auto_now=False, null=True, blank=True)

    published_at = models.DateTimeField(u'发布时间', auto_now=False, null=True, blank=True)
    updated_at = models.DateTimeField(u'更新时间', auto_now=False, null=True, blank=True)
    product_type = models.CharField(u'product_type', default='', max_length=100,null=True, blank=True)

    tags = models.CharField(u'tags', default='', max_length=256,null=True, blank=True)

    metafields_global_title_tag = models.CharField(u'SEO_name', default='', max_length=200,null=True, blank=True)
    metafields_global_description_tag = models.CharField(u'SEO_desc', default='', max_length=500, null=True,blank=True)
    vendor = models.CharField(u'供应商', default='', max_length=100, null=True,blank=True)


    listed = models.BooleanField(u'已发布', default=False)

    listing_status = models.BooleanField(u'发布到Facebook', default=False)

    supply_status = models.CharField(u'供应状态', choices=SUPPLY_STATUS, max_length=50, default='NORMAL', blank=True)
    supply_comments = models.CharField(u'供应备注', max_length=500, default='', blank=True)


    category_code = models.CharField(u'类目', default='', max_length=100, null=True,blank=True)

    total_orders = models.IntegerField(u'总订单数', default=0, blank=True, null=True)
    total_quantity = models.IntegerField(u'总销售数', default=0, blank=True, null=True)

    class Meta:
        verbose_name = "shopify商品"
        verbose_name_plural = verbose_name

        app_label = 'shop'

    def __str__(self):
        return self.handle

class ShopifyVariant(models.Model):
    SUPPLY_STATUS = (
        ("NORMAL", "正常"),
        ("DELAY", "供货延迟"),
        ("STOP", "断货"),
        # ("PAUSE", "缺货"),
    )

    shopifyproduct = models.ForeignKey(ShopifyProduct, related_name='product_variant', null=True, on_delete=models.CASCADE,
                                 verbose_name="商品")
    product_no = models.CharField(u'product_no',  max_length=100,default='', blank=True, null=True)
    variant_no = models.CharField(u'id', default='', max_length=100, blank=True)
    barcode  =  models.CharField(u'barcode', default='', max_length=100, blank=True)
    compare_at_price = models.CharField(u'原价', default='', max_length=100, blank=True)
    created_at = models.DateTimeField(u'创建时间', auto_now=False, null=True, blank=True)
    updated_at = models.DateTimeField(u'更新时间', auto_now=False, null=True, blank=True)
    fulfillment_service = models.CharField(u'fulfillment_service', default='', max_length=100, blank=True)

    grams = models.IntegerField(u'克量',default=0,blank=True, null=True)
    weight = models.IntegerField(u'weight',default=0,blank=True, null=True)
    weight_unit = models.CharField(u'weight_unit', default='g', max_length=100, blank=True)

    image_no = models.CharField(u'image_no', default='', max_length=200, null=True,blank=True)
    inventory_item_no = models.CharField(u'inventory_item_no', default='', max_length=500, blank=True)
    inventory_management = models.CharField(u'inventory_management', default='', max_length=100, blank=True)

    inventory_policy = models.CharField(u'inventory_policy', default='', max_length=200, blank=True)
    inventory_quantity = models.CharField(u'inventory_quantity', default='', max_length=500, blank=True)
    option1 = models.CharField(u'option1', default='', max_length=500, null=True,blank=True)
    option2 = models.CharField(u'option2', default='', max_length=500, null=True,blank=True)
    option3 = models.CharField(u'option3', default='', max_length=500, null=True,blank=True)
    position = models.IntegerField(u'position', default=0, blank=True, null=True)
    price = models.DecimalField(u'price', max_digits = 10,decimal_places=2, default='', blank=True, null=True)

    requires_shipping = models.BooleanField(u'requires_shipping', default=True)

    taxable = models.BooleanField(u'taxable', default=True)

    tax_code = models.CharField(u'tax_code', default='', max_length=200, blank=True)
    title = models.CharField(u'title', default='', max_length=500,  null=True,blank=True)
    sku = models.CharField(u'sku', default='', max_length=100,  null=True,blank=True)

    listing_status = models.BooleanField(u'发布到Facebook', default=False)
    supply_status = models.CharField(u'供应状态', choices=SUPPLY_STATUS, max_length=50, default='NORMAL', blank=True)
    supply_comments = models.CharField(u'供应备注', max_length=500, default='', blank=True)

    total_orders = models.IntegerField(u'总订单数', default=0, blank=True, null=True)
    total_quantity = models.IntegerField(u'总销售数', default=0, blank=True, null=True)

    class Meta:
        verbose_name = "变体"
        verbose_name_plural = verbose_name

        app_label = "shop"

    def __str__(self):
        return self.variant_no



class ShopifyImage(models.Model):
    shopifyproduct = models.ForeignKey(ShopifyProduct, related_name='product_image', null=True,
                                       on_delete=models.CASCADE, verbose_name="商品")
    product_no = models.CharField(u'product_no', default='', max_length=100, blank=True)

    image_no = models.CharField(u'image_no', default='', max_length=100, blank=True)
    position  =  models.IntegerField(u'position', default=0, blank=True, null=True)

    created_at = models.DateTimeField(u'created_at', auto_now=False, null=True, blank=True)
    updated_at = models.DateTimeField(u'updated_at', auto_now=False, null=True, blank=True)

    width = models.IntegerField(u'width', default=0, blank=True, null=True)
    height = models.IntegerField(u'height', default=0, blank=True, null=True)
    src = models.CharField(u'src', default='', max_length=256, blank=True)



    class Meta:
        verbose_name = "ShopifyImage"
        verbose_name_plural = verbose_name


    def __str__(self):
        return self.image_no

class ShopifyOptions(models.Model):
    shopifyproduct = models.ForeignKey(ShopifyProduct, related_name='product_options', null=True,
                                       on_delete=models.CASCADE, verbose_name="商品")
    option_no = models.CharField(u'option_no', default='', max_length=100, blank=True)
    product_no = models.CharField(u'product_no', default='', max_length=100, blank=True)

    name = models.CharField(u'option_no', default='', max_length=100, blank=True)
    values  =  models.CharField(u'values', default='', max_length=5000, blank=True)

    class Meta:
        verbose_name = "ShopifyOptions"
        verbose_name_plural = verbose_name


    def __str__(self):
        return self.name

class Combination(models.Model):
    shopifyproduct = models.ForeignKey(ShopifyProduct, related_name='product_combination', null=True,
                                       on_delete=models.CASCADE, verbose_name="商品")
    #product_no = models.CharField(u'product_no', default='', max_length=100, blank=True)
    handle = models.CharField(u'handle', default='', max_length=256, null=True, blank=True)
    sku = models.CharField(u'title', default='', max_length=100, null=True, blank=True)
    quantity = models.IntegerField(u'数量', default=0, blank=True, null=True)


    class Meta:
        verbose_name = "组合商品sku"
        verbose_name_plural = verbose_name


    def __str__(self):
        return self.sku

'''
class ShopifyOptionValues(models.Model):
    ShopifyOptions = models.ForeignKey(ShopifyOptions, related_name='option_values', null=True,
                                       on_delete=models.CASCADE, verbose_name="options")

    option_value = models.CharField(u'option_value', default='', max_length=100, blank=True)


    class Meta:
        verbose_name = "ShopifyOptionValues"
        verbose_name_plural = verbose_name


    def __str__(self):
        return self.option_value
'''

class ShopifyCustomer(models.Model):
    #shop = models.ForeignKey(Shop, related_name='shop_customer', null=True, on_delete=models.CASCADE,
    #                             verbose_name="店铺")
    shop_name = models.CharField(u'店铺名', default='', max_length=100, blank=True)
    customer_no = models.CharField(u'customer_no', default='', max_length=100, blank=True)
    accepts_marketing = models.BooleanField(u'accepts_marketing', default=False)


    default_address = models.CharField(u'客户缺省地址', default='', max_length=100, blank=True)

    created_at = models.DateTimeField(u'创建时间', auto_now=False, null=True, blank=True)
    updated_at = models.DateTimeField(u'updated_at', auto_now=False, null=True, blank=True)
    email = models.EmailField(u'email', max_length=254, null=True, blank=True)
    first_name = models.CharField(u'first_name', default='', max_length=100,null=True, blank=True)
    last_name = models.CharField(u'last_name', default='', max_length=100, null=True,blank=True)
    last_order_no = models.CharField(u'last_order_no', default='', max_length=100, null=True,blank=True)
    last_order_name = models.CharField(u'last_order_name', default='', max_length=100, null=True,blank=True)
    note = models.CharField(u'note', default='', max_length=100,null=True, blank=True)

    orders_count  =  models.IntegerField(u'orders_count', default=0, blank=True, null=True)

    phone = models.CharField(u'phone', default='', max_length=100, null=True,blank=True)
    state= models.CharField(u'state', default='', max_length=100,null=True, blank=True)

    tags = models.CharField(u'tags', default='', max_length=100, null=True,blank=True)
    tax_exempt = models.BooleanField(u'tax_exempt', default=True)
    total_spent = models.DecimalField(u'total_spent', max_digits = 10,decimal_places=2, default='', blank=True, null=True)

    verified_email = models.BooleanField(u'verified_email', default=False)

    class Meta:
        verbose_name = "ShopifyCustomer"
        verbose_name_plural = verbose_name


    def __str__(self):
        return self.customer_no

class ShopifyAddress(models.Model):
    customer = models.ForeignKey(ShopifyCustomer, related_name='customer_address', null=True,
                                 on_delete=models.CASCADE, verbose_name="customer")
    customer_no=models.CharField(u'customer_no', default='', max_length=100, blank=True)
    address_no = models.CharField(u'address_no', default='', max_length=100, blank=True)


    address1 = models.CharField(u'address1', default='', max_length=500, null=True,blank=True)
    address2 = models.CharField(u'address2', default='', max_length=500, null=True,blank=True)
    city = models.CharField(u'city', default='', max_length=100, null=True,blank=True)
    country = models.CharField(u'country', default='', max_length=100, null=True,blank=True)
    country_code = models.CharField(u'country_code', default='', max_length=100, null=True,blank=True)
    country_name = models.CharField(u'country_name', default='', max_length=100, null=True,blank=True)
    company = models.CharField(u'company', default='', max_length=100, null=True,blank=True)
    first_name = models.CharField(u'first_name', default='', max_length=100, null=True,blank=True)
    last_name = models.CharField(u'last_name', default='', max_length=100, null=True,blank=True)
    name = models.CharField(u'name', default='', max_length=100, null=True,blank=True)
    phone = models.CharField(u'phone', default='', max_length=100, null=True,blank=True)
    province = models.CharField(u'province', default='', max_length=100,  null=True,blank=True)
    province_code = models.CharField(u'province_code', default='', max_length=100, null=True,blank=True)
    zip = models.CharField(u'zip', default='', max_length=100, null=True,blank=True)
    default = models.BooleanField(u'default', default=False)

    class Meta:
        verbose_name = "ShopifyAddress"
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.address_no

'''
class ShopifyCustomerAddress(models.Model):
    customer = models.ForeignKey(ShopifyCustomer, related_name='customer_address', null=True, on_delete=models.CASCADE,
                                verbose_name="客户")
    address = models.ForeignKey(ShopifyAddress, related_name='address_customer', null=True, on_delete=models.CASCADE,
                                 verbose_name="地址")



    class Meta:
        verbose_name = "ShopifyCustomerAddress"
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.customer.customer_no
'''
'''
class OverseaSell(Package):
    class Meta:
        proxy = True

        verbose_name = "海外仓销售"
        verbose_name_plural = verbose_name


    def __str__(self):
        return self.logistic_no
'''

class ProductCategory(models.Model):
    """
    商品类别
    """
    code = models.CharField(u'code', default='', max_length=256, null=True, blank=True)
    cate_1 = models.CharField(u'cate_1', default='', max_length=256, null=True, blank=True)
    cate_2 = models.CharField(u'cate_2', default='', max_length=256, null=True, blank=True)
    cate_3 = models.CharField(u'cate_3', default='', max_length=256, null=True, blank=True)
    keywords = models.CharField(u'关键词', default='', max_length=256, null=True, blank=True)
    ali_list_link = models.TextField(u'1688搜索链接', default='', max_length=512, null=True, blank=True)
    class Meta:
        verbose_name = "商品类别"
        verbose_name_plural = verbose_name

    def __str__(self):
        if self.code:
            return self.code
        else:
            return "None"




class ProductCategoryMypage(models.Model):
    mypage = models.ForeignKey(MyPage, null=True, blank=True, verbose_name="主页", help_text="主页",
                                        related_name="page_category",on_delete=models.CASCADE)
    productcategory = models.ForeignKey(ProductCategory, null=True, blank=True, verbose_name="产品类别", help_text="产品类别",
                               related_name="page_category", on_delete=models.CASCADE)

    album_name = models.CharField(u'相册名', default='', max_length=256, null=True, blank=True)
    album_no = models.CharField(u'相册编码', default='', max_length=256, null=True, blank=True)
    #last_no = models.BigIntegerField(u'最后更新产品ID', default=0, null=True,blank=True)

    active = models.BooleanField(u'page类目状态', default=True)
    error =  models.CharField(u'相册配对错误', default='', max_length=256, null=True, blank=True)


    class Meta:
        verbose_name = "品类对应主页"
        verbose_name_plural = verbose_name

    def __str__(self):
        if self.album_name:
            return self.album_name
        else:
            return "None"

'''

class MyPorduct(models.Model):
    OBJ_TYPE = (
        ("PRODUCT", "单品"),
        ("OVERSEAS", "海外仓包裹"),

    )

    obj_type = models.CharField(choices=OBJ_TYPE,default='PRODUCT',max_length=30, null=True, blank=True, verbose_name="产品类型")

    shopifyproduct = models.ForeignKey('ShopifyProduct', null=True, blank=True, verbose_name="shopify产品", help_text="shopify产品",
                                related_name="product_shop", on_delete=models.CASCADE)
    shopifyvariant = models.ForeignKey('ShopifyVariant', null=True, blank=True, verbose_name="海外仓商品", help_text="海外仓商品",
                                related_name="variant_shop", on_delete=models.CASCADE)


    def name(self):  # 计算字段要显示在修改页面中只能定义在只读字段中(否则不显示):readonly_fields = ('sc',)
        if self.obj_type == "PRODUCT":
            return self.shopifyproduct.handle
        else:
            return  self.shopifyvariant.sku

    name.short_description = '产品名'  # 用于显示时的名字 , 没有这个,字段标题将显示'name'


    class Meta:
        verbose_name = "爆款"
        verbose_name_plural = verbose_name

    def __str__(self):

        if self.obj_type == "PRODUCT":
            return self.shopifyproduct.handle
        else:
            return  self.shopifyvariant.sku


class ProductResources(models.Model):
    product = models.ForeignKey(MyPorduct, null=True, blank=True, verbose_name="fb产品",
                                        related_name="resouse_product",on_delete=models.CASCADE)

    resource = models.FileField(u'资源', upload_to='resource/', default="", null=True, blank=True)

    RESOURCE_CATE = (
        ("IMAGE", "图片"),
        ("VIDEO", "视频"),
    )
    resource_cate = models.CharField(choices=RESOURCE_CATE, default='IMAGE', max_length=30, null=True, blank=True,
                                     verbose_name="资源性质")

    RESOURCE_TYPE = (
        ("SKU", "sku自带"),
        ("AUTO", "自带生成"),
        ("RAW", "素材"),
        ("PS", "成品"),
    )
    resource_type = models.CharField(choices=RESOURCE_TYPE, default='RAW', max_length=30, null=True, blank=True,
                                verbose_name="资源类型")



    created_time = models.DateTimeField(null=True, blank=True, verbose_name="上传时间")
    staff = models.CharField(u'上传人', default='', max_length=100, null=True,blank=True)


    class Meta:
        verbose_name = "资源"
        verbose_name_plural = verbose_name
    def __str__(self):
        if self.product.obj_type == "PRODUCT":
            return self.product.shopifyproduct.handle
        else:
            return  self.product.shopifyvariant.sku
'''

class ShopOriOrder(models.Model):

    order_id = models.CharField(u'订单id', default='', max_length=100, blank=True)
    order_no = models.CharField(u'订单号', default='', max_length=50, blank=True)
    created_at = models.DateTimeField(u'创建时间', auto_now=False, blank=True, null=True)
    order_json  =  models.TextField(u'订单json', default='', null=True, blank=True)


    class Meta:
        verbose_name = "原始订单"
        verbose_name_plural = verbose_name


    def __str__(self):
        return self.order_id
