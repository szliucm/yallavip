#coding:utf-8
import os
import cv2
from PIL import Image

'''
def jpg2video(sp, fps):
    """ 将图片合成视频. sp: 视频路径，fps: 帧率 """
    fourcc = cv2.VideoWriter_fourcc(*"MJPG")
    images = os.listdir('mv')
    im = Image.open('mv/' + images[0])
    vw = cv2.VideoWriter(sp, fourcc, fps, im.size)

    os.chdir('mv')
    for image in range(len(images)):
        # Image.open(str(image)+'.jpg').convert("RGB").save(str(image)+'.jpg')
        jpgfile = str(image + 1) + '.jpg'
        try:
            frame = cv2.imread(jpgfile)
            vw.write(frame)
        except Exception as exc:
            print(jpgfile, exc)
    vw.release()
    print(sp, 'Synthetic success!')
'''
import requests
from io import BytesIO
import os,random
from shop.models import ShopifyVariant,ShopifyImage
from shop.photo_mark import photo_mark,get_remote_image,fill_image,clipResizeImg_new
from django.conf import settings

def get_order_video(order):
    """ 将图片合成视频. sp: 视频路径，fps: 帧率 """
    fourcc = cv2.VideoWriter_fourcc(*"MJPG")
    images = get_order_photos(order)
    if not images:
        print("no got images")
        return

    im = cv2.imread(images[0])
    imgInfo =im.shape
    print(imgInfo)
    size = (imgInfo[1],imgInfo[0])

    print("*****size*****",size)


    video_filename = order.order_no+".avi"
    sp = os.path.join(settings.MEDIA_ROOT, "package/", video_filename)
    fps = 0.5
    vw = cv2.VideoWriter(sp, fourcc, fps, size)

    #os.chdir('mv')
    for image in images:

        try:
            frame = cv2.imread(image)
            vw.write(frame)
            print("we are doing ", image)
        except Exception as exc:
            print(image, exc)
    vw.release()
    print(sp, 'Synthetic success!')


# -*- coding: utf-8 -*-
import os
from PIL import Image
from ffmpy3 import FFmpeg

def get_order_video_v2(order):



    images = get_order_photos(order)
    if not images:
        print("no got images")
        return
    video_filename = order.order_no + ".yuv"
    outname = os.path.join(settings.MEDIA_ROOT, "package/", video_filename)

    for pic in images:

        img = Image.open(pic)
        in_wid, in_hei = img.size
        out_wid = in_wid // 16 * 16
        out_hei = in_hei // 16 * 16
        size = '{}x{}'.format(out_wid, out_hei)  # 输出文件会缩放成这个大小


        ff = FFmpeg(inputs={pic: None},
                    outputs={outname: '-s {} -pix_fmt yuv420p'.format(size)})
        print(ff.cmd)
        ff.run()


def get_order_photos(order):

    order_details = order.order_orderdetail.all().order_by("-price")

    image_list = []
    n=0
    for order_detail in order_details:
        variant =  ShopifyVariant.objects.filter(sku = order_detail.sku).first()
        print("type variant", type(variant), variant)
        if not variant:
            print("no got variant")
            continue

        shopify_image = ShopifyImage.objects.filter(product_no = variant.product_no ,image_no = variant.image_no).first()
        if not shopify_image:
            continue



        image = get_remote_image(shopify_image.src)

        if not image:
            continue

        '''
        #缩放成统一大小
        image = image.convert('RGB')
        image = fill_image(image)
        image =  clipResizeImg_new(image,600,600)
        '''

        image_filename = order.order_no+"_"+str(n) + '.jpg'

        destination = os.path.join(settings.MEDIA_ROOT, "package/", image_filename)

        print("destination", destination)

        image.save(destination, 'JPEG', quality=95)

        image_list.append(destination)

        n = n + 1
    return  image_list

def jpg2video(sp, fps,images):
    """ 将图片合成视频. sp: 视频路径，fps: 帧率 """
    fourcc = cv2.VideoWriter_fourcc(*"MJPG")

    im = images[0]
    vw = cv2.VideoWriter(sp, fourcc, fps, im.size)

    os.chdir('mv')
    for image in range(len(images)):
        # Image.open(str(image)+'.jpg').convert("RGB").save(str(image)+'.jpg')
        jpgfile = str(image + 1) + '.jpg'
        try:
            frame = cv2.imread(jpgfile)
            vw.write(frame)
        except Exception as exc:
            print(jpgfile, exc)
    vw.release()
    print(sp, 'Synthetic success!')


