import xadmin
from django.utils.safestring import mark_safe
from django.db.models import Count,Sum


from .models import *
'''
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

'''





@xadmin.sites.register(Yallavip_SKU)
class Yallavip_SKUAdmin(object):


    def sku_photo(self, obj):
        if obj.image is not None and len(obj.image)>0 :
           img = '<a><img src="%s" width="100px"></a>' % (obj.image)
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
    actions = ["batch_add_cart",]
    ordering = ['-o_quantity']



    def batch_add_cart(self, request, queryset):
        from django.utils import timezone as dt
        #如果还没有购物车，就新增一个购物车
        #如果已经有，就在原有的基础上增加或更新
        cart, created = Cart.objects.get_or_create(
            distributor = str(self.request.user),
            defaults={'create_time':dt.now},
        )

        for sku in queryset:
            obj, created = CartDetail.objects.update_or_create(cart=cart,
                                                               sku = sku,
                                                           defaults={'price': sku.vendor_supply_price,
                                                                     'quantity': sku.o_quantity,
                                                                     'amount': sku.vendor_supply_price * sku.o_quantity,

                                                                     }
                                                           )



    batch_add_cart.short_description = "加入购物车"

    def queryset(self):
        qs = super().queryset()
        return qs.filter( lightin_spu__vendor = "gw", o_quantity__isnull=False)


@xadmin.sites.register(Cart)
class CartAdmin(object):

    def quantity(self, obj):
        quantity = obj.cart_detail.aggregate(nums=Sum('quantity')).get("nums")
        return str(quantity)

    quantity.short_description = "SKU 数量"

    def amount(self, obj):
        return str(obj.cart_detail.aggregate(nums=Sum('amount')).get("nums"))

    amount.short_description = "金额(CNY)"


    list_display = ["distributor","quantity", "amount", "create_time","checked", "checked_time",  ]

    search_fields = []
    list_filter = []
    list_editable = []
    readonly_fields = ()
    actions = ['check_cart',]

    #提交购物车到订单
    def check_cart(self, request, queryset):
        queryset.update(checked=True)
    batch_add_cart.short_description = "提交订单"

    def queryset(self):
        qs = super().queryset()
        distributor = str(self.request.user)
        return qs.filter( distributor = distributor)

@xadmin.sites.register(CartDetail)
class CartDetailAdmin(object):

    def sku_photo(self, obj):
        if obj.image is not None and len(obj.image)>0 :
           img = '<a><img src="%s" width="384px"></a>' % (obj.image)
        else:
            img = "no photo"

        return mark_safe(img)

    sku_photo.short_description = "sku图片"

    def sellable(self, obj):

        return obj.sku.o_quantity

    sellable.short_description = "可用数量"

    list_display = ["cart", "sku", 'price','sellable', 'quantity', 'amount', 'sku_photo', ]


    search_fields = []
    list_filter = []
    list_editable = ['quantity',]
    readonly_fields = ()
    actions = []
    readonly_fields = ["cart", "sku", 'price', 'amount',]

    def queryset(self):
        qs = super().queryset()
        distributor = str(self.request.user)
        return qs.filter(cart__distributor=distributor)
