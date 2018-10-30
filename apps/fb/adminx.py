# -*- coding: utf-8 -*-
__author__ = 'bobby'


import requests
import json
import time
import datetime
import  re

import xadmin
from facebook_business.api import FacebookAdsApi
from facebook_business.adobjects.adaccount import AdAccount
from facebook_business.adobjects.page import Page


from django.shortcuts import get_object_or_404,get_list_or_404,render
from import_export import resources,fields
from import_export.widgets import ForeignKeyWidget
from .models import Ad, Feed, Album,Photo, Message, Conversation, MyPage, FeedUpdate,AlbumUpdate, ConversationUpdate

@xadmin.sites.register(MyPage)
class MyPageUpdateAdmin(object):
    actions = ["batch_updatepage", ]
    list_display = ( 'page_no','page', 'feed_create_time','album_create_time','conversation_update_time','token',
                   )
    list_editable = ['token']
    #search_fields = ['logistic_no', ]
    # list_filter = ("update_time", )
    ordering = []


#@xadmin.sites.register(Feed)
class FeedAdmin(object):

    list_display = ["page_no", "feed_no", "type","sku","created_time", "actions_link", "actions_name", "share_count",
                    "comment_count", "like_count", "message",]
    search_fields = ['feed_no', ]
    actions = ["batch_update_sku", ]

    def batch_update_sku(self, request, queryset):
        # 定义actions函数
        for row in queryset:

            tmp = re.split(r"\[|\]", str(row.message))

            if (1 < len(tmp)):
                sku = tmp[1]
                Feed.objects.filter(feed_no=row.feed_no).update(sku=sku)


    batch_update_sku.short_description = "批量更新sku"

@xadmin.sites.register(Ad)
class AdAdmin(object):

    list_display = ["page_no", "ad_no", ]
    search_fields = ['ad_no', ]
    actions = [ "update_ad",]

    def update_ad(self, request, queryset):
        # 定义actions函数



        my_app_id = '562741177444068'
        my_app_secret = 'e6df363351fb5ce4b7f0080adad08a4d'
        my_access_token = 'EAAHZCz2P7ZAuQBAL97ZC58IlV3r3uxAHhcfJEZBPiVaiWWsO9iabyUVQ5AKN4SFnUUtE5YtEFJDrV3jXv63IPVmB6NmZB6CkY8KLoScDVYJs7KbwEiO9Dw8lu771ayC9ECTO8eg5VWLCoqZCjZBFtJtN3ihHz4zHAbkyyXqinPOZBNeTSucQjhha8TJ3TsgYZBgsZD'
        adobjects = FacebookAdsApi.init(my_app_id, my_app_secret, my_access_token)
        my_account = AdAccount('act_1173703482769259')
        campaigns = my_account.get_campaigns()
        print(campaigns)

        fields = [
        ]
        params = {
            'message': 'This is a test message',
        }
        post = Page( 358078964734730).create_feed(
            fields=fields,
            params=params,
        )
        post_id = post.get_id()
        fields = [
        ]
        params = {
        }
        PagePost(post_id).api_delete(
            fields=fields,
            params=params,
        )

    update_ad.short_description = "批量更新ad"

