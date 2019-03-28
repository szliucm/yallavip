import  json
import xadmin
from django.utils.safestring import mark_safe
from django.utils.html import format_html
from django.db.models import Q, Count
from django.utils import timezone as dt

from .models import  *
from prs.models import  Lightin_SPU,Lightin_SKU
from orders.models import  Order, OrderDetail

def info(color_code, message):
    return   '<span style="color:%s;">%s</span>'%(color_code,message)

@xadmin.sites.register(Customer)
class CustomerAdmin(object):
    #记录操作日志
    def deal_log(self, queryset, deal,content):
        for row in queryset:
            DealLog.objects.create(
                customer=row,
                deal_action=deal,
                content = content,
                deal_staff=str(self.request.user),
                deal_time=dt.now(),
            )

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
        #货号或者sku
        handles = obj.handles.split()

        #规格
        q_attr = Q()
        q_attr.connector = 'OR'
        if obj.attrs:
            for attr in obj.attrs.split(" "):
                q_attr.children.append(('skuattr__contains', "="+attr))



        con = Q()
        con.add(q_attr, 'AND')



        lightin_spus = Lightin_SPU.objects.filter( handle__in=handles).distinct()
        print(con, lightin_spus)

        img = ''

        for lightin_spu in lightin_spus:
            img += '<br><a>handle: %s</a><br><br>' % (lightin_spu.handle)

            #lightin_skus = lightin_spu.spu_sku.filter( (Q(skuattr__contains ="Size"),q_attr)|~Q(skuattr__contains ="Size"),o_sellable__gt=0).distinct()
            lightin_skus = lightin_spu.spu_sku.filter(o_sellable__gt=0).distinct()
            if not lightin_skus:
                img += '<br><a>out of stock</a><br><br>'
                continue

            skus = lightin_skus.values_list("SKU",   "o_sellable","lightin_spu__shopify_price", "skuattr",)
            for sku in skus:
                #img += '<br><a>%s<br>规格: %s<br>库存: %s</a><br>' % ( sku[0], sku[1], str(sku[2]))
                img += '<a>%s   [ %s sets]  [ %s SR]<br>%s</a><br>' % (sku[0],  str(sku[1]),sku[2], sku[3])


            if lightin_spu.images_dict :
                images= json.loads(lightin_spu.images_dict).values()
                n=0
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
                    n+=1
                    if n%4 == 0:
                        img += "<br>"






            else:
                img = img + "no photo"
        lightin_skus = Lightin_SKU.objects.filter(SKU__in=handles).distinct()

        for lightin_sku in lightin_skus:
            #            img += '<br><a>sku: %s</a><br><br>' % (lightin_sku.SKU)
            #print (lightin_sku, lightin_sku.SKU,  lightin_sku.o_sellable, lightin_sku.lightin_spu.shopify_price, lightin_sku.skuattr)
            #print ("what's wrong",lightin_sku, lightin_sku.SKU,  lightin_sku.skuattr)
            #continue
            image = None

            img += '<br><a>%s   [ %s sets]  [ %s SR]</a><br>' % (lightin_sku.SKU,  lightin_sku.o_sellable, lightin_sku.sku_price)


            if lightin_sku.image_marked:
                image = lightin_sku.image_marked
            elif lightin_sku.image:
                image = lightin_sku.image
            else:
                image = None



            if image:
                img += '<a><img src="%s" width="100px"></a>' % (image)


        return mark_safe(img)

    photo.short_description = "产品图片"

    def abs_order(self, obj):
        #遍历订单表
        obj.customer_order.filter()


    abs_order.short_description = "订单摘要"

    def abs_draft(self, obj):
        #遍历草稿表，把所有数量大于0的加起来

        img = ""
        subtotal = 0
        count = 0
        error = ""
        if not obj.discount:
            discount = 0
        else:
            discount = obj.discount

        drafts =  obj.customer_draft.filter(quantity__gt=0)

        for draft in drafts:
            try:
                sku = draft.lightin_sku
                subtotal += float(draft.price) *  draft.quantity
                count += draft.quantity
                #print (sku, subtotal, count)
                image = None

                if sku.image_marked:
                    image = sku.image_marked
                elif sku.image:
                    image = sku.image
                 #   print("sku 图片")
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

                img += '<br><a>%s <br>%s<br>%s SR<br>%s sets<br>subtotal %s SR</a><br>' % (sku, sku.skuattr,draft.price, draft.quantity,int(float(draft.price) *  draft.quantity))

               # print (img)

            except Exception as e:
                print(e)
                error = "计算出错" + draft.lightin_sku.SKU
                break


        if error == "":
            tax = subtotal * 0.05
            COD = 20
            content = "<br><a>Subtotal  %sitems    %s SR<a><br>"%(count,int(subtotal))
            content += "<a>COD Fee              %s SR<a><br>" % (COD)
            content += "<a>VAT Tax              %s SR<a><br>"%(tax)
            content += "<a>Discount             %s SR<a><br>" % (discount)
            content += "<a>Total                %s SR<a><br>" % (int(subtotal+COD+tax-float(discount)))

            img += content
            return mark_safe(img)
        else:
            return  error

    abs_draft.short_description = "草稿摘要"


    # 客户信息摘要
    def abs_customer(self, obj):
        orders = Order.objects.filter(customer=obj)
        abs = dict (orders.values_list('status').annotate(Count('id')))
        content = ""

        content += "<span>开放  %s<span><br>" % (abs.get("open",0))
        content += "<span>在途  %s<span><br>" % (abs.get("transit", 0))
        content += "<span>签收  %s<span><br>" % (abs.get("delivered", 0))
        content += "<span>拒签  %s<span><br>" % (abs.get("refused", 0))



        return format_html(content)

    abs_customer.short_description = "客户信息"

    #收件信息摘要
    def abs_receiver(self, obj):
        content =""
        #如果有活跃订单号，就显示订单号
        order = obj.customer_order.filter(status="open").order_by("-order_time")
        if order:
            content += "<span>order_no  %s<span><br><br>" % (order[0].order_no)

        content += "<span>name  %s<span><br>" % (obj.receiver.name)
        content += "<span>country_code  %s<span><br>" % (obj.receiver.country_code)
        content += "<span>city  %s<span><br>" % (obj.receiver.city)
        content += "<span>address  %s<span><br>" % (obj.receiver.address1)
        content += "<span>address2  %s<span><br>" % (obj.receiver.address2)
        content += "<span>address3  %s<span><br>" % (obj.receiver.address3)
        content += "<span>phone_1  %s<span><br>" % (obj.receiver.phone_1)
        content += "<span>phone_2  %s<span><br>" % (obj.receiver.phone_2)
        content += "<span>comments  %s<span><br>" % (obj.receiver.comments)

        return format_html(content)



    abs_receiver.short_description = "收件人信息"
    def color_message(self, obj):
        return format_html(obj.message)

    color_message.short_description = "message"

    list_display = ['name',"active","color_message", 'handles',"attrs", 'photo', "discount", "abs_draft","abs_customer","abs_receiver", "sales"]
    list_editable = ["handles","attrs", "discount","active", ]
    search_fields = ['name']
    ordering = ["-update_time"]
    list_filter = ('name',"sales","active")
    '''
    list_bookmarks = [{
        "title": "只看自己的客户",
        "query": {"sales": self.request.user},
        "order": ("-name",),
        #"cols": ('user_name', 'user_email', 'user_mobile'),
    }]
    '''


    actions = ['batch_prepare_draft','batch_submit_draft',]
    relfield_style = 'fk_ajax'
    inlines = [ ConversationInline ]

    #,, ReceiverInline

    def batch_prepare_draft(self, request, queryset):
        # 定义actions函数
        #根据货号找到所有有库存的sku，把sku插到草稿表里，供进一步编辑
        #如果对应的sku已经有了，就什么也不做
        for row in queryset:
            handles = row.handles.split()

            # 规格
            q_attr = Q()
            q_attr.connector = 'OR'

            if row.attrs:
                for attr in row.attrs.split(" "):
                    q_attr.children.append(('skuattr__contains', "=" + attr))

            q_spu = Q(lightin_spu__handle__in=handles)


            con = Q()
            con.add(q_attr, 'AND')
            con.add(q_spu, 'AND')

            #lightin_skus = Lightin_SKU.objects.filter( Q(SKU__in=handles) | ( Q(lightin_spu__handle__in=handles) &((Q(skuattr__contains="Size"), q_attr) | ~Q(skuattr__contains="Size"))) , o_sellable__gt=0)
            lightin_skus = Lightin_SKU.objects.filter( Q(SKU__in=handles) | Q(lightin_spu__handle__in=handles) , o_sellable__gt=0)

            for lightin_sku in lightin_skus:
                if lightin_sku.comboed ==True or lightin_sku.SKU.find("579815")>=0 :
                    price = lightin_sku.sku_price
                else:
                    price = lightin_sku.lightin_spu.shopify_price


                obj, created = Draft.objects.update_or_create(
                    customer=row,
                    lightin_sku = lightin_sku,

                    defaults={
                        'price': price
                    }
                )

            #最后的操作员作为销售
            row.message = info("blue", "更新草稿成功")
            row.sales = str(self.request.user)
            row.save()
            #记录操作日志
            self.deal_log( queryset, "更新草稿","锁定sku %s个"%(len(lightin_skus)))



        return

    batch_prepare_draft.short_description = "更新草稿"

    def batch_submit_draft(self, request, queryset):
        # 定义actions函数
        #当前草稿对应的订单发货时，清空草稿
        #历史订单暂时不考虑
        #上一个订单如果已经发货，没有签收前，不允许创建新订单
        #上一个订单如果还没有发货，则删除原订单
        #把草稿表里数量大于1 的sku找出来，插入新订单表
        #自动把COD和VAT加到总价里

        for customer in queryset:
            # 检查草稿是否正常
            drafts = customer.customer_draft.filter(quantity__gt=0)
            if not drafts:
                customer.message = info("red", "没有草稿明细，不能提交订单")
                customer.save()
                continue

            #先检查客户已有订单状态
            ori_order = customer.customer_order.filter(~Q(status="cancel")).order_by("-order_time").first()
            if ori_order:

                if ori_order.status == "open":
                    print("还没有发货，先把订单关闭，重新创建新订单")
                    ori_order.status = "cancel"
                    ori_order.save()
                elif ori_order.status == "delivered":
                    print("订单已签收，可以创建新订单")

                else:
                    print (ori_order.status)
                    customer.message = info("red", "订单不是开放状态，不允许创建新订单，也不能修改订单了")
                    customer.save()
                    continue

            #取最大订单号作为新订单号
            order_prefix = "yalla_"
            order = Order.objects.filter(order_no__startswith=order_prefix).last()
            if order:
                order_num = int(order.order_no[6:]) + 1
            else:
                order_num = 1

            order_no = order_prefix + str(order_num).zfill(5)



            #创建新订单
            receiver = customer.receiver
            order = Order.objects.create(
                customer=customer,

                status="open",
                financial_status="paid",
                order_no = order_no,

                buyer_name = customer.name,
                #facebook_user_name =",".join(list(customer.customer_conversation.values_list("name",flat=True))),

                #sales = customer.sales,
                #conversation_link = ",".join(list(customer.customer_conversation.values_list("coversation",flat=True))),

                receiver_name= receiver.name,
                receiver_addr1= receiver.address1,
                receiver_addr2= receiver.address2,
                receiver_city =  receiver.get_city_display(),
                receiver_country =  receiver.country_code,
                receiver_phone =  receiver.phone_1,
                receiver_phone_2 = receiver.phone_2,
                order_amount=customer.order_amount,
                order_time = dt.now(),
            )
            if order:
                # 一开始就取了drafts，所以这里不取了
                # drafts = customer.customer_draft.filter(quantity__gt=0)
                orderdetail_list = []
                subtotal = 0
                for draft in drafts:
                    if draft.quantity > draft.lightin_sku.o_sellable:
                        print("缺货")
                        break
                    subtotal += float(draft.price) * draft.quantity

                    orderdetail = OrderDetail(
                        order=order,
                        sku=draft.lightin_sku.SKU,
                        product_quantity=draft.quantity,
                        price=draft.price,
                    )
                    orderdetail_list.append(orderdetail)

                if len(orderdetail_list) < len(drafts):
                    customer.message = info("red", "缺货， 不能提交订单")
                    customer.save()
                    order.status = "cancel"

                else:
                    orderdetails = OrderDetail.objects.bulk_create(orderdetail_list)
                    if not orderdetails:
                        customer.message = info("red", "创建订单明细出错")
                        customer.save()

                        order.status = "cancel"
                        break
                    else:
                        # 更新总金额
                        tax = subtotal * 0.05
                        COD = 20
                        order.order_amount = int(subtotal + COD + tax - float(customer.discount))

                        # 最后的操作员作为销售
                        customer.message = info("blue", "创建订单%s成功" % (order.order_no))
                        customer.sales = str(self.request.user)
                        customer.save()
                        # 记录操作日志
                        self.deal_log(queryset, "提交订单", order_no)
                # 更新订单状态
                order.save()
            else:
                customer.message = info("red", "创建订单出错")
                customer.save()

        return

    batch_submit_draft.short_description = "提交订单"

