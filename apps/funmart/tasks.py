# Create your tasks here
from __future__ import absolute_import, unicode_literals

import json
import requests
import os

from celery import shared_task, task
from django.db.models import Count, Q, Sum
from django.conf import settings

from prs.tasks import my_custom_sql
from shop.photo_mark import  get_remote_image
from .models import *


def test_funmart_product():
    url = "http://47.96.143.109:9527/api/getInfoBySku"
    param = dict()
    param["sku"] = "C-170809038"
    r = requests.post(url, data=json.dumps(param))
    print(r.status_code, r.text)


def download_funmart_orders():
    to_download_orders = list(FunmartOrder.objects.filter(downloaded=False).values_list("track_code", flat=True))
    for track_code in to_download_orders:
        download_funmart_order.apply_async((track_code,False), queue='funmart')


def deal_funmart_orders():
    # 按批次扫描包裹，没有的sku则新增sku
    '''
    skus_to_add = FunmartOrderItem.objects.filter(order__downloaded=True, order__dealed=False)\
        .exclude(sku__in=list(FunmartSKU.objects.all().values_list('SKU',flat=True)))\
        .values_list("sku", flat=True).distinct()
    '''
    skus_to_add = FunmartOrderItem.objects.all() \
        .exclude(sku__in=list(FunmartSKU.objects.all().values_list('SKU', flat=True))) \
        .values_list("sku", flat=True).distinct()
    print("有%s个sku需要新增" % skus_to_add.count())

    sku_list = []
    for sku_to_add in skus_to_add:
        sku = FunmartSKU(
            SKU=sku_to_add,
        )

        sku_list.append(sku)

    print(sku_list)
    FunmartSKU.objects.bulk_create(sku_list)


def download_skus():
    # 没有下载的sku就下载sku；
    skus = FunmartSKU.objects.filter(download_error="",downloaded=False )
    for sku in skus:
        get_funmart_sku.apply_async((sku.SKU,), queue='funmart')


def download_spus():
    # 把新的spu插入到spu列表
    spus_to_add = FunmartSKU.objects.filter(downloaded=True).exclude(SPU__in=
    FunmartSPU.objects.all().values_list(
        'SPU', flat=True)).values_list("SPU", flat=True).distinct()

    spu_list = []
    for spu_to_add in spus_to_add:
        spu = FunmartSPU(
            SPU=spu_to_add,
        )
        spu_list.append(spu)

    print(spu_list)
    FunmartSPU.objects.bulk_create(spu_list)

    # 外键关联
    mysql = "update funmart_funmartspu p , funmart_funmartsku k set k.funmart_spu_id = p.id where p.SPU=k.SPU"
    my_custom_sql(mysql)

    # spu没有下载的就下载spu
    funmartspus = FunmartSPU.objects.filter(download_error="", downloaded=False)
    for spu in funmartspus:
        get_funmart_spu.apply_async((spu.SPU,), queue='funmart')


@shared_task
# 从funmart获取订单数据，插入订单，订单明细
def get_funmart_order(track_code=None, order_no=None,order_ref=None, batch_no=None):


    if order_ref:
        orders = FunmartOrder.objects.filter( order_ref=order_ref)
    elif track_code:
        orders = FunmartOrder.objects.filter(Q(track_code=track_code)|Q(ret_track_code=track_code))
    else:
        return  None

    if orders:
        return  orders[0]

    order =  download_funmart_order(track_code, order_no, order_ref)
    return order



@shared_task
def download_funmart_order(track_code=None, order_no=None, order_ref=None,update=True, ):
    url = " http://47.98.80.172/api/searchOrder"
    param = dict()
    # 如果输入了order_ref，就忽略track_code
    if order_ref:
        if not track_code:
            return None
        param["order_ref"] = order_ref
    elif track_code:
        param["track_code"] = track_code
    elif order_no:
        param["order_no"] = order_no
    else :
        return None

    #print("查询条件", param)

    r = requests.post(url, data=json.dumps(param))
    if r.status_code == 200:
        return_data = json.loads(r.text)
        if return_data.get("code") == '00001':
            data = return_data.get("data")
            #print(data)

            order_no = data.get("order_no")
            order, created = FunmartOrder.objects.update_or_create(
                track_code =  track_code,

                defaults={
                    'order_no' : order_no,
                    'ret_track_code': data.get("track_code"),
                     'order_ref': data.get("order_ref"),
                     'order_date': data.get("order_date"),
                    'ship_method': data.get("ship_method"),
                    'scanned': False,
                    'downloaded': True
                }
            )

            orderitems = data.get("orderItems")
            if update:
                quantity = update_order_item(order, orderitems)
            else:
                quantity = create_order_item(order, orderitems)

            order.quantity = quantity
            order.save()


            return  order
        else:
            print (return_data.get("message"))


    return  None

