from django.shortcuts import render
from rest_framework import mixins, viewsets, status
from rest_framework.permissions import IsAuthenticated
from utils.permissions import IsOwnerOrReadOnly
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.authentication import SessionAuthentication

from .serializers import OrderSerializer, OrderListSerializer
from .models import Order,OrderDetail
from customer.models import CustomerCart

from rest_framework.response import Response
from rest_framework import mixins, viewsets
from rest_framework import generics

from rest_framework.pagination import PageNumberPagination

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from rest_framework.authentication import TokenAuthentication
# Create your views here.


class OrderViewSet(mixins.ListModelMixin, mixins.CreateModelMixin, mixins.RetrieveModelMixin,mixins.DestroyModelMixin, viewsets.GenericViewSet):
    """
    订单管理
    list:
        获取个人订单
    create:
        新建订单
    delete:
        删除订单
    detail:
        订单详情
    """
    permission_classes = (IsAuthenticated, IsOwnerOrReadOnly)  # 用户必须登录才能访问
    authentication_classes = (JWTAuthentication, SessionAuthentication)  # 配置登录认证：支持JWT认证和DRF基本认证
    queryset = Order.objects.all()

    #serializer_class = OrderSerializer  # 添加序列化
    def get_serializer_class(self):
        """
        不同的action使用不同的序列化
        :return:
        """

        if self.action == 'list':
            return OrderListSerializer
        else:
            return OrderSerializer

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user)

    def perform_create(self, serializer):
        # 完成创建后保存到数据库，可以拿到保存的OrderInfo对象
        print("perform_create")
        order = serializer.save()

        customer_carts = CustomerCart.objects.filter(conversation=order.conversation)
        # 将该用户购物车所有商品都取出来放在订单商品中

        for customer_cart in customer_carts:
            OrderDetail.objects.create(
                order=order,
                #F_SKU=customer_cart.sku,
                product_quantity=customer_cart.quantity,
                price=customer_cart.price,


            )
        # 然后清空该用户购物车
        customer_carts.delete()



