from django.db import models

# Create your models here.

class TomtopCategory(models.Model):
    cate_no = models.IntegerField(u'分类ID', default=0, blank=True, null=True)
    name = models.CharField(default='', max_length=300, null=True, blank=True, verbose_name="分类名称")
    parent_no = models.IntegerField(u'父级ID', default=0, blank=True, null=True)
    level = models.IntegerField(u'层级', default=0, blank=True, null=True)


    class Meta:
        verbose_name = "Tomtop分类"
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.name

