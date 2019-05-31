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
from django.urls import path
from django.conf.urls.static import static
from django.conf import settings
import  xadmin
from prs.views import  SelectView
from funmart.views import  demo_add, order_item, ajax_list,ajax_dict
from . import view




urlpatterns = [
    path('admin/', admin.site.urls),
    path('xadmin/', xadmin.site.urls),
    # 二级联动页面请求
    path('select/mypage_myalbum/', SelectView.as_view(), name='mypage_myalbum'),
    path('hello/', view.Hello.as_view()),
    path('demo_add/', demo_add),
    path('order_item/', order_item),
    path('ajax_list/', ajax_list),
    path('ajax_dict/', ajax_dict),



    #path('ueditor/', include('DjangoUeditor.urls')),
    #url(r'^media/(?P<path>.*)', serve, {"document_root":MEDIA_ROOT}),
]
#if settings.DEBUG:
#	urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

urlpatterns += static(settings.MEDIA_URL , document_root=settings.MEDIA_ROOT)





