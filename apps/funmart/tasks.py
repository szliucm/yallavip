# Create your tasks here
from __future__ import absolute_import, unicode_literals

from celery import shared_task, task

import json
import requests
from  .models import *
from prs.tasks import my_custom_sql
from django.db.models import Count,Q,Sum

def test_funmart_product():
    url = "http://47.96.143.109:9527/api/getInfoBySku"
    param = dict()
    param["sku"] = "C-170809038"
    r = requests.post(url, data=json.dumps(param))
    print(r.status_code, r.text)

def download_funmart_orders():


    orders = ScanOrder.objects.filter(downloaded=False)

    # 已经有的直接设置为已下载
    downloaded_orders = list(FunmartOrder.objects.filter(downloaded=True).values_list("track_code",flat=True))
    orders.filter(track_code__in=downloaded_orders).update(downloaded=True)

    to_download_orders = orders.exclude(track_code__in=downloaded_orders)
    for order in to_download_orders:
        get_funmart_order.apply_async((order.track_code,), queue='funmart')



def deal_funmart_orders():
    #按批次扫描包裹，没有的sku则新增sku
    '''
    skus_to_add = FunmartOrderItem.objects.filter(order__downloaded=True, order__dealed=False)\
        .exclude(sku__in=list(FunmartSKU.objects.all().values_list('SKU',flat=True)))\
        .values_list("sku", flat=True).distinct()
    '''
    skus_to_add = FunmartOrderItem.objects.all()\
        .exclude(sku__in=list(FunmartSKU.objects.all().values_list('SKU',flat=True)))\
        .values_list("sku", flat=True).distinct()
    print("有%s个sku需要新增"%skus_to_add.count())

    sku_list = []
    for sku_to_add in skus_to_add:
        sku = FunmartSKU(
            SKU = sku_to_add,
        )

        sku_list.append(sku)

    print(sku_list)
    FunmartSKU.objects.bulk_create(sku_list)





def download_skus():


    # 没有下载的sku就下载sku；
    skus = FunmartSKU.objects.filter(downloaded=False)
    for sku in skus:
        get_funmart_sku.apply_async((sku.SKU,), queue='funmart')

def download_spus():
    # 把新的spu插入到spu列表
    spus_to_add = FunmartSKU.objects.filter(downloaded=True).exclude(SPU__in=
                        FunmartSPU.objects.all().values_list(
                            'SPU', flat=True)).values_list("SPU", flat=True).distinct()

    spu_list = []
    for spu_to_add in spus_to_add:
        spu = FunmartSPU(
            SPU=spu_to_add,
        )
        spu_list.append(spu)

    print(spu_list)
    FunmartSPU.objects.bulk_create(spu_list)

    #外键关联
    mysql = "update funmart_funmartspu p , funmart_funmartsku k set k.funmart_spu_id = p.id where p.SPU=k.SPU"
    my_custom_sql(mysql)

    # spu没有下载的就下载spu
    funmartspus = FunmartSPU.objects.filter(downloaded=False)
    for spu in funmartspus:
        get_funmart_spu.apply_async((spu.SPU,), queue='funmart')



@shared_task
def get_funmart_order(track_code):
    #order = FunmartOrder.objects.get(track_code=track_code)


    url = " http://47.98.80.172/api/searchOrder"
    param = dict()
    param["track_code"] = track_code
    r = requests.post(url, data=json.dumps(param))
    if r.status_code == 200:
        return_data = json.loads(r.text)
        if return_data.get("code") == '00001':
            data = return_data.get("data")
            order, created = FunmartOrder.objects.update_or_create(
                                    track_code=track_code,
                                    defaults={
                                        'order_no' : data.get("order_no"),
                                        'ship_method' : data.get("ship_method"),
                                        'downloaded': True
                                    }
            )


            orderitems = data.get("orderItems")

            FunmartOrderItem.objects.filter(order_no=data.get("order_no")).delete()
            orderitem_list = []
            for item in orderitems:
                orderitem = FunmartOrderItem(
                    order=order,
                    order_no=data.get("order_no"),
                    sku=item.get("sku"),
                    quantity=item.get("qty"),
                    price=item.get("price"),
                    category_cn=item.get("category_cn"),
                    category_en=item.get("category_en"),
                    name=item.get("name"),

                )

                orderitem_list.append(orderitem)

            print(orderitem_list)
            FunmartOrderItem.objects.bulk_create(orderitem_list)
        else:
            print (return_data.get("message"))


