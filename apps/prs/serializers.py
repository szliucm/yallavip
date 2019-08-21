# goods/serializers.py

from rest_framework import serializers
from .models import Lightin_SPU,Lightin_SKU

import json


#Serializer实现商品列表页
# class GoodsSerializer(serializers.Serializer):
#     name = serializers.CharField(required=True,max_length=100)
#     click_num = serializers.IntegerField(default=0)
#     goods_front_image = serializers.ImageField()

class SkusSerializer(serializers.ModelSerializer):
    '''SKU'''
    skuimage = serializers.SerializerMethodField()
    class Meta:
        model = Lightin_SKU
        fields = "__all__"

    def get_skuimage(self, obj):
        if obj.image:
            images = json.loads(obj.image)
            if images:
                return  images[0]
        return ""



class SpusSerializer(serializers.ModelSerializer):
    '''SPU'''
    spu_skus = SkusSerializer(many=True)
    class Meta:
        model = Lightin_SPU
        fields = "__all__"




