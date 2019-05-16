from django.db import models

# Create your models here.
class StaffSchedule(models.Model):
    staff = models.CharField(default='', max_length=256, null=True, blank=True, verbose_name="staff")
    on_date = models.ForeignKey(DateSchedule, null=True, blank=True, verbose_name="DateSchedule",
                                       related_name="dateschedule_staff", on_delete=models.CASCADE)

    on_time = models.CharField(default='', max_length=256, null=True, blank=True, verbose_name="on_time")



class DateSchedule(models.Model):
    date = models.DateField(verbose_name="Date")
    staff_count_0 = models.IntegerField(u'0', default=0, blank=True, null=True)
    staff_count_1 = models.IntegerField(u'1', default=0, blank=True, null=True)
    staff_count_2 = models.IntegerField(u'2', default=0, blank=True, null=True)
    staff_count_3 = models.IntegerField(u'3', default=0, blank=True, null=True)
    staff_count_4 = models.IntegerField(u'4', default=0, blank=True, null=True)
    staff_count_5 = models.IntegerField(u'5', default=0, blank=True, null=True)
    staff_count_6 = models.IntegerField(u'6', default=0, blank=True, null=True)
    staff_count_7 = models.IntegerField(u'7', default=0, blank=True, null=True)

    staff_count_8 = models.IntegerField(u'8', default=0, blank=True, null=True)
    staff_count_9 = models.IntegerField(u'9', default=0, blank=True, null=True)
    staff_count_10 = models.IntegerField(u'10', default=0, blank=True, null=True)
    staff_count_11 = models.IntegerField(u'11', default=0, blank=True, null=True)
    staff_count_12 = models.IntegerField(u'12', default=0, blank=True, null=True)
    staff_count_13 = models.IntegerField(u'13', default=0, blank=True, null=True)
    staff_count_14 = models.IntegerField(u'14', default=0, blank=True, null=True)
    staff_count_15 = models.IntegerField(u'15', default=0, blank=True, null=True)

    staff_count_16 = models.IntegerField(u'16', default=0, blank=True, null=True)
    staff_count_17 = models.IntegerField(u'17', default=0, blank=True, null=True)
    staff_count_18 = models.IntegerField(u'18', default=0, blank=True, null=True)
    staff_count_19 = models.IntegerField(u'19', default=0, blank=True, null=True)
    staff_count_20 = models.IntegerField(u'20', default=0, blank=True, null=True)
    staff_count_21 = models.IntegerField(u'21', default=0, blank=True, null=True)
    staff_count_22 = models.IntegerField(u'22', default=0, blank=True, null=True)
    staff_count_23 = models.IntegerField(u'23', default=0, blank=True, null=True)





