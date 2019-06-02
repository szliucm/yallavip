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

def get_package_info(request):

    track_code = request.POST['track_code']
    order_no = request.POST['order_no']
    item ={}
    order, orderitem_list = get_funmart_order(track_code, order_no)
    if order:
        item['track_code'] =  order.track_code
        item['order_no'] = order.order_no

    else:
        item['track_code'] =  'Not Found!'
        item['order_no'] = 'Not Found!'

    return JsonResponse(item)