@xadmin.sites.register(Album)
class AlbumAdmin(object):

    list_display = ["page_no", "album_no","created_time", "name", "count", "like_count", "comment_count",]
    search_fields = ['album_no', ]
    actions = ["batch_update", ]

    def get_data(self, target_page, token,  fields ):
        """
        This method will get the feed data
        """
        url = "https://graph.facebook.com/v3.2/{}/photos".format(target_page)
        param = dict()
        param["access_token"] = token
        param["limit"] = "100"

        param["fields"] = fields

        r = requests.get(url, param)

        data = json.loads(r.text)


        return data

    def convert_data(self, album_no, response_json_list):
        '''This method takes response json data and convert to csv'''
        for response_json in response_json_list:


            try:
                data = response_json["data"]
            except KeyError:
                print("convert_photo_data {} completed")
                break

            for i in range(len(data)):

                row = data[i]
                photo_no = row["id"]


                try:
                    created_time = row["created_time"].split('+')[0]
                except KeyError:
                    created_time = ""

                try:
                    #name = row["name"].encode('utf-8')[:499]
                    name = row["name"]
                except KeyError:
                    name = ""

                try:
                    image = row["images"][0]["source"]

                except KeyError:
                    image = ""

                try:
                    link = row["link"]
                except KeyError:
                    link = ""
                try:
                    comment_count = row["comments"]["summary"]["total_count"]
                except KeyError:
                    comment_count = ""
                try:
                    like_count = row["likes"]["summary"]["total_count"]
                except KeyError:
                    like_count = ""


                #print("feed %s长度 is name %s message %s, des %s"%(feed_no, len(name), len(message),len(description)) )
                #print("message is ", message)

                obj, created = Photo.objects.update_or_create(photo_no=photo_no,
                                                                defaults={'album_no' : album_no,
                                                                          'photo_no': photo_no,

                                                                          'created_time': created_time,
                                                                          'name': name,

                                                                          'image': image,
                                                                          'link': link,

                                                                          'comment_count': comment_count,
                                                                          'like_count': like_count,
                                                                        }
                                                                     )
                #print("update feed %s ok"%(feed_no))



        return


    def update(self, album_no, token):
        field_input = 'id,created_time,name,images,link,\
                    likes.summary(true),comments.summary(true)'


        json_list = []
        i = 0

        try:
            data = self.get_data(album_no, token, field_input)
            json_list.append(data)
        except KeyError:
            print("Error with get request.")
            return

        while True:
            try:
                i = i + 100
                print("i = %s"%(i))
                next = data["paging"]["next"]
                r = requests.get(next.replace("limit=25", "limit=100"))
                data = json.loads(r.text)
                json_list.append(data)
            except KeyError:
                print("Phontoes for the album {} completed".format(album_no))
                # conversation_dic[conversation_id] = date_since
                # createDictCSV('conversation_dic.csv', conversation_dic)

                break


        self.convert_data(album_no,json_list)
        #messages_table_list = self.convert_messages_data( json_list, date_since)
        #if(len(messages_table_list)>0):
        #    self.create_table(messages_table_list, '/root/data/messages_' + target_page + '_'+ now_time.strftime("%Y-%m-&d %H:%M:%S")+'.csv', target_page, "messages")

    def batch_update(self, request, queryset):
        # 定义actions函数



        for row in queryset:
            album_no = row.album_no
            page_no = Album.objects.get(album_no=row.album_no).page_no
            token = AlbumUpdate.objects.get(page_no=page_no).token

            self.update(album_no, token)

    batch_update.short_description = "批量更新Album内容"

@xadmin.sites.register(Photo)
class PhotoAdmin(object):

    list_display = [ "album_no","photo_no","created_time", "name", "image","link", "like_count", "comment_count",]
    search_fields = ['photo_no', ]
    actions = [ ]

class ConversationResource(resources.ModelResource):

    class Meta:
        model = Conversation
        skip_unchanged = True
        report_skipped = True
        import_id_fields = ('conversation_no',)
        fields = ('page_no','conversation_no','link','updated_time','customer')
        # exclude = ()



@xadmin.sites.register(Conversation)
class ConversationAdmin(object):

    import_export_args = {'import_resource_class': ConversationResource, 'export_resource_class': ConversationResource}

    list_display = ["conversation_no", "page_no", "link", "updated_time", ]
    search_fields = ['conversation_no', ]

    class MessageInline(object):
        model = Message
        extra = 1
        style = 'tab'

    inlines = [MessageInline]


class MessageResource(resources.ModelResource):


    class Meta:
        model = Message
        skip_unchanged = True
        report_skipped = True
        import_id_fields = ('message_no',)
        fields = ( 'conversation_no', 'message_no','message_content','from_id','from_name','to_id','to_name',)
        # exclude = ()

@xadmin.sites.register(Message)
class MessageAdmin(object):
    import_export_args = {'import_resource_class': MessageResource, 'export_resource_class': MessageResource}

    list_display = ["conversation_no", "message_no", "message_content", "created_time",'from_name', ]



