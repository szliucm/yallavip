from django.db.models import Count, Sum, Q, F
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect
import  json
# Create your views here.
from xadmin.views import BaseAdminView
from django.views.decorators.csrf import csrf_exempt,csrf_protect
from django.conf import settings    # 获取 settings.py 里边配置的信息
import os
from django.utils import timezone as dt

from .models import *


class testView(BaseAdminView):
    template_name = 'funmart/index.html'

    def get(self, request, *args, **kwargs):
        data = 'test'
        return render(request, self.template_name, {'data': data})


def index(request):
    return render(request, 'funmart/index.html')


def demo_add(request):
    a = request.GET['a']
    b = request.GET['b']
    a = int(a)
    b = int(b)
    return HttpResponse(str(a + b))


import json

def order_item(request):
    order_items = [
        {"sku":"123",
         "quantity":1
         },
        {"sku": "456",
         "quantity": 2
         },
    ]
    print (order_items)
    return JsonResponse(order_items,safe=False)

def ajax_list(request):
    a = list(range(100))
    return HttpResponse(json.dumps(a), content_type='application/json')


def ajax_dict(request):
    name_dict = {'twz': 'Love python and Django', 'zqxt': 'I am teaching Django'}
    return HttpResponse(json.dumps(name_dict), content_type='application/json')

def scanpackage(request):
    from funmart.tasks import get_funmart_order
    if request.method == 'GET':
        pass
    elif request.method == 'POST':
        item = {}
        item['scan_result'] = ""
        item['track_code'] = ""
        item['order_no'] = ""
        item['order_ref'] = ""

        posts = request.POST
        print(posts)
        batch_no = posts.get('batch_no')
        track_code = posts.get('track_code')
        order_ref = posts.get('order_ref')

        if not batch_no  :
            item['scan_result'] = 'Please Input Batch_no'
            item['batch_package_count'] = ""
            return JsonResponse(item)

        batch_package_count = FunmartOrder.objects.filter(batch_no=batch_no, scanned=True).count()
        item['batch_package_count'] = batch_package_count

        if not track_code :
            item['scan_result'] = 'Please Input track_code'
            return JsonResponse(item)


        #从funmart查，并更新本地数据库
        #暂时没有考虑效率问题
        '''
        if order_ref:
            scanorders = ScanOrder.objects.filter(batch_no=batch_no,order_ref=order_ref)
        else:
            scanorders = ScanOrder.objects.filter(batch_no=batch_no, track_code=track_code)

        #print ("ScanOrder 查询结果",scanorders )

        if scanorders:

            item['scan_result'] = 'Package has been Scanned'
            return JsonResponse(item)
        '''


        order = get_funmart_order(track_code=track_code, order_ref=order_ref,batch_no=batch_no)
        #print("result of get_funmart_order", order)
        if order:

            if order.scanned :
                item['scan_result'] = 'Package has been Scanned'
                return JsonResponse(item)
            else:

                item['scan_result'] = 'Success'
                item['track_code'] =  order.track_code
                item['order_no'] = order.order_no
                item['order_ref'] = order.order_ref
                item['batch_package_count'] = batch_package_count +1

                order.scanner = str(request.user)
                order.scan_time = dt.now()
                order.scanned =True
                order.batch_no = batch_no
                order.save()

        else:
            if order_ref:
                item['scan_result'] = 'order_ref not found'
            else:
                item['scan_result'] = 'Not Found. Input order_ref Search Again'

        return JsonResponse(item)




def preparebatch(request):
    from funmart.tasks import batch_sku

    if request.method == 'GET':
        pass
    elif request.method == 'POST':
        item = {}


        posts = request.POST
        #print(posts)
        batch_no = posts.get('batch_no')

        if not batch_no  :
            item['scan_result'] = 'Please Input Batch_no'
            item['batch_package_count'] = ""
            return JsonResponse(item)

        #汇总包裹信息
        item['scanned_packages_counts'] = FunmartOrder.objects.filter(batch_no=batch_no).count()

        #汇总sku信息
        batch_sku(batch_no)
        batchskus = BatchSKU.objects.filter(batch_no=batch_no)

        # 拼接
        items_list = []
        action_counts = batchskus.values("action").annotate(skus=Count("SKU"), pcs=Sum("quantity"))
        for action_count in action_counts:
            item_info = {
                "action": action_count.get("action"),
                "skus": action_count.get("skus"),
                "pcs": action_count.get("pcs"),


            }
            items_list.append(item_info)

        item["items_info"] = items_list
        #print ("response ",item)
        return JsonResponse(item)

