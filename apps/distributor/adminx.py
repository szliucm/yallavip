import xadmin
from django.utils.safestring import mark_safe

from .models import *

@xadmin.sites.register(Yallavip_SPU)
class Yallavip_SPUAdmin(object):

    def photo(self, obj):
        sku = obj.spu_sku.first()
        if sku.image is not None and len(sku.image)>0 :
           img = '<a><img src="%s" width="384px"></a>' % (sku.image)
        else:
            img = "no photo"

        return mark_safe(img)
    photo.short_description = "图片"

    def quantity(self, obj):
        return  obj.spu_sku.aggregate(nums=Sum('o_quantity')).get("nums")

    quantity.short_description = "可售数量"

    list_display = [ "SPU", "quantity",  "en_name", "cate_1","cate_2","cate_3","photo", ]
    # 'sku_name','img',

    search_fields = ["SPU","handle", ]
    list_filter = ["cate_1","cate_2","cate_3",]
    list_editable = []
    readonly_fields = ()
    actions = []
    ordering = ['-sellable']

    def queryset(self):
        qs = super().queryset()
        return qs.filter( vendor = "gw")







@xadmin.sites.register(Yallavip_SKU)
class Yallavip_SKUAdmin(object):


    def sku_photo(self, obj):
        if obj.image is not None and len(obj.image)>0 :
           img = '<a><img src="%s" width="384px"></a>' % (obj.image)
        else:
            img = "no photo"

        return mark_safe(img)

    sku_photo.short_description = "sku图片"

    def supply_price(self, obj):
        return obj.vendor_supply_price

    supply_price.short_description = "供货价"

    def en_name(self, obj):
        return obj.lightin_spu.en_name

    en_name.short_description = "商品名"

    list_display = ["SKU", "SPU", 'en_name', "o_quantity", "supply_price", "sku_photo",  "skuattr", ]

    # 'sku_name','img',
    search_fields = ["SPU", "SKU",  ]
    list_filter = ["skuattr", "SPU", "o_quantity", ]
    list_editable = []
    readonly_fields = ()
    actions = []
    ordering = ['-o_quantity']

    def queryset(self):
        qs = super().queryset()
        return qs.filter( lightin_spu__vendor = "gw")


@xadmin.sites.register(Cart)
class CartAdmin(object):
    list_display = ["pk", "create_time", 'update_time', ]

    search_fields = []
    list_filter = []
    list_editable = []
    readonly_fields = ()
    actions = []

    def queryset(self):
        qs = super().queryset()
        distributor = str(self.request.user)
        return qs.filter( distributor = distributor)

@xadmin.sites.register(CartDetail)
class CartDetailAdmin(object):

    list_display = ["cart", "sku", 'amount', ]


    search_fields = []
    list_filter = []
    list_editable = []
    readonly_fields = ()
    actions = []

    def queryset(self):
        qs = super().queryset()
        distributor = str(self.request.user)
        return qs.filter(cart__distributor=distributor)
