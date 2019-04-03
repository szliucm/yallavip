from django.db import models

#from shop.models import  ShopifyProduct,ShopifyVariant





# Create your models here.
class MyPage(models.Model):
    page_no = models.CharField(u'主页ID', default='', max_length=100, blank=True)
    page = models.CharField(u'主页', default='', max_length=100, blank=True)
    access_token = models.CharField(u'access_token', max_length=500, null=True, blank=True)

    message = models.TextField(u'促销文案', max_length=500, null=True, blank=True)
    slogan = models.CharField(u'slogan', max_length=500, null=True, blank=True)

    is_published = models.BooleanField(u"page发布状态",default=False, null=True, blank=True)
    link = models.CharField(u'链接', max_length=500, null=True, blank=True)

    #feed_update_time = models.DateTimeField(u'feed最后更新时间', auto_now=False, null=True, blank=True)
    #album_update_time = models.DateTimeField(u'album最后更新时间', auto_now=False, null=True, blank=True)
    conversation_update_time = models.DateTimeField(u'会话最后更新时间', auto_now=False, null=True, blank=True)

    logo = models.ImageField(u'logo', upload_to='material/',default="",null=True, blank=True)
    price = models.ImageField(u'价格标签', upload_to='material/',default="",null=True, blank=True)
    promote = models.ImageField(u'促销标签', upload_to='material/',default="",null=True, blank=True)

    active = models.BooleanField(u"page状态",default=False)

    class Meta:
        verbose_name = "主页"
        verbose_name_plural = verbose_name

        app_label = 'fb'
    def __str__(self):
        return self.page

class MyAdAccount(models.Model):
    adaccout_no = models.CharField(u'广告账户', default='', max_length=100, blank=True)
    account_status = models.CharField(u'广告账户状态', max_length=200, null=True, blank=True)
    disable_reason = models.CharField(u'disable_reason', max_length=200, null=True, blank=True)
    name = models.CharField(u'广告账户名', max_length=200, null=True, blank=True)
    active = models.BooleanField(u"状态", default=False)

    class Meta:
        verbose_name = "广告账户"
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.adaccout_no


class MyCampaign(models.Model):
    adaccout_no = models.CharField(u'广告账户', default='', max_length=100, null=True,blank=True)
    campaign_no = models.CharField(u'广告系列', default='', max_length=100, null=True,blank=True)
    name = models.CharField(u'广告系列名字', max_length=200, null=True, blank=True)
    objective = models.CharField(u'目标', max_length=200, null=True, blank=True)
    active =  models.BooleanField(u"状态", default=False)

    class Meta:
        verbose_name = "广告系列"
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.campaign_no

