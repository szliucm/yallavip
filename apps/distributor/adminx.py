import xadmin
from django.utils.safestring import mark_safe

from .models import Yallavip_SPU, Yallavip_SKU

@xadmin.sites.register(Yallavip_SPU)
class Yallavip_SPUAdmin(object):

    def photo(self, obj):
        if obj.images is not None and len(obj.images)>0 :
            photos = json.loads(obj.images)
            img = ''

            for photo in photos:
                try:
                    img = img + '<a><img src="%s" width="100px"></a>' % (photo)
                except Exception as e:
                    print("获取图片出错", e)

            return mark_safe(img)

        else:
            photos = "no photo"

    photo.short_description = "图片"

    list_display = [ "SPU","handle", "sellable", "en_name","cn_name", "cate_1","cate_2","cate_3", ]
    # 'sku_name','img',

    search_fields = ["SPU","handle", ]
    list_filter = ["cate_1","cate_2","cate_3","got","got_time","got_error","vendor"]
    list_editable = []
    readonly_fields = ()
    actions = []

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

    def queryset(self):
        qs = super().queryset()
        return qs.filter( lightin_spu__vendor = "gw")
