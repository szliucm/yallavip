from django.db import models


# Create your models here.
class ActionLog(models.Model):
    issue = models.CharField(u'操作类型', default='', max_length=100, blank=True)

    action_time = models.DateTimeField(u'操作时间', auto_now=False, null=True, blank=True)
    targer = models.DateTimeField(u'操作对象', auto_now=False, null=True, blank=True)
    action = models.CharField(u'操作', max_length=100, null=True, blank=True)
    staff = models.CharField(u'操作人', max_length=100, null=True, blank=True)


    class Meta:
        verbose_name = "操作日志"
        verbose_name_plural = verbose_name


    def __str__(self):
        return self.issue