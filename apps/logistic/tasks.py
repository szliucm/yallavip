# Create your tasks here
from __future__ import absolute_import, unicode_literals
import numpy as np, re
from celery import shared_task,task
from django.utils import timezone as dt


import requests
import json
import base64
from _datetime import datetime,timedelta
import  pytz
#from django.utils import timezone as datetime
from .models import Package, LogisticTrail
from orders.models import  Order
from django.utils import timezone
from django.db.models import Q

@shared_task
def updatelogistic_trail(type=None):

    if type == 1:
        queryset = Package.objects.filter(file_status="OPEN").order_by("-send_time")

    else:
        queryset = Package.objects.filter(
            Q(update_trail_time__lt=(timezone.now() - timedelta(days=1))) | Q(update_trail_time__isnull=True),
            file_status="OPEN")

    total = queryset.count()
    n=0
    for row in queryset:
        print("一共还有  %d  个包裹需要更新轨迹"%(total - n ))
        n += 1

        '''
        if row.update_trail_time is not None:
            if row.update_trail_time>=(timezone.now()- timedelta(days=1)):
                print("更新时间少于一天")
                continue
        '''

        update_trail(row.logistic_no)

    sync_balance(2)
    sync_balance(3)


    return

def update_trail(logistic_no):
    requrl = "http://api.jcex.com/JcexJson/api/notify/sendmsg"

    # 货物跟踪信息
    param = dict()
    param["service"] = 'track'

    param_data = dict()
    param_data["customerid"] = "3c917d0c-6290-11e8-a277-6c92bf623ff2"
    param_data["isdisplaydetail"] = "true"

    param_data["waybillnumber"] = logistic_no
    data_body = base64.b64encode(json.dumps(param_data).encode('utf-8'))
    param["data_body"] = data_body

    print("start update track requrl is %s waybillnumber is %s " % (requrl, logistic_no))

    res = requests.post(requrl, params=param)
    print(requrl, param)

    if res.status_code != 200:
        print("error !!!!!! response is ", res, res.content)
        return

    data = json.loads(res.text)
    print("data", data)

    waybillnumber = data.get('waybillnumber', 'none')

    if (waybillnumber == 'none'):
        return

    # recipientcountry = data["recipientcountry"]

    statusdetail = data["displaydetail"][0]["statusdetail"]
    if (len(statusdetail) == 0):
        return

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
        print(latest_status, logistic_no)

        Package.objects.filter(logistic_no = logistic_no).update(
                                                update_trail_time =  timezone.now(),
                                                logistic_update_date =  datetime.strptime(latest_status["time"] , "%Y-%m-%d %H:%M:%S").replace(tzinfo=pytz.timezone('Asia/Riyadh')),
                                                logistic_update_status=latest_status["status"],
                                                logistic_update_locate= latest_status["locate"],)

@shared_task
def sync_balance(type):
    logistic_suppplier = "佳成"
    '''
    packages_to_sync = Package.objects.raw('SELECT * FROM logistic_package  A WHERE '
                                                 'logistic_supplier = %s and file_status = "OPEN" '
                                                 'and logistic_no  IN  ( SELECT  B.waybillnumber FROM logistic_logisticbalance B where balance_type="COD") ',
                                                 [logistic_suppplier])

    packages_to_sync.objects.update(file_status="CLOSED")
    '''
    if type == "DELIVERED":
        #更新已对账的包裹的状态
        mysql = "update logistic_package set file_status = 'CLOSED' , yallavip_package_status = 'DELIVERED' WHERE file_status = 'OPEN'  and logistic_no  IN  (SELECT  waybillnumber as logistic_no FROM logistic_logisticbalance  where balance_type in ('COD') )"
    elif type == "RETURNED":
        mysql = "update logistic_package set file_status = 'CLOSED' , yallavip_package_status = 'RETURNED' WHERE file_status = 'OPEN'  and logistic_no  IN  (SELECT  waybillnumber as logistic_no FROM logistic_logisticbalance  where balance_type in ('RETURN') )"
    elif type == 2:
        #将物流轨迹显示“Delivered”的包裹标记成待对账
        mysql = "update logistic_package set warehouse_check = 'TOREFUND', wait_status=TRUE WHERE file_status = 'OPEN'  and warehouse_check='NONE' and logistic_update_status='Delivered' "

    elif type == 3:
        # 将物流轨迹显示       "RECEIVER UNABLE TO BE CONNECTED",
        #                      "receiver refused to accept the shipment",
        #                      "DELIVERY INFO INCORRECT/INCOMPLETE/MISSING"
        #                      的包裹标记成问题单

        mysql = "update logistic_package set yallavip_package_status = 'PROBLEM' ,problem_time = '%s' " \
                " where deal = 'NONE' and logistic_update_status in (" \
                "'delivery address corrected/changed - delivery rescheduled as per customer request',"\
                "'receiver unable to be connected'," \
                "'receiver refused to accept the shipment'," \
                "'delivery info incorrect/incomplete/missing'," \
                "'unsendable - incomplete/incorrect delivery address'"\
                ") "%(dt.now().strftime("%Y-%m-%d %H:%M:%S"))


    my_custom_sql(mysql)