def scanpackageitem(request):


    from funmart.tasks import get_funmart_barcode

    if request.method == 'GET':
        pass
    elif request.method == 'POST':
        item = {}
        item['scan_result'] = ""
        item['track_code'] = ""

        item['order_ref'] = ""




        posts = request.POST
        #print(posts)
        batch_no = posts.get('batch_no')
        track_code = posts.get('track_code')
        barcode = posts.get('barcode')
        item_code = posts.get('item_code')
        SKU = posts.get('SKU')

        if not batch_no  :
            item['scan_result'] = 'Please Input Batch_no'
            item['batch_package_count'] = ""
            return JsonResponse(item)

        batch_package_count = FunmartOrder.objects.filter(batch_no=batch_no).count()
        item['batch_package_count'] = batch_package_count

        if not track_code  :
            item['scan_result'] = 'Please Input track_code'
            return JsonResponse(item)


        try:
            funmartorder = FunmartOrder.objects.get(track_code=track_code)
        except:
            item['scan_result'] = 'Cannot find package with the track_code'
            return JsonResponse(item)


        if not barcode  :
            item['scan_result'] = 'Please Input Barcode'

        elif not item_code and not SKU:
            item['scan_result'] = 'Please Input Item_code'


        else:
            #如果有SKU，就用SKU查，否则就用原来的item_code查
            if SKU:
                try:
                    funmart_sku = FunmartSKU.objects.get(SKU=SKU)
                except:
                    item['scan_result'] = 'SKU not Found'

            else:
                item_code = item_code.replace("－", "-")

                funmartbarcodes = FunmartBarcode.objects.filter(barcode=item_code)
                if not funmartbarcodes:
                    funmartbarcode = get_funmart_barcode(item_code)
                    #print("get from funmart", funmartbarcode)
                else:
                    funmartbarcode = funmartbarcodes[0]

                if not funmartbarcode :
                    item['scan_result'] = 'SKU not Found'
                    return JsonResponse(item)


                funmart_sku  = funmartbarcode.funmart_sku

                #print("get from yallavip", funmartbarcode, funmart_sku)
                SKU = funmart_sku.SKU

            #找到SKU后拼接相应的信息
            try:
                fummartorder_item = FunmartOrderItem.objects.get(track_code=track_code,sku = SKU)
            except:
                item['scan_result'] = 'Item not belong to the package'
                return JsonResponse(item)

            try:
                action = BatchSKU.objects.get(batch_no = batch_no, SKU=SKU).action
                item["action"] = action
            except:
                item['scan_result'] = 'SKU not prepared'
                return JsonResponse(item)

            item["sku"] = SKU

            item["new_barcode"] = barcode
            item["sku_name"] = funmart_sku.name


            item['scan_result'] = 'Success'
            item['scannned_items__count'] = funmartorder.scanned_quantity + 1



            funmartorder.scanned_quantity = F("scanned_quantity") + 1
            funmartorder.save()

            fummartorder_item.item_code = item_code
            fummartorder_item.barcode = barcode
            fummartorder_item.scanned_quantity = F("scanned_quantity") + 1
            fummartorder_item.action = action
            fummartorder_item.batch_no = batch_no

            fummartorder_item.scanner = str(request.user)
            fummartorder_item.scan_time = dt.now()
            fummartorder_item.save()



            yallavip_barcode, created = YallavipBarcode.objects.update_or_create(
                barcode=barcode,
                defaults={
                    'funmart_sku': funmart_sku,
                    'SKU': SKU,

                }
            )

        # 统计包裹摘要


        item['package_items_count'] = funmartorder.quantity

        # 拼接订单明细
        items_list = []
        funmart_items = FunmartOrderItem.objects.filter(track_code=track_code)
        for funmart_item in funmart_items:
            sku_image = json.loads(funmart_item.funmart_sku.images)[0]
            #print(sku_image)

            item_info = {
                "item_code": funmart_item.item_code,
                "SKU": funmart_item.sku,
                "name": funmart_item.category_en,
                "barcode": funmart_item.barcode,
                "quantity": funmart_item.quantity,
                "scanned_quantity": funmart_item.scanned_quantity,
                "action": funmart_item.action,
                "sku_image": sku_image,

            }
            items_list.append(item_info)

        item["items_info"] = items_list

        #print ("response ",item)
        return JsonResponse(item)



