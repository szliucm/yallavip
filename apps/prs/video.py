#coding:utf-8
import os
#import cv2
from PIL import Image
from shop.photo_mark import  price_for_video

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


FONT = os.path.join(settings.BASE_DIR, "static/font/ARIAL.TTF")

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
#from ffmpy3 import FFmpeg

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

def fb_slideshow(images, target_page):
    from fb.adminx import get_token
    import requests
    import json
    if not images:
        print("no got images")
        return
    url = "https://graph.facebook.com/v3.3/{}/videos".format(target_page)
    params = {
        'slideshow_spec': {
            "images_urls": images,
            "duration_ms": 2000,
            "transition_ms": 1000,
        },

        'access_token': get_token(target_page)
    }

    headers = {
        "Content-Type": "application/json",
        "charset": "utf-8",

    }
    r = requests.post(url, headers=headers, data=json.dumps(params))

    data = json.loads(r.text)
    print("r", r)
    print("request response is ", data)
    return data.get("id")


def logo_video(video,logo,price,handle,price1,price2,no_logo=True):
    import os
    import subprocess




    ori_video = os.path.join(settings.MEDIA_ROOT, video)
    ori_logo = os.path.join(settings.MEDIA_ROOT, str(logo))


    video_output = ori_video.rpartition(".")[0] +  "_watermark.mp4"
    price_dest = ori_video.rpartition(".")[0] +  ".png"
    print(handle, ori_video,ori_logo,price)

    price_for_video(price, price1, price2, price_dest)

    if no_logo:
        sub = 'ffmpeg -y -i %s -acodec copy -b:v 2073k -vf "[in]drawtext=fontsize=30:fontfile=%s:text=%s:x=(w-text_w)/2:y=(h-text_h)-50:box=1:boxcolor="yellow":boxborderw=10[text];movie=%s[logo];movie=%s[price];[text][logo]overlay=20:20[a];[a][price]overlay=20:main_h-overlay_h[out]" %s'\
                %(ori_video,FONT,handle,ori_logo,price_dest, video_output)
    else:
        sub = 'ffmpeg -y -i %s -acodec copy -b:v 2073k -vf "[in]drawtext=fontsize=30:fontfile=%s:text=%s:x=(w-text_w)/2:y=(h-text_h)-50:box=1:boxcolor="yellow":boxborderw=10[text];movie=%s[price];[text][price]overlay=20:main_h-overlay_h[out]" %s' \
              % (ori_video, FONT, handle,  price_dest, video_output)

    videoresult = subprocess.run(args=sub, shell=True)
    if videoresult.returncode == 0:
        return  True
    else:
        return False




'''
 #视频打水印： 文字+图片+图片
 ffmpeg -i a.mp4 -acodec copy -b:v 2073k -vf "[in]drawtext=fontsize=30:fontfile=ARIAL.TTF:text='a1234':x=(w-text_w)/2:y=(h-text_h)-50:box=1:boxcolor="yellow":boxborderw=10[text];movie=logo.png[logo];movie=logo.png[price];[text][logo]overlay=20:20[a];[a][price]overlay=20:main_h-overlay_h[out]" output.mp4
'''


#########################
####扫描创意，把处理过的视频，生成缩略图
#########################
def thumbnail_video():
    import subprocess
    from .models import MyProductResources

    videos = MyProductResources.objects.filter(thumbnail=False,resource_cate="VIDEO")
    for video in videos:
        ori_video = os.path.join(settings.MEDIA_ROOT,str(video.resource))


        dest_img = ori_video.rpartition(".")[0]+".jpg"

        print("type", ori_video, dest_img)
        sub =  "ffmpeg -i %s -y -f mjpeg -ss 3 -t 0.001 -s 320x240 %s" % (ori_video, dest_img)

        videoresult = subprocess.run(args=sub, shell=True)
        if videoresult.returncode == 0:
            MyProductResources.objects.filter(pk=video.pk).update(thumbnail=True)
        else:
            print("转换失败")


