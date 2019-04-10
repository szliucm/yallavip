from django.http import HttpResponse
from django.shortcuts import render

def hello(request):
    if request.method == "GET":
        name = request.GET.get('domain_name')
        print name
        result = "OK!"
        return HttpResponse(result)


