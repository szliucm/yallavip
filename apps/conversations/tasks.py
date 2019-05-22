from __future__ import absolute_import, unicode_literals

from .models import *
from fb.models import MyPage, PageSync

from prs.fb_action import  get_token
import  json, requests
import  time
import  datetime
import pytz
from django.utils import timezone as dt
from celery import shared_task, task

def convert_conversation_data(page_no, response_json, got_time, datetime_since):


    data = response_json.get("data")
    for i in range(len(data)):
        row = data[i]
        conversation_no = row.get("id")
        print("conversation_no", conversation_no,row.get("updated_time"))
        update_time = datetime.datetime.strptime(row.get("updated_time"), "%Y-%m-%dT%H:%M:%S+0000")
        update_time = update_time.replace(tzinfo=pytz.timezone('UTC'))

        if (update_time < datetime_since):
            print("page %s conversation 无新可更"%page_no, update_time, datetime_since)
            break


        conversation, created = FbConversation.objects.update_or_create(conversation_no=conversation_no,
                                                             defaults={
                                                                       'page_no': page_no,
                                                                       'link': row.get("link"),
                                                                       'updated_time': row.get("updated_time"),
                                                                        'has_newmessage':True,

                                                                        "got_time": got_time,
                                                                       'customer': row["participants"]["data"][0]["name"][:50]
                                                                       }
                                                             )

        if conversation.task_type == "已解决":
            conversation.task_type = "售前"
            conversation.save()

        convert_messages(conversation, row, conversation_no, datetime_since)

        #flush_conversation( conversation)


    return

def get_conversation_data(page_no, token, offset, field_input,  datetime_since):
    url = "https://graph.facebook.com/v3.1/{}/conversations".format(page_no)
    param = dict()
    param["access_token"] = token
    param["limit"] = "100"
    param["offset"] = offset
    param["fields"] = field_input
    param["since"] = datetime_since

    r = requests.get(url, param)
    if r.status_code == 200:
        return  True, json.loads(r.text)
    else:
        return  False, json.loads(r.text)



def get_conversations(page_no):


    field_input = 'id,is_subscribed,link,participants,message_count,unread_count,\
                                    updated_time,messages{created_time,id,message,\
                                    sticker,tags,from,to,attachments}'
    token , long_token = get_token(page_no)
    offset = 0

    try:
        pagesync = PageSync.objects.get(page_no=page_no)

        datetime_since = pagesync.conversation_update_time
    except:
        datetime_since = datetime.datetime(2019, 5, 16, 0, 0, 0)
        datetime_since = datetime_since.replace(tzinfo=pytz.timezone('UTC'))

    datetime_since_stamp = int(datetime_since.timestamp())


    conversation_update_time = dt.now()



    while True:
        try:
            got_time = dt.now()
            got, data = get_conversation_data(page_no, token, str(offset), field_input, datetime_since_stamp)

            if not got:
                break

            check = data['data']
            print("当前的更新时间", offset, check[0]["updated_time"])
            update_time = datetime.datetime.strptime(check[0]["updated_time"], "%Y-%m-%dT%H:%M:%S+0000")

            update_time = update_time.replace(tzinfo=pytz.timezone('UTC'))

            if (update_time < datetime_since):
                print("page %s 无新可更"%page_no)
                break


            convert_conversation_data(page_no, data, got_time, datetime_since)

            if (len(check) >= 100):
                offset += 100
            else:
                print("End of loop for obtaining more than 100 conversation records.")
                break

        except KeyError:
            print("Error with get request.")
            return

    obj, created = PageSync.objects.update_or_create(page_no=page_no,
                                                         defaults={
                                                             'conversation_update_time': conversation_update_time,

                                                         }
                                                         )
@shared_task
def batch_get_conversations():
    from prs.tasks import my_custom_sql
    pages = MyPage.objects.filter(is_published=True, active=True, promotable=True)

    for page in pages:
        page_no = page.page_no
        get_conversations(page_no)

    flush_conversations(hours=1)
    mysql = "update conversations_fbconversation c , fb_mypage p set c.page_id = p.id where c.page_no = p.page_no and c.page_id is NULL"
    my_custom_sql(mysql)
        

