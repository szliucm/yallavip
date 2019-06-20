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


#把价格大于40的，全部设置成单件包邮
def set_spu_free_delivery_price():


    spus = Lightin_SPU.objects.filter(vendor="funmart")
    for spu in spus:
      cal_promote_price(spu)

#计算某个spu的促销价，修改sku，spu的促销价
#原价大于40的，都设成单件包邮
def cal_promote_price(spu):



    #供货价的6倍 3.75*6

    multiple_price = spu.vendor_supply_price * 22.5

    # 供应商售价的6折 3.75*0.6
    discount_price = spu.vendor_sale_price * 2.25
    if multiple_price < discount_price:
        promote_price = round(discount_price)
    else:
        promote_price = round(multiple_price)


    fee = 25
    free_shipping_price = promote_price + fee
    spu.free_shipping_price = free_shipping_price
    spu.spu_sku.update(free_shipping_price=free_shipping_price, sku_price = promote_price)


    #修改spu价格
    spu.free_shipping_price = free_shipping_price
    spu.yallavip_price = promote_price

    spu.promoted = True
    spu.save()




    return  True