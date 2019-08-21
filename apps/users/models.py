from django.db import models

# Create your models here.
# users/models.py
__author__ = 'derek'


from datetime import datetime
from django.db import models
from django.contrib.auth.models import AbstractUser


class UserProfile(AbstractUser):
    """
    扩展用户，需要在settings设置认证model
    """
    name = models.CharField(max_length=30, blank=True, null=True, verbose_name='姓名', help_text='姓名')
    birthday = models.DateField(null=True, blank=True, verbose_name='出生年月', help_text='出生年月')
    mobile = models.CharField(max_length=11, blank=True, null=True, verbose_name='电话', help_text='电话')
    gender = models.CharField(max_length=6, choices=(('male', '男'), ('female', '女')), default='male', verbose_name='性别', help_text='性别')

    class Meta:
        verbose_name = "用户信息"
        verbose_name_plural = verbose_name


    def __str__(self):
        return self.username


class VerifyCode(models.Model):
    """
    验证码
    """
    code = models.CharField("验证码",max_length=10)
    mobile = models.CharField("电话",max_length=11)
    add_time = models.DateTimeField("添加时间",default=datetime.now)

    class Meta:
        verbose_name = "短信验证"
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.code