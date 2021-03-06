
@xadmin.sites.register(MyCategory)
class MyCategoryAdmin(object):
    def spu_count(self, obj):

        return  Lightin_SPU.objects.filter(sellable__gt=0, breadcrumb__contains=obj.tags).count()

    spu_count.short_description = "SPU数量"

    def spu_onesize(self, obj):

        return  Lightin_SPU.objects.filter(one_size=True, sellable__gt=0,breadcrumb__icontains=obj.tags).count()

    spu_onesize.short_description = "均码的SPU数量"


    def spu_count_5(self, obj):

        return  Lightin_SPU.objects.filter(sellable__gt=5, breadcrumb__icontains=obj.tags).count()

    spu_count_5.short_description = ">5的SPU数量"

    def spu_count_10(self, obj):

        return  Lightin_SPU.objects.filter(sellable__gt=10, breadcrumb__icontains=obj.tags).count()

    spu_count_10.short_description = ">10的SPU数量"

    def longaded_count(self, obj):

        return  Lightin_SPU.objects.filter(longaded=True, breadcrumb__icontains=obj.tags).count()

    longaded_count.short_description = "longaded_count"

    def size(self, obj):
        size_count = obj.cate_size.values("size","sku_quantity")
        return  str(size_count)

    size.short_description = "尺码汇总"


    list_display = ["super_cate", "super_name", "name", "level","tags","spu_count","spu_onesize","spu_count_5","spu_count_10", "longaded_count","size", "active","published" ,]


    search_fields = ["name", ]
    list_filter = ["super_name","level","active","published", ]
    list_editable = []
    readonly_fields = ()
    actions = []

@xadmin.sites.register(SizeAbsLabel)
class SizeAbsLabelAdmin(object):
    def show_label(self, obj):

        try:
            img = mark_safe('<img src="%s" width="100px" />' % (obj.size_label.url,))
        except Exception as e:
            img = ''
        return img

    show_label.short_description = 'size_label'
    show_label.allow_tags = True

    def show_label_split(self, obj):

        try:
            img = mark_safe('<img src="%s" width="100px" />' % (obj.size_label_split.url,))
        except Exception as e:
            img = ''
        return img

    show_label_split.short_description = 'size_label_new'
    show_label_split.allow_tags = True

    list_display = ["size_abs", "show_label", "show_label_split",]

    search_fields = ["size_abs", ]
    list_filter = []
    list_editable = []
    readonly_fields = ()
    actions = []

@xadmin.sites.register(SizeAbs)
class SizeAbsAdmin(object):
    list_display = ["size", "size_abs", "size_abs_label", ]

    search_fields = ["size", "size_abs", ]
    list_filter = []
    list_editable = ["size_abs",]
    readonly_fields = ()
    actions = ["create_abs_label",]
    ordering = ["-catesize_count"]

    def create_abs_label(self, request, queryset):

        create_abs_label()
        return


@xadmin.sites.register(MyCategorySize)
class MyCategorySizeAdmin(object):


    list_display = ["cate", "size", "sku_quantity",'size_abs',]


    search_fields = ["cate__name", "size",]
    list_filter = ["cate","size","cate__level", 'size_abs__size_abs',]
    list_editable = []
    readonly_fields = ()
    actions = []

@xadmin.sites.register(MyProduct)
class MyProductAdmin(object):
    list_display = [ ]
    # 'sku_name','img',

    search_fields = [ ]
    list_filter = [ ]
    list_editable = []
    readonly_fields = ()
    actions = []

    def save_models(self):
        obj = self.new_obj
        obj.staff = str(self.request.user)
        obj.created_time = datetime.now()

        obj.save()


class MyProductShopifyResource(resources.ModelResource):
    #product_no = fields.Field(attribute='product_no', column_name='product_no')
    #total_orders = fields.Field(attribute='total_orders', column_name='total_orders')
    #total_quantity = fields.Field(attribute='total_quantity', column_name='total_quantity')

    class Meta:
        model = MyProductShopify
        skip_unchanged = True
        report_skipped = True
        import_id_fields = ('product_no',)
        fields = ('product_no','handle','total_orders', 'total_quantity',"week_orders","week_quantity", )
        # exclude = ()

