import re
from django.utils.timezone import now
from datetime import timedelta
from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from .models import Order, OrderDetail

from prs.serializers import SpusSerializer, SkusSerializer

class OrderDetailSerializer(serializers.ModelSerializer):

    class Meta:
        model = OrderDetail
        fields = "__all__"

class OrderListSerializer(serializers.ModelSerializer):
    user = serializers.HiddenField(
        default=serializers.CurrentUserDefault()  # 表示user为隐藏字段，默认为获取当前登录用户
    )
    '''
    def generate_order_sn(self):
        # 取最大订单号作为新订单号
        order_prefix = "yalla_"
        order = Order.objects.filter(order_no__startswith=order_prefix).last()
        if order:
            order_num = int(order.order_no[6:]) + 1
        else:
            order_num = 1

        order_no = order_prefix + str(order_num).zfill(5)
        return  order_no
    '''
    def generate_order_sn(self):
        # 当前时间+userid+随机数
        import time
        from random import randint
        order_sn = '{time_str}{user_id}{random_str}'.format(time_str=time.strftime('%Y%m%d%H%M%S'), user_id=self.context['request'].user.id, random_str=randint(10, 99))
        return order_sn

    def validate(self, attrs):
        # 数据验证成功后，生成一个订单号
        attrs['order_no'] = self.generate_order_sn()
        return attrs
    class Meta:
        model = Order
        fields = "__all__"

class OrderSerializer(serializers.ModelSerializer):
    user = serializers.HiddenField(
        default=serializers.CurrentUserDefault()  # 表示user为隐藏字段，默认为获取当前登录用户
    )

    order_orderdetail = OrderDetailSerializer(many=True)

    class Meta:
        model = Order
        fields = "__all__"