@xadmin.sites.register(Draft)
class DraftAdmin(object):
    list_display = [ 'lightin_sku', 'customer','handle','sellable','quantity', 'skuattr', "photo",]
    list_editable = ["quantity", ]

    search_fields = []

    ordering = []
    list_filter = ()

    actions = [ ]

    def photo(self, obj):
        # 如果sku有属性图片则用属性图片，否则用spu图片的第一张
        image = None
        sku = obj.lightin_sku
        if sku.comboed:
            image = sku.image_marked
        elif sku.image:
            image = sku.image
            print("sku 图片")
        else:

            spu = sku.lightin_spu
            if spu.images_dict:
                image = json.loads(spu.images_dict).values()
                if image and len(image) > 0:
                    a = "/"
                    image_split = list(image)[0].split(a)

                    image_split[4] = '800x800'
                    image = a.join(image_split)
                    print("spu 图片", spu, image)

        img = '<a><img src="%s" width="200px"></a>' % (image)

        return mark_safe(img)

    photo.short_description = "product photo"

    def skuattr(self,obj):
        return  obj.lightin_sku.skuattr

    skuattr.short_description = "skuattr"

    def sellable(self, obj):
        return obj.lightin_sku.o_sellable

    sellable.short_description = "sellable"

    def handle(self, obj):
        return obj.lightin_sku.lightin_spu.handle

    handle.short_description = "handle"

@xadmin.sites.register(Receiver)
class ReceiverAdmin(object):
    list_display = ['name', 'customer', 'country_code','city','address1', 'address2', "address3",
                    'city','phone_1', 'phone_2', "comments",]
    list_editable = [ ]

    search_fields = []

    ordering = []
    list_filter = ()

    actions = [ ]

@xadmin.sites.register(Conversation)
class ConversationAdmin(object):
    list_display = ['name', 'customer', 'coversation','comments',]
    list_editable = [ ]

    search_fields = []

    ordering = []
    list_filter = ()

    actions = [ ]

@xadmin.sites.register(DealLog)
class DealLogAdmin(object):
    list_display = ['deal_action', 'customer', "content", 'deal_staff','deal_time',]
    list_editable = [ ]

    search_fields = []

    ordering = ["-deal_time"]
    list_filter = ()

    actions = [ ]