@xadmin.sites.register(MyProductShopify)
class MyProductShopifyAdmin(object):
    import_export_args = {"import_resource_class": MyProductShopifyResource,
                          "export_resource_class": MyProductShopifyResource}

    def show_resource(self, obj):

        resource = obj.resource_product.values_list('resource_target').annotate(Count('id'))
        #resource = str(resource)
        resource = re.split(r"\[|\]", str(resource))

        #return  re.split(r"\[|\]", resource)
        if len(resource)>1:

            return resource[1]
        else:
            return ''

    show_resource.short_description = "创意统计"

    def show_fb(self, obj):

        fb = obj.fb_product.values_list('obj_type','mypage__page').annotate(Count('id'))

        fb = re.split(r"\[|\]", str(fb))


        if len(fb) > 1:

            return fb[1]
        else:
            return ''

    show_fb.short_description = "接触点统计"

    def show_image(self, obj):

        try:
            #img = mark_safe('<img src="%s" width="100px" />' % (obj.logo.url,))

            img = mark_safe(
                '<a href="%s" target="view_window"><img src="%s" width="100px"></a>' % (
                    "https://www.yallavip.com/products/"+obj.handle,
                    ShopifyImage.objects.get(product_no=obj.product_no,position=1).src,
                    ))

        except Exception as e:
            img = ''
        return img

    show_image.short_description = "产品图"

    def show_link(self, obj):

        try:
            #img = mark_safe('<img src="%s" width="100px" />' % (obj.logo.url,))
            link = mark_safe(
                u'<a href="https://yallasale-com.myshopify.com/admin/products/%s" target="view_window">%s</a>' % (
                    obj.product_no,
                    str(obj.product_no)

                    ))
            '''
            return mark_safe(
                u'<a href="http://business.facebook.com%s" target="view_window">%s</a>' % (
                obj.conversation.link, u'会话'))
            '''


        except Exception as e:
            link = ''

        return link

    show_link.short_description = "管理产品"



    list_display = [ "handle","category_code", "show_image","obj_type", "week_orders","week_quantity","total_orders", 'total_quantity','show_resource','show_fb',]


    search_fields = ["handle",]
    list_filter = ["obj_type","category_code", ]
    list_editable = []
    readonly_fields = ()
    ordering = ['-week_orders']
    actions = ["reset_count",]

    def reset_count(self, request, queryset):
        MyProductShopify.objects.all().update(total_orders=0,total_quantity=0,week_orders=0,week_quantity=0)
        return

    reset_count.short_description = "重置统计信息"


@xadmin.sites.register(MyProductAli)
class MyProductAliAdmin(object):
    def show_image(self, obj):

        try:
            #img = mark_safe('<img src="%s" width="100px" />' % (obj.logo.url,))

            img = mark_safe(
                '<a href="%s" target="view_window"><img src="%s" width="100px"></a>' % (
                    "https://www.yallavip.com/products/"+obj.handle,
                    ShopifyImage.objects.get(product_no=obj.product_no,position=1).src,
                    ))

        except Exception as e:
            img = ''
        return img

    show_image.short_description = "产品图"

    list_display = [ "show_image","myproductcate",'handle', 'listing',"posted_mainshop","created_time","staff","active",]

    # 'sku_name','img',

    search_fields = ["vendor_no", ]
    list_filter = ["myproductcate","created_time","staff",  'listing',"posted_mainshop",]
    list_editable = ['listing',"active","posted_mainshop",]
    readonly_fields = ("vendor_no","created_time","staff",)
    actions = ["sync"]

    def sync(self, request, queryset):
        dest_shop = "yallasale-com"



        for row in queryset:
            product = ShopifyProduct.objects.filter(shop_name=dest_shop, vendor=row.vendor_no).first()

            if product:
                MyProductAli.objects.filter(pk=row.pk).update(posted_mainshop=True, handle=product.handle,
                                                                 product_no=product.product_no, )

    sync.short_description = "批量同步shopify信息"

    def save_models(self):
        obj = self.new_obj
        obj.staff = str(self.request.user)
        obj.created_time = datetime.now()
        obj.vendor_no = obj.url.partition(".html")[0].rpartition("/")[2]

        obj.save()

