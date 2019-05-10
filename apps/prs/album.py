@shared_task
#根据page cate 规则，更新page的相册
#将page中失效的相册找出来并删掉
#未创建的则创建之
def sync_cate_album(page_no=None):
    from django.db import connection, transaction

    # 找出所有活跃的page
    pages = MyPage.objects.filter(active=True)
    if page_no:
        pages = pages.filter(page_no=page_no)

    for page in pages:

        print("page is ", page)
        yallvip_album = YallavipAlbum.objects.filter(page__pk=page.pk)
        #先全部设置成 active=False
        if yallvip_album:
            yallvip_album.update(active=False)

        # 一次处理一个cate
        cates  = PagePromoteCate.objects.get(mypage__pk=page.pk).cate.all().distinct()

        for cate in cates:
            cate_sizes = cate.cate_size.all().distinct()
            #有尺码和无尺码的要分开处理
            if cate_sizes:
                # 相册已经有了的，就设为active=True
                yallvip_album.filter(catesize__in=cate_sizes).update(active=True)

                #相册里没有的，要创建
                catesize_to_add = cate_sizes.exclude(id__in = yallvip_album.values("catesize__pk")).distinct()
                # 根据规则创建相册，成功后记录到数据库里

                for catesize in catesize_to_add:
                    print(catesize.cate.name+ " "+ catesize.size)
                    continue

                    new_album = create_album(page.page_no, catesize.cate.name+ " "+ catesize.size)
                    YallavipAlbum.objects.create(
                        page=page,
                        cate=cate,
                        catesize=catesize,
                        album=new_album,
                        published=True,
                        publish_error="",
                        published_time=dt.now(),
                        active=True
                    )



            else:
                # 相册已经有了，置为active，否则要创建
                cate_album = yallvip_album.filter(cate = cate)
                if cate_album:
                    cate_album.update(active=True)
                else:
                    print (cate.name)
                    new_album = create_album(page.page_no, cate.name)
                    YallavipAlbum.objects.create(
                        page=page,
                        cate=cate,
                        catesize=None,
                        album=new_album,
                        published=True,
                        publish_error="",
                        published_time=dt.now(),
                        active=True
                    )






        #print("page %s 待删除 %s  待创建 %s 已有 %s "%(page, rules_to_del,rules_to_add,rules_have))
        print("page %s 待删除 %s  待创建 %s 已有 %s " % (page, rules_to_del.count(), rules_to_add.count(), rules_have.count()))