@shared_task
def get_funmart_sku(sku):
    print("get sku info", sku)
    url = "http://47.96.143.109:9527/api/getInfoBySku"
    param = dict()
    param["sku"] = sku
    r = requests.post(url, data=json.dumps(param))

    if r.status_code == 200:
        return_data = json.loads(r.text)
        if return_data.get("code") == '00001':
            data = return_data.get("data")


            funmartsku, created = FunmartSKU.objects.update_or_create(
                                    SKU=data.get("sku"),
                                    defaults={
                                        'SPU' : data.get("spu"),
                                        'skuattr' : json.dumps(data.get("skuattr")),
                                        'images' : json.dumps(data.get("images")),
                                        'sale_price' : data.get("price"),
                                        'downloaded': True
                                    }
                                )
            return  funmartsku

        else:
            funmartsku, created = FunmartSKU.objects.update_or_create(
                                    SKU=data.get("sku"),
                                    defaults={

                                        'download_error': return_data.get("message")
                                    }
                                )

            print (return_data.get("message"))

    return None

@shared_task
def get_funmart_spu(spu):
    print("get spu info", spu)

    url = "http://47.96.143.109:9527/api/getInfoBySku"
    param = dict()
    param["sku"] = spu
    r = requests.post(url, data=json.dumps(param))
    if r.status_code == 200:
        return_data = json.loads(r.text)
        if return_data.get("code") == '00001':
            data = return_data.get("data")


            funmartspu ,created= FunmartSPU.objects.update_or_create(
                SPU=data.get("spu"),
                defaults ={
                    'cate_1': data.get("top_category"),
                    'cate_2': data.get("second_category"),
                    'cate_3': data.get("third_category"),
                    'en_name': data.get("en_name"),
                    'skuattr': json.dumps(data.get("skuattr")),
                    'description': data.get("description"),
                    'images': json.dumps(data.get("images")),
                    'link': data.get("online_url"),
                    'sale_price': data.get("price"),
                    "skuList":json.dumps(data.get("skuList")),
                    'downloaded': True
                }
            )




            return  funmartspu
    else:
        print (return_data.get("message"))

    return None

#根据订单汇总，给spu打标
#订单数>30,hot
#5<订单数<30,normal
#订单数<5， drug
def lable_spus():
    mysql = "update funmart_funmartorderitem i , funmart_funmartsku k set i.funmart_sku_id = k.id where i.sku=k.SKU"
    my_custom_sql(mysql)

    spus_count = FunmartOrderItem.objects.filter(~Q(funmart_sku__SPU="")).values("funmart_sku__SPU").annotate(order_count=Count("order_no",distinct=True))

    hot_spus =  spus_count.filter(order_count__gte=30).values_list("funmart_sku__SPU", flat=True)
    FunmartSPU.objects.filter(SPU__in = list(hot_spus)).update(sale_type="hot")

    normal_spus = spus_count.filter(order_count__lt=30,order_count__gte=5).values_list("funmart_sku__SPU", flat=True)
    FunmartSPU.objects.filter(SPU__in=list(normal_spus)).update(sale_type="normal")

    drug_spus = spus_count.filter(order_count__lt=5).values_list("funmart_sku__SPU", flat=True)
    FunmartSPU.objects.filter(SPU__in=list(drug_spus)).update(sale_type="drug")

def batch_sku():
    track_code_list = list(ScanOrder.objects.filter(downloaded=True,shelfed=False ).values_list("track_code",flat=True))
    orderitems =  FunmartOrderItem.objects.filter(track_code__in=track_code_list)
    skus_list = orderitems.values_list("sku",flat=True)

    sku_counts = orderitems.values("sku").annotate(order_count=Count("track_code",distinct=True), quantity=Sum("quantity"))
    skus = FunmartSKU.objects.filter(SKU__in=skus_list).values("SKU","funmart_spu__sale_type" ,"skuattr","uploaded")


    BatchSKU.objects.all().delete()
    batch_sku_list=[]
    for sku in skus_list:
        sku_count = sku_counts.get(sku=sku)
        funmart_sku = skus.get(SKU = sku)

        order_count = sku_count.get("order_count")
        quantity = sku_count.get("quantity")

        sale_type = funmart_sku.get("funmart_spu__sale_type")
        sku_attr = funmart_sku.get("skuattr")
        uploaded = funmart_sku.get("uploaded")

        if sale_type == "hot":
            action = "Shelf"

        elif sale_type == "normal":

            if order_count >=3:
                action = "Shelf"
            else:
                action = "Normal_Case"
        else:
            if sku_attr.find("One Size") >-1 or sku_attr.find("Free Size") >-1:
                action = "Drug_No_Size"
            else:
                action = "Drug_Size"

        batch_sku = BatchSKU(
            SKU=sku,
            sale_type=sale_type,
            order_count=order_count,
            quantity=quantity,
            uploaded=uploaded,
            action=action,

        )
        batch_sku_list.append(batch_sku)

    BatchSKU.objects.bulk_create(batch_sku_list)






