import requests
from io import BytesIO
import os

from django.conf import settings

try:
    from PIL import Image, ImageDraw, ImageFont, ImageEnhance

except ImportError:
    import Image, ImageDraw, ImageFont, ImageEnhance


DEV = False

if DEV:
    domain = "http://dev.yallavip.com:8000"
else:
    domain = "http://admin.yallavip.com"
FONT = os.path.join(settings.BASE_DIR, "static/font/ARIAL.TTF")

# 获取远程图片
def get_remote_image(img_url):


    response = requests.get(img_url)

    try:
        return  Image.open(BytesIO(response.content))
    except:
        print("open image error: image_url %s response %s "%(img_url,response))
        return  False


# 裁剪压缩图片
def clipResizeImg_new(im, dst_w, dst_h, qua=95):
    '''''
        先按照一个比例对图片剪裁，然后在压缩到指定尺寸
        一个图片 16:5 ，压缩为 2:1 并且宽为200，就要先把图片裁剪成 10:5,然后在等比压缩
    '''
    ori_w, ori_h = im.size



    dst_scale = float(dst_w) / dst_h  # 目标高宽比
    ori_scale = float(ori_w) / ori_h  # 原高宽比

    if ori_scale <= dst_scale:
        # 过高
        width = ori_w
        height = int(width / dst_scale)

        x = 0
        y = (ori_h - height) / 2

    else:
        # 过宽
        height = ori_h
        width = int(height * dst_scale)

        x = (ori_w - width) / 2
        y = 0

        # 裁剪
    box = (x, y, width + x, height + y)
    # 这里的参数可以这么认为：从某图的(x,y)坐标开始截，截到(width+x,height+y)坐标
    # 所包围的图像，crop方法与php中的imagecopy方法大为不一样
    newIm = im.crop(box)
    im = None

    # 压缩
    ratio = float(dst_w) / width
    newWidth = int(width * ratio)
    newHeight = int(height * ratio)
    #newIm.resize((newWidth, newHeight), Image.ANTIALIAS).save("test6.jpg", "JPEG", quality=95)
    return newIm.resize((newWidth, newHeight), Image.ANTIALIAS)




def fill_image(image):
    width, height = image.size
    new_len = max(width, height)

    # 将新图片是正方形，长度为原宽高中最长的
    new_image = Image.new(image.mode, (new_len, new_len), color='white')

    # 根据两种不同的情况，将原图片放入新建的空白图片中部
    if width > height:
        new_image.paste(image, (0, int((new_len - height) / 2)))
    else:
        new_image.paste(image, (int((new_len - width) / 2), 0))
    return new_image

#各种打标
def deal_image(im,logo = None ,handle = None, price = None,price1 = None, price2=None, promote = None,type="album"):
    version = ''  # 调试用


    # 准备画布
    im = im.convert('RGB')
    im = fill_image(im)

    layer = Image.new('RGBA', im.size, (0, 0, 0, 0))

    bw, bh = im.size
    scale = bw / 900

    # 打logo
    if logo :
        mark = Image.open(logo)
        lw, lh = mark.size

        # 缩放
        # mark =  mark.resize( (int(lw*scale),int(lh*scale)), Image.ANTIALIAS)
        layer.paste(mark, (0, 0))

        out = Image.composite(layer, im, layer)

    # 打货号
    if handle:
        font = ImageFont.truetype(FONT, int(45 * scale))
        draw1 = ImageDraw.Draw(im)
        # 简单打货号
        draw1.rectangle((int(bw / 2 - 70 * scale), int(bh - 70 * scale - 2), int(bw / 2 + 70 * scale),
                         int(bh - 8 * scale)), fill='yellow')
        draw1.text((int(bw / 2 - 70 * scale), int(bh - 70 * scale)), handle, font=font,
                   fill=(0, 0, 0))  # 设置文字位置/内容/颜色/字体
        '''
        #两种打货号的方式：组合商品和单品
        if(version == 'combo'):
            draw1.rectangle((int(bw / 2 - 65*scale - 150 ), int(bh - 60*scale-2), int(bw / 2 +65*scale - 145), int(bh-10*scale)), fill='yellow')
            draw1.text((int(bw / 2 - 60*scale - 150), int(bh - 60*scale)), sku_no,  font=font, fill=(0 ,0 ,0))  # 设置文字位置/内容/颜色/字体
        else:
            draw1.rectangle((int(bw / 2 - 65 * scale ), int(bh - 60 * scale - 2), int(bw / 2 + 65 * scale ),
                             int(bh - 10 * scale)), fill='yellow')
            draw1.text((int(bw / 2 - 60 * scale ), int(bh - 60 * scale)), sku_no, font=font,
                       fill=(0, 0, 0))  # 设置文字位置/内容/颜色/字体
        '''
        draw1 = ImageDraw.Draw(im)

    # 打促销标
    if promote:

        mark = Image.open(promote)
        lw, lh = mark.size
        mark = mark.resize((int(lw * scale), int(lh * scale)), Image.ANTIALIAS)


        # 根据不同促销形式，打标到不同位置'
        if (version == 'combo'):
            layer.paste(mark, (bw - 300 - int(lw * scale / 2), 0))
        elif (version == 'surprise'):
            layer.paste(mark, (bw - int(lw * scale), 0))
        else:
            layer.paste(mark, (bw - int(lw * scale ), 0))

        out = Image.composite(layer, im, layer)

    # 价格
    if price:
        if (version == 'surprise'):  # 猜价格
            mark = Image.open('what.png')
            lw, lh = mark.size

            mark = mark.resize((int(lw * scale), int(lh * scale)), Image.ANTIALIAS)
            layer.paste(mark, (0, bh - int(lh * scale)))
        else:  # 原价 ，促销价
            mark = Image.open(price)
            # 画图
            # 设置所使用的字体
            font = ImageFont.truetype(FONT, int(70))
            draw = ImageDraw.Draw(mark)
            draw.text((40 + int(30 * (3 - len(price1))), 60), price1, (255, 255, 255), font=font)  # 设置文字位置/内容/颜色/字体
            draw = ImageDraw.Draw(mark)  # Just draw it!

            font = ImageFont.truetype(FONT, int(30))
            draw.text((50 + int(10 * (3 - len(price2))), 160), price2, (255, 182, 193), font=font)  # 设置文字位置/内容/颜色/字体
            draw = ImageDraw.Draw(mark)
            lw, lh = mark.size

            mark = mark.resize((int(lw), int(lh)), Image.ANTIALIAS)

            layer.paste(mark, (0, bh - int(lh)))

    out = Image.composite(layer, im, layer)

    out = out.convert('RGB')

    return out


def photo_mark(ori_image,  product, price1, price2, targer_page,  type="album" ):
    # 获取远程图片

    image = get_remote_image(ori_image.src)

    if not image:
        return  False

    # 对图片进行处理
    ################
    logo = targer_page.logo
    promote = targer_page.promote
    price = targer_page.price
    print("logo %s promote %s price %s "%(logo,promote,price   ))

    handle = product.handle





    image = deal_image(image, logo=logo, handle=handle, price=price, promote=promote,  price1=price1,
                       price2=price2, type="album")

    #################

    # 处理完的图片保存到本地

    image_filename = handle + '_' + str(ori_image.position) + '_'+ targer_page.page + '.jpg'
    image_filename = image_filename.replace(' ', '')
    destination = os.path.join(settings.MEDIA_ROOT, "product/", image_filename)

    print("destination", destination)

    image.save(destination,'JPEG',quality = 95)

    destination_url = domain + os.path.join(settings.MEDIA_URL, "product/", image_filename)

    return  destination, destination_url
