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
    url = "http://47.96.143.109:9527/api/getInfoBySku"
    param = dict()
    items = FunmartOrderItem.objects.filter(order__downloaded=True, order__dealed=False)

    skus = items.values_list("sku",flat=True).distinct()

    for order in orders:
        param["order_no"] = order.order_no
        r = requests.post(url, data=json.dumps(param))
        if r.status_code == 200:
            return_data = json.loads(r.text)
