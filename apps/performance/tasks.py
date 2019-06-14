

# Create your tasks here
from __future__ import absolute_import, unicode_literals

import json
import numpy as np
import random
import re
import requests
import time

from celery import shared_task, task
from django.db.models import Q, Count, Max
from django.utils import timezone as datetime
from django.utils import timezone as dt


from funmart.models import *

from .models import *


# 更新ali产品数据，把vendor和产品信息连接起来
@shared_task
def update_scan_performance(days=3):
    from django.db.models import Count, Sum, Q,F
    import pytz
    from datetime import datetime,timedelta
    # from django.utils import timezone as dt
    from django.db.models.functions import TruncDate

    riyadh = pytz.timezone('Asia/Riyadh')
    now = datetime.now(riyadh)
    today = datetime(now.year, now.month, now.day, tzinfo=riyadh)

    items_counts = FunmartOrderItem.objects.filter(scan_time__isnull=False,scan_time__gt=(today - timedelta(days=days))).\
        annotate(date=TruncDate("scan_time", tzinfo=riyadh)).\
        values("scanner", 'date').\
        annotate(items_quantity=Sum("scanned_quantity"), package_count =Count("order", distinct=True))

    #把相应的记录先删掉
    ScanItem.objects.filter(scan_date__gt=(today - timedelta(days=days))).delete()

    for items_count in items_counts:

        obj, created = ScanItem.objects.update_or_create(scan_date=items_count.get("date"),
                                                      scanner=items_count.get("scanner"),
                                                      defaults={
                                                          "packages": items_count.get("package_count"),
                                                          "items": items_count.get("items_quantity"),

                                                                }
                                                      )
