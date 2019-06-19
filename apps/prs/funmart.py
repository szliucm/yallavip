from .models import *



def funmart_cates():
    cates = Lightin_SPU.objects.filter(vendor='funmart').values_list("cate_1","cate_2", "cate_3").distinct()

    catelist = []

    for cate in list(cates):

        if not cate:
            continue

        tag_list = list(cate)

        if cate[0]:
            tag = tag_list
            cate_1 = ("", cate[0].strip() , 1, ",".join(list(cate)[:1]))
            if cate_1 not in catelist:
                catelist.append(cate_1)
        if cate[1]:
            cate_2 = (cate[0].strip(), cate[1].strip() , 2, ",".join(list(cate)[:2]))
            if cate_2 not in catelist:
                catelist.append(cate_2)

        if cate[2]:
            cate_3 = (cate[1].strip(), cate[2].strip() , 3, ",".join(list(cate)[:3]))
            if cate_3 not in catelist:
                catelist.append(cate_3)

    for cate in catelist:
        obj, created = MyCategory.objects.update_or_create(
            tags = cate[3],

            defaults={
                "super_name": cate[0],
                "name": cate[1],
                "level": cate[2],
                "vendor": "funmart",


            }
        )


