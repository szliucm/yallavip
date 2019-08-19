from django.shortcuts import render
from rest_framework import mixins, viewsets, status
from .serializers import CustomerSerializer, CustomerDetailSerializer
# Create your views here.


class CustomerViewSet(mixins.CreateModelMixin, mixins.RetrieveModelMixin, mixins.UpdateModelMixin, viewsets.GenericViewSet):
    """
    create:
        创建用户

    retrieve:
        显示用户详情
    """

    serializer_class = CustomerSerializer
    queryset = Customer.objects.all()  # 实际测试好像不加也可以完成注册，可以测试下
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