#@xadmin.sites.register(FeedUpdate)
class FeedUpdateAdmin(object):
    actions = ["batch_update", ]
    list_display = ('page',  'feed_create_time','page_no','show_feed'
                   )
    #list_editable = ['feed_create_time']
    #search_fields = ['logistic_no', ]
    # list_filter = ("update_time", )
    ordering = ['-feed_create_time']

    def    show_feed(self, obj):
        return Feed.objects.filter(page_no=obj.page_no).first().created_time

    show_feed.short_description = "最后更新时间"

    def get_feed_data(self, target_page, token, offset, fields,  datetime_since ):
        """
        This method will get the feed data
        """
        url = "https://graph.facebook.com/v3.1/{}/feed".format(target_page)
        param = dict()
        param["access_token"] = token
        param["limit"] = "100"
        param["offset"] = offset
        param["fields"] = fields
        param["since"] = int(time.mktime(datetime_since.timetuple()))

        r = requests.get(url, param)

        data = json.loads(r.text)

        return data

    def convert_feed_data(self, target_page, response_json_list, date_since):
        '''This method takes response json data and convert to csv'''



        for response_json in response_json_list:


            try:
                data = response_json["data"]
            except KeyError:
                print("convert_conversation_data {} completed")
                break

            for i in range(len(data)):

                row = data[i]
                feed_no = row["id"]



                try:
                    type = row["type"]
                except KeyError:
                    type = ""
                try:
                    created_time = row["created_time"].split('+')[0]
                except KeyError:
                    created_time = ""
                try:
                    message = row["message"]
                except KeyError:
                    message = ""

                try:
                    tmp = re.split(r"\[|\]", str(message))
                    if (1 < len(tmp)):
                        sku = tmp[1]
                    else:
                        sku = ""

                except KeyError:
                    sku = ""


                try:
                    name = row["name"]
                except KeyError:
                    name = ""
                try:
                    description = row["description"]
                except KeyError:
                    description = ""
                try:
                    actions_link = row["actions"][0]["link"]
                except KeyError:
                    actions_link = ""
                try:
                    actions_name = row["actions"][0]["name"]
                except KeyError:
                    actions_name = ""
                try:
                    share_count = row["shares"]["count"]
                except KeyError:
                    share_count = ""
                try:
                    comment_count = row["comments"]["summary"]["total_count"]
                except KeyError:
                    comment_count = ""
                try:
                    like_count = row["likes"]["summary"]["total_count"]
                except KeyError:
                    like_count = ""

                #print("feed %s长度 is name %s message %s, des %s"%(feed_no, len(name), len(message),len(description)) )
                #print("message is ", message)

                obj, created = Feed.objects.update_or_create(feed_no=feed_no,
                                                                defaults={'feed_no' : feed_no,
                                                                          'page_no': target_page,
                                                                          'type' : type,
                                                                          'created_time': created_time,
                                                                          'message': message[:1000],
                                                                          'sku': sku,
                                                                          'name' : name[:500],
                                                                          'description': description[:1000],
                                                                          'actions_link': actions_link,
                                                                          'actions_name': actions_name,
                                                                          'share_count': share_count,
                                                                          'comment_count': comment_count,
                                                                          'like_count': like_count,
                                                                        }
                                                                     )
                #print("update feed %s ok"%(feed_no))



        return


    def create_table(self, list_rows, file_path, page_name,table_name):
        '''This method will create a table according to header and table name'''


        if table_name == "feed":
            header = ["page_name", "id", "type", "created_time", "message", "name", \
                      "description", "actions_link", "actions_name", "share_count", \
                      "comment_count", "like_count"]
        else:
            print("Specified table name is not valid.")
            quit()

        file = open(file_path, 'w',encoding='utf-8')
        file.write(','.join(header) + '\n')
        for i in list_rows:
            file.write('"' + page_name + '",')
            for j in range(len(i)):
                row_string = ''
                if j < len(i) - 1:
                    row_string += '"' + str(i[j]).replace('"', '').replace('\n', '') + '"' + ','
                else:
                    row_string += '"' + str(i[j]).replace('"', '').replace('\n', '') + '"' + '\n'
                file.write(row_string)
        file.close()
        print("Generated {} table csv File for {}".format(table_name, page_name))


    def update(self, target_page, token,  datetime_since, now_time):
        field_input = 'id,created_time,name,message,comments.summary(true),\
                        shares,type,published,link,likes.summary(true),actions,place,tags,\
                        object_attachment,targeting,feed_targeting,scheduled_publish_time,\
                        backdated_time,description'

        offset = 0
        json_list = []

        date_since = datetime_since.strftime("%Y-%m-%dT%H:%M:%S+0000")

        while True:
            try:

                data = self.get_feed_data(target_page, token, str(offset), field_input, datetime_since)

                check = data['data']


                if ( check[0]["created_time"] < date_since):
                    print("无新可更", check[0]["created_time"] , date_since)
                    break

                json_list.append(data)

                if (len(check) >= 100):

                    offset += 100
                else:
                    print("End of loop for obtaining more than 100 feed records.")
                    break

            except KeyError:
                print("Error with get request.")
                return


        self.convert_feed_data(target_page,json_list,date_since)
        #messages_table_list = self.convert_messages_data( json_list, date_since)
        #if(len(messages_table_list)>0):
        #    self.create_table(messages_table_list, '/root/data/messages_' + target_page + '_'+ now_time.strftime("%Y-%m-&d %H:%M:%S")+'.csv', target_page, "messages")

    def batch_update(self, request, queryset):
        # 定义actions函数



        for row in queryset:
            target_page = row.page_no
            token = row.token
            datetime_since = row.feed_create_time
            now_time = datetime.datetime.utcnow()

            self.update(target_page, token, datetime_since, now_time)

            FeedUpdate.objects.filter(page_no = target_page).update(feed_create_time = now_time )

    batch_update.short_description = "批量更新主页Feed"

