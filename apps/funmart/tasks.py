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
    url = " http://47.98.80.172/api/searchOrder"
    param = dict()
#    param["order_no"] = "112115244631159272"

    orders = FunmartOrder.objects.filter(downloaded=False)
    for order in orders:
        param["order_no"] = order.order_no
        r = requests.post(url, data=json.dumps(param))
        if r.status_code == 200:
            return_data = json.loads(r.text)
            if return_data.get("code") == '00001':
                data = return_data.get("data")

                order.track_code = data.get("track_code")
                order.ship_method = data.get("ship_method")
                order.downloaded = True
                order.save()

                orderitems = data.get("orderItems")

                FunmartOrderItem.objects.filter(order_no = data.get("order_no")).delete()
                orderitem_list = []
                for item in orderitems:
                    orderitem = FunmartOrderItem(
                        order = order,
                        order_no = data.get("order_no"),
                        sku = item.get("sku"),
                        quantity = item.get("qty"),
                        price = item.get("price"),



                    )

                    orderitem_list.append(orderitem)

                print(orderitem_list)
                FunmartOrderItem.objects.bulk_create(orderitem_list)
            else:
                print (return_data.get("message"))

def deal_funmart_orders():

    #遍历所有没有处理的订单，sku没有的就下载sku，对应的spu没有下载的就下载spu
    items = FunmartOrderItem.objects.filter(order__downloaded=True, order__dealed=False)

    skus = items.values_list("sku",flat=True).distinct()

    for sku in skus:
        funmartskus = FunmartSKU.objects.filter(SKU=sku)
        if funmartskus and funmartskus[0].funmart_spu:
            continue

        funmartsku = get_funmart_sku(sku)
        spu = funmartsku.SPU

        funmartspus = FunmartSPU.objects.filter(SPU=spu)
        if funmartspus:
            funmartsku.funmart_spu = funmartspus[0]
        else:
            funmartspu = get_funmart_spu(spu)
            funmartsku.funmart_spu = funmartspu



        funmartsku.save()

    orders = items.values_list("order__pk",flat=True).distinct()
    FunmartOrder.objects.filter(pk__in=orders).update(order__dealed=True)



def get_funmart_sku(sku):
    url = "http://47.96.143.109:9527/api/getInfoBySku"
    param = dict()
    param["sku"] = sku
    r = requests.post(url, data=json.dumps(param))
    if r.status_code == 200:
        return_data = json.loads(r.text)
        if return_data.get("code") == '00001':
            data = return_data.get("data")

            funmartsku = FunmartSKU.objects.create(
                SPU=data.get("spu"),
                SKU=data.get("sku"),
                skuattr=data.get("skuattr"),
                image=data.get("images"),
                sale_price=data.get("price"),

            )
            return  funmartsku

    return None

def get_funmart_spu(spu):
    url = "http://47.96.143.109:9527/api/getInfoBySku"
    param = dict()
    param["sku"] = spu
    r = requests.post(url, data=json.dumps(param))
    if r.status_code == 200:
        return_data = json.loads(r.text)
        if return_data.get("code") == '00001':
            data = return_data.get("data")

            funmartspu = FunmartSPU.objects.create(
                SPU=data.get("spu"),
                cate_1=data.get("top_category"),
                cate_2=data.get("second_category"),
                cate_3=data.get("third_category"),
                en_name=data.get("en_name"),
                skuattr=data.get("skuattr"),
                description=data.get("description"),
                images=data.get("images"),
                link=data.get("online_url"),
                sale_price=data.get("price"),
                skuList=data.get("skuList"),

            )
            return  funmartspu

    return None


