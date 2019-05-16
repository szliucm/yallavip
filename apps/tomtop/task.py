import  json, requests
def get_token():
    params = {
        "email": "aaron@honhot.com",
        "password": "PH2wqyFSX8hrrMw",
    }
    headers = {
        "Content-Type": "application/json",
        "charset": "utf-8",

    }
    # 初始化SDK

    url = "http://dpapi.quarkscm.com/v1/customer/login"

    print("开始创建主体")
    print(url, json.dumps(params))

    r = requests.post(url, headers=headers, data=json.dumps(params))
    if r.status_code == 200:

        try:
            data = json.loads(r.text)
            print("创建的新产品", r, data)
            return  data.get("access-token")
        except:
            print("创建产品主体失败")
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

    print("开始创建主体")
    print(url, json.dumps(params))

    r = requests.post(url, headers=headers, data=json.dumps(params))
    if r.status_code == 200:

        try:
            data = json.loads(r.text)
            print("创建的新产品", r, data)
        except:
            print("创建产品主体失败")
            print(url, json.dumps(params))
            print(r)
            print(r.text)
            return None
