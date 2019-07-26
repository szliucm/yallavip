import xadmin

from .models import *
from orders.models import Order
from conversations.models import FbMessage

def update_performance(days=60):
    from django.db.models import Count, Sum, Q,F
    import pytz
    from datetime import datetime,timedelta
    # from django.utils import timezone as dt
    from django.db.models.functions import TruncDate


    riyadh = pytz.timezone('Asia/Riyadh')
    now = datetime.now(riyadh)
    today = datetime(now.year, now.month, now.day, tzinfo=riyadh)



    #统计订单


    #orders = Order.objects.all()

    orders = Order.objects.filter(order_time__gt=(today - timedelta(days=days)))

    #先统计整体销售情况
    sales_counts = orders.annotate(date=TruncDate("order_time", tzinfo=riyadh)) \
        .values("date", "status").annotate(orders=Count("order_no"),amount=Sum("order_amount")).order_by("-date")

    #把相应的记录先删掉
    Sales.objects.filter(order_date__gt=(today - timedelta(days=days))).delete()

    for sales_count in sales_counts:
        if sales_count.get("status") in ['open', 'transit','delivered', 'refused', 'cancelled']:
            obj, created = Sales.objects.update_or_create(order_date=sales_count.get("date"),
                                                      #type=sales_count.get("status"),
                                                      defaults={sales_count.get("status"): sales_count.get("orders"),
                                                                sales_count.get("status")+"_amount": sales_count.get("amount"),
                                                                #"delivered_rate": int(100 * F("delivered")/(F('transit')+F('delivered')+F('refused')))

                                                                }
                                                      )

    # 统计会话
    session_counts = FbMessage.objects.filter(created_time__gt=(today - timedelta(days=days)))\
        .annotate(date=TruncDate("created_time", tzinfo=riyadh)) \
        .values("date").annotate(conversation_count=Count("conversation_no", distinct=True),
                                 message_count=Count("message_no")).order_by("-date")

    for session_count in session_counts:
        obj, created = Sales.objects.update_or_create(order_date=session_count.get("date"),

                                                      defaults={
                                                          "conversation_count": session_count.get(
                                                              "conversation_count"),
                                                          "message_count": session_count.get("message_count"),

                                                      }
                                                      )

    #统计客服业绩跟踪
    track_counts = orders.annotate(date=TruncDate("order_time", tzinfo=riyadh)) \
        .values("date", "status","verify__sales").annotate(orders=Count("order_no"),amount=Sum("order_amount")).order_by("-date")

    # 把相应的记录先删掉
    StaffTrack.objects.filter(order_date__gt=(today - timedelta(days=days))).delete()

    for track_count in track_counts:
        staff=track_count.get("verify__sales")
        if not staff:
            staff = "unknown"
        print(track_count.get("status"))
        if track_count.get("status") in ['open','transit','delivered', 'refused','cancelled']:
            obj, created = StaffTrack.objects.update_or_create(order_date=track_count.get("date"),
                                                        staff=staff,
                                                      defaults={track_count.get("status"): track_count.get("orders"),
                                                                track_count.get("status") + "_amount": track_count.get(
                                                                    "amount"),
                                                                }
                                                      )
    # 统计page业绩跟踪
    page_counts = orders.annotate(date=TruncDate("order_time", tzinfo=riyadh)) \
        .values("date", "status", "verify__mailbox_id").annotate(orders=Count("order_no"),
                                                            amount=Sum("order_amount")).order_by("-date")

    # 把相应的记录先删掉
    PageTrack.objects.filter(order_date__gt=(today - timedelta(days=days))).delete()

    for page_count in page_counts:
        page_no = page_count.get("verify__mailbox_id")

        if not page_no:
            page_no = "unknown"
        if page_count.get("status") in ['open', 'transit', 'delivered', 'refused', 'cancelled']:
            obj, created = PageTrack.objects.update_or_create(order_date=page_count.get("date"),
                                                           page_no=page_no,
                                                           defaults={page_count.get("status"): page_count.get(
                                                               "orders"),
                                                                     page_count.get(
                                                                         "status") + "_amount": page_count.get(
                                                                         "amount"),
                                                                     }
                                                           )

@xadmin.sites.register(Sales)
class SalesAdmin(object):
    list_display = ["order_date", "conversation_count", "message_count", "delivered_rate", "open","open_amount", 'transit',"transit_amount",  'delivered',"delivered_amount", 'refused',"refused_amount","cancelled","cancelled_amount", ]

    # 'sku_name','img',
    search_fields = [ ]
    list_filter = [ "order_date",]
    list_editable = []
    readonly_fields = ()
    actions = ["batch_update_performance", ]
    ordering = ['-order_date',]
    '''
    data_charts = {
        "open_count": {'title': u"交运订单数", "x-field": "order_date", "y-field": ("transit", ),
                       "order": ('order_date',)},
        #"avg_count": {'title': u"Avg Report", "x-field": "date", "y-field": ('avg_count',), "order": ('date',)}
    }
    '''


    #更新最近7天的销售记录
    def batch_update_performance(self, request, queryset):

        update_performance(60)

    batch_update_performance.short_description = "更新业绩"

'''
@xadmin.sites.register(StaffPerformace)
class StaffPerformaceAdmin(object):
    list_display = ["order_date", "staff", "order_status", 'count',  ]

    # 'sku_name','img',
    search_fields = ["staff", ]
    list_filter = [ "order_date",'staff',"order_status", ]
    list_editable = []
    readonly_fields = ()
    actions = [ ]
    ordering = ['-order_date',"staff",'order_status']
'''

@xadmin.sites.register(StaffTrack)
class StaffTrackAdmin(object):
    list_display = ["order_date", "staff", "delivered_rate","open","open_amount", 'transit',"transit_amount", 'delivered',"delivered_amount", 'refused',"refused_amount","cancelled","cancelled_amount",   ]

    # 'sku_name','img',
    search_fields = ["staff", ]
    list_filter = [ "order_date",'staff', ]
    list_editable = []
    readonly_fields = ()
    actions = [ ]
    ordering = ['-order_date',"staff",]

@xadmin.sites.register(PageTrack)
class PageTrackTrackAdmin(object):
    def page(self, obj):
        from fb.models import MyPage
        try:
            return  MyPage.objects.get(page_no= obj.page_no).page
        except:
            return "unknown"
    page.short_description = "Page"

    list_display = ["order_date", "page", "delivered_rate","open","open_amount", 'transit',"transit_amount", 'delivered',"delivered_amount", 'refused',"refused_amount","cancelled","cancelled_amount",   ]

    # 'sku_name','img',
    search_fields = [ ]
    list_filter = [ "order_date",'page_no', ]
    list_editable = []
    readonly_fields = ()
    actions = [ ]
    ordering = ['-order_date',"page_no",]

@xadmin.sites.register(ScanPackage)
class ScanPackageAdmin(object):
    list_display = ["scan_date", "scan_hour", "scanner", "packages", ]

    search_fields = [ ]
    list_filter = [ "scan_date",'scanner', ]
    list_editable = []
    readonly_fields = ()
    actions = [ ]
    ordering = ['-scan_date',"scanner",]

@xadmin.sites.register(ScanItem)
class ScanItemAdmin(object):
    list_display = ["scan_date", "scan_hour", "scanner", "packages","items", ]

    search_fields = [ ]
    list_filter = [ "scan_date",'scanner', ]
    list_editable = []
    readonly_fields = ()
    actions = [ ]
    ordering = ['-scan_date',"scanner",]