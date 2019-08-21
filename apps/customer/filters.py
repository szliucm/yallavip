# user_operation/filters.py

from django_filters import rest_framework as filters

from .models import CustomerFav, CustomerCart
from django.db.models import Q

class CustomerFavFilter(filters.FilterSet):
    """
    过滤类
    """
    #user_id = filters.NumberFilter(field_name='user_id', lookup_expr='=')
    #goods_id = filters.NumberFilter(field_name='good_id', lookup_expr='=')


    class Meta:
        model = CustomerFav
        fields = ['user__id', 'spu__handle','conversation', 'conversation__customer','conversation__conversation_no']

class CustomerCartFilter(filters.FilterSet):
    """
    过滤类
    """
    #user_id = filters.NumberFilter(field_name='user_id', lookup_expr='=')
    #goods_id = filters.NumberFilter(field_name='good_id', lookup_expr='=')


    class Meta:
        model = CustomerCart
        fields = ['user__id', 'sku__SKU','sku__size','sku__color','conversation', 'conversation__customer','conversation__conversation_no']
