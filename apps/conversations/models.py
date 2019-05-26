from django.db import models
from django.utils.html import format_html
from pytz import timezone
from datetime import datetime,timedelta
from fb.models import  MyPage

# Create your models here.
class FbConversation(models.Model):

    conversation_no = models.CharField(default='', unique=True, max_length=50,  blank=True, verbose_name="会话ID")
    page = models.ForeignKey(MyPage, related_name='page_conversation', null=True, blank=True,
                                     verbose_name="Page", on_delete=models.CASCADE)
    page_no = models.CharField(max_length=30, null=True, blank=True, verbose_name="PageID")
    message_count =  models.IntegerField(u'messages_count', default=0, blank=True, null=True)

    link = models.CharField(max_length=100,null=True, blank=True, verbose_name="链接")
    updated_time = models.DateTimeField(null=True, blank=True, verbose_name="最后更新时间")
    has_newmessage = models.BooleanField(default=False, verbose_name="有新消息")

    got_time = models.DateTimeField(null=True, blank=True, verbose_name="最后获取时间")

    customer = models.CharField(max_length=500,null=True, blank=True, verbose_name="客户")
    last_message = models.CharField(max_length=500,null=True, blank=True, verbose_name="最后的对话")

    STATUS = (

        ("待回复", "待回复"),
        ("已回复", "已回复"),

    )
    status = models.CharField(choices=STATUS,max_length=500,null=True, blank=True, verbose_name="状态")
    #lost_time = models.CharField(max_length=500,null=True, blank=True, verbose_name="重要性")
    TASK_TYPE = (

        ("售前", "售前"),
        ("售后", "售后"),

    )
    TASK_STAT = (

        ("未解决", "未解决"),
        ("已解决", "已解决"),

    )
    task_type = models.CharField(choices=TASK_TYPE,default="售前", max_length=50,null=True, blank=True, verbose_name="任务类型")
    task_stat = models.CharField(choices=TASK_STAT, default="未解决", max_length=50, null=True, blank=True,
                                 verbose_name="任务状态")

    def cal_status(self):
        if self.status == "待回复" and self.task_type =="售前":
            color_code = "red"
        elif self.task_stat == "未解决" and self.task_type =="售后":
            color_code = "red"
        else:
            color_code = "white"


        return format_html(
            '<span style="background-color:{};">{}</span>',
            color_code,
            self.status,
        )

    cal_status.short_description = "状态"
    color_status = property(cal_status)





    class Meta:
        verbose_name = "实时会话"
        verbose_name_plural = verbose_name
        ordering = ["-updated_time",]
    def __str__(self):
        #return 'business.facebook.com'+ self.link
        return  self.conversation_no


class FbMessage(models.Model):
    #conversation_no = models.ForeignKey(Conversation,to_field = 'conversation_no',  related_name='conversation', null=True, blank=True, verbose_name="会话",
    #                             on_delete=models.CASCADE)
    conversation = models.ForeignKey(FbConversation, related_name='fbconversation_message',null=True, blank=True, verbose_name="会话",on_delete=models.CASCADE)
    conversation_no = models.CharField(max_length=50, null=True, blank=True, verbose_name="会话ID")
    message_no = models.CharField(max_length=100, null=True, blank=True, verbose_name="消息ID")
    created_time = models.DateTimeField(null=True, blank=True, verbose_name="消息创建时间")
    message_content = models.CharField(max_length=5000,null=True, blank=True, verbose_name="消息正文")
    from_id  = models.CharField(max_length=50,null=True, blank=True, verbose_name="发送ID")
    from_name = models.CharField(max_length=500,null=True, blank=True, verbose_name="发送者")
    to_id = models.CharField(max_length=50,null=True, blank=True, verbose_name="接收ID")
    to_name  = models.CharField(max_length=500,null=True, blank=True, verbose_name="接收者")
    attachments= models.CharField(max_length=30,null=True, blank=True, verbose_name="附件")

    class Meta:
        verbose_name = "消息"
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.message_no


class PageUpdate(models.Model):
    page_no = models.CharField(u'主页ID', default='', max_length=100, blank=True)
    page = models.CharField(u'主页', default='', max_length=100, blank=True)
    token = models.CharField(u'token', max_length=200, null=True, blank=True)
    update_time = models.DateTimeField(u'更新时间', auto_now=False, null=True, blank=True)

    class Meta:
        verbose_name = "主页更新"
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.page