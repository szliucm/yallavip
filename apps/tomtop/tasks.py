import  json, requests
from tomtop.models import *
def get_token():
    params = {
        "email": "aaron@honhot.com",
        "password": "PH2wqyFSX8hrrMw",
    }
    headers = {
        "Content-Type": "application/json",
        "charset": "utf-8",

    }
    url = "http://dpapi.quarkscm.com/v1/customer/login"

    r = requests.post(url, headers=headers, data=json.dumps(params))
    if r.status_code == 200:

        try:
            data = json.loads(r.text)
            return  data.get("access-token")
        except:
            print("获取token失败")
            print(url, json.dumps(params))
            print(r)
            print(r.text)
            return None

def download_category():

    params = {
        'lang' : "en_US",
    }
    headers = {
        'Accept': 'application/json',
        "Content-Type": "application/json",
        "charset": "utf-8",
        'access-token': get_token(),

    }
    url = "http://dpapi.quarkscm.com/v1/catalog/download"

    print("开始下载分类")

    r = requests.post(url, headers=headers, data=json.dumps(params))
    if r.status_code == 200:

        try:
            data = json.loads(r.text)

        except:
            print("下载分类失败")
            print(url, json.dumps(params))
            print(r)
            print(r.text)
            return None

    if data.get("code") == 200:
        cates = data.get("data")
        category_list=[]
        TomtopCategory.objects.all().delete()
        for cate in cates:
            # print("row is ",row)
            category = TomtopCategory(
                cate_no=cate.get("_id"),
                name=cate.get("name"),
                parent_no=cate.get("parent_id"),

                level=cate.get("level"),
            )
            category_list.append(category)
        TomtopCategory.objects.bulk_create(category_list)


