# Create your tasks here
from __future__ import absolute_import, unicode_literals

from celery import shared_task, task

import json
import requests
from  .models import *

def test_funmart_product():
    url = "http://47.96.143.109:9527/api/getInfoBySku"
    param = dict()
    param["sku"] = "C-170809038"
    r = requests.post(url, data=json.dumps(param))
    print(r.status_code, r.text)

def download_funmart_orders():


    orders = FunmartOrder.objects.filter(downloaded=False)
    for order in orders:

        get_funmart_order.apply_async((order.track_code,), queue='funmart')


def deal_funmart_orders():
    #按批次扫描包裹，没有的sku则新增sku
    skus_to_add = FunmartOrderItem.objects.filter(order__downloaded=True, order__dealed=False).exclude(sku__in=
                        FunmartSKU.objects.all().values_list(
                            'SKU',flat=True)).values_list("sku", flat=True).distinct()

    sku_list = []
    for sku_to_add in skus_to_add:
        sku = FunmartSKU(
            SKU = sku_to_add,
        )

        sku_list.append(sku)

    print(sku_list)
    FunmartSKU.objects.bulk_create(sku_list)





def download_skus():
    from prs.tasks import my_custom_sql

    # 没有下载的sku就下载sku；
    skus = FunmartSKU.objects.filter(downloaded=False)
    for sku in skus:
        get_funmart_sku(sku.SKU)

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

    # spu没有下载的就下载spu
    funmartspus = FunmartSPU.objects.filter(downloaded=False)
    for spu in funmartspus:
        get_funmart_spu(spu.SPU)

    #外键关联
    mysql = "update funmart_funmartspu p , funmart_funmartsku k set k.funmart_spu_id = p.id where p.SPU=k.SPU"
    my_custom_sql(mysql)

@shared_task
def get_funmart_order(track_code):
    order = FunmartOrder.objects.get(track_code=track_code)
    url = " http://47.98.80.172/api/searchOrder"
    param = dict()
    param["track_code"] = track_code
    r = requests.post(url, data=json.dumps(param))
    if r.status_code == 200:
        return_data = json.loads(r.text)
        if return_data.get("code") == '00001':
            data = return_data.get("data")

            order.track_code = data.get("track_code")
            order.order_no = data.get("order_no")
            order.ship_method = data.get("ship_method")
            order.downloaded = True
            order.save()

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

                )

                orderitem_list.append(orderitem)

            print(orderitem_list)
            FunmartOrderItem.objects.bulk_create(orderitem_list)
        else:
            print (return_data.get("message"))



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
                                        'skuattr' : data.get("skuattr"),
                                        'images' : data.get("images"),
                                        'sale_price' : data.get("price"),
                                        'downloaded': True
                                    }
                                )
            return  funmartsku

        else:
            print (return_data.get("message"))

    return None

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
                    'skuattr': data.get("skuattr"),
                    'description': data.get("description"),
                    'images': data.get("images"),
                    'link': data.get("online_url"),
                    'sale_price': data.get("price"),
                    "skuList":data.get("skuList"),
                    'downloaded': True
                }
            )




            return  funmartspu
    else:
        print (return_data.get("message"))

    return None