def update_order_item(order, orderitems):
    quantity = 0
    for item in orderitems:
        quantity += item.get("qty")
        FunmartOrderItem.objects.update_or_create(
            order = order,
            sku = item.get("sku"),

            defaults={

                'order_no' : order.order_no,
                'track_code' : order.track_code,

                'quantity': item.get("qty"),
                'price': item.get("price"),
                'category_cn': item.get("category_cn"),
                'category_en': item.get("category_en"),
                'name': item.get("name"),
            }
        )

    return quantity


def create_order_item(order, orderitems):
    # 先删除对应的订单明细
    FunmartOrderItem.objects.filter(order_no=order.order_no).delete()
    orderitem_list = []
    quantity = 0
    for item in orderitems:
        quantity += item.get("qty")

        orderitem = FunmartOrderItem(
            order=order,
            order_no=order.order_no,
            track_code=order.track_code,

            sku=item.get("sku"),
            quantity=item.get("qty"),
            price=item.get("price"),
            category_cn=item.get("category_cn"),
            category_en=item.get("category_en"),
            name=item.get("name"),

        )

        orderitem_list.append(orderitem)

    print(orderitem_list)
    FunmartOrderItem.objects.bulk_create(orderitem_list)

    return quantity


@shared_task
def get_funmart_sku(sku):
    print("get sku info", sku)
    url = "http://47.96.143.109:9527/api/getInfoBySku"
    param = dict()
    param["sku"] = sku
    r = requests.post(url, data=json.dumps(param))

    if r.status_code == 200:
        return_data = json.loads(r.text)
        if return_data.get("code") == '00001':
            data = return_data.get("data")


            funmartsku, created = FunmartSKU.objects.update_or_create(
                SKU=sku,
                defaults={
                    'SPU': data.get("spu"),
                    'name': data.get("en_name"),
                    'cn_name': data.get("cn_name"),
                    'skuattr': json.dumps(data.get("skuattr")),
                    'images': json.dumps(data.get("images")),
                    'sale_price': data.get("price"),
                    'pack_height': data.get("pack_height"),
                    'pack_length': data.get("pack_length"),
                    'pack_weight': data.get("price"),
                    'pack_width': data.get("pack_width"),
                    'download_error': "",

                    'downloaded': True
                }
            )
            return funmartsku

        else:
            funmartsku, created = FunmartSKU.objects.update_or_create(
                SKU=sku,
                defaults={

                    'download_error': return_data.get("message")
                }
            )

            print (return_data.get("message"))

    return None


@shared_task
def get_funmart_spu(spu):
    print("get spu info", spu)

    url = "http://47.96.143.109:9527/api/getInfoBySku"
    param = dict()
    param["sku"] = spu
    r = requests.post(url, data=json.dumps(param))
    if r.status_code == 200:
        return_data = json.loads(r.text)
        if return_data.get("code") == '00001':
            data = return_data.get("data")

            funmartspu, created = FunmartSPU.objects.update_or_create(
                SPU=data.get("spu"),
                defaults={
                    'cate_1': data.get("top_category"),
                    'cate_2': data.get("second_category"),
                    'cate_3': data.get("third_category"),
                    'en_name': data.get("en_name"),
                    'skuattr': json.dumps(data.get("skuattr")),
                    'description': data.get("description"),
                    'images': json.dumps(data.get("images")),
                    'link': data.get("online_url"),
                    'sale_price': data.get("price"),
                    "skuList": json.dumps(data.get("skuList")),
                    'downloaded': True
                }
            )

            return funmartspu
    else:
        print (return_data.get("message"))

    return None


@shared_task
def get_funmart_barcode(barcode):
    print("get barcode info", barcode)
    url = "http://47.96.143.109:9527/api/getInfoBySku"
    param = dict()
    param["sku"] = barcode
    r = requests.post(url, data=json.dumps(param))

    if r.status_code == 200:
        return_data = json.loads(r.text)
        if return_data.get("code") == '00001':
            data = return_data.get("data")

            sku = data.get("sku")


            funmart_skus = FunmartSKU.objects.filter(SKU =sku)
            if funmart_skus:
                funmart_sku = funmart_skus[0]
            else:
                funmart_sku, created = FunmartSKU.objects.update_or_create(
                    SKU=sku,
                    defaults={
                        'SPU': data.get("spu"),
                        'name': data.get("en_name"),
                        'skuattr': json.dumps(data.get("skuattr")),
                        'images': json.dumps(data.get("images")),
                        'sale_price': data.get("price"),
                        'downloaded': True
                    }
                )

            funmartbarcode, created = FunmartBarcode.objects.update_or_create(
                barcode=barcode,
                defaults={
                    'funmart_sku': funmart_sku,
                    'SKU': data.get("sku"),


                }
            )
            return funmartbarcode

        else:
            funmartbarcode, created = FunmartBarcode.objects.update_or_create(
                barcode=barcode,
                defaults={

                    'download_error': return_data.get("message")
                }
            )

            print (return_data.get("message"))

    return None

