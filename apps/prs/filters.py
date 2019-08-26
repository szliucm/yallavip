# user_operation/filters.py

from django_filters import rest_framework as filters

from .models import Lightin_SPU, Lightin_SKU
from django.db.models import Q

class SpusFilter(filters.FilterSet):
    """
    过滤类
    """
    handle = filters.CharFilter(field_name='handle', lookup_expr='contains')
    SPU = filters.CharFilter(field_name='SPU', lookup_expr='contains')
    top_category = filters.NumberFilter(method='top_category_filter', field_name='mycategory_id',lookup_expr='=')  # 自定义过滤，过滤某个一级分类
    sizes = filters.CharFilter(method='sizes_filter',lookup_expr='in')  # 自定义过滤
    colors = filters.CharFilter(method='colors_filter',lookup_expr='in')  # 自定义过滤

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


    def sizes_filter(self, queryset, field_name, value):
        """
        自定义过滤内容

        :param queryset:
        :param field_name:
        :param value: 需要过滤的值
        :return:
        """

        spus_list = list(self.queryset.values_list("id", flat=True).distinct())
        spus_list_filtered = Lightin_SKU.objects.filter(lightin_spu__id__in=spus_list, size__in=sizes).values_list("lightin_spu__id", flat=True)

        queryset = Lightin_SPU.objects.filter(id__in=list(spus_list_filtered))


        return queryset

    def color_filter(self, queryset, field_name, value):
        """
        自定义过滤内容

        :param queryset:
        :param field_name:
        :param value: 需要过滤的值
        :return:
        """

        spus_list = list(self.queryset.values_list("id", flat=True).distinct())

        spus_list_filtered = Lightin_SKU.objects.filter(lightin_spu__id__in=spus_list, color__in=colors).values_list("lightin_spu__id", flat=True)
        queryset = Lightin_SPU.objects.filter(id__in=list(spus_list_filtered))
        return queryset

    class Meta:
        model = Lightin_SPU
        fields = "__all__"



