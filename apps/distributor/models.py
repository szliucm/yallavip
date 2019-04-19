from django.db import models
from prs.models import Lightin_SPU, Lightin_SKU

# Create your models here.
class Yallavip_SPU(Lightin_SPU):
    class Meta:
        proxy = True

        verbose_name = "SPU"
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.SPU

class Yallavip_SKU(Lightin_SKU):
    class Meta:
        proxy = True

        verbose_name = "SKU"
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.SKU