# 根据订单汇总，给spu打标
# 订单数>30,hot
# 5<订单数<30,normal
# 订单数<5， drug
def lable_spus():
    mysql = "update funmart_funmartorderitem i , funmart_funmartsku k set i.funmart_sku_id = k.id where i.sku=k.SKU"
    my_custom_sql(mysql)

    spus_count = FunmartOrderItem.objects.filter(~Q(funmart_sku__SPU="")).values("funmart_sku__SPU").annotate(
        order_count=Count("order", distinct=True))

    hot_spus = spus_count.filter(order_count__gte=30).values_list("funmart_sku__SPU", flat=True)
    FunmartSPU.objects.filter(SPU__in=list(hot_spus)).update(sale_type="hot")

    normal_spus = spus_count.filter(order_count__lt=30, order_count__gte=5).values_list("funmart_sku__SPU", flat=True)
    FunmartSPU.objects.filter(SPU__in=list(normal_spus)).update(sale_type="normal")

    drug_spus = spus_count.filter(order_count__lt=5).values_list("funmart_sku__SPU", flat=True)
    FunmartSPU.objects.filter(SPU__in=list(drug_spus)).update(sale_type="drug")

'''
def batch_sku():
    track_code_list = list(
        ScanOrder.objects.filter(downloaded=True, shelfed=False).values_list("track_code", flat=True)
    )
    orderitems = FunmartOrderItem.objects.filter(track_code__in=track_code_list)
    skus_list = list(
        orderitems.values_list("sku", flat=True)
    )

    sku_counts = orderitems.values("sku").annotate(order_count=Count("track_code", distinct=True),
                                                   quantity=Sum("quantity"))
    skus = FunmartSKU.objects.filter(SKU__in=skus_list).values("SKU", "funmart_spu__sale_type", "uploaded", "skuattr",
                                                               "funmart_spu__en_name", "images")

    BatchSKU.objects.all().delete()
    batch_sku_list = []
    for sku in skus_list:
        print("sku is ", sku)
        sku_count = sku_counts.get(sku=sku)
        funmart_sku = skus.get(SKU=sku)

        order_count = sku_count.get("order_count")
        quantity = sku_count.get("quantity")
        sale_type = funmart_sku.get("funmart_spu__sale_type")
        skuattr = funmart_sku.get("skuattr")

        if sale_type == "hot":
            action = "Put Away"

        elif sale_type == "normal":

            if order_count >= 3:
                action = "Put Away"
            else:
                action = "Normal_Case"
        else:
            if skuattr.find("One Size") > -1 or skuattr.find("Free Size") > -1:
                action = "Dead_No_Size"
            else:
                action = "Dead_Size"

        batch_sku = BatchSKU(
            SKU=sku,
            sale_type=sale_type,
            order_count=order_count,
            quantity=quantity,
            uploaded=funmart_sku.get("uploaded"),
            skuattr=skuattr,
            images=funmart_sku.get("images"),
            en_name=funmart_sku.get("funmart_spu__en_name"),

            action=action,

        )
        batch_sku_list.append(batch_sku)

    BatchSKU.objects.bulk_create(batch_sku_list)
'''

#分析批次的上架策略
def batch_sku(batch_no):


    orderitems = FunmartOrderItem.objects.filter(order__batch_no =batch_no)


    sku_counts = orderitems.values("sku").annotate(order_count=Count("track_code", distinct=True),
                                                   quantity=Sum("quantity"))

    BatchSKU.objects.filter(batch_no=batch_no).delete()
    batch_sku_list = []
    for sku_count in sku_counts:
        print("sku is ", sku_count)

        SKU = sku_count.get("sku")

        order_count = sku_count.get("order_count")
        quantity = sku_count.get("quantity")


        batch_sku = BatchSKU(
            batch_no=batch_no,
            SKU=SKU,
            order_count=order_count,
            quantity=quantity,
        )
        batch_sku_list.append(batch_sku)

    BatchSKU.objects.bulk_create(batch_sku_list)


    mysql = "update funmart_batchsku b ,funmart_funmartsku s set b.SKU = s.SKU , b.SPU = s.SPU,b.uploaded = s.uploaded,b.skuattr = s.skuattr, b.images = s.images where b.SKU = s.SKU"
    my_custom_sql(mysql)
    mysql = "update funmart_batchsku b ,funmart_funmartspu p set b.sale_type = p.sale_type  where b.SPU = p.SPU"
    my_custom_sql(mysql)

    BatchSKU.objects.filter(sale_type = "hot").update(action = "Put Away")
    BatchSKU.objects.filter(order_count__gte=3).update(action="Put Away")

    BatchSKU.objects.filter(sale_type="normal", order_count__lt=3).update(action="Normal_Case")
    BatchSKU.objects.filter(Q(skuattr__icontains="One Size")|Q(skuattr__icontains="Free Size"), sale_type="drug").update(action="Dead_No_Size")
    BatchSKU.objects.filter(~Q(skuattr__icontains="One Size") ,~Q(skuattr__icontains="Free Size"),
                            sale_type="drug").update(action="Dead_Size")

