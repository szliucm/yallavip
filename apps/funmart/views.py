from django.shortcuts import render
from django.http import HttpResponse

# Create your views here.
from xadmin.views import BaseAdminView
class testView(BaseAdminView):
	template_name = 'test.html'
	def get(self, request, *args, **kwargs):
		data = 'test'
		return render(request, self.template_name, {'data': data})


def demo_ajax(request):
    print ("i'm here demo_ajax")
    return render(request, 'demo_ajax.html')

def demo_add(request):
    print("i'm here, demo_add")
    a=request.GET['a']
    b=request.GET['b']

    if request.is_ajax():
        ajax_string = 'ajax request: '
    else:
        ajax_string = 'not ajax request: '

    c = int(a) + int(b)
    r = HttpResponse(ajax_string + str(c))
    return r
