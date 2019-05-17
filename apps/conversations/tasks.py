from .models import Conversation
from fb.models import PageSync

from prs.fb_action import  get_token
import  json, requests
import  time
from django.utils import timezone as dt


def convert_conversation_data(page_no, response_json_list, datetime_since):

    for response_json in response_json_list:
        data = response_json.get("data")
        for i in range(len(data)):
            row = data[i]
            obj, created = Conversation.objects.update_or_create(conversation_no=row.get("id"),
                                                                 defaults={
                                                                           'page_no': page_no,
                                                                           'link': row.get("link"),
                                                                           'updated_time': row.get("updated_time"),
                                                                           'customer': row["participants"]["data"][0]["name"]
                                                                           }
                                                                 )

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
        datetime_since = int(pagesync.conversation_update_time.timestamp())
    else:
        datetime_since = int(time.mktime((2018, 1, 1, 0, 0, 0, 0, 0, 0)))

    pagesync.conversation_update_time = dt.now()

    while True:
        try:

            got, data = self.get_conversation_data(page_no, token, str(offset), field_input, datetime_since)

            if not got:
                break

            check = data['data']
            print(check[0]["updated_time"])
            '''
            if (check[0]["updated_time"] < date_since):
                print("无新可更")
                break
            '''

            response_json_list.append(data)

            if (len(check) >= 100):
                offset += 100
            else:
                print("End of loop for obtaining more than 100 conversation records.")
                break

        except KeyError:
            print("Error with get request.")
            return

    convert_conversation_data(page_no, response_json_list, datetime_since)
    pagesync.save()

def batch_get_conversations():
    pages = MyPage.objects.filter(is_published=True, active=True, promotable=True)

    for page in pages:
        page_no = page.page_no
        get_conversations(page_no)