'''
@xadmin.sites.register(MyProductAliShop)
class MyProductAliShopAdmin(object):
    list_display = ['vendor_nname', 'updated', 'url',]
    # 'sku_name','img',

    search_fields = ["vendor_nname","url","updated", ]
    list_filter = ["updated", ]
    list_editable = ["updated",]
    #readonly_fields = ("myproduct","vendor_no",)
    actions = []
'''

@xadmin.sites.register(MyProductResources)
class MyProductResourcesAdmin(object):
    def show_fb(self, obj):

        #fb = obj.fb_resource.values_list('obj_type','mypage__page','published',).annotate(Count('id'))
        fb = obj.fb_resource.values_list( 'mypage__page', 'published', )

        fb = re.split(r"\[|\]", str(fb))


        if len(fb) > 1:

            return fb[1]
        else:
            return ''

    show_fb.short_description = "接触点统计"

    def show_resource(self, obj):
        DEV = False
        if DEV:
            domain = "http://dev.yallavip.com:8000"
        else:
            domain = "http://admin.yallavip.com"
        resource = str(obj.resource)
        if obj.resource_cate == "IMAGE":
            destination_url = domain + os.path.join(settings.MEDIA_URL, resource)
        else:
            dest_image = resource.rpartition(".")[0] + ".jpg"
            destination_url = domain + os.path.join(settings.MEDIA_URL, dest_image)

        try:
            img = mark_safe('<img src="%s" width="100px" />' % (destination_url))
        except Exception as e:
            img = ''
        return img



    show_resource.short_description = '创意图'

    list_display = [ 'name','handle','show_resource', "myproductali","title","message", "resource_target","resource_cate","resource_type","show_fb","created_time","staff", ]
    # 'sku_name','img',

    search_fields = ["resource" ,'name',"title","message",]
    list_filter = ["resource_target","resource_cate","resource_type" ,"created_time","staff", ]
    list_editable = ['handle',]
    readonly_fields = ("created_time","staff", )
    actions = [ChoosePage,"sync"]

    def sync(self, request, queryset):
        dest_shop = "yallasale-com"



        for row in queryset:
            product = ShopifyProduct.objects.filter(shop_name=dest_shop, vendor=row.myproductali.vendor_no).first()

            #if product:
            MyProductResources.objects.filter(pk=row.pk).update(handle=row.myproductali.handle)

    sync.short_description = "批量同步shopify信息"

    def save_models(self):
        obj = self.new_obj
        obj.staff = str(self.request.user)
        obj.created_time = datetime.now()
        obj.save()




@xadmin.sites.register(MyProductFb)
class MyProductFbAdmin(object):
    def show_handle(self, obj):

        return obj.myproduct.handle

    show_handle.short_description = '货号'

    list_display = [ "mypage", "myresource", 'myproduct',"myphoto", 'myfeed',"myad","obj_type", "published", ]
    # 'sku_name','img',

    search_fields = ["myresource__handle","pk" ]
    list_filter = ["myproduct","obj_type","mypage","published",]
    list_editable = []
    readonly_fields = ("myphoto", 'myfeed',"myad",)
    actions = []


'''
class MyProductCategoryResource(resources.ModelResource):


    class Meta:
        model = MyProductCategory
        skip_unchanged = True
        report_skipped = True
        import_id_fields = ('code',)
        fields = ('code','cate_1', 'cate_2', 'cate_3', 'album_name',)
        # exclude = ()

@xadmin.sites.register(MyProductCategory)
class MyProductCategoryAdmin(object):

    import_export_args = {"import_resource_class": MyProductCategoryResource, "export_resource_class": MyProductCategoryResource}

    list_display = [ 'code','cate_1', 'cate_2', 'cate_3', 'album_name',]


    search_fields = ["album_name",]
    list_filter = ['cate_1', 'cate_2', 'cate_3',]
    list_editable = []
    actions = []
'''


