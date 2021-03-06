from django.shortcuts import render
from rest_framework import mixins, viewsets, status
from rest_framework.permissions import IsAuthenticated
from utils.permissions import IsOwnerOrReadOnly
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.authentication import SessionAuthentication

from xadmin.views import BaseAdminView
from django.http import JsonResponse
from fb.models import  MyAlbum
from .serializers import SpusSerializer
from .models import Lightin_SPU
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters

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

class SpusListViewSet(mixins.ListModelMixin,mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    '商品列表页'

    permission_classes = (IsAuthenticated, IsOwnerOrReadOnly)
    authentication_classes = (JWTAuthentication, SessionAuthentication)  # 配置登录认证：支持JWT认证和DRF基本认证

    # 这里必须要定义一个默认的排序,否则会报错
    queryset = Lightin_SPU.objects.all().order_by('handle')
    # 分页
    #pagination_class = GoodsPagination

    serializer_class = SpusSerializer
    filter_backends = (DjangoFilterBackend,filters.SearchFilter,filters.OrderingFilter)
    filterset_fields = ('handle',)
    # 设置filter的类为我们自定义的类
    #filter_class = SpusFilter
    # 搜索,=name表示精确搜索，也可以使用各种正则表达式

    search_fields = ('handle')
    # 排序
    ordering_fields = ('handle')

