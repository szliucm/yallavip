import xadmin

from .models import *
from orders.models import Order



def update_performance(days=None):
    from django.db.models import Count, Sum, Q
    import pytz
    from datetime import datetime,timedelta
    # from django.utils import timezone as dt
    from django.db.models.functions import TruncDate


    riyadh = pytz.timezone('Asia/Riyadh')
    now = datetime.now(riyadh)
    today = datetime(now.year, now.month, now.day, tzinfo=riyadh)


    orders = Order.objects.all()
    if days:
        orders = orders.filter(order_time__range=(today - timedelta(days=days), today))

    order_counts = orders.annotate(date=TruncDate("order_time", tzinfo=riyadh)) \
        .values("date", "status").annotate(orders=Count("order_no")).order_by("-date")

    sales = {}
    for order_count in order_counts:
        obj, created = Sales.objects.update_or_create(order_date=order_count.get("date"),
                                                      type=order_count.get("status"),
                                                      defaults={'count': order_count.get("orders"),

                                                                }
                                                      )


@xadmin.sites.register(Sales)
class SalesAdmin(object):
    list_display = ["order_date", "type", 'count',  ]

    # 'sku_name','img',
    search_fields = [ ]
    list_filter = [ "order_date",'type',]
    list_editable = []
    readonly_fields = ()
    actions = ["batch_update_performance", ]
    ordering = ['-order_date','type']
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

    batch_update_performance.short_description = "更新销售业绩"
