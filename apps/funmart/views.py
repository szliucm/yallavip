from django.shortcuts import render
from django.http import HttpResponse, JsonResponse

# Create your views here.
from xadmin.views import BaseAdminView
class testView(BaseAdminView):
	template_name = 'index.html'

	def get(self, request, *args, **kwargs):
		data = 'test'
		return render(request, self.template_name, {'data': data})


def index(request):
    return render(request, 'index.html')


def add(request):
    a = request.GET['a']
    b = request.GET['b']
    a = int(a)
    b = int(b)
    return HttpResponse(str(a+b))


import json

def ajax_list(request):
    a = list(range(100))
    return HttpResponse(json.dumps(a), content_type='application/json')

def ajax_dict(request):
    name_dict = {'twz': 'Love python and Django', 'zqxt': 'I am teaching Django'}
    return HttpResponse(json.dumps(name_dict), content_type='application/json')

