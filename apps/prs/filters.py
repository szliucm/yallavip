# user_operation/filters.py

from django_filters import rest_framework as filters

from .models import Lightin_SPU
from django.db.models import Q

class SpusFilter(filters.FilterSet):
    """
    过滤类
    """
    handle = filters.CharFilter(field_name='handle', lookup_expr='contains')
    SPU = filters.CharFilter(field_name='SPU', lookup_expr='contains')
    top_category = filters.NumberFilter(method='top_category_filter', field_name='mycategory_id',
                                        lookup_expr='=')  # 自定义过滤，过滤某个一级分类

    def top_category_filter(self, queryset, field_name, value):
        """
        自定义过滤内容
        这儿是传递一个分类的id，在已有商品查询集基础上获取分类id，一级一级往上找，直到将三级类别找完
        :param queryset:
        :param field_name:
        :param value: 需要过滤的值
        :return:
        """
        queryset = queryset.filter(Q(mycategory_id=value)
                                   | Q(mycategory__super_cate__id=value)
                                   | Q(mycategory__super_cate__super_cate__id=value))
        return queryset
    class Meta:
        model = Lightin_SPU
        fields = "__all__"


