from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
# Create your views here.
from xadmin.views import BaseAdminView


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
        posts = request.POST
        print(posts)
        batch_no = posts.get('batch_no')
        if batch_no == "":
            item['track_code'] = 'Please Input Batch_no'

        else:
            track_code = posts.get('track_code')
            order_no = posts.get('order_no')

            order, orderitem_list = get_funmart_order(track_code, order_no,batch_no)
            if order:
                item['track_code'] =  order.track_code
                item['order_no'] = order.order_no

            else:
                if track_code:
                    item['track_code'] =  'Not Found!'
                    item['order_no'] = ''
                else:
                    item['track_code'] = ''
                    item['order_no'] = 'Not Found!'

        return JsonResponse(item)

def scanpackageitem(request):
    from funmart.tasks import get_funmart_sku
    if request.method == 'GET':
        pass
    elif request.method == 'POST':
        item = {}
        posts = request.POST
        print(posts)
        item_code = posts.get('item_code')
        if item_code == "":
            item['item_code'] = 'Please Input Item_no'

        else:

            get_funmart_sku(item_code)
            item['track_code'] = "aaa"
            item['order_no'] = "bbbb"
            item['barcode'] = "01234566789"
            '''
            if order:
                item['track_code'] =  "aaa"
                item['order_no'] = "bbbb"

            else:
                if track_code:
                    item['track_code'] =  'Not Found!'
                    item['order_no'] = ''
                else:
                    item['track_code'] = ''
                    item['order_no'] = 'Not Found!'
                    '''

        return JsonResponse(item)