from django.db import models

# Create your models here.
class MyPage(models.Model):
    page_no = models.CharField(u'主页ID', default='', max_length=100, blank=True)
    page = models.CharField(u'主页', default='', max_length=100, blank=True)
    token = models.CharField(u'token', max_length=200, null=True, blank=True)
    #feed_update_time = models.DateTimeField(u'feed最后更新时间', auto_now=False, null=True, blank=True)
    #album_update_time = models.DateTimeField(u'album最后更新时间', auto_now=False, null=True, blank=True)
    conversation_update_time = models.DateTimeField(u'会话更新时间', auto_now=False, null=True, blank=True)

    class Meta:
        verbose_name = "主页更新"
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.page_no

class Ad(models.Model):
    page_no = models.CharField(u'主页ID', default='', max_length=100, blank=True)
    ad_no = models.CharField(u'主页', default='', max_length=100, blank=True)
    #token = models.CharField(u'token', max_length=200, null=True, blank=True)
    #feed_create_time = models.DateTimeField(u'feed创建时间', auto_now=False, null=True, blank=True)
    #album_create_time = models.DateTimeField(u'album创建时间', auto_now=False, null=True, blank=True)
    #conversation_update_time = models.DateTimeField(u'会话更新时间', auto_now=False, null=True, blank=True)

    class Meta:
        verbose_name = "广告"
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.ad_no


class Feed(models.Model):
    page_no = models.CharField(max_length=30, null=True, blank=True, verbose_name="PageID")
    feed_no = models.CharField(default='', unique=True, max_length=50, blank=True, verbose_name="FeedID")
    type = models.CharField(default='',  max_length=50, blank=True, verbose_name="type")
    message = models.CharField(default='',  max_length=3000, blank=True, verbose_name="message")
    sku = models.CharField(default='', max_length=100, blank=True, verbose_name="sku")

    created_time = models.DateTimeField(null=True, blank=True, verbose_name="创建时间")
    name = models.CharField(max_length=500, null=True, blank=True, verbose_name="name")

    description = models.CharField(max_length=1000, null=True, blank=True, verbose_name="description")
    actions_link = models.CharField(max_length=100, null=True, blank=True, verbose_name="actions_link")
    actions_name = models.CharField(max_length=100, null=True, blank=True, verbose_name="actions_name")
    share_count = models.CharField(max_length=100, null=True, blank=True, verbose_name="share_count")

    comment_count = models.CharField(max_length=100,null=True, blank=True, verbose_name="comment_count")

    like_count = models.CharField(max_length=100,null=True, blank=True, verbose_name="like_count")

    class Meta:
        verbose_name = "Feed"
        verbose_name_plural = verbose_name
    def __str__(self):
        #return 'business.facebook.com'+ self.link
        return  self.feed_no

class Album(models.Model):
    page_no = models.CharField(max_length=30, null=True, blank=True, verbose_name="PageID")
    album_no = models.CharField(default='', unique=True, max_length=50, blank=True, verbose_name="album_no")
    created_time = models.DateTimeField(null=True, blank=True, verbose_name="创建时间")
    name = models.CharField(max_length=500, null=True, blank=True, verbose_name="name")

    count = models.CharField(max_length=1000, null=True, blank=True, verbose_name="count")
    like_count = models.CharField(max_length=100, null=True, blank=True, verbose_name="like_count")
    comment_count = models.CharField(max_length=100,null=True, blank=True, verbose_name="comment_count")
    update_time = models.DateTimeField(null=True, blank=True, verbose_name="更新时间")


    class Meta:
        verbose_name = "Album"
        verbose_name_plural = verbose_name
    def __str__(self):
        #return 'business.facebook.com'+ self.link
        return  self.album_no

class Photo(models.Model):
    photo_no = models.CharField(max_length=30, null=True, blank=True, verbose_name="photo_no")
    album_no = models.CharField(default='', null=True, max_length=50, blank=True, verbose_name="album_no")

    created_time = models.DateTimeField(null=True, blank=True, verbose_name="创建时间")
    name = models.CharField(max_length=1000, null=True, blank=True, verbose_name="name")

    image = models.CharField(max_length=500, null=True, blank=True, verbose_name="image")
    link = models.CharField(max_length=500, null=True, blank=True, verbose_name="link")


    like_count = models.CharField(max_length=100, null=True, blank=True, verbose_name="like_count")
    comment_count = models.CharField(max_length=100,null=True, blank=True, verbose_name="comment_count")



    class Meta:
        verbose_name = "Photo"
        verbose_name_plural = verbose_name
    def __str__(self):
        #return 'business.facebook.com'+ self.link
        return  self.photo_no


class Conversation(models.Model):

    conversation_no = models.CharField(default='', unique=True, max_length=50,  blank=True, verbose_name="会话ID")
    page_no = models.CharField(max_length=30, null=True, blank=True, verbose_name="PageID")
    link = models.CharField(max_length=100,null=True, blank=True, verbose_name="链接")
    updated_time = models.DateTimeField(null=True, blank=True, verbose_name="最后更新时间")
    customer = models.CharField(max_length=100,null=True, blank=True, verbose_name="客户")

    class Meta:
        verbose_name = "会话"
        verbose_name_plural = verbose_name
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
    message_content = models.CharField(max_length=1000,null=True, blank=True, verbose_name="消息正文")
    from_id  = models.CharField(max_length=50,null=True, blank=True, verbose_name="发送ID")
    from_name = models.CharField(max_length=100,null=True, blank=True, verbose_name="发送者")
    to_id = models.CharField(max_length=50,null=True, blank=True, verbose_name="接收ID")
    to_name  = models.CharField(max_length=100,null=True, blank=True, verbose_name="接收者")
    #image= models.CharField(max_length=30,null=True, blank=True, verbose_name="接收者")

    class Meta:
        verbose_name = "消息"
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.message_no



class FeedUpdate(MyPage):
    class Meta:
        proxy = True

        verbose_name = "更新Feed"
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.page_no

class AlbumUpdate(MyPage):
    class Meta:
        proxy = True

        verbose_name = "更新Album"
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.page_no

class ConversationUpdate(MyPage):
    class Meta:
        proxy = True

        verbose_name = "更新会话"
        verbose_name_plural = verbose_name
    def __str__(self):
        return self.page_no