@xadmin.sites.register(AlbumUpdate)
class AlbumUpdateAdmin(object):
    actions = ["batch_update", ]
    list_display = ('page',  'page_no',
                   )
    #list_editable = ['feed_create_time']
    #search_fields = ['logistic_no', ]
    # list_filter = ("update_time", )
    ordering = []



    def get_data(self, target_page, token, offset, fields ):
        """
        This method will get the feed data
        """
        url = "https://graph.facebook.com/v3.2/{}/albums".format(target_page)
        param = dict()
        param["access_token"] = token
        param["limit"] = "100"
        param["offset"] = offset
        param["fields"] = fields


        r = requests.get(url, param)

        data = json.loads(r.text)

        return data

    def convert_data(self, target_page, response_json_list):
        '''This method takes response json data and convert to csv'''



        for response_json in response_json_list:


            try:
                data = response_json["data"]
            except KeyError:
                print("convert_conversation_data {} completed")
                break

            for i in range(len(data)):

                row = data[i]
                album_no = row["id"]

                try:
                    created_time = row["created_time"].split('+')[0]
                except KeyError:
                    created_time = ""

                try:
                    name = row["name"]
                except KeyError:
                    name = ""
                try:
                    count = row["count"]
                except KeyError:
                    count = ""

                try:
                    comment_count = row["comments"]["summary"]["total_count"]
                except KeyError:
                    comment_count = ""
                try:
                    like_count = row["likes"]["summary"]["total_count"]
                except KeyError:
                    like_count = ""



                #print("feed %s长度 is name %s message %s, des %s"%(feed_no, len(name), len(message),len(description)) )
                #print("message is ", message)

                obj, created = Album.objects.update_or_create(album_no=album_no,
                                                                defaults={'album_no' : album_no,
                                                                          'page_no': target_page,

                                                                          'created_time': created_time,
                                                                          'name': name,

                                                                          'count': count,


                                                                          'comment_count': comment_count,
                                                                          'like_count': like_count,
                                                                        }
                                                                     )
                #print("update feed %s ok"%(feed_no))



        return


    def update(self, target_page, token):
        field_input = 'id,created_time,name,count,comments.summary(true),likes.summary(true)'

        offset = 0
        json_list = []



        while True:
            try:

                data = self.get_data(target_page, token, str(offset), field_input)

                check = data['data']




                json_list.append(data)

                if (len(check) >= 100):

                    offset += 100
                else:
                    print("End of loop for obtaining more than 100 album records.")
                    break

            except KeyError:
                print("Error with get request.")
                return


        self.convert_data(target_page,json_list)
        #messages_table_list = self.convert_messages_data( json_list, date_since)
        #if(len(messages_table_list)>0):
        #    self.create_table(messages_table_list, '/root/data/messages_' + target_page + '_'+ now_time.strftime("%Y-%m-&d %H:%M:%S")+'.csv', target_page, "messages")

    def batch_update(self, request, queryset):
        # 定义actions函数



        for row in queryset:
            target_page = row.page_no
            token = row.token
            now_time = datetime.datetime.utcnow()

            self.update(target_page, token)

            #AlbumUpdate.objects.filter(page_no = target_page).update(album_create_time = now_time )

    batch_update.short_description = "批量更新主页Album"