def fulfillbag(request):


    if request.method == 'GET':
        pass
    elif request.method == 'POST':
        item = {}

        posts = request.POST
        #print(posts)
        batch_no = posts.get('batch_no')

        if not batch_no  :
            item['scan_result'] = 'Please Input Batch_no'

            return JsonResponse(item)



        # 拼接订单明细
        items_list = []
        funmart_items = FunmartOrderItem.objects.filter(batch_no=batch_no,bag_no=0).values("action").annotate(pcs=Sum("scanned_quantity"))
        for funmart_item in funmart_items:

            item_info = {
                "action": funmart_item.get("action"),
                "unbaged_pcs": funmart_item.get("pcs"),



            }
            items_list.append(item_info)
        item['scan_result'] = 'Success'
        item["items_info"] = items_list





        print ("response ",item)
        return JsonResponse(item)

def packlbag(request):


    if request.method == 'GET':
        pass
    elif request.method == 'POST':
        item = {}

        posts = request.POST
        print(posts)
        batch_no = posts.get('batch_no')

        if not batch_no  :
            item['scan_result'] = 'Please Input Batch_no'

            return JsonResponse(item)





        # 拼接订单明细
        items_list = []
        funmart_items = FunmartOrderItem.objects.filter(batch_no=batch_no,bag_no=0).values("action").annotate(pcs=Sum("scanned_quantity"))
        for funmart_item in funmart_items:

            item_info = {
                "action": funmart_item.get("action"),
                "unbaged_pcs": funmart_item.get("pcs"),



            }
            items_list.append(item_info)
        item['scan_result'] = 'Success'
        item["items_info"] = items_list





        print ("response ",item)
        return JsonResponse(item)

# 1.1.前往 index 页（all）
def all_page(request):

    data = student_info.objects.all()
    content={'data': data}
    return render(request, 'funmart/all.html', content)

# 1.2.前往 add 页
def add_page( request ):
    return render(request, 'funmart/add.html')

# 2.增
@csrf_exempt
def add_student(request):
    t_name = request.POST['tName']
    t_age = request.POST['tAge']
    t_image = request.FILES['tImage']
    fname = os.path.join(settings.MEDIA_ROOT, t_image.name)
    with open(fname, 'wb') as pic:
        for c in t_image.chunks():
            pic.write(c)

    student=student_info()
    student.t_name=t_name
    student.t_age=t_age
    # 存访问路径到数据库
    student.t_image = os.path.join("/static/media/", t_image.name)
    student.save()

    return redirect('/allPage')


# 3.1.查 - name
def search_student(request):
    t_name = request.GET['q']
    student=student_info.objects.filter(t_name=t_name)
    content={'data':student}
    return render(request,'funmart/all.html', content)


#表单
# 1.1.前往 index 页（all）
def demo(request):

    data = student_info.objects.all()
    content={'data': data}
    return render(request, 'funmart/demo.html', content)

