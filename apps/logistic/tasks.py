# Create your tasks here
from __future__ import absolute_import, unicode_literals
import numpy as np, re
from celery import shared_task,task


import requests
import json
import base64
from _datetime import datetime,timedelta
import  pytz
#from django.utils import timezone as datetime
from .models import Package, LogisticTrail
from django.utils import timezone
from django.db.models import Q

@shared_task
def updatelogistic_trail():

    requrl = "http://api.jcex.com/JcexJson/api/notify/sendmsg"

    # 货物跟踪信息
    param = dict()
    param["service"] = 'track'

    param_data = dict()
    param_data["customerid"] = "3c917d0c-6290-11e8-a277-6c92bf623ff2"
    param_data["isdisplaydetail"] = "true"

    queryset = Package.objects.filter(Q(logistic_update_date__lt = (timezone.now()- timedelta(days=1)).date())|Q(logistic_update_date__isnull = True),
                                      logistic_supplier="佳成",
                                      file_status= "OPEN")

    total = queryset.count()
    n=0
    for row in queryset:
        print("一共还有  %d  个包裹需要更新轨迹"%(total - n ))
        n += 1

        if row.logistic_update_date is not None:
            if row.logistic_update_date>=(timezone.now()- timedelta(days=1)).date():
                print("更新时间少于一天")
                continue

        param_data["waybillnumber"] = row.logistic_no
        data_body = base64.b64encode(json.dumps(param_data).encode('utf-8'))
        param["data_body"] = data_body

        print("start update track requrl is %s waybillnumber is %s " % (requrl, row.logistic_no))

        res = requests.post(requrl, params=param)
        print(requrl, param)

        if res.status_code != 200:
            print("error !!!!!! response is ", res, res.content)
            continue

        data = json.loads(res.text)
        print("data", data)

        waybillnumber = data.get('waybillnumber', 'none')

        if (waybillnumber == 'none'):
            continue

        # recipientcountry = data["recipientcountry"]

        statusdetail = data["displaydetail"][0]["statusdetail"]
        if (len(statusdetail) == 0):
            continue

        #逆序，最新动态在最前面
        statusdetail.reverse()
        trail =  LogisticTrail.objects.filter(waybillnumber=waybillnumber).order_by("-trail_time")

        if trail.exists() :
            #print(trail)
            #print(trail.first())
            trail_time = trail.first().trail_time
        else:
            trail_time = datetime.strptime("2018-01-01 00:00:00", "%Y-%m-%d %H:%M:%S").replace(tzinfo=pytz.timezone('Asia/Riyadh'))


        #print("!!!!!!!!!!!",trail_time)
        for status_d in statusdetail:

            new_trail_time =   datetime.strptime(status_d["time"] , "%Y-%m-%d %H:%M:%S").replace(tzinfo=pytz.timezone('Asia/Riyadh'))
            if new_trail_time <= trail_time:
                #print("@@@@@@@@@@@@ ", new_trail_time)
                break

            #print("#######",new_trail_time )

            LogisticTrail.objects.update_or_create(
                waybillnumber=waybillnumber,trail_time = new_trail_time,
                defaults={
                           'trail_locaiton': status_d.get("locate"),
                           'trail_status': status_d.get("status"),
                            'trail_statuscnname': status_d.get("statuscnname"),

                           }
                 )
        if len(statusdetail)>=1:
            latest_status = statusdetail[0]
            Package.objects.filter(pk = row.pk).update(logistic_update_date =  timezone.now(),
                                                    logistic_update_status=latest_status["status"],
                                                    logistic_update_locate= latest_status["locate"],)

    return

@shared_task
def sync_balance():
    logistic_suppplier = "佳成"
    packages_to_sync = Package.objects.raw('SELECT * FROM logistic_package  A WHERE '
                                                 'logistic_supplier = %s and file_status = "OPEN" '
                                                 'and logistic_no  IN  ( SELECT  B.waybillnumber FROM logistic_logisticbalance B where balance_type="COD") ',
                                                 [logistic_suppplier])

    packages_to_sync.objects.update(file_status="CLOSED")