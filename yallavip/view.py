from django.http import HttpResponse
from django.shortcuts import render

def hello(request):
    if request.method == "GET":
        response = request.GET.get('response')
        print("从前台返回的结果",response)
        result = "OK!"
        return HttpResponse(result)


