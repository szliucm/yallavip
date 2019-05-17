from .models import Conversation
from fb.models import PageSync

from prs.fb_action import  get_token
import  json, requests
import  time
import  datetime
from django.utils import timezone as dt


def convert_conversation_data(page_no, response_json, got_time, datetime_since):


    data = response_json.get("data")
    for i in range(len(data)):
        row = data[i]
        conversation_no = row.get("id")
        obj, created = Conversation.objects.update_or_create(conversation_no=conversation_no,
                                                             defaults={
                                                                       'page_no': page_no,
                                                                       'link': row.get("link"),
                                                                       'updated_time': row.get("updated_time"),
                                                                        "got_time": got_time,
                                                                       'customer': row["participants"]["data"][0]["name"]
                                                                       }
                                                             )

        convert_messages(row, conversation_no, datetime_since)

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
    response_json_list = []
    pagesync = PageSync.objects.filter(page_no=page_no)
    if pagesync:
        datetime_since = pagesync.conversation_update_time
    else:
        datetime_since = datetime.datetime(2019, 3, 1, 0, 0, 0)

    datetime_since_stamp = int(datetime_since.timestamp())


    pagesync.conversation_update_time = dt.now()

    while True:
        try:
            got_time = dt.now()
            got, data = get_conversation_data(page_no, token, str(offset), field_input, datetime_since_stamp)

            if not got:
                break

            check = data['data']
            print(check[0]["updated_time"])
            '''
            if (check[0]["updated_time"] < datetime_since):
                print("无新可更")
                break
            '''

            convert_conversation_data(page_no, data, got_time, datetime_since)

            if (len(check) >= 100):
                offset += 100
            else:
                print("End of loop for obtaining more than 100 conversation records.")
                break

        except KeyError:
            print("Error with get request.")
            return


    pagesync.save()

def batch_get_conversations():
    pages = MyPage.objects.filter(is_published=True, active=True, promotable=True)

    for page in pages:
        page_no = page.page_no
        get_conversations(page_no)
        

def convert_messages(row,conversation_no, datetime_since):
    '''This will get the list of people who commented on the post,
    which can be joined to the feed table by post_id. '''
    message_count = row.get("message_count")


    if message_count > 0:
        message_list = []
        messages_data = row["messages"]
        while True:
            all_got, new_message_list = convert_messages_data(conversation_no, messages_data["data"], datetime_since)
            message_list += new_message_list

            if not all_got:
                # Check if the next link exists
                try:
                    next_link = messages_data["paging"]["next"]
                except KeyError:
                    next_link = None

                if next_link:
                    r = requests.get(next_link.replace("limit=25", "limit=100"))
                    try:
                        next_messages_data = json.loads(r.text)

                    except KeyError:
                        print("convert_messages_data  completed")
                        return message_list

                    message_list += convert_messages_data(conversation_no, next_messages_data, datetime_since)

                else:
                    break
            else:
                break

        Proxy.objects.bulk_create(message_list)

def convert_messages_data(conversation_no,messages, datetime_since):
    message_list = []
    all_got = False

    for message in messages:


        created_time = message["created_time"]
        message_no = message["id"]

        print("update message : ", message_no, created_time)
        update_time = datetime.datetime.strptime(created_time, "%Y-%m-%dT%H:%M:%S+0000")
        if update_time <= datetime_since:
            all_got = True
            print("无新可更了")
            break

        message = Message(
            conversation_no=conversation_no,
            message_no=message_no,

            created_time=created_time,
            message_content=message["message"].encode('utf-8'),
            from_id=message["from"]["id"],
            from_name=message["from"]["name"],
            to_id=message["to"]["data"][0]["id"],
            to_name=message["to"]["data"][0]["name"],



        )
        message_list.append(message)

    return  all_got , message_list




