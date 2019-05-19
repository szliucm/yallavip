from django.db import models

# Create your models here.
class Conversation(models.Model):

    conversation_no = models.CharField(default='', unique=True, max_length=50,  blank=True, verbose_name="会话ID")
    page_no = models.CharField(max_length=30, null=True, blank=True, verbose_name="PageID")
    link = models.CharField(max_length=100,null=True, blank=True, verbose_name="链接")
    updated_time = models.DateTimeField(null=True, blank=True, verbose_name="最后更新时间")

    got_time = models.DateTimeField(null=True, blank=True, verbose_name="最后获取时间")

    customer = models.CharField(max_length=500,null=True, blank=True, verbose_name="客户")

    def cal_status(self):
        message = Message.objects.filter(conversation_no=self.conversation_no).order_by("-created_time").first()
        if message.from_name == self.customer:
            color_code = "red"
            status = "待回复"
        else:
            color_code = "blue"
            status = "已回复"

        return  format_html(
            '<span style="background-color::{};">{}</span>',
            color_code,
            status,
        )


    cal_status.short_description = "状态"
    status = property(cal_status)

    class Meta:
        verbose_name = "会话"
        verbose_name_plural = verbose_name
        ordering = ["updated_time",]
    def __str__(self):
        #return 'business.facebook.com'+ self.link
        return  self.conversation_no


class Message(models.Model):
    #conversation_no = models.ForeignKey(Conversation,to_field = 'conversation_no',  related_name='conversation', null=True, blank=True, verbose_name="会话",
    #                             on_delete=models.CASCADE)
    #conversation = models.ForeignKey(Conversation, related_name='conversation',null=True, blank=True, verbose_name="会话",on_delete=models.CASCADE)
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
        return self.message_id


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