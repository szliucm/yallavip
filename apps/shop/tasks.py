# Create your tasks here
from __future__ import absolute_import, unicode_literals
from celery import shared_task


from .photo_mark import  photo_mark
from product.models import ProductCategory,ProductCategoryMypage
from fb.models import  MyPage,MyAlbum,MyPhoto
from .models import ShopifyProduct
from .shop_action import  *
@shared_task
def add(x, y):
    return x + y


@shared_task
def mul(x, y):
    return x * y


@shared_task
def xsum(numbers):
    return sum(numbers)

@shared_task
def post_to_album():
    #每个pange，每次发布一个新产品没发布过的产品到对应相册
    #选择产品ID比已有的大的产品
    #如果产品的品类不符合，就选下一条
    #如果相册不存在，就创建一个相册
    #把产品对应的图片进行打标
    #把打标后的图片发布到相册

    #选择所有可用的page
    mypages = MyPage.objects.filter(active=True)
    for mypage in mypages:
        posted = 0
        # 主页的三级品类
        categories_list = []
        print("type of ",type(mypage), mypage)
        categories = mypage.category_page.all()
        for category in categories:
            print("category", category)
            subcategories = ProductCategory.objects.filter(parent_category=category.productcategory.name)

            for subcategorie in subcategories:
                print("subcategorie", subcategorie)
                categories_list.append(subcategorie.name)

        # 主页已有的相册
        album_list = []
        album_dict = {}
        albums = MyAlbum.objects.filter(page_no=mypage.page_no)
        for album in albums:
            album_list.append(album.name)
            album_dict[album.name] = album.album_no
        print("主页已有相册", album_list)
        print("主页已有相册", album_dict)


        #找出还没发布的产品
        product = MyPhoto.objects.filter(page_no = mypage).order_by("product_no").last()
        if not product:
            product_no = 0
        else:
            product_no = product.product_no
        print("product_no", product_no)



        products = ShopifyProduct.objects.filter(product_no__gt =product_no)

        for product in products:
            # 产品的tags
            tmp_tags = product.tags.split(',')
            tags = [i.strip() for i in tmp_tags]
            print("tags is ", tags)
            print("type of product ", type(product), product)

            # 目标相册
            # 产品tag 和page的三级类目 交集就是目标相册
            target_albums = list((set(categories_list).union(set(tags))) ^ (set(categories_list) ^ set(tags)))
            print("target_album is ", target_albums)

            # 目标相册是否已经存在
            # 目标相册和已有相册交集为空，就是不存在，需要新建相册
            new_albums = list(set(target_albums) - set(album_list))
            print("album ", new_albums)


            #非空则创建新相册
            if new_albums:
                new_album_list = create_new_album(mypage.page_no, new_albums)
            else:
                new_album_list = []

            for target_album in target_albums:
                new_album_list.append(album_dict.get(target_album))

            #空则意味着品类不符合，跳过
            if not new_album_list:
                continue

            # 把产品图片发到目标相册中去

            for new_album in new_album_list:
                print("new_album is ", new_album)
                if new_album:
                    posted = posted + post_photo_to_album(mypage, new_album, product)

                else:
                    print("album not exist")

            if posted > 1:
                break

    return

