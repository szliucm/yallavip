from prs.models import  *
from commodity.models import Breadcrumb
from django.db.models import Q, Count

def update_breadcrumb_count(sellable=10):
    spus = Lightin_SPU.objects.filter(vendor="lightin", sellable__gt=sellable)
    spus_counts = spus.values("breadcrumb").annotate(spus_count = Count("SPU"))

    Breadcrumb.objects.all().delete()
    breadcrumb_list = []
    for spus_count in spus_counts:
        # print("row is ",row)
        breadcrumb = Breadcrumb(
            breadcrumb=spus_count["breadcrumb"],
            spus_count=spus_count["spus_count"],

        )
        breadcrumb_list.append(breadcrumb)

    Breadcrumb.objects.bulk_create(breadcrumb_list)



