import xadmin

from .models import Yallavip_SKU

@xadmin.sites.register(Yallavip_SKU)
class Yallavip_SKUAdmin(object):


    def sku_photo(self, obj):
        if obj.image is not None and len(obj.image)>0 :
           img = '<a><img src="%s" width="384px"></a>' % (obj.image)
        else:
            img = "no photo"

        return mark_safe(img)

    sku_photo.short_description = "sku图片"

    def shopify_price(self, obj):
        return obj.lightin_spu.shopify_price

    shopify_price.short_description = "price"

    def cn_name(self, obj):
        return obj.lightin_spu.cn_name

    cn_name.short_description = "cn_name"

    list_display = ["SKU", "SPU", 'cn_name', "o_sellable", "sku_photo",  "skuattr", ]

    # 'sku_name','img',
    search_fields = ["SPU", "SKU",  ]
    list_filter = ["skuattr", "SPU",  ]
    list_editable = []
    readonly_fields = ()
    actions = []
