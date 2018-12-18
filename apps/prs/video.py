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

def fb_slideshow(images, target_page):
    from fb.adminx import get_token
    import requests
    import json
    if not images:
        print("no got images")
        return
    url = "https://graph.facebook.com/v3.2/{}/videos".format(target_page)
    params = {
        'slideshow_spec': {
            "images_urls": images,
            "duration_ms": 1000,
            "transition_ms": 200,
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


def logo_video(video,logo,handle,price):
    import os
    import subprocess

    video_output = "watermark_"+ video
    #sub = "ffmpeg -i " + video + " -i /home/facelive/Downloads/image/11.png -filter_complex overlay=W-w " + url3 + file + ''
    sub = 'ffmpeg -i %s -acodec copy -b:v 2073k -vf "[in]drawtext=fontsize=30:fontfile=ARIAL.TTF:text=%s:x=(w-text_w)/2:y=(h-text_h)-50:box=1:boxcolor="yellow":boxborderw=10[text];movie=%s[logo];movie=%s[price];[text][logo]overlay=20:20[a];[a][price]overlay=20:main_h-overlay_h[out]" %s'\
                %(video,handle,logo,price, video_output)

    videoresult = subprocess.run(args=sub, shell=True)



    print("视频%s  logo完成！！",video)

'''
 #视频打水印： 文字+图片+图片
 ffmpeg -i a.mp4 -acodec copy -b:v 2073k -vf "[in]drawtext=fontsize=30:fontfile=ARIAL.TTF:text='a1234':x=(w-text_w)/2:y=(h-text_h)-50:box=1:boxcolor="yellow":boxborderw=10[text];movie=logo.png[logo];movie=logo.png[price];[text][logo]overlay=20:20[a];[a][price]overlay=20:main_h-overlay_h[out]" output.mp4
'''

