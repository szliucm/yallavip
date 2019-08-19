import re
from django.utils.timezone import now
from datetime import timedelta
from rest_framework import serializers
from rest_framework.validators import UniqueValidator


class CustomerSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = ('username', 'mobile', 'code', 'password')  # username是Django自带的字段，与mobile的值保持一致

class CustomerDetailSerializer(serializers.ModelSerializer):
    """
    用户详情序列化类
    """

    class Meta:
        model = User
        fields = ('username', 'name','email', 'birthday', 'mobile', 'gender')