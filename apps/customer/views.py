from django.shortcuts import render
from rest_framework import mixins, viewsets, status
from rest_framework.permissions import IsAuthenticated
from utils.permissions import IsOwnerOrReadOnly
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.authentication import SessionAuthentication

from .serializers import CustomerSerializer, CustomerDetailSerializer, \
                        CustomerFavSerializer, CustomerFavListSerializer,\
                        CustomerCartSerializer, CustomerCartListSerializer,\
                        ReceiverSerializer
from .models import Customer, CustomerFav, CustomerCart, Receiver, CITY

from rest_framework.response import Response
from rest_framework import mixins, viewsets
from rest_framework import generics

from rest_framework.pagination import PageNumberPagination
from .filters import CustomerFavFilter, CustomerCartFilter, ReceiverFilter
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from rest_framework.authentication import TokenAuthentication
# Create your views here.


class CustomerViewSet(mixins.ListModelMixin,mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    """
    create:
        创建用户

    retrieve:
        显示用户详情
    """

    serializer_class = CustomerSerializer
    queryset = Customer.objects.all().order_by('id')
    '''
    #authentication_classes = (SessionAuthentication, JWTAuthentication)  # 自定义VieSet认证方式：JWT用于前端登录认证，Session用于方便在DRF中调试使用
    def get_permissions(self):
        """
        动态设置不同action不同的权限类列表
        """
        if self.action == 'retrieve':
            return [permissions.IsAuthenticated()]  # 一定要加()表明返回它的实例
        elif self.action == 'create':
            return []
        else:
            return []

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = self.perform_create(serializer)

        # 添加自己的逻辑，通过user，生成token并返回
        refresh = RefreshToken.for_user(user)
        tokens_for_user = {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            # 数据定制化
            'username': user.username,  # 由于前端也需要传入username，需要将其加上。cookie.setCookie('name', response.data.username, 7);
        }

        headers = self.get_success_headers(serializer.data)
        return Response(tokens_for_user, status=status.HTTP_201_CREATED, headers=headers)

    def perform_create(self, serializer):
        return serializer.save()

    
    def get_object(self):
        # 获取操作的对象，在RetrieveModelMixin和DestroyModelMixin都需要用到
        return self.request.user
    '''

    # serializer_class = UserSerializer
    def get_serializer_class(self):
        """
        不同的action使用不同的序列化
        :return:
        """
        if self.action == 'retrieve':
            return CustomerDetailSerializer  # 使用显示用户详情的序列化类。这儿就直接返回类名，不需要实例化
        elif self.action == 'create':
            return UserSerializer  # 使用原来的序列化类，创建用户专用
        else:
            return CustomerDetailSerializer

class CustomerFavViewSet(mixins.CreateModelMixin, mixins.DestroyModelMixin, mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    """
    create:
        用户收藏商品

    destroy:
        取消收藏商品

    list:
        显示收藏商品列表

    retrieve:
        根据商品id显示收藏详情
    """
    queryset = CustomerFav.objects.all()

    filter_backends = (DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter)

    # 设置filter的类为我们自定义的类
    filter_class = CustomerFavFilter
    # 搜索,=name表示精确搜索，也可以使用各种正则表达式
    # authentication_classes = (TokenAuthentication,)  # 只在本视图中验证Token
    search_fields = ('conversation__customer')


    # serializer_class = UserFavSerializer
    def get_serializer_class(self):
        """
        不同的action使用不同的序列化
        :return:
        """

        if self.action == 'list':
            return CustomerFavListSerializer  # 显示用户收藏列表序列化
        else:
            return CustomerFavSerializer


    permission_classes = (IsAuthenticated, IsOwnerOrReadOnly)
    authentication_classes = (JWTAuthentication, SessionAuthentication)  # 配置登录认证：支持JWT认证和DRF基本认证
    #lookup_field = 'goods_id'



    def get_queryset(self):
        # 过滤当前用户的收藏记录
        return self.queryset.filter(user=self.request.user)


class CustomerCartViewSet(mixins.CreateModelMixin, mixins.DestroyModelMixin, mixins.ListModelMixin, mixins.RetrieveModelMixin,mixins.UpdateModelMixin, viewsets.GenericViewSet):
    """
    create:
        用户购物车商品

    destroy:
        取消购物车商品

    list:
        显示购物车商品列表

    retrieve:
        根据商品id显示购物车详情
    """
    queryset = CustomerCart.objects.all()

    filter_backends = (DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter)

    # 设置filter的类为我们自定义的类
    filter_class = CustomerCartFilter
    # 搜索,=name表示精确搜索，也可以使用各种正则表达式
    # authentication_classes = (TokenAuthentication,)  # 只在本视图中验证Token
    search_fields = ('conversation__customer')



    def get_serializer_class(self):
        """
        不同的action使用不同的序列化
        :return:
        """

        if self.action == 'list':
            return CustomerCartListSerializer  # 显示用户收藏列表序列化
        else:
            return CustomerCartSerializer


    permission_classes = (IsAuthenticated, IsOwnerOrReadOnly)
    authentication_classes = (JWTAuthentication, SessionAuthentication)  # 配置登录认证：支持JWT认证和DRF基本认证
    #lookup_field = 'goods_id'



    def get_queryset(self):
        # 过滤当前用户的购物车记录
        return self.queryset.filter(user=self.request.user)


from django.views.generic import View
from django.db import transaction   # 导入事务
from django.http import JsonResponse

class OrderCommitView(View):
    """乐观锁"""
    # 开启事务装饰器
    @transaction.atomic
    def post(self,request):
        """订单并发 ———— 乐观锁"""
        # 拿到id
        goods_ids = request.POST.get('goods_ids')
        print("hello", request, request.POST)
        return JsonResponse({'res': 0, 'errmsg': goods_ids})


        if len(goods_ids) == 0 :
            return JsonResponse({'res':0,'errmsg':'数据不完整'})
        # 当前时间字符串
        now_str = datetime.now().strftime('%Y%m%d%H%M%S')
        # 订单编号
        order_id = now_str + str(request.user.id)
        # 地址
        pay_method = request.POST.get('pay_method')
        # 支付方式
        address_id = request.POST.get('address_id')
        try:
            address = Address.objects.get(id=address_id)
        except Address.DoesNotExist:
            return JsonResponse({'res':1,'errmsg':'地址错误'})


        # 商品数量
        total_count = 0
        # 商品总价
        total_amount = 0
        # 订单运费
        transit_price = 10


        # 创建保存点
        sid = transaction.savepoint()


        order_info = OrderInfo.objects.create(
            order_id = order_id,
            user = request.user,
            addr = address,
            pay_method = pay_method,
            total_count = total_count,
            total_price = total_amount,
            transit_price = transit_price
        )
        # 获取redis连接
        goods = get_redis_goodsection('default')
        # 拼接key
        cart_key = 'cart_%d' % request.user.id

        for goods_id in goods_ids:
            # 尝试查询商品
            # 此处考虑订单并发问题,


            # redis中取出商品数量
            count = goods.hget(cart_key, goods_id)
            if count is None:
                # 回滚到保存点
                transaction.savepoint_rollback(sid)
                return JsonResponse({'res': 3, 'errmsg': '商品不在购物车中'})
            count = int(count)

            for i in range(3):
                # 若存在订单并发则尝试下单三次
                try:

                    goods = Goodsgoods.objects.get(id=goods_id)  # 不加锁查询
                    # goods = Goodsgoods.objects.select_for_update().get(id=goods_id)  # 加互斥锁查询
                except Goodsgoods.DoesNotExist:
                    # 回滚到保存点
                    transaction.savepoint_rollback(sid)
                    return JsonResponse({'res':2,'errmsg':'商品信息错误'})

                origin_stock = goods.stock
                print(origin_stock, 'stock')
                print(goods.id, 'id')

                if origin_stock < count:


                    # 回滚到保存点
                    transaction.savepoint_rollback(sid)
                    return JsonResponse({'res':4,'errmsg':'库存不足'})


                # # 商品销量增加
                # goods.sales += count
                # # 商品库存减少
                # goods.stock -= count
                # # 保存到数据库
                # goods.save()

                # 如果下单成功后的库存
                new_stock = goods.stock - count
                new_sales = goods.sales + count

                res = Goodsgoods.objects.filter(stock=origin_stock,id=goods_id).update(stock=new_stock,sales=new_sales)
                print(res)
                if res == 0:
                    if i == 2:
                        # 回滚
                        transaction.savepoint_rollback(sid)
                        return JsonResponse({'res':5,'errmsg':'下单失败'})
                    continue
                else:
                    break

            OrderGoods.objects.create(
                order = order_info,
                goods = goods,
                count = count,
                price = goods.price
            )

            # 删除购物车中记录
            goods.hdel(cart_key,goods_id)
            # 累加商品件数
            total_count += count
            # 累加商品总价
            total_amount += (goods.price) * count

        # 更新订单信息中的商品总件数
        order_info.total_count = total_count
        # 更新订单信息中的总价格
        order_info.total_price = total_amount + order_info.transit_price
        order_info.save()

        # 事务提交
        transaction.savepoint_commit(sid)

        return JsonResponse({'res':6,'errmsg':'订单创建成功'})


class ReceiverViewSet(mixins.CreateModelMixin, mixins.DestroyModelMixin, mixins.ListModelMixin, mixins.RetrieveModelMixin,mixins.UpdateModelMixin, viewsets.GenericViewSet):
    """
    create:
        用户购物车商品

    destroy:
        取消购物车商品

    list:
        显示购物车商品列表

    retrieve:
        根据商品id显示购物车详情
    """
    queryset = Receiver.objects.all()
    serializer_class = ReceiverSerializer
    filter_backends = (DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter)

    # 设置filter的类为我们自定义的类
    filter_class = ReceiverFilter
    # 搜索,=name表示精确搜索，也可以使用各种正则表达式
    # authentication_classes = (TokenAuthentication,)  # 只在本视图中验证Token
    search_fields = ()


    permission_classes = (IsAuthenticated, IsOwnerOrReadOnly)
    authentication_classes = (JWTAuthentication, SessionAuthentication)  # 配置登录认证：支持JWT认证和DRF基本认证
    #lookup_field = 'id'

    def get_queryset(self):
        # 过滤当前用户的购物车记录
        return self.queryset.filter(user=self.request.user)


def get_cities(request):
    print(CITY)
    return JsonResponse(CITY, safe=False)