@xadmin.sites.register(MyFbProduct)
class MyFbProductAdmin(object):
    def show_image(self, obj):

        try:

            aliproduct = obj.myaliproduct

            if aliproduct:

                images = json.loads(aliproduct.images)

                if images and len(images) > 0:
                    image = images[0]
                else:
                    image = 'http://admin.yallavip.com/media/material/sale-12_sH6nsyI.png'
            else:
                image = 'http://admin.yallavip.com/media/material/sale-11_iGr0k4Q.png'



        except Exception as e:
            image = 'http://admin.yallavip.com/media/material/sale-7_WqFydd8.png'

        print("########")
        print(image)
        print(obj.myaliproduct.handle)


        img = mark_safe(
            '<a href="%s" target="view_window"><img src="%s" width="100px"></a>' % (
                "https://www.yallavip.com/products/" + obj.myaliproduct.handle,
                image
            ))

        return img

    show_image.short_description = "产品图片"

    list_display = [ "myaliproduct","show_image", "mypage", "cate_code","obj_type", "fb_id", "published", "publish_error", "published_time", ]
    # 'sku_name','img',

    search_fields = ["myaliproduct__handle","myaliproduct__offer_id"]
    list_filter = ["mypage","cate_code","published", "published_time","publish_error",]
    list_editable = []
    readonly_fields = ()
    actions = ["delete_fb_photo",]

    def delete_fb_photo(self, request, queryset):
        from facebook_business.api import FacebookAdsApi
        from facebook_business.adobjects.photo import Photo

        n=1
        for fb in queryset:

            FacebookAdsApi.init(access_token=get_token(fb.mypage.page_no))
            fields = [
            ]
            params = {

            }
            try:
                response = Photo(fb.fb_id).api_delete(
                    fields=fields,
                    params=params,
                )
                print("%s response is %s" % (n, response))
                n += 1
            except:
                continue

        queryset.update(fb_id = "",
                    published = False,
                    published_time = None)

class AliProductResource(resources.ModelResource):
    priority = fields.Field(attribute='priority', column_name='优先级')
    created_time = fields.Field(attribute='created_time', column_name='爬取时间(__time)')
    created = fields.Field(attribute='created',column_name='created')
    offer_id = fields.Field(attribute='offer_id', column_name='商品ID(pid)')
    title_zh = fields.Field(attribute='title_zh', column_name='商品名称(name)')
    price_range = fields.Field(attribute='price_range', column_name='价格(price)')
    trade_info = fields.Field(attribute='trade_info', column_name='批发信息(trade_info)')
    sales_count = fields.Field(attribute='sales_count', column_name='总销量(sales_count)')
    sku_info = fields.Field(attribute='sku_info', column_name='商品规格(sku)')
    sku_detail = fields.Field(attribute='sku_detail', column_name='规格详情(sku_detail)')
    params = fields.Field(attribute='params', column_name='商品参数(params)')
    images = fields.Field(attribute='images', column_name='商品图片(images)')
    shipping_from = fields.Field(attribute='shipping_from', column_name='发货地(shipping_from)')
    score = fields.Field(attribute='score', column_name='商品评分(score)')
    comments_count = fields.Field(attribute='comments_count', column_name='评价数(comments_count)')
    sid = fields.Field(attribute='sid', column_name='店铺ID(sid)')
    company_name = fields.Field(attribute='company_name', column_name='公司名称(company_name)')
    class Meta:
        model = AliProduct
        skip_unchanged = True
        report_skipped = True
        import_id_fields = ('offer_id',)
        fields = ('priority','created_time','created','offer_id','title_zh', 'price_range',"trade_info","sales_count",
                  'sku_info', 'sku_detail', 'params',"images", "shipping_from", "score",
                  'comments_count', "sid", "company_name",)
        # exclude = ()


