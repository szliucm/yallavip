# -*- coding: utf-8 -*-
from django.shortcuts import render
from rest_framework import mixins, viewsets, status
from rest_framework.permissions import IsAuthenticated
from utils.permissions import IsOwnerOrReadOnly
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.authentication import SessionAuthentication

from xadmin.views import BaseAdminView
from django.http import JsonResponse
from fb.models import  MyAlbum
from .serializers import SpusSerializer, CategorySerializer
from .models import Lightin_SPU, Lightin_SKU, MyCategory
from .filters import SpusFilter
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from rest_framework.pagination import PageNumberPagination
from rest_framework.decorators import action
from django.http import HttpResponse, JsonResponse
from rest_framework.response import Response
# Create your views here.


# 导入serializers
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

class SpusPagination(PageNumberPagination):
    '''
    商品列表自定义分页
    '''
    #默认每页显示的个数
    page_size = 12
    #可以动态改变每页显示的个数
    page_size_query_param = 'page_size'
    #页码参数
    page_query_param = 'page'
    #最多能显示多少页
    max_page_size = 100

class SpusListViewSet(mixins.ListModelMixin,mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    '商品列表页'
    pagination_class = SpusPagination  # 分页
    permission_classes = (IsAuthenticated, IsOwnerOrReadOnly)
    authentication_classes = (JWTAuthentication, SessionAuthentication)  # 配置登录认证：支持JWT认证和DRF基本认证

    # 这里必须要定义一个默认的排序,否则会报错
    queryset = Lightin_SPU.objects.filter(sellable__gt=0).order_by('handle')
    # 分页
    #pagination_class = GoodsPagination

    serializer_class = SpusSerializer
    filter_backends = (DjangoFilterBackend,filters.SearchFilter,filters.OrderingFilter)
    filterset_fields = ('handle',)
    # 设置filter的类为我们自定义的类
    filter_class = SpusFilter
    # 搜索,=name表示精确搜索，也可以使用各种正则表达式

    search_fields = ('handle')
    # 排序
    ordering_fields = ('handle')

    #
    # detail为False 表示不需要处理具体的对象
    @action(methods=['get'], detail=False)
    def attrs(self, request):
        """
        返回按sizes和colors,给选择用
        """
        queryset = self.filter_queryset(self.get_queryset())
        print("当前数据集", queryset.count())
        spus_list = list(queryset.values_list("id", flat=True).distinct())

        sizes_list = Lightin_SKU.objects.filter(lightin_spu__id__in=spus_list).values_list("size", flat=True).distinct()
        #sizes_list = self.queryset.values_list("size", flat=True).distinct()
        return JsonResponse(list(sizes_list), safe=False)


class CategoryViewSet(mixins.ListModelMixin,mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    '商品列表页'

    permission_classes = (IsAuthenticated, IsOwnerOrReadOnly)
    authentication_classes = (JWTAuthentication, SessionAuthentication)  # 配置登录认证：支持JWT认证和DRF基本认证

    # 这里必须要定义一个默认的排序,否则会报错
    queryset = MyCategory.objects.filter(level=1).order_by('name')
    # 分页
    #pagination_class = GoodsPagination

    serializer_class = CategorySerializer
    #filter_backends = (DjangoFilterBackend,filters.SearchFilter,filters.OrderingFilter)
    filterset_fields = ()
    # 设置filter的类为我们自定义的类
    #filter_class = SpusFilter
    # 搜索,=name表示精确搜索，也可以使用各种正则表达式

    #search_fields = ('handle')
    # 排序
    #ordering_fields = ('handle')