def download_spus_images():
    spu_pks = FunmartSPU.objects.filter(image_downloaded=False).values_list("pk",flat=True)
    for spu_pk in spu_pks:
        #download_spu_images(spu_pk)
        download_spu_images.apply_async((spu_pk, ), queue="funmart_image")

@shared_task
def download_spu_images(spu_pk):
    spu = FunmartSPU.objects.get(pk=spu_pk)

    if not spu.images:
        print ("no images")
        spu.download_error = "no images"
        spu.save()


        return False

    images = json.loads(spu.images)

    try:
        yallavip_images = json.loads(spu.yallavip_images)
    except Exception as e:
        spu.download_error = e
        spu.save()


    i = 0
    for remote_image in images:
        filename = os.path.join(settings.PRODUCT_ROOT, yallavip_images[i])

        # 将文件路径分割出来
        file_dir = os.path.split(filename)[0]
        # 判断文件路径是否存在，如果不存在，则创建，此处是创建多级目录
        if not os.path.isdir(file_dir):
            os.makedirs(file_dir)
        # 然后再判断文件是否存在，如果不存在，则从远程获取并保存
        if not os.path.exists(filename):
            image = get_remote_image(remote_image)
            if not image:
                print ("cannot get remote images", remote_image)
                obj, created = FunmartImage.objects.update_or_create(SPU=spu.SPU,
                                                                     image=remote_image,
                                                                    defaults = {'downloaded': False,
                                                                                'download_error': "cannot get remote images",
                                                                                }
                )
                return False

            if image.mode != "RGB" :
                image = image.convert('RGB')
            try:
                image.save(filename, 'JPEG', quality=95)
            except Exception as e:
                obj, created = FunmartImage.objects.update_or_create(SPU=spu.SPU,
                                                                     image=remote_image,
                                                                     defaults={'downloaded': False,
                                                                               'download_error': e,
                                                                               }
                                                                     )


        i += 1

    spu.image_downloaded=True
    spu.save()

#把spu插入到系统spu
def deal_funmart_spus():

    spus_to_add = FunmartSPU.objects.all() \
        .exclude(SPU__in=list(Lightin_SPU.objects.filter(vendor="funmart").values_list('SPU', flat=True))) \

    print("有%s个spu需要新增" % spus_to_add.count())

    spu_list = []
    for spu_to_add in spus_to_add:
        spu = Lightin_SPU(
            SPU=spu_to_add.SPU,
            vendor = 'funmart',
            en_name = spu_to_add.en_name,


            cate_1 = spu_to_add.cate_1,
            cate_2 = spu_to_add.cate_2,
            cate_3 = spu_to_add.cate_3,

            vendor_sale_price = spu_to_add.sale_price,
            vendor_supply_price = spu_to_add.sale_price * 0.1,
            link = spu_to_add.link,

            title = spu_to_add.en_name,
            images = spu_to_add.images,

        )

        spu_list.append(spu)

    print(spu_list)
    Lightin_SPU.objects.bulk_create(spu_list)
    
#把sku插入到系统sku
def deal_funmart_skus():

    skus_to_add = FunmartSKU.objects.all() \
        .exclude(SKU__in=list(Lightin_SKU.objects.filter(funmart_spu__vendor="funmart").values_list('SKU', flat=True))) \

    print("有%s个sku需要新增" % skus_to_add.count())

    sku_list = []
    for sku_to_add in skus_to_add:
        sku = Lightin_SKU(
            SPU=sku_to_add.SPU,
            SKU=sku_to_add.SKU,
            vendor_sale_price=sku_to_add.sale_price,
            vendor_supply_price=sku_to_add.sale_price * 0.1,

            skuattr = 'funmart',
            size = sku_to_add.en_name,


            cate_1 = sku_to_add.cate_1,
            cate_2 = sku_to_add.cate_2,
            cate_3 = sku_to_add.cate_3,


            link = sku_to_add.link,

            title = sku_to_add.en_name,
            images = sku_to_add.images,

        )

        sku_list.append(sku)

    print(sku_list)
    Lightin_SKU.objects.bulk_create(sku_list)