@xadmin.sites.register(ConversationUpdate)
class ConversationUpdateAdmin(object):
    actions = ["batch_update", ]
    list_display = ('page', 'page_no', 'conversation_update_time',
                   )
    #list_editable = ['conversation_update_time']
    #search_fields = ['logistic_no', ]
    # list_filter = ("update_time", )
    ordering = ['-conversation_update_time']

    def get_conversation_data(self, target_page, token, offset, fields,  datetime_since ):
        """
        This method will get the feed data
        """
        url = "https://graph.facebook.com/v3.1/{}/conversations".format(target_page)
        param = dict()
        param["access_token"] = token
        param["limit"] = "100"
        param["offset"] = offset
        param["fields"] = fields
        param["since"] = int(time.mktime(datetime_since.timetuple()))

        r = requests.get(url, param)

        data = json.loads(r.text)
        return data

    def convert_conversation_data(self, target_page, response_json_list, date_since):
        '''This method takes response json data and convert to csv'''



        for response_json in response_json_list:


            try:
                data = response_json["data"]
            except KeyError:
                print("convert_conversation_data {} completed")
                break

            for i in range(len(data)):

                row = data[i]
                conversation_no = row["id"]



                try:
                    link = row["link"]
                except KeyError:
                    link = ""
                try:
                    updated_time = row["updated_time"].split('+')[0]
                except KeyError:
                    updated_time = ""

                print("update: ", conversation_no, updated_time)

                if ( updated_time < date_since ):
                    break

                try:
                    customer = row["participants"]["data"][0]["name"]
                except KeyError:
                    customer = ""





                obj, created = Conversation.objects.update_or_create(conversation_no=conversation_no,
                                                                    defaults={'conversation_no' : conversation_no,
                                                                              'page_no' : target_page,
                                                                              'link': link,
                                                                              'updated_time': updated_time,
                                                                              'customer' : customer
                                                                            }
                                                                         )



        return

    def convert_messages_data(self, response_json_list,date_since ):
        '''This will get the list of people who commented on the post,
        which can be joined to the feed table by post_id. '''
        print("start update messages")
        list_all = []

        if(len(response_json_list) ==0):
            return list_all;

        for messages_data in response_json_list:
            try:
                data = messages_data["data"]
            except KeyError:
                print("convert_messages_data  completed")
                break

            for i in range(len(data)):
                likes_count = 0
                row = data[i]
                conversation_no = row["id"]


                try:
                    message_count = row["message_count"]
                except KeyError:
                    message_count = ""
                if message_count > 0:
                    messages = row["messages"]["data"]
                    for message in messages:
                        row_list = []
                        message_no = message["id"]
                        created_time = message["created_time"].split('+')[0]

                        print("update message : ", message_no, created_time)

                        if (created_time < date_since):
                            print("无新可更")
                            break


                        message_content = message["message"].encode('utf-8')

                        from_id = message["from"]["id"]
                        from_name = message["from"]["name"]
                        to_id = message["to"]["data"][0]["id"]
                        to_name = message["to"]["data"][0]["name"]

                        row_list.extend((conversation_no, message_no, created_time, message_content,
                                         from_id, from_name, to_id, to_name))
                        list_all.append(row_list)

                        '''
                        obj, created = Message.objects.update_or_create(conversation_no=conversation_no,message_no= message_no,
                                                                     defaults={'conversation_no': conversation_no,
                                                                               'message_no': message_no,
                                                                               'created_time': created_time,
                                                                               'message_content': message_content,
                                                                               'from_id': from_id,
                                                                               'from_name': from_name,
                                                                               'to_id': to_id,
                                                                               'to_name': to_name,

                                                                               },
                                                                     )
                        '''


                # Check if the next link exists
                try:
                    next_link = row["messages"]["paging"]["next"]
                except KeyError:
                    next_link = None
                    continue

                if next_link is not None:
                    r = requests.get(next_link.replace("limit=25", "limit=100"))
                    try:
                        messages_data = json.loads(r.text)

                    except KeyError:
                        print("convert_messages_data  completed")
                        break

                    while True:

                        for i in range(len(messages_data["data"])):
                            row_list=[]
                            message = messages_data["data"][i]

                            message_no = message["id"]
                            created_time = message["created_time"].split('+')[0]

                            print("update message : ", message_no, created_time)

                            if (created_time < date_since):
                                print("无新可更")
                                break

                            message_content = message["message"].encode('utf-8')

                            from_id = message["from"]["id"]
                            from_name = message["from"]["name"]
                            to_id = message["to"]["data"][0]["id"]
                            to_name = message["to"]["data"][0]["name"]



                            row_list.extend((conversation_no, message_no, created_time, message_content,
                                             from_id, from_name, to_id, to_name))
                            list_all.append(row_list)

                        try:
                            next = messages_data["paging"]["next"]
                            r = requests.get(next.replace("limit=25", "limit=100"))
                            messages_data = json.loads(r.text)
                        except KeyError:
                            print("Messages for the conversation {} completed".format(conversation_no))
                            break

        return list_all

    def create_table(self, list_rows, file_path, page_name,table_name):
        '''This method will create a table according to header and table name'''


        if table_name == "messages":
            header = ["page_name","conversation_no","message_no","created_time",\
                      "message_content","from_id","from_name","to_id","to_name"]
        else:
            print("Specified table name is not valid.")
            quit()

        file = open(file_path, 'w',encoding='utf-8')
        file.write(','.join(header) + '\n')
        for i in list_rows:
            file.write('"' + page_name + '",')
            for j in range(len(i)):
                row_string = ''
                if j < len(i) - 1:
                    row_string += '"' + str(i[j]).replace('"', '').replace('\n', '') + '"' + ','
                else:
                    row_string += '"' + str(i[j]).replace('"', '').replace('\n', '') + '"' + '\n'
                file.write(row_string)
        file.close()
        print("Generated {} table csv File for {}".format(table_name, page_name))


    def update(self, target_page, token,  datetime_since, now_time):
        field_input = 'id,is_subscribed,link,participants,message_count,unread_count,\
                                updated_time,messages{created_time,id,message,\
                                sticker,tags,from,to,attachments}'

        offset = 0
        json_list = []

        date_since = datetime_since.strftime("%Y-%m-%dT%H:%M:%S+0000")

        while True:
            try:

                data = self.get_conversation_data(target_page, token, str(offset), field_input, datetime_since)

                check = data['data']


                if ( check[0]["updated_time"] < date_since):
                    print("无新可更")
                    break

                json_list.append(data)

                if (len(check) >= 100):
                    offset += 100
                else:
                    print("End of loop for obtaining more than 100 conversation records.")
                    break

            except KeyError:
                print("Error with get request.")
                return


        self.convert_conversation_data(target_page,json_list,date_since)
        #messages_table_list = self.convert_messages_data( json_list, date_since)
        #if(len(messages_table_list)>0):
        #    self.create_table(messages_table_list, '/root/data/messages_' + target_page + '_'+ now_time.strftime("%Y-%m-&d %H:%M:%S")+'.csv', target_page, "messages")

    def batch_update(self, request, queryset):
        # 定义actions函数



        for row in queryset:
            target_page = row.page_no
            token = row.token
            datetime_since = row.conversation_update_time
            now_time = datetime.datetime.utcnow()

            self.update(target_page, token, datetime_since, now_time)

            ConversationUpdate.objects.filter(page_no = target_page).update(conversation_update_time = now_time )

    batch_update.short_description = "批量更新主页会话"

