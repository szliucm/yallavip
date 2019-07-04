from .models import *



def funmart_cates():
    cates = Lightin_SPU.objects.filter(vendor='funmart').values_list("cate_1","cate_2", "cate_3").distinct()

    catelist = []

    for cate in list(cates):

        if not cate:
            continue



        if cate[0]:

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

    #供货价的5.5倍 3.75*5.5

    multiple_price = spu.vendor_supply_price * 20.6

    # 供应商售价的6折 3.75*0.55
    discount_price = spu.vendor_sale_price * 2.06
    if multiple_price < discount_price:
        new_price = round(discount_price)
    else:
        new_price = round(multiple_price)



    #小于5块的都卖10块，小于20块都加10块
    if new_price <5:
        new_price += 5
    elif new_price <20:
        new_price += 10

    #价格大于30的，都包邮
    if new_price >= 30:
        spu.free_shipping = True
    else:
        spu.free_shipping = False

    #两件包邮，只加 15 SAR
    free_shipping_price = new_price + 15

    #推广价
    promote_price = int(new_price )
    promote_free_shipping_price = promote_price + 15

    spu.spu_sku.update(free_shipping_price=free_shipping_price, sku_price = new_price,
                        promote_price=promote_price, promote_free_shipping_price = promote_free_shipping_price)

    #修改spu价格
    spu.free_shipping_price = free_shipping_price
    spu.yallavip_price = new_price

    spu.promote_price = promote_price
    spu.promote_free_shipping_price = promote_free_shipping_price

    spu.promoted = True
    spu.save()
    return  True
