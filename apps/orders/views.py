from django.shortcuts import render
from rest_framework import mixins, viewsets, status
from rest_framework.permissions import IsAuthenticated
from utils.permissions import IsOwnerOrReadOnly
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.authentication import SessionAuthentication

from .serializers import OrderSerializer, OrderListSerializer
from .models import Order,OrderDetail
from customer.models import CustomerCart
from prs.models import Lightin_SKU

from rest_framework.response import Response
from rest_framework import mixins, viewsets
from rest_framework import generics

from rest_framework.pagination import PageNumberPagination

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from rest_framework.authentication import TokenAuthentication

from django.db import transaction   # 导入事务

from django.core.exceptions import ValidationError

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
    queryset = Order.objects.all().order_by('-id')

    #serializer_class = OrderSerializer  # 添加序列化
    def get_serializer_class(self):
        """
        不同的action使用不同的序列化
        :return:
        """
        print("########", self.action)
        if self.action == 'retrieve':
            return OrderSerializer
        else:
            return OrderListSerializer

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user)

    #@transaction.atomic
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        # 验证合法
        serializer.is_valid(raise_exception=True)

        order = self.perform_create(serializer)

        re_dict = serializer.data
        headers = self.get_success_headers(serializer.data)
        return Response(re_dict, status=status.HTTP_201_CREATED, headers=headers)

    def perform_create(self, serializer):
        return serializer.save()

        '''
        sms_status =0
        if sms_status != 0:
            return Response("我不滚", status=status.HTTP_400_BAD_REQUEST)
        else:

            return Response("滚吧", status=status.HTTP_201_CREATED)
        
    def perform_create(self, serializer):
        # 完成创建后保存到数据库，可以拿到保存的OrderInfo对象
        print("perform_create")
        #
        # 创建保存点
        #sid = transaction.savepoint()

        # 商品数量
        total_count = 0
        # 商品总价
        total_amount = 0
        order = serializer.save()

        customer_carts = CustomerCart.objects.filter(conversation=order.conversation)
        # 将该用户购物车所有商品都取出来放在订单商品中

        for customer_cart in customer_carts:
            # 尝试查询商品
            # 此处考虑订单并发问题,

            try:
                goods = Lightin_SKU.objects.get(id=customer_cart.sku.id)  # 不加锁查询
                #goods = Lightin_SKU.objects.select_for_update().get(id=customer_cart.sku.id)  # 加互斥锁查询

            except Lightin_SKU.DoesNotExist:
                # 回滚到保存点

                transaction.rollback(sid)
                return JsonResponse({'res': 2, 'errmsg': '商品信息错误'})


            # 取出商品数量

            count = customer_cart.quantity

            if goods.stock < count:
                # 回滚到保存点
                print("我要滚啦----------1")
                #transaction.savepoint_rollback(sid)
                print("我要滚啦----------2")
                handler500 = 'rest_framework.exceptions.server_error'
                raise ValidationError(
                            "快滚吧",code="come_on"
                    )# 要传递到错误信息的参数)


            print("我要滚啦！")

            # 商品销量增加
            goods.sales += count
            # 商品库存减少
            goods.stock -= count
            # 保存到数据库
            goods.save()

            OrderDetail.objects.create(
                order=order,
                F_SKU=goods,
                product_quantity=count,
                price=goods.price
            )

            # 累加商品件数
            total_count += count
            # 累加商品总价
            total_amount += (goods.price) * count

            # 更新订单信息中的商品总件数
        order.order_quantity = total_count
        # 更新订单信息中的总价格
        order.order_amount = total_amount
        order.save()

        # 事务提交
        transaction.commit()

        # 然后清空该用户购物车
        customer_carts.delete()
        '''