def my_custom_sql(mysql):
    from django.db import connection, transaction
    with connection.cursor() as c:
        c.execute(mysql)

    # Data retrieval operation - no commit required
    #cursor.execute("SELECT foo FROM bar WHERE baz = %s", [self.baz])
    #row = cursor.fetchone()

    return

################# 用订单表的发货时间更新包裹表的发货时间
#  update logistic_package l, orders_order o set l.send_time = o.send_time where l.logistic_no = o.logistic_no and l.send_time is null
###################
###############  更新已对账包裹的状态
#   update logistic_package set file_status = "CLOSED" WHERE logistic_supplier ="佳成" and file_status = "OPEN"  and logistic_no  IN  (SELECT  waybillnumber as logistic_no FROM logistic_logisticbalance  where balance_type="COD")

#  update logistic_package set file_status = "CLOSED" WHERE logistic_supplier ="佳成" and file_status = "OPEN"  and logistic_no  IN  (SELECT  waybillnumber as logistic_no FROM logistic_logisticbalance  where balance_type="RETURN")

##################### 没有轨迹的订单
#      select * from logistic_package where datediff(logistic_update_date , logistic_start_date)  <6 and datediff(CURDATE(), logistic_start_date) >20 and file_status = "OPEN" and wait_status = false

############更新包裹表对应的订单号
#       update logistic_package l, orders_order o set l.ref_order_id  = o.id where l.logistic_no = o.logistic_no and l.ref_order_id is null
def sync_logistic_problem():
    queryset = Package.objects.all()
    for row in queryset:
        trail = LogisticTrail.objects.filter(waybillnumber=row.logistic_no,
                                             trail_status__in =[
                        'delivery address corrected/changed - delivery rescheduled as per customer request',
                        'receiver unable to be connected',
                        'receiver refused to accept the shipment',
                        'delivery info incorrect/incomplete/missing',
                        'unsendable - incomplete/incorrect delivery address']
                                             ).order_by("trail_time").first()
        if trail is not None:
            Package.objects.filter(pk=row.pk).update(yallavip_package_status = 'PROBLEM' ,problem_trail = trail.trail_status, problem_time = trail.trail_time)

def sync_logistic_sendtime():
    queryset = Package.objects.all()
    for row in queryset:
        order = Order.objects.filter(logistic_no=row.logistic_no,).first()
        if order is not None:
            Package.objects.filter(pk=row.pk).update(send_time = order.send_time)

def sync_logistic_order():
    queryset = Package.objects.filter(ref_order__isnull=True)
    for row in queryset:
        order = Order.objects.filter(logistic_no=row.logistic_no,).first()
        if order is not None:
            Package.objects.filter(pk=row.pk).update(ref_order = order)

#更新兰亭物流轨迹
@shared_task
def updatelogistic_trail_lightin(type=None):
    from prs.tasks import  getTrack
    #扫描订单，生成待追踪列表
    queryset = Order.objects.filter(~Q(track_status__in = ["CC"]),wms_status = "D" )

    logistic_no_list = list(queryset.values_list("logistic_no",flat=True))
    print("一共有  %d  个包裹需要更新轨迹"%(queryset.count() ))
    result = getTrack(logistic_no_list)
    if result.get("ask") == "Success":
        order_id_list = []
        oriorders_list = []
        for row in result.get("Data"):
            #处理单个订单
            waybillnumber = row["TrackingNumber"]
            Package.objects.update_or_create(
                logistic_no=waybillnumber,
                ref_order=queryset.get(logistic_no = waybillnumber),
                defaults={
                    'logistic_update_date': row["New_date"],
                    'logistic_update_status': row["Status"],
                    'logistic_update_comment': row["New_Comment"],

                }
            )

            trails_list = []
            for trail_row in row.get("Detail"):
                #处理订单的轨迹明细

                trail = LogisticTrail(
                    waybillnumber=waybillnumber,
                    trail_time=trail_row["Occur_date"],
                    trail_statuscnname=trail_row["Comment"],
                    trail_status=trail_row["track_code"],
                    trail_locaiton=trail_row["track_area"],
                )
                trails_list.append(trail)
                pass

            # 删除所有可能重复的轨迹信息
            LogisticTrail.objects.filter(waybillnumber=row["TrackingNumber"]).delete()
            LogisticTrail.objects.bulk_create(trails_list)

    #print(result)
    return



