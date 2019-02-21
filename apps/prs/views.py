from django.shortcuts import render
from xadmin.views import BaseAdminView
from django.http import JsonResponse
from fb.models import  MyAlbum
# Create your views here.


#导入serializers
from django.core import serializers
# 二级联动View函数
class SelectView(BaseAdminView):
    def get(self, request):
        # 通过get得到父级选择项
        page_id = request.GET.get('module', '')

        # 筛选出符合父级要求的所有子级，因为输出的是一个集合，需要将数据序列化 serializers.serialize（）
        albums = serializers.serialize("json", MyAlbum.objects.filter( mypage__pk=int(page_id) ))
        # 判断是否存在，输出
        if albums:

            return JsonResponse({'album': albums})

