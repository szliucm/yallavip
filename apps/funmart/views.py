from django.shortcuts import render

# Create your views here.
from xadmin.views import BaseAdminView
class testView(BaseAdminView):
	template_name = 'test.html'
	def get(self, request, *args, **kwargs):
		data = 'test'
		return render(request, self.template_name, {'data': data})