class MyAdset(models.Model):
    adaccout_no = models.CharField(max_length=200, null=True, blank=True, verbose_name="广告账户")
    campaign_no = models.CharField(u'广告系列', default='', max_length=100, blank=True)
    adset_no = models.CharField(u'广告组', default='', max_length=100, blank=True)
    name = models.CharField(u'广告组名字', max_length=200, null=True, blank=True)


    attribution_spec = models.CharField(max_length=201, null=True, blank=True, verbose_name="attribution_spec")
    bid_amount = models.CharField(max_length=202, null=True, blank=True, verbose_name="bid_amount")
    bid_info = models.CharField(max_length=203, null=True, blank=True, verbose_name="bid_info")
    billing_event = models.CharField(max_length=204, null=True, blank=True, verbose_name="billing_event")
    budget_remaining = models.CharField(max_length=205, null=True, blank=True, verbose_name="budget_remaining")

    configured_status = models.CharField(max_length=208, null=True, blank=True, verbose_name="configured_status")
    created_time = models.CharField(max_length=209, null=True, blank=True, verbose_name="created_time")
    destination_type = models.CharField(max_length=210, null=True, blank=True, verbose_name="destination_type")
    effective_status = models.CharField(max_length=211, null=True, blank=True, verbose_name="effective_status")

    is_dynamic_creative = models.CharField(max_length=213, null=True, blank=True, verbose_name="is_dynamic_creative")
    lifetime_imps = models.CharField(max_length=214, null=True, blank=True, verbose_name="lifetime_imps")

    optimization_goal = models.CharField(max_length=216, null=True, blank=True, verbose_name="optimization_goal")
    recurring_budget_semantics = models.CharField(max_length=217, null=True, blank=True,
                                                  verbose_name="recurring_budget_semantics")
    source_adset_id = models.CharField(max_length=218, null=True, blank=True, verbose_name="source_adset_id")
    start_time = models.DateTimeField(auto_now=False, null=True, blank=True,verbose_name="start_time")
    updated_time = models.DateTimeField(auto_now=False, null=True, blank=True,verbose_name="updated_time")

    status = models.CharField(max_length=220, null=True, blank=True, verbose_name="status")
    targeting = models.CharField(max_length=221, null=True, blank=True, verbose_name="targeting")

    use_new_app_click = models.CharField(max_length=223, null=True, blank=True, verbose_name="use_new_app_click")
    active = models.BooleanField(u"状态", default=False)

    class Meta:
        verbose_name = "广告组"
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.adset_no

class MyAd(models.Model):
    ad_no = models.CharField(u'广告', default='', max_length=100, blank=True)
    account_no =  models.CharField(u'广告账号', default='', max_length=100,null=True, blank=True)
    adset_no = models.CharField(u'广告组', default='', max_length=100,null=True, blank=True)
    campaign_no = models.CharField(u'campaign_id', default='', max_length=100, blank=True)

    name = models.CharField(u'广告名字', max_length=200, null=True, blank=True)
    #ad_review_feedback = models.CharField(u'ad_review_feedback', max_length=200, null=True, blank=True)
    #adlabels = models.CharField(u'adlabels', default='', max_length=100, blank=True)

    status = models.CharField(u'status', max_length=200, null=True, blank=True)
    effective_status = models.CharField(u'effective_status', max_length=200, null=True, blank=True)
    #creative = models.CharField(u'creative', max_length=200, null=True, blank=True)
    created_time = models.DateTimeField(u'创建时间', auto_now=False, null=True, blank=True)
    updated_time = models.DateTimeField(u'创建时间', auto_now=False, null=True, blank=True)

    active = models.BooleanField(u"状态", default=False)
    local_status = models.CharField(u'本地状态', default="", max_length=50, null=True, blank=True)


    class Meta:
        verbose_name = "广告"
        verbose_name_plural = verbose_name

        app_label = 'fb'
    def __str__(self):
        return self.ad_no

class MyFeed(models.Model):
    page_no = models.CharField(max_length=30, null=True, blank=True, verbose_name="PageID")
    feed_no = models.CharField(default='', unique=True, max_length=50, blank=True, verbose_name="FeedID")
    type = models.CharField(default='',  max_length=50, blank=True, verbose_name="type")
    message = models.CharField(default='',  max_length=3000, null=True, blank=True, verbose_name="message")
    sku = models.CharField(default='', max_length=100, blank=True, verbose_name="sku")

    created_time = models.DateTimeField(null=True, blank=True, verbose_name="创建时间")
    active = models.BooleanField(u"feed状态", default=False)
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
        app_label = 'fb'
    def __str__(self):
        #return 'business.facebook.com'+ self.link
        return  self.feed_no

#选品规则
class SelectionRule(models.Model):
    name = models.CharField(u'选品规则', default='', max_length=200, blank=True)

    cates = models.CharField(max_length=300,null=True, blank=True, verbose_name="关联品类",help_text="多个品类用逗号隔开")
    prices = models.CharField(max_length=300, null=True, blank=True, verbose_name="价格区间",help_text="最低价最高价，用逗号隔开")
    attrs = models.CharField(max_length=300, null=True, blank=True, verbose_name="规格",help_text="多个规格用逗号隔开")

    class Meta:
        verbose_name = "选品规则"
        verbose_name_plural = verbose_name


    def __str__(self):
        return self.name

