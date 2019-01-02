import requests
import json
import base64
import  time
from django.utils import timezone as datetime
from .models import Package, LogisticTrail

def updatelogistic_trail():

    requrl = "http://api.jcex.com/JcexJson/api/notify/sendmsg"

    # 货物跟踪信息
    param = dict()
    param["service"] = 'track'

    param_data = dict()
    param_data["customerid"] = "3c917d0c-6290-11e8-a277-6c92bf623ff2"
    param_data["isdisplaydetail"] = "true"

    queryset = Package.objects.filter(file_status= "OPEN")
    for row in queryset:

        param_data["waybillnumber"] = row.logistic_no
        data_body = base64.b64encode(json.dumps(param_data).encode('utf-8'))
        param["data_body"] = data_body

        print("start update track requrl is %s param is %s " % (requrl, param))

        res = requests.post(requrl, params=param)

        if res.status_code != 200:
            print("error !!!!!! response is ", res)
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
        trail =  LogisticTrail.objects.filter(waybillnumber=waybillnumber).order_by("-trail_time").first()
        trail_time = trail.trail_time
        print("!!!!!!!!!!!",trail_time)
        for status_d in statusdetail:

            new_trail_time =   time.strptime(status_d["time"] , "%Y-%m-%d %H:%M:%S")
            if new_trail_time <= trail_time.timetuple():
                print("@@@@@@@@@@@@ ", new_trail_time)
                break

            print("#######",new_trail_time )

            LogisticTrail.objects.update_or_create(
                waybillnumber=waybillnumber,trail_time = status_d["time"],
                defaults={
                           'trail_locaiton': status_d["locate"],
                           'trail_status': status_d["status"],

                           }
                 )

    return