@xadmin.sites.register(AliProduct)
class AliProductAdmin(object):
    import_export_args = {"import_resource_class": AliProductResource,
                          "export_resource_class": AliProductResource}


    def price_try(self, obj):
        return int(obj.maxprice * obj.price_rate)

    price_try.short_description = "价格(SAR)"

    def show_image(self, obj):

        try:
            #img = mark_safe('<img src="%s" width="100px" />' % (obj.logo.url,))

            images = json.loads(obj.images)
            if images and len(images)>0:
                image = images[0]

            img = mark_safe(
                '<a href="%s" target="view_window"><img src="%s" width="100px"></a>' % (
                    "https://detail.1688.com/offer/%s.html"%(obj.offer_id),
                    image
                    ))

        except Exception as e:
            img = ''
        return img

    show_image.short_description = "产品图片"

    list_display = [ "offer_id", "show_image","handle", "sku_info","cate_code","created","published", ]
    # 'sku_name','img',

    search_fields = ["offer_id","handle","sku_info"]
    list_filter = ["created","published","stopped","cate_code","priority",]
    list_editable = ["price_rate",]
    readonly_fields = ()
    actions = ["reset_aliproduct","batch_stop",SelectCategory]

    def reset_aliproduct(self, request, queryset):

        for aliproduct in queryset:


            shop_obj = Shop.objects.get(shop_name="yallasale-com")
            # 初始化SDK
            shop_url = "https://%s:%s@%s.myshopify.com" % (shop_obj.apikey, shop_obj.password, shop_obj.shop_name)
            products = ShopifyProduct.objects.filter(vendor=aliproduct.offer_id)
            for product in products:
                # delete a product

                product_no = product.product_no
                if product_no is None:
                    continue
                else:
                    url = shop_url + "/admin/products/%s.json" % (product_no)

                    headers = {
                        "Content-Type": "application/json",
                        "charset": "utf-8",

                    }

                    r = requests.delete(url, headers=headers)
                    print("response is ",r)
                # 删除本地数据库记录

                ShopifyVariant.objects.filter(product_no=product_no).delete()
                ShopifyImage.objects.filter(product_no=product_no).delete()
                ShopifyOptions.objects.filter(product_no=product_no).delete()

            products.delete()

        queryset.update(published=False,publish_error="",published_time=None)

    reset_aliproduct.short_description = "重置ali产品"

    def batch_stop(self, request, queryset):
        queryset.update(stopped=True)
        return

    batch_stop.short_description = "批量停用"



    def get_list_queryset(self):
        """批量查询订单号"""
        queryset = super().get_list_queryset()

        query = self.request.GET.get(SEARCH_VAR, '')

        if (len(query) > 0):
            queryset |= self.model.objects.filter(offer_id__in=query.split(","))

        return queryset

class MyFbAlbumCateResource(resources.ModelResource):
    mypage = fields.Field(
        column_name='mypage',
        attribute='mypage',
        widget=ForeignKeyWidget(MyPage, 'page'))

    '''
    myalbum = fields.Field(
        column_name='myalbum',
        attribute='myalbum',
        widget=ForeignKeyWidget(MyAlbum, 'name'))
    '''

    mycategory = fields.Field(
        column_name='mycategory',
        attribute='mycategory',
        widget=ForeignKeyWidget(MyCategory, 'code'))

    '''
    def get_diff_headers(self):
        return ['myalbum__mypage', 'myalbum', 'mycategory']


    def clean_dataset_data(self, data):
        data = super().clean_dataset_data(data)
        clean_data = []
        for index, row in enumerate(data):
            _index = index + 2
            _row = self.get_clean_row(row)

            album = self.clean_dataset_album((_row[0], _row[1]), _index, row)
            clean_data.append([album] + _row[2:])
        return clean_data

    def clean_dataset_album(self, myalbum, index, row):
        try:
            return MyAlbum.objects.get(mypage__page=myalbum[0],name=myalbum[1])
        except MyAlbum.DoesNotExist:
            raise self.get_error(u'相册', index, row)
    '''

    class Meta:
        model = MyFbAlbumCate
        skip_unchanged = True
        report_skipped = True
        import_id_fields = ['mypage','myalbum','mycategory']
        fields = ('mypage','myalbum','mycategory',)
        # exclude = ()

