from django.shortcuts import render
from rest_framework import mixins, viewsets, status
from rest_framework.permissions import IsAuthenticated
from utils.permissions import IsOwnerOrReadOnly
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.authentication import SessionAuthentication

from .serializers import CustomerSerializer, CustomerDetailSerializer, \
                        CustomerFavSerializer, CustomerFavListSerializer,\
                        CustomerCartSerializer, CustomerCartListSerializer
from .models import Customer, CustomerFav, CustomerCart

from rest_framework.response import Response
from rest_framework import mixins, viewsets
from rest_framework import generics

from rest_framework.pagination import PageNumberPagination
from .filters import CustomerFavFilter, CustomerCartFilter
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


class CustomerCartViewSet(mixins.CreateModelMixin, mixins.DestroyModelMixin, mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
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