#套装规则
class ComboRule(models.Model):
    selection_rule = models.ForeignKey(SelectionRule, related_name='selection_combo', null=True, blank=True,
                                     verbose_name="选品规则", on_delete=models.CASCADE)

    name = models.CharField(u'套装规则', default='', max_length=200, blank=True)
    items_count = models.CharField(max_length=300, null=True, blank=True, verbose_name="数量区间",help_text="用逗号隔开")
    items_amount = models.CharField(max_length=300, null=True, blank=True, verbose_name="金额区间", help_text="用逗号隔开")

    class Meta:
        verbose_name = "套装规则"
        verbose_name_plural = verbose_name


    def __str__(self):
        return self.name


#调价规则
class PriceRule(models.Model):
    selection_rule = models.ForeignKey(SelectionRule, related_name='selection_price', null=True, blank=True,
                                     verbose_name="选品规则", on_delete=models.CASCADE)

    name = models.CharField(u'调价规则', default='', max_length=200, blank=True)
    TYPE = (
        ("取整","取整"),
        ("倍数", "倍数"),
    )



    type = models.CharField(u'类型', choices=TYPE,default='', max_length=200, blank=True)
    rules = models.CharField(max_length=300, null=True, blank=True, verbose_name="定价规则")

    commit = models.BooleanField(u'是否提交', default=False)

    class Meta:
        verbose_name = "调价规则"
        verbose_name_plural = verbose_name


    def __str__(self):
        return self.name

class MyAlbum(models.Model):
    selection_rule = models.ForeignKey(SelectionRule, related_name='selection_album', null=True, blank=True,
                                      verbose_name="选品规则", on_delete=models.CASCADE)

    mypage = models.ForeignKey(MyPage, null=True, blank=True, verbose_name="主页",
                               related_name="myalbum_page", on_delete=models.CASCADE)
    page_no = models.CharField(max_length=30, null=True, blank=True, verbose_name="PageID")
    album_no = models.CharField(default='', unique=True, max_length=50, blank=True, verbose_name="album_no")
    created_time = models.DateTimeField(null=True, blank=True, verbose_name="创建时间")
    name = models.CharField(max_length=1000, null=True, blank=True, verbose_name="name")
    link = models.CharField(max_length=500, null=True, blank=True, verbose_name="link")

    count = models.IntegerField( null=True, blank=True, verbose_name="count")
    like_count = models.CharField(max_length=100, null=True, blank=True, verbose_name="like_count")
    comment_count = models.CharField(max_length=100,null=True, blank=True, verbose_name="comment_count")
    updated_time = models.DateTimeField(null=True, blank=True, verbose_name="更新时间")
    active = models.BooleanField(u"相册状态",default=False)

    cates = models.CharField(max_length=300,null=True, blank=True, verbose_name="关联品类",help_text="多个品类用逗号隔开")
    prices = models.CharField(max_length=300, null=True, blank=True, verbose_name="价格区间",help_text="最低价最高价，用逗号隔开")
    attrs = models.CharField(max_length=300, null=True, blank=True, verbose_name="规格",help_text="多个规格用逗号隔开")

    album_promte = models.ImageField(u'相册促销标', upload_to='material/', default="", null=True, blank=True)
    updated = models.BooleanField(u"相册更新状态",default=False)
    class Meta:
        verbose_name = "Album"
        verbose_name_plural = verbose_name
    def __str__(self):
        #return 'business.facebook.com'+ self.link
        return  self.name

