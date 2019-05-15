from django.db import models

# Create your models here.
class StaffSchedule(models.Model):
    staff = publish_error = models.CharField(default='', max_length=256, null=True, blank=True, verbose_name="staff")
    date = models.DateField(verbose_name="Date")
    time = models.ManyToManyField(TimeSchedule, blank=False, verbose_name="Time", related_name="date_staff")

class TimeSchedule(models.Model):
    start_time = models.DateField(verbose_name="start_time")
    end_time = models.TimeField(verbose_name="end_time")

class DateSchedule(models.Model):
    date = models.DateField(verbose_name="Date")
    time = models.ManyToManyField(TimeSchedule, blank=False, verbose_name="Time", related_name="date_staff")



