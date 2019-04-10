
from django.shortcuts import render
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from django.views import View
from django.utils import timezone as dt
import requests

def get_token(short_lived_token):
    app_id = "1976935359278305"
    app_secret = "f4ee797596ed236c0bc74d33f52e6a54"

    #url = "https://graph.facebook.com/v3.2/{}?fields=access_token".format(target_page)
    url = "https://graph.facebook.com/v3.2/oauth/access_token?grant_type=fb_exchange_token" \
          "&client_id=%s&client_secret=%s&fb_exchange_token=%s"%(app_id,app_secret ,short_lived_token)
    #param = dict()
    #param["access_token"] = my_access_token

    #r = requests.get(url, param)
    r = requests.get(url)

    data = json.loads(r.text)

    # print("request response is ", data["access_token"])
    return data["access_token"]

class Hello(View):
    def get(self, request):
        print(request.method)
        return render(request, "hello.html")

    #@csrf_exempt
    def post(self, request):
        data = request.POST

        token = data.get('token')

        long_token = get_token(token)
        user_name = data.get('user_name')
        user_no = data.get('user_id')


        obj, created = Token.objects.update_or_create(
            user_no=user_no,
            defaults={
                'user_name': user_name,
                'long_token': long_token,
                'update_at': dt.now(),
                'active': True

            },

        )

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