@xadmin.sites.register(MyFbAlbumCate)
class MyFbAlbumCateAdmin(object):
    import_export_args = {"import_resource_class": MyFbAlbumCateResource,
                          "export_resource_class": MyFbAlbumCateResource}




    def mypage(self, obj):
        return obj.myalbum.mypage.page

    mypage.short_description = "主页"

    list_display = ["mypage", "myalbum", "mycategory",  "cate_active", ]


    search_fields = ["myalbum", ]
    list_filter = ["myalbum__mypage","mycategory","cate_active", ]
    list_editable = []
    readonly_fields = ()
    actions = []



class AliProduct_vendorResource(resources.ModelResource):
    ali_url = fields.Field(attribute='ali_url', column_name='链接')
    vendor = fields.Field(attribute='vendor',column_name='供应商')
    cate_code = fields.Field(attribute='cate_code', column_name='品类')

    class Meta:
        model = AliProduct_vendor
        skip_unchanged = True
        report_skipped = True
        import_id_fields = ('ali_url',)
        fields = ('ali_url','vendor','cate_code',)
        # exclude = ()


@xadmin.sites.register(AliProduct_vendor)
class AliProduct_vendorAdmin(object):


    import_export_args = {"import_resource_class": AliProduct_vendorResource,
                          "export_resource_class": AliProduct_vendorResource}

    list_display = [ "ali_url", "vendor","cate_code", "got", ]
    # 'sku_name','img',

    search_fields = ["ali_url",]
    list_filter = ["vendor","got",]
    list_editable = []
    readonly_fields = ()
    actions = []


@xadmin.sites.register(Combo)
class ComboAdmin(object):
    class ComboItemInline(object):
        model = ComboItem
        fk_name = "combo"
        extra = 1
        # style = 'row'
        '''
        form_layout = (
            Main(
                Fieldset('组合明细',
                         # Row( 'lightin_sku','product_quantity','price',),
                         'combo', 'SKU',

                         ),
            )
        )
        '''

    inlines = [ComboItemInline, ]


    def photo(self, obj):

        try:
            img =  '<a><img src="%s" width="500px"></a>' % (obj.image_marked)
        except Exception as e:
            img = "获取图片出错 "+ e

        return mark_safe(img)



    photo.short_description = "图片"


    list_display = ['SKU',"checked","sku_price","o_sellable", 'photo', 'listed', 'items' ]
    list_editable = ["checked",]
    exclude = ["lightin_spu", "SPU",]
    search_fields = ['SKU',]

    ordering = []
    list_filter = ('listed',"imaged","locked","checked")

    actions = [ ]

    relfield_style = 'fk_ajax'

    form_layout = (
        Main(
            Fieldset('组合产品信息',
                     Row('SKU', ),
                     ),

        ),

    )
    def queryset(self):
        qs = super().queryset()
        return qs.filter( comboed = True)


@xadmin.sites.register(ComboItem)
class ComboItemAdmin(object):
    def sku_photo(self, obj):
        sku = obj.lightin_sku
        try:
            img =  '<a><img src="%s" width="100px"></a>' % (sku.image)
        except Exception as e:
            img = "获取图片出错 "

        return mark_safe(img)



    sku_photo.short_description = "sku图片"

    def photo(self, obj):
        spu = obj.lightin_sku.lightin_spu
        if spu.images is not None and len(spu.images) > 0:
            photos = json.loads(spu.images)
            img = ''

            for photo in photos:
                try:
                    img = img + '<a><img src="%s" width="100px"></a>' % (photo)
                except Exception as e:
                    print("获取图片出错", e)

            return mark_safe(img)

        else:
            photos = "no photo"

    photo.short_description = "spu图片"

    def price(self, obj):
        return  int(obj.lightin_sku.vendor_supply_price * 5.63)

    price.short_description = "price"

    def skuattr(self, obj):
        return  obj.lightin_sku.skuattr

    skuattr.short_description = "skuattr"

    def o_sellable(self, obj):
        return  obj.lightin_sku.o_sellable

    o_sellable.short_description = "可售数量"



    list_display = ['lightin_sku','o_sellable',"price", "skuattr",'sku_photo',  'combo','photo', ]

    search_fields = ['lightin_sku__SKU','combo__SKU', ]

    ordering = []
    list_filter = ()

    actions = [ ]


