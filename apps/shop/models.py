from django.db import models

# Create your models here.
class Shop(models.Model):

    shop_name = models.CharField(u'店铺名', default='', max_length=100, blank=True)
    apikey  =  models.CharField(u'API_KEY', default='', max_length=100, blank=True)
    password =  models.CharField(u'PASSWORD', default='', max_length=100, blank=True)

    class Meta:
        verbose_name = "店铺"
        verbose_name_plural = verbose_name


    def __str__(self):
        return self.shop_name