class MyPhoto(models.Model):
    page_no = models.CharField(max_length=30, null=True, blank=True, verbose_name="page_no")
    photo_no = models.CharField(max_length=30, null=True, blank=True, verbose_name="photo_no")
    album_no = models.CharField(default='', null=True, max_length=50, blank=True, verbose_name="album_no")

    created_time = models.DateTimeField(null=True, blank=True, verbose_name="创建时间")
    updated_time = models.DateTimeField(null=True, blank=True, verbose_name="更新时间")
    name = models.CharField(max_length=3000, null=True, blank=True, verbose_name="name")
    active = models.BooleanField(u"photo状态", default=False)

    picture = models.CharField(max_length=500, null=True, blank=True, verbose_name="picture")
    link = models.CharField(max_length=500, null=True, blank=True, verbose_name="link")


    like_count = models.IntegerField(u'like_count', default=0, blank=True, null=True)

    comment_count = models.CharField(max_length=100,null=True, blank=True, verbose_name="comment_count")

    product_no = models.CharField(max_length=30, null=True, blank=True, verbose_name="product_no")
    listing_status = models.BooleanField(u'发布到相册的状态', default=True)

    posted_times = models.IntegerField(u'发布到主页的次数',default=0,blank=True, null=True)

    class Meta:
        verbose_name = "Photo"
        verbose_name_plural = verbose_name
        app_label = 'fb'
    def __str__(self):
        #return 'business.facebook.com'+ self.link
        return  self.photo_no

class MyInsight(models.Model):
    obj_no = models.CharField(max_length=30, null=True, blank=True, verbose_name="obj_no")
    obj_type = models.CharField(max_length=30, null=True, blank=True, verbose_name="obj_type")
    insight_name = models.CharField(default='', null=True, max_length=50, blank=True, verbose_name="insight_name")

    insight_value = models.IntegerField(u'insight_value', default=0, blank=True, null=True)
    updated_time = models.DateTimeField(null=True, blank=True, verbose_name="更新时间")

    '''
    album_no = models.CharField(default='', null=True, max_length=50, blank=True, verbose_name="album_no")

    created_time = models.DateTimeField(null=True, blank=True, verbose_name="创建时间")
    updated_time = models.DateTimeField(null=True, blank=True, verbose_name="更新时间")
    name = models.CharField(max_length=1000, null=True, blank=True, verbose_name="name")

    picture = models.CharField(max_length=500, null=True, blank=True, verbose_name="picture")
    link = models.CharField(max_length=500, null=True, blank=True, verbose_name="link")


    like_count = models.CharField(max_length=100, null=True, blank=True, verbose_name="like_count")
    comment_count = models.CharField(max_length=100,null=True, blank=True, verbose_name="comment_count")
    '''


    class Meta:
        verbose_name = "MyInsight"
        verbose_name_plural = verbose_name
    def __str__(self):
        #return 'business.facebook.com'+ self.link
        return  self.obj_no


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

class PostToFeed(models.Model):

    mypage = models.ForeignKey(MyPage, null=True, blank=True, verbose_name="FB Page",
                               related_name="post_feed_page", on_delete=models.CASCADE)
    feed_no = models.CharField(default='',  max_length=200, blank=True, verbose_name="FeedID")

    message = models.TextField(default='', null=True, blank=True, verbose_name="message")
    post_now = models.BooleanField(u"Post Now", default=True)
    posted = models.BooleanField(u"Posted", default=False)

    created_time = models.DateTimeField(null=True, blank=True, verbose_name="创建时间")
    class Meta:
        verbose_name = "Post to FB Page"
        verbose_name_plural = verbose_name

    def __str__(self):
        if self.message:
            return self.message
        else:
            return ""

class SysConfig(models.Model):


    user = models.CharField(default='', unique=True, max_length=50, blank=True, verbose_name="User")
    token = models.CharField(default='', max_length=300, blank=True, verbose_name="token")



    class Meta:
        verbose_name = "Facebook Config"
        verbose_name_plural = verbose_name

    def __str__(self):
        if self.user:
            return self.user
        else:
            return ""