def convert_messages(fbconversation, row,conversation_no, datetime_since):
    '''This will get the list of people who commented on the post,
    which can be joined to the feed table by post_id. '''
    message_count = row.get("message_count")


    if message_count > 0:

        messages_data = row["messages"]

        all_got = convert_messages_data(fbconversation, conversation_no, messages_data["data"], datetime_since)



        while not all_got:
            # Check if the next link exists
            try:
                next_link = messages_data["paging"]["next"]
            except KeyError:
                next_link = None

            if next_link:
                print("有下一页")

                r = requests.get(next_link.replace("limit=25", "limit=100"))
                try:
                    messages_data = json.loads(r.text)

                except KeyError:
                    print("convert_messages_data  completed")
                    break


                all_got = convert_messages_data(fbconversation, conversation_no,messages_data["data"] , datetime_since)

            else:
                break



def convert_messages_data(fbconversation, conversation_no,messages, datetime_since):
    message_list = []
    message_no_list = []

    all_got = False

    for message in messages:


        created_time = message["created_time"]
        message_no = message["id"]

        #print("update message : ", message_no, created_time)
        update_time = datetime.datetime.strptime(created_time, "%Y-%m-%dT%H:%M:%S+0000")
        update_time = update_time.replace(tzinfo=pytz.timezone('UTC'))
        if update_time <= datetime_since:
            all_got = True
            print("message 无新可更了")
            break

        content = message["message"]
        if len(content) > 300:
            content = content[:300]
        elif len(content) == 0:
            content = "attachments"

        new_message = FbMessage(
            conversation = fbconversation,
            conversation_no=conversation_no,
            message_no=message_no,

            created_time=created_time,
            message_content= content,
            from_id=message["from"]["id"],
            from_name=message["from"]["name"][:50],
            to_id=message["to"]["data"][0]["id"],
            to_name=message["to"]["data"][0]["name"][:50],



        )



        message_list.append(new_message)
        message_no_list.append(message_no)

    FbMessage.objects.filter(message_no__in=message_no_list).delete()
    FbMessage.objects.bulk_create(message_list)


    return  all_got

def flush_conversations(hours=1):

    start_time = str(dt.now() - datetime.timedelta(hours=hours))

    #取出有新消息的会话
    conversations = FbConversation.objects.filter(updated_time__gt=start_time)

    n = conversations.count()
    print ("一共有%s个对话待更新"%n)
    for conversation in conversations:
        flush_conversation(conversation)
        n -= 1
        if n % 100 == 0:
            print ("还有%s个对话待更新" % n)

def flush_conversation(conversation):
    messages = FbMessage.objects.filter(conversation_no=conversation.conversation_no).order_by("created_time").values(
        "from_name", "message_content","created_time")
    if not messages:
        print ("没有消息")
        return

    last_message , status = deal_message(conversation.customer, messages)
    # 保存到数据库中
    conversation.last_message = last_message[:499]
    conversation.status = status
    # conversation.lost_time = lost_time
    conversation.has_newmessage = False
    conversation.save()

def deal_message(customer, messages):
    #取最新三条消息，拼接起来
    length = messages.count()
    if length > 3:
        first = length - 3
    else:
        first = 0
    latest_messages = messages[first:length]
    last_message = ""
    for message in latest_messages:
        last_message += "[" + message['from_name'] + "]: " + message['message_content'] + "-----"

    #根据最后一条信息的发送人，设定对话的状态：已回复 or 等待回复
    message = messages[length-1]
    if message.get("from_name") == customer:
        status = "待回复"
    else:
        status = "已回复"

    return  last_message, status

    #计算最后一条消息的时间和当前时间的差
    '''
    time_span = now - message["created_time"]

    lost_time = ""
    if time_span.days >= 1:
        lost_time = str(time_span.days) + "天前"
    elif time_span.seconds >= 3600:
        lost_time += str(int(time_span.seconds / 3600)) + "小时前"
    else:
        lost_time += str(int(time_span.seconds / 60)) + "分钟前"

    print(conversation)
    print (last_message)
    print(status)
    print (now, message["created_time"], lost_time)
    '''












