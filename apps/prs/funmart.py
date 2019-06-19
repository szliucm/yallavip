from .models import *

def funmart_cates():
    cates = Lightin_SPU.objects.filter(vendor='funmart').values_list("cate_1","cate_2", "cate_3").distinct()

    catelist = []

    for cate in list(cates):
        if not cate:
            continue

        if len(cate)>0:
            cate_1 = ("", cate[0].strip() , 1)
            if cate_1 not in catelist:
                catelist.append(cate_1)
        if len(tag) > 1:
            cate_2 = (cates[0].strip(), cates[1].strip() , 2)
            if cate_2 not in catelist:
                catelist.append(cate_2)

        if len(tag) > 2:
            cate_3 = (cates[1].strip(), cates[2].strip() , 3)
            if cate_3 not in catelist:
                catelist.append(cate_3)

    for cate in catelist:
        obj, created = MyCategory.objects.update_or_create(
            super_name=cate[0],
            name=cate[1],
            level=cate[2],
            defaults={
                "vendor":"funmart",

            }
        )
