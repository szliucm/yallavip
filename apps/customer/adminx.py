import  json
import xadmin
from django.utils.safestring import mark_safe

from .models import  *
from prs.models import  Lightin_SPU,Lightin_SKU

@xadmin.sites.register(Customer)
class CustomerAdmin(object):
    class ReceiverInline(object):
        model = Receiver
        extra = 1
        style = 'tab'
        '''
        form_layout = (
            Main(
                Fieldset('订单明细',
                         # Row( 'lightin_sku','product_quantity','price',),
                         'handle', 'lightin_sku', 'price', 'quantity', 'amount',

                         ),

            )
        )
        '''

    class ConversationInline(object):
        model = Conversation
        extra = 1
        style = 'tab'
        '''
        form_layout = (
            Main(
                Fieldset('订单明细',
                         # Row( 'lightin_sku','product_quantity','price',),
                         'handle', 'lightin_sku', 'price', 'quantity', 'amount',

                         ),

            )
        )
        '''



    def photo(self, obj):
        handles = obj.handles.split()
        lightin_spus = Lightin_SPU.objects.filter(handle__in=handles).distinct()
        img = ''

        for lightin_spu in lightin_spus:
            img += '<br><a>handle: %s</a><br><br>' % (lightin_spu.handle)

            lightin_skus = lightin_spu.spu_sku.filter(o_sellable__gt=0).distinct()
            skus = lightin_skus.values_list("SKU",   "o_sellable","sku_price", "skuattr",)
            for sku in skus:
                #img += '<br><a>%s<br>规格: %s<br>库存: %s</a><br>' % ( sku[0], sku[1], str(sku[2]))
                img += '<a>%s   %s  %s    %s</a><br>' % (sku[0],  str(sku[1]),sku[2], sku[3])


            if lightin_spu.images_dict :
                images= json.loads(lightin_spu.images_dict).values()

                for image in images:
                    '''
                    a = "/"
                    image_split = image.split(a)

                    image_split[4] = '800x800'
                    photo = a.join(image_split)
                    print("spu 图片", lightin_spu, photo)
                    img = img + '<a><img src="%s" width="100px"></a>' % (photo)
                    '''
                    img = img + '<a><img src="%s" width="100px"></a>' % (image)






            else:
                img = img + "no photo"





        return mark_safe(img)

    photo.short_description = "产品图片"

    def abs_order(self, obj):
        #遍历草稿表，把所有数量大于0的加起来

        img = ""
        subtotal = 0
        count = 0
        error = ""
        if not obj.discount:
            discount = 0
        else:
            discount = obj.discount

        details =  obj.cs_order_detail.filter(quantity__gt=0)

        for detail in details:
            try:
                sku = detail.lightin_sku
                subtotal += sku.sku_price *  detail.quantity
                count += detail.quantity

                image = None

                if sku.image:
                    image = sku.image
                    print("sku 图片")
                else:

                    spu = sku.lightin_spu
                    if spu.images_dict:
                        images = json.loads(spu.images_dict).values()

                        if images and len(images) > 0:
                            '''
                            a = "/"
                            image_split = list(image)[0].split(a)

                            image_split[4] = '800x800'
                            image = a.join(image_split)
                            print("spu 图片", spu, image)
                            '''
                            image = list(images)[0]
                if image:
                    img += '<a><img src="%s" width="100px"></a>' % (image)

                img += '<br><a>%s %s   (%s sets)</a><br>' % (sku, sku.skuattr, detail.quantity)

            except Exception as e:
                print(e)
                error = "计算出错" + detail.lightin_sku.SKU
                break


        if error == "":
            tax = subtotal * 0.05
            COD = 20
            content = "<br><a>Subtotal  %sitems    %s SR<a><br>"%(count,subtotal)
            content += "<a>COD Fee              %s SR<a><br>" % (COD)
            content += "<a>VAT Tax              %s SR<a><br>"%(tax)
            content += "<a>Discount             %s SR<a><br>" % (discount)
            content += "<a>Total                %s SR<a><br>" % (int(subtotal+COD+tax-float(discount)))

            img += content
            return mark_safe(img)
        else:
            return  error

    abs_order.short_description = "订单摘要"

    #客户收件信息摘要
    def abs_customer(self, obj):
        content =""

        content += "<span>phone_1  %s<span><br>" % (obj.customer.phone_1)
        content += "<span>address  %s<span><br>" % (obj.customer.address1)

        #return  mark_safe(content)

        return format_html(content)



    abs_customer.short_description = "收件信息摘要"


    list_display = ['name','handles', 'photo', "discount", "abs_order","abs_customer", ]
    list_editable = ["handles","discount", ]
    search_fields = ['name']
    ordering = []
    list_filter = ()

    actions = ['batch_prepare_draft',]
    relfield_style = 'fk_ajax'
    inlines = [ReceiverInline, ConversationInline ]

    def batch_prepare_draft(self, request, queryset):
        # 定义actions函数
        #根据货号找到所有有库存的sku，把sku插到草稿表里，供进一步编辑
        #如果对应的sku已经有了，就什么也不做
        for row in queryset:
            handles = row.handles.split()
            lightin_skus = Lightin_SKU.objects.filter(lightin_spu__handle__in = handles, o_sellable__gt=0)

            for lightin_sku in lightin_skus:
                obj, created = CsOrderDetail.objects.get_or_create(
                    csorder=row,
                    lightin_sku = lightin_sku,
                    defaults={'quantity': 0})

        return

    batch_prepare_draft.short_description = "更新草稿"