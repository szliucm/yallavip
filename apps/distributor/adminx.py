
import xadmin

from .models import Yallavip_SKU

@xadmin.sites.register(Yallavip_SKU)
class Yallavip_SKUAdmin(object):

    def photo(self, obj):
        if obj.lightin_spu.images is not None and len(obj.lightin_spu.images)>0 :
            photos = json.loads(obj.lightin_spu.images)
            img = ''

            for photo in photos:
                try:
                    img = img + '<a><img src="%s" width="384px"></a>' % (photo)
                except Exception as e:
                    img = "获取图片出错 "+ e

        else:
            img = "no photo"

        return mark_safe(img)

    photo.short_description = "spu图片"

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

    list_display = ["SKU", "SPU", 'cn_name', "o_sellable", "sku_photo", "handle", "sku_price", "photo", "skuattr", ]

    # 'sku_name','img',
    search_fields = ["SPU", "SKU", "lightin_spu__handle", ]
    list_filter = ["skuattr", "SPU", "lightin_spu__breadcrumb", ]
    list_editable = []
    readonly_fields = ()
    actions = []
