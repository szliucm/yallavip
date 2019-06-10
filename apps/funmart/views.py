from django.db.models import Count, Sum, Q, F
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
# Create your views here.
from xadmin.views import BaseAdminView

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
        print(posts)
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
        print ("response ",item)
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
        print(posts)
        batch_no = posts.get('batch_no')
        track_code = posts.get('track_code')
        barcode = posts.get('barcode')
        item_code = posts.get('item_code')
        if not batch_no  :
            item['scan_result'] = 'Please Input Batch_no'
            item['batch_package_count'] = ""
            return JsonResponse(item)

        batch_package_count = FunmartOrder.objects.filter(batch_no=batch_no).count()
        item['batch_package_count'] = batch_package_count

        if not track_code  :
            item['scan_result'] = 'Please Input track_code'
            return JsonResponse(item)



        #统计包裹摘要
        try:
            funmartorder = FunmartOrder.objects.get(track_code=track_code)
        except:
            item['scan_result'] = 'Cannot find package with the track_code'
            return JsonResponse(item)

        item['package_items_count'] = funmartorder.quantity

        # 拼接订单明细
        items_list = []
        funmart_items = FunmartOrderItem.objects.filter(track_code=track_code)
        for funmart_item in funmart_items:
            item_info = {
                "item_code": funmart_item.item_code,
                "SKU": funmart_item.sku,
                "name": funmart_item.category_en,
                "barcode": funmart_item.barcode,
                "quantity": funmart_item.quantity,
                "scanned_quantity": funmart_item.scanned_quantity,
                "action": funmart_item.action,

            }
            items_list.append(item_info)

        item["items_info"] = items_list

        if not barcode  :
            item['scan_result'] = 'Please Input Barcode'
            return JsonResponse(item)

        if not item_code :
            item['scan_result'] = 'Please Input Item_code'
            return JsonResponse(item)


        item_code = item_code.replace("－", "-")

        funmartbarcodes = FunmartBarcode.objects.filter(barcode=item_code)
        if not funmartbarcodes:
            funmartbarcode = get_funmart_barcode(item_code)
            print("get from funmart", funmartbarcode)
        else:
            funmartbarcode = funmartbarcodes[0]

        if not funmartbarcode :
            item['scan_result'] = 'SKU not Found'
            return JsonResponse(item)


        funmart_sku  = funmartbarcode.funmart_sku
        print("get from yallavip", funmartbarcode, funmart_sku)


        try:
            fummartorder_item = FunmartOrderItem.objects.get(track_code=track_code,sku = funmartbarcode.SKU)
        except:
            item['scan_result'] = 'Item not belong to the package'
            return JsonResponse(item)

        try:
            action = BatchSKU.objects.get(batch_no = batch_no, SKU=funmart_sku.SKU).action
            item["action"] = action
        except:
            item['scan_result'] = 'SKU not prepared'
            return JsonResponse(item)

        item["sku"] = funmart_sku.SKU

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

        fummartorder_item.save()


        yallavip_barcode, created = YallavipBarcode.objects.update_or_create(
            barcode=barcode,
            defaults={
                'funmart_sku': funmart_sku,
                'SKU': funmart_sku.SKU,

            }
        )



        print ("response ",item)
        return JsonResponse(item)

def scanitem(request):


    from funmart.tasks import get_funmart_barcode

    if request.method == 'GET':
        pass
    elif request.method == 'POST':
        item = {}
        item['scan_result'] = ""
        item['track_code'] = ""

        item['order_ref'] = ""




        posts = request.POST
        print(posts)
        batch_no = posts.get('batch_no')
        track_code = posts.get('track_code')

        item_code = posts.get('item_code')
        if not batch_no  :
            item['scan_result'] = 'Please Input Batch_no'
            item['batch_package_count'] = ""
            return JsonResponse(item)

        batch_package_count = FunmartOrder.objects.filter(batch_no=batch_no).count()
        item['batch_package_count'] = batch_package_count

        if not track_code  :
            item['scan_result'] = 'Please Input track_code'
            return JsonResponse(item)

        #统计包裹摘要
        try:
            funmartorder = FunmartOrder.objects.get(track_code=track_code)
        except:
            item['scan_result'] = 'Cannot find package with the track_code'
            return JsonResponse(item)

        item['package_items_count'] = funmartorder.quantity

        # 拼接订单明细
        items_list = []
        funmart_items = FunmartOrderItem.objects.filter(track_code=track_code)
        for funmart_item in funmart_items:
            item_info = {
                "item_code": funmart_item.item_code,
                "SKU": funmart_item.sku,
                "name": funmart_item.category_en,
                "barcode": funmart_item.barcode,
                "quantity": funmart_item.quantity,
                "scanned_quantity": funmart_item.scanned_quantity,
                "action": funmart_item.action,

            }
            items_list.append(item_info)

        item["items_info"] = items_list

        if not item_code :
            item['scan_result'] = 'Please Input Item_code'
            return JsonResponse(item)


        item_code = item_code.replace("－", "-")

        funmartbarcodes = FunmartBarcode.objects.filter(barcode=item_code)
        if not funmartbarcodes:
            funmartbarcode = get_funmart_barcode(item_code)
            print("get from funmart", funmartbarcode)
        else:
            funmartbarcode = funmartbarcodes[0]

        if not funmartbarcode :
            item['scan_result'] = 'SKU not Found'
            return JsonResponse(item)


        funmart_sku  = funmartbarcode.funmart_sku
        print("get from yallavip", funmartbarcode, funmart_sku)


        try:
            fummartorder_item = FunmartOrderItem.objects.get(track_code=track_code,sku = funmartbarcode.SKU)
        except:
            item['scan_result'] = 'Item not belong to the package'
            return JsonResponse(item)

        try:
            action = BatchSKU.objects.get(batch_no = batch_no, SKU=funmart_sku.SKU).action
            item["action"] = action
        except:
            item['scan_result'] = 'SKU not prepared'
            return JsonResponse(item)

        item["sku"] = funmart_sku.SKU

        SKU = str(funmart_sku.id).zfill(9)
        barcode = SKU[:5] + '-' + SKU[5:]
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

        fummartorder_item.save()



        print ("response ",item)
        return JsonResponse(item)

def fulfillbag(request):


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