def get_order_image_src(order):
    order_details = order.order_orderdetail.all().order_by("-price")

    image_list = []
    n = 0
    for order_detail in order_details:
        print("order_detail",order_detail)
        variant = ShopifyVariant.objects.filter(sku=order_detail.sku).first()
        print("type variant", type(variant), variant)
        if not variant:
            print("no got variant")
            continue

        shopify_image = ShopifyImage.objects.filter(product_no=variant.product_no, image_no=variant.image_no).first()
        if not shopify_image:
            continue

        image_list.append(shopify_image.src)
    print("image_list", image_list)
    return image_list


def get_order_slideshow(order):
    from fb.adminx import get_token
    import requests
    import json

    target_page = "546407779047102"

    images = get_order_image_src(order)
    if not images:
        print("no got images")
        return


    url = "https://graph.facebook.com/v3.2/{}/videos".format(target_page)
    '''
    params = dict()
    #params["access_token"] = get_token(target_page)
    slideshow_spec = {
                         "images_urls": images,
                         "duration_ms": 1500,
                         "transition_ms": 300,
                     },

    slideshow_spec = json.dumps(slideshow_spec)
    params["slideshow_spec"] = slideshow_spec

    print("url slideshow_spec", url, slideshow_spec)
    '''

    params = {
        'slideshow_spec' : {
                         "images_urls": images,
                         "duration_ms": 1000,
                         "transition_ms": 200,
                     },

        'access_token':get_token(target_page)
    }

    headers = {
        "Content-Type": "application/json",
        "charset": "utf-8",

    }

    #url ="https://graph.facebook.com/v3.2/358078964734730/videos?access_token=EAAGOOkWV6LgBAAfSaSCOnZCg0kPPfbSJ1nQ5ZAMPq1XHLtvGynhUtf5QQZB8RWORI7br6VdreUGaF9V8Bq7ZAE8dl1BTIHmddLytdhOKLii2P3neX9TSwZA7isDhQ4Qq5hsTXAnPMR56TDYOGFE4EDHqN6nJ8SCSSjFIF3qbGSiD8SDOgTmKfqWZAZANZAqAKesjyDtAD6f4d5v7bQpdvBYJ"
    #var = "&slideshow_spec"
    #params = "%7b%22images_urls%22%3a+%5b%22https%3a%2f%2fcdn.shopify.com%2fs%2ffiles%2f1%2f2729%2f0740%2fproducts%2fIL201706091336481875_998.jpg%3fv%3d1531934096%22%2c+%22https%3a%2f%2fcdn.shopify.com%2fs%2ffiles%2f1%2f2729%2f0740%2fproducts%2f8182265194_1099362143_914.jpg%3fv%3d1537862177%22%2c+%22https%3a%2f%2fcdn.shopify.com%2fs%2ffiles%2f1%2f2729%2f0740%2fproducts%2f8182265194_1099362143_914.jpg%3fv%3d1537862177%22%2c+%22https%3a%2f%2fcdn.shopify.com%2fs%2ffiles%2f1%2f2729%2f0740%2fproducts%2f8182259332_1099362143_416.jpg%3fv%3d1537862177%22%2c+%22https%3a%2f%2fcdn.shopify.com%2fs%2ffiles%2f1%2f2729%2f0740%2fproducts%2f8169757733_1099362143_370.jpg%3fv%3d1537862177%22%5d%2c+%22duration_ms%22%3a+1500%2c%22transition_ms%22%3a+300%7d"
    r = requests.post(url,headers=headers,data=json.dumps(params))




    data = json.loads(r.text)
    print("r", r)
    print("request response is ", data)
    return data.get("id")


    '''
    curl \
    - F
    'slideshow_spec={\
         "images_urls":[\
           "https://scontent.xx.fbcdn.net/hads-xtf1/t45.1600-4/11410027_6032434826375_425068598_n.png",\
           "https://scontent.xx.fbcdn.net/hads-xtp1/t45.1600-4/11410105_6031519058975_1161644941_n.png",\
           "http://vignette1.wikia.nocookie.net/parody/images/2/27/Minions_bob_and_his_teddy_bear_2.jpg"\
         ],\
         "duration_ms": 2000,\
         "transition_ms": 200\
       }' \
    - F
    'access_token=XXXXXXXXXXXXXX' \
    "https://graph-video.facebook.com/<API_VERSION>/<PAGE_ID/USER_ID>/videos"
    '''

    return