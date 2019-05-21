# -*- coding: utf-8 -*-
__author__ = 'bobby'


import requests
import json
import time
import datetime

import xadmin

from django.shortcuts import get_object_or_404,get_list_or_404,render
from import_export import resources,fields
from import_export.widgets import ForeignKeyWidget
from .models import FbMessage, FbConversation  ,PageUpdate

from django.utils.safestring import mark_safe
from django.utils import timezone as dt

class FbConversationResource(resources.ModelResource):

    class Meta:
        model = FbConversation
        skip_unchanged = True
        report_skipped = True
        import_id_fields = ('conversation_no',)
        fields = ('page_no','conversation_no','link','updated_time','customer')
        # exclude = ()

@xadmin.sites.register(FbConversation)
class FbConversationAdmin(object):


    def customer_link(self, obj):
        return mark_safe(
            '<a href="http://business.facebook.com%s" target="view_window">%s</a>'
            % (obj.link,obj.customer))

    customer_link.short_description = '会话链接'
    customer_link.allow_tags = True

    def lost_time(self,obj):
        time_span = dt.now() - obj.updated_time

        lost_time = ""
        if time_span.days >= 1:
            lost_time = str(time_span.days) + "天前"
        elif time_span.seconds >= 3600:
            lost_time += str(int(time_span.seconds / 3600)) + "小时前"
        else:
            lost_time += str(int(time_span.seconds / 60)) + "分钟前"

    lost_time.short_description = "状态"


    import_export_args = {'import_resource_class': FbConversationResource, 'export_resource_class': FbConversationResource}

    list_display = ["conversation_no", "customer_link" , "lost_time","color_status", "task_type", "last_message",]
    list_editable = ["task_type",]
    search_fields = ['customer', ]
    list_filter = ["status","task_type", "page_no", ]
    ordering = ["-updated_time"]


    class MessageInline(object):
        model = FbMessage
        extra = 1
        style = 'tab'

    inlines = [MessageInline]


class MessageResource(resources.ModelResource):


    class Meta:
        model = FbMessage
        skip_unchanged = True
        report_skipped = True
        import_id_fields = ('message_no',)
        fields = ( 'conversation_no', 'message_no','message_content','from_id','from_name','to_id','to_name',)
        # exclude = ()

@xadmin.sites.register(FbMessage)
class FbMessageAdmin(object):
    import_export_args = {'import_resource_class': MessageResource, 'export_resource_class': MessageResource}

    list_display = ["conversation_no", "message_no", "message_content", "created_time",'from_name', ]
    ordering = ["conversation_no","created_time",]

class PageUpdateAdmin(object):
    actions = ["batch_updatepage", ]
    list_display = ('page', 'page_no', 'update_time', 'token',
                   )
    list_editable = ['token','update_time']
    #search_fields = ['logistic_no', ]
    # list_filter = ("update_time", )
    ordering = ['-update_time']

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





                obj, created = FbConversation.objects.update_or_create(conversation_no=conversation_no,
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


    def update_page(self, target_page, token,  datetime_since, now_time):
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

    def batch_updatepage(self, request, queryset):
        # 定义actions函数



        for row in queryset:
            target_page = row.page_no
            token = row.token
            datetime_since = row.update_time
            now_time = datetime.datetime.utcnow()

            self.update_page(target_page, token, datetime_since, now_time)

            PageUpdate.objects.filter(page_no = target_page).update(update_time = now_time )

    batch_updatepage.short_description = "批量更新主页会话"

xadmin.site.register(PageUpdate,PageUpdateAdmin)