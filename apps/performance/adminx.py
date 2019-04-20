import xadmin

from .models import *

@xadmin.sites.register(Sales)
class SalesAdmin(object):
    list_display = ["order_date", "open_num", 'cancel_nmu', "transit_num", ]

    # 'sku_name','img',
    search_fields = [ ]
    list_filter = [ ]
    list_editable = []
    readonly_fields = ()
    actions = ["update_performance", ]
    ordering = ['-order_date']

    #更新最近7天的销售记录
    def update_performance(self, request, queryset):
        from django.db.models import Count, Sum, Q
        import pytz
        import datetime
        #from django.utils import timezone as dt
        from django.db.models.functions import  TruncDate

        today = datetime.date.today()

        riyadh = pytz.timezone('Asia/Riyadh')

        order_counts = Order.objects.filter(order_time__range=(today - datetime.timedelta(days=7), today))\
            .annotate(date=TruncDate("order_time", tzinfo=riyadh))\
            .values("date", "status").annotate(orders=Count("order_no")).order_by("-date")

        sales = {}
        for order_count in order_counts:

            obj, created = Sales.objects.update_or_create(order_date=order_count.date,
                                                          type = order_count.status,
                                                           defaults={'count': order_count.orders,

                                                                     }
                                                           )



    update_performance.short_description = "更新销售业绩"

