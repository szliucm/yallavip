
"""yallavip URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path,include, re_path
from django.conf.urls.static import static
from django.conf import settings
import  xadmin
from prs.views import  SelectView
from funmart.views import  *
from customer.views import  *
from conversations.views import  *
from prs.views import SpusListViewSet
from orders.views import OrderViewSet

from . import view
from rest_framework.documentation import include_docs_urls
from rest_framework.routers import DefaultRouter
from rest_framework.authtoken import views
from rest_framework_simplejwt import views as simplejwt_views  # 引入simplejwt


router = DefaultRouter()

#配置customer的url
router.register(r'customers', CustomerViewSet)
#FbConversation
router.register(r'fbconversation', FbConversationViewSet)
#CustomerFavViewSet
router.register(r'customerfav', CustomerFavViewSet)
#CustomerCartViewSet
router.register(r'customercart', CustomerCartViewSet)
#配置spus的url
router.register(r'spus', SpusListViewSet)
# 订单管理
router.register(r'order', OrderViewSet, base_name='order')
# 收件人管理
router.register(r'receiver', ReceiverViewSet, base_name='receiver')


urlpatterns = [
    path('admin/', admin.site.urls),
    path('xadmin/', xadmin.site.urls),
    path('api-auth/', include('rest_framework.urls')),  # drf 认证url
    path('login/', simplejwt_views.TokenObtainPairView.as_view(), name='token_obtain_pair'),  # simplejwt认证接口

    # DRF文档
    #path('docs/', include_docs_urls(title='DRF文档')),

    # 二级联动页面请求
    path('select/mypage_myalbum/', SelectView.as_view(), name='mypage_myalbum'),
    path('hello/', view.Hello.as_view()),
    path('demo_add/', demo_add),
    path('order_item/', order_item),
    #path('get_package_info/', get_package_info),

    path('scanpackage/', scanpackage),
    path('preparebatch/', preparebatch),
    path('scanpackageitem/', scanpackageitem),
    path('update_item/', update_item),

    path('fulfillbag/', fulfillbag),
    #path('packbag/', packbag),

    path('allPage/', all_page),
    path('addPage/', add_page),
    path('addStudent/', add_student),
    path('search/', search_student),

    path('demo/', demo),
    path('data/', response_data),

    path('', include(router.urls)),  # API url现在由路由器自动确定。







    #path('ueditor/', include('DjangoUeditor.urls')),
    #url(r'^media/(?P<path>.*)', serve, {"document_root":MEDIA_ROOT}),
]
#if settings.DEBUG:
#	urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

urlpatterns += static(settings.MEDIA_URL , document_root=settings.MEDIA_ROOT)





