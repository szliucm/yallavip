
from django.shortcuts import render
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from django.views import View
class Hello(View):
    def get(self, request):
        print(request.method)
        return render(request, "hello.html")

    #@csrf_exempt
    def post(self, request):
        data = request.POST

        token = data.get('token')
        print(token)
        response_data = {}
        response_data['result'] = 's'
        response_data['message'] = "登录成功啦！"
        return JsonResponse(response_data)





'''
from django.shortcuts import render


def p1(request):
    return render(request,"p1.html")

def p2(request):
    if request.method == "GET":
        return render(request,"p2.html")
    elif request.method == "POST":
        city =request.POST.get("city")
        print(city)
        return render(request,"popup_response.html",{"city":city})
'''