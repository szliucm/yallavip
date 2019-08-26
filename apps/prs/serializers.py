# goods/serializers.py

from rest_framework import serializers
from .models import Lightin_SPU,Lightin_SKU, MyCategory

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
    spuimage = serializers.SerializerMethodField()
    spu_skus = SkusSerializer(many=True)


    def get_spuimage(self, obj):
        if obj.images:
            images = json.loads(obj.images)
            if images:
                return  images[0]
        return ""

    class Meta:
        model = Lightin_SPU
        fields = "__all__"

class CategorySerializer3(serializers.ModelSerializer):
    '''三级分类'''
    class Meta:
        model = MyCategory
        fields = "__all__"


class CategorySerializer2(serializers.ModelSerializer):
    '''
    二级分类
    '''
    #在parent_category字段中定义的related_name="sub_cat"
    sub_cat = CategorySerializer3(many=True)
    class Meta:
        model = MyCategory
        fields = "__all__"


class CategorySerializer(serializers.ModelSerializer):
    """
    商品一级类别序列化
    """
    sub_cat = CategorySerializer2(many=True)
    class Meta:
        model = MyCategory
        fields = "__all__"



