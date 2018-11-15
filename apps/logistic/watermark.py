# 图片的基本参数获取
try:
    from PIL import Image, ImageDraw, ImageFont, ImageEnhance
    import csv
    import math
except ImportError:
    import Image, ImageDraw, ImageFont, ImageEnhance

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

def logo_watermark(sku_no,im,price1,price2,pic_type,version):
    #im = Image.open(source)
    im = im.convert('RGB')

    #if (pic_type == 'album'):
    im = fill_image(im)

    bw, bh = im.size
    scale = bw/900

    layer = Image.new('RGBA', im.size, (0, 0, 0, 0))


    # logo
    mark = Image.open('logo.png')
    lw, lh = mark.size
    #测试
    #mark =  mark.resize( (int(lw*scale),int(lh*scale)), Image.ANTIALIAS)





    #layer.paste(mark, (bw - int(lw/2), bh - int(lh/2)))
    layer.paste(mark, (0, 0))
    out = Image.composite(layer, im, layer)


    #货号
    font = ImageFont.truetype("C:\Windows\Fonts\Arial.ttf", int(45*scale))
    draw1 = ImageDraw.Draw(im)
    if(version == 'combo'):
        draw1.rectangle((int(bw / 2 - 65*scale - 150 ), int(bh - 60*scale-2), int(bw / 2 +65*scale - 145), int(bh-10*scale)), fill='yellow')
        draw1.text((int(bw / 2 - 60*scale - 150), int(bh - 60*scale)), sku_no,  font=font, fill=(0 ,0 ,0))  # 设置文字位置/内容/颜色/字体
    else:
        draw1.rectangle((int(bw / 2 - 65 * scale ), int(bh - 60 * scale - 2), int(bw / 2 + 65 * scale ),
                         int(bh - 10 * scale)), fill='yellow')
        draw1.text((int(bw / 2 - 60 * scale ), int(bh - 60 * scale)), sku_no, font=font,
                   fill=(0, 0, 0))  # 设置文字位置/内容/颜色/字体

    draw1 = ImageDraw.Draw(im)
    #im.show()


    if(pic_type == 'post'):
        # 买赠
        if(version== 'surprise'):
            mark = Image.open('surprise.png')
            lw, lh = mark.size
            mark = mark.resize((int(lw * scale ), int(lh * scale)), Image.ANTIALIAS)
        else:
            mark = Image.open('buy.png')
            lw, lh = mark.size
            mark =  mark.resize( (int(lw *scale/2), int(lh *scale/2)), Image.ANTIALIAS)



        #layer.paste(mark, (bw - int(lw/2), bh - int(lh/2)))

        if (version == 'combo'):
            layer.paste(mark, (bw -300- int(lw *scale/ 2), 0))
        elif (version== 'surprise'):
            layer.paste(mark, (bw - int(lw * scale), 0))
        else:
            layer.paste(mark, (bw - int(lw * scale / 2), 0))
        out = Image.composite(layer, im, layer)

    # 价格
    if (version == 'surprise'):
        mark = Image.open('what.png')
        lw, lh = mark.size
        #测试
        #mark = mark.resize((int(lw * scale / 2), int(lh * scale / 2)), Image.ANTIALIAS)
        mark = mark.resize((int(lw * scale), int(lh * scale )), Image.ANTIALIAS)
        layer.paste(mark, (0, bh - int(lh * scale )))
    else:
        mark = Image.open('price.png')
        # 画图
        # 设置所使用的字体
        font = ImageFont.truetype("C:\Windows\Fonts\Arial.ttf", int(90))
        draw = ImageDraw.Draw(mark)
        draw.text((40+int(30*(3-len(price1))), 40), price1, (255, 255, 255), font=font)  # 设置文字位置/内容/颜色/字体
        draw = ImageDraw.Draw(mark)  # Just draw it!

        font = ImageFont.truetype("C:\Windows\Fonts\Arial.ttf", int(30))
        draw.text((120+int(10*(3-len(price2))), 140), price2, (255, 182, 193), font=font)  # 设置文字位置/内容/颜色/字体
        draw = ImageDraw.Draw(mark)
        lw, lh = mark.size
        #测试
        #mark = mark.resize((int(lw *scale/2), int(lh *scale/2)), Image.ANTIALIAS)
        mark = mark.resize((int(lw ), int(lh )), Image.ANTIALIAS)
        # layer.paste(mark, (bw - int(lw/2), bh - int(lh/2)))
        layer.paste(mark, (0, bh - int(lh )))


    out = Image.composite(layer, im, layer)

    out = out.convert('RGB')
    #out.show()
    if (pic_type == 'post'):
        out.save('./post/'+ sku_no + '_'+version+'.jpg', 'JPEG')
    else:
        out.save('./album/'+ sku_no + '_'+version +'.jpg', 'JPEG')


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

    print
    "old size  %s  %s" % (ori_w, ori_h)
    print
    "new size %s %s" % (newWidth, newHeight)
    print
    u"剪裁后等比压缩完成"

if __name__ == '__main__':
    csv_reader = csv.reader(open('water.csv', encoding='utf-8'))
    for row in csv_reader:

        if (len(row[0]) == 0):
            break
        print(row[0])

        #start
        n=0
        m=1
        ims = []
        while n<4:
            try:
                im = Image.open('./ori/'+str(row[0])+'_'+str(m)+'.jpg')  # image 对象
            except:
                m=m+1
                if m>20:
                    #im = Image.new("RGB", (300, 300), "white")
                    break
                else:
                    continue

            if (n == 0):
                ims.append(clipResizeImg_new(im, 600, 900))
                im_main = im
            else:
                ims.append(clipResizeImg_new(im, 299, 299))
            n=n+1
            m=m+1

        layer = Image.new("RGB", (900, 900), "white")

        layer.paste(ims[0], (0, 0))
        # layer.paste("blue", (0,0,900,900))
        # out = Image.composite(layer, im1, layer)
        for index in range(len(ims)):
            layer.paste(ims[index], (601, 300*(index-1)))

        # out = Image.composite(layer, im2, layer)

        out = layer.convert('RGB')
        # out.show()
        #out.save('target.jpg', 'JPEG')

        #end


        logo_watermark(row[0], out,row[1],row[2],'album','combo')
        logo_watermark(row[0], out, row[1], row[2], 'post','combo')


        logo_watermark(row[0], im_main, row[1], row[2], 'album','single')
        logo_watermark(row[0], im_main, row[1], row[2], 'post','single')

        logo_watermark(row[0], im_main, row[1], row[2], 'post', 'surprise')
