from django.db import models
from prs.models import Lightin_SKU

# Create your models here.

class Yallavip_SKU(Lightin_SKU):
    class Meta:
        proxy = True

        verbose_name = "SKU"
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.page_no