def response_data(request):
    data = {"code":0,"msg":"","count":1000,"data":[{"id":10000,"username":"user-0","sex":"女","city":"城市-0","sign":"签名-0","experience":255,"logins":24,"wealth":82830700,"classify":"作家","score":57},{"id":10001,"username":"user-1","sex":"男","city":"城市-1","sign":"签名-1","experience":884,"logins":58,"wealth":64928690,"classify":"词人","score":27},{"id":10002,"username":"user-2","sex":"女","city":"城市-2","sign":"签名-2","experience":650,"logins":77,"wealth":6298078,"classify":"酱油","score":31},{"id":10003,"username":"user-3","sex":"女","city":"城市-3","sign":"签名-3","experience":362,"logins":157,"wealth":37117017,"classify":"诗人","score":68},{"id":10004,"username":"user-4","sex":"男","city":"城市-4","sign":"签名-4","experience":807,"logins":51,"wealth":76263262,"classify":"作家","score":6},{"id":10005,"username":"user-5","sex":"女","city":"城市-5","sign":"签名-5","experience":173,"logins":68,"wealth":60344147,"classify":"作家","score":87},{"id":10006,"username":"user-6","sex":"女","city":"城市-6","sign":"签名-6","experience":982,"logins":37,"wealth":57768166,"classify":"作家","score":34},{"id":10007,"username":"user-7","sex":"男","city":"城市-7","sign":"签名-7","experience":727,"logins":150,"wealth":82030578,"classify":"作家","score":28},{"id":10008,"username":"user-8","sex":"男","city":"城市-8","sign":"签名-8","experience":951,"logins":133,"wealth":16503371,"classify":"词人","score":14},{"id":10009,"username":"user-9","sex":"女","city":"城市-9","sign":"签名-9","experience":484,"logins":25,"wealth":86801934,"classify":"词人","score":75},{"id":10010,"username":"user-10","sex":"女","city":"城市-10","sign":"签名-10","experience":1016,"logins":182,"wealth":71294671,"classify":"诗人","score":34},{"id":10011,"username":"user-11","sex":"女","city":"城市-11","sign":"签名-11","experience":492,"logins":107,"wealth":8062783,"classify":"诗人","score":6},{"id":10012,"username":"user-12","sex":"女","city":"城市-12","sign":"签名-12","experience":106,"logins":176,"wealth":42622704,"classify":"词人","score":54},{"id":10013,"username":"user-13","sex":"男","city":"城市-13","sign":"签名-13","experience":1047,"logins":94,"wealth":59508583,"classify":"诗人","score":63},{"id":10014,"username":"user-14","sex":"男","city":"城市-14","sign":"签名-14","experience":873,"logins":116,"wealth":72549912,"classify":"词人","score":8},{"id":10015,"username":"user-15","sex":"女","city":"城市-15","sign":"签名-15","experience":1068,"logins":27,"wealth":52737025,"classify":"作家","score":28},{"id":10016,"username":"user-16","sex":"女","city":"城市-16","sign":"签名-16","experience":862,"logins":168,"wealth":37069775,"classify":"酱油","score":86},{"id":10017,"username":"user-17","sex":"女","city":"城市-17","sign":"签名-17","experience":1060,"logins":187,"wealth":66099525,"classify":"作家","score":69},{"id":10018,"username":"user-18","sex":"女","city":"城市-18","sign":"签名-18","experience":866,"logins":88,"wealth":81722326,"classify":"词人","score":74},{"id":10019,"username":"user-19","sex":"女","city":"城市-19","sign":"签名-19","experience":682,"logins":106,"wealth":68647362,"classify":"词人","score":51},{"id":10020,"username":"user-20","sex":"男","city":"城市-20","sign":"签名-20","experience":770,"logins":24,"wealth":92420248,"classify":"诗人","score":87},{"id":10021,"username":"user-21","sex":"男","city":"城市-21","sign":"签名-21","experience":184,"logins":131,"wealth":71566045,"classify":"词人","score":99},{"id":10022,"username":"user-22","sex":"男","city":"城市-22","sign":"签名-22","experience":739,"logins":152,"wealth":60907929,"classify":"作家","score":18},{"id":10023,"username":"user-23","sex":"女","city":"城市-23","sign":"签名-23","experience":127,"logins":82,"wealth":14765943,"classify":"作家","score":30},{"id":10024,"username":"user-24","sex":"女","city":"城市-24","sign":"签名-24","experience":212,"logins":133,"wealth":59011052,"classify":"词人","score":76},{"id":10025,"username":"user-25","sex":"女","city":"城市-25","sign":"签名-25","experience":938,"logins":182,"wealth":91183097,"classify":"作家","score":69},{"id":10026,"username":"user-26","sex":"男","city":"城市-26","sign":"签名-26","experience":978,"logins":7,"wealth":48008413,"classify":"作家","score":65},{"id":10027,"username":"user-27","sex":"女","city":"城市-27","sign":"签名-27","experience":371,"logins":44,"wealth":64419691,"classify":"诗人","score":60},{"id":10028,"username":"user-28","sex":"女","city":"城市-28","sign":"签名-28","experience":977,"logins":21,"wealth":75935022,"classify":"作家","score":37},{"id":10029,"username":"user-29","sex":"男","city":"城市-29","sign":"签名-29","experience":647,"logins":107,"wealth":97450636,"classify":"酱油","score":27}]}
    return HttpResponse(json.dumps(data), content_type="application/json")

