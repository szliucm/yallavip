import xadmin

from .models import *
from orders.models import Order



def update_performance(days=3):
    from django.db.models import Count, Sum, Q
    import pytz
    from datetime import datetime,timedelta
    # from django.utils import timezone as dt
    from django.db.models.functions import TruncDate


    riyadh = pytz.timezone('Asia/Riyadh')
    now = datetime.now(riyadh)
    today = datetime(now.year, now.month, now.day, tzinfo=riyadh)


    #orders = Order.objects.all()

    orders = Order.objects.filter(order_time__gt=(today - timedelta(days=days)))

    #先统计整体销售情况
    sales_counts = orders.annotate(date=TruncDate("order_time", tzinfo=riyadh)) \
        .values("date", "status").annotate(orders=Count("order_no")).order_by("-date")

    for sales_count in sales_counts:
        obj, created = Sales.objects.update_or_create(order_date=sales_count.get("date"),
                                                      #type=sales_count.get("status"),
                                                      defaults={sales_count.get("status"): sales_count.get("orders"),

                                                                }
                                                      )

    #统计客服业绩
    '''
    staff_counts = orders.annotate(date=TruncDate("order_time", tzinfo=riyadh)) \
        .values("date", "status","verify__sales").annotate(orders=Count("order_no")).order_by("-date")

    for staff_count in staff_counts:
        staff=staff_count.get("verify__sales")
        if not staff:
            staff = "unknown"
        obj, created = StaffPerformace.objects.update_or_create(order_date=staff_count.get("date"),
                                                        staff=staff,
                                                      order_status=staff_count.get("status"),
                                                      defaults={'count': staff_count.get("orders"),

                                                                }
                                                      )
                                                      '''

    #统计客服业绩跟踪
    track_counts = orders.annotate(date=TruncDate("order_time", tzinfo=riyadh)) \
        .values("date", "status","verify__sales").annotate(orders=Count("order_no")).order_by("-date")

    for track_count in track_counts:
        staff=track_count.get("verify__sales")
        if not staff:
            staff = "unknown"
        obj, created = StaffTrack.objects.update_or_create(order_date=track_count.get("date"),
                                                        staff=staff,
                                                      defaults={track_count.get("status"): track_count.get("orders"),

                                                                }
                                                      )

@xadmin.sites.register(Sales)
class SalesAdmin(object):
    list_display = ["order_date", "open", 'transit',"cancelled", ]

    # 'sku_name','img',
    search_fields = [ ]
    list_filter = [ "order_date",]
    list_editable = []
    readonly_fields = ()
    actions = ["batch_update_performance", ]
    ordering = ['-order_date',]
    '''
    data_charts = {
        "open_count": {'title': u"开放订单", "x-field": "order_date", "y-field": ("count", ),
                       "order": ('order_date',)},
        #"avg_count": {'title': u"Avg Report", "x-field": "date", "y-field": ('avg_count',), "order": ('date',)}
    }
    '''

    #更新最近7天的销售记录
    def batch_update_performance(self, request, queryset):

        update_performance(7)

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
    list_display = ["order_date", "staff", "open", 'transit',"cancelled",  ]

    # 'sku_name','img',
    search_fields = ["staff", ]
    list_filter = [ "order_date",'staff', ]
    list_editable = []
    readonly_fields = ()
    actions = [ ]
    ordering = ['-order_date',"staff",]

