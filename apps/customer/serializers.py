import re
from django.utils.timezone import now
from datetime import timedelta
from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from .models import Customer,CustomerFav, CustomerCart, Receiver
from conversations.models import FbConversation
from prs.serializers import SpusSerializer, SkusSerializer



class CustomerSerializer(serializers.ModelSerializer):

    class Meta:
        model = Customer
        fields = ('name', )  # username是Django自带的字段，与mobile的值保持一致

class CustomerDetailSerializer(serializers.ModelSerializer):
    """
    用户详情序列化类
    """

    class Meta:
        model = Customer
        fields = ('name',)

class CustomerFavListSerializer(serializers.ModelSerializer):
    user = serializers.HiddenField(
        default=serializers.CurrentUserDefault()  # 表示user为隐藏字段，默认为获取当前登录用户
    )

    spu = SpusSerializer()

    class Meta:
        model = CustomerFav
        fields = ('id','conversation','user','spu', 'add_time')
        #fields = "__all__"



class CustomerFavSerializer(serializers.ModelSerializer):
    user = serializers.HiddenField(
        default=serializers.CurrentUserDefault()  # 表示user为隐藏字段，默认为获取当前登录用户
    )

    class Meta:
        model = CustomerFav
        fields = ('id','conversation','user','spu','add_time')
        #fields = "__all__"
        read_only_fields = ()

class CustomerCartListSerializer(serializers.ModelSerializer):
    user = serializers.HiddenField(
        default=serializers.CurrentUserDefault()  # 表示user为隐藏字段，默认为获取当前登录用户
    )

    sku = SkusSerializer()

    class Meta:
        model = CustomerCart
        fields = ('id', 'conversation','user','sku',  'price','quantity', 'add_time')
        #fields = "__all__"



class CustomerCartSerializer(serializers.ModelSerializer):
    user = serializers.HiddenField(
        default=serializers.CurrentUserDefault()  # 表示user为隐藏字段，默认为获取当前登录用户
    )

    class Meta:
        model = CustomerCart
        fields = ('id', 'conversation','user','sku', 'price','quantity', 'add_time')
        #fields = "__all__"
        read_only_fields = ()

class ReceiverSerializer(serializers.ModelSerializer):
    user = serializers.HiddenField(
        default=serializers.CurrentUserDefault()  # 表示user为隐藏字段，默认为获取当前登录用户
    )
    country_code = serializers.HiddenField(default="SA")
    class Meta:
        model = Receiver
        fields = "__all__"
