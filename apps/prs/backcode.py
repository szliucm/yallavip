#先post，然后基于post发广告
#这是link page post
#会导致图片被裁剪，效果不好，所以停用

def yallavip_post_and_ads(page_no, to_create_count):
    import time

    access_token, long_token = get_token(page_no)
    print (access_token, long_token, page_no)
    if not long_token:
        return

    adaccount_no = "act_1903121643086425"
    adset_no = choose_ad_set(page_no)


    ads = YallavipAd.objects.filter(active=True, published=False,yallavip_album__page__page_no=page_no )
    i=0
    for ad in ads:
        if i>to_create_count:
            break
        else:
            i += 1

        # 创建Link Page Post with Call to Action
        post_name = page_no + '_' + ad.spus_name
        try:

            adobjects = FacebookAdsApi.init(access_token=access_token, debug=True)
            fields = [
            ]
            params = {
                'url': ad.image_marked_url,
                'published': 'false',
            }
            photo_to_be_post = Page(page_id).create_photo(
                fields=fields,
                params=params,
            )
            photo_to_be_post_id = photo_to_be_post.get_id()


            fields = [
                'object_id',
            ]
            params = {
                "call_to_action": {"type": "MESSAGE_PAGE",
                                   "value": {"app_destination": "MESSENGER"}},

                #"picture": ad.image_marked_url,
                'attached_media': [{'media_fbid': photo_to_be_post_id}],
                "link": "http://www.yallavip.com",

                "message": ad.message,
                "name": "Yallavip.com",
                "description": "Online Flash Sale Everyhour",
                "use_flexible_image_aspect_ratio": False,

            }
            feed_post = Page(page_no).create_feed(
                fields=fields,
                params=params,
            )
            print (feed_post)

            object_story_id = feed_post.get_id()

            # 在post的基础上创建广告
            adobjects = FacebookAdsApi.init(access_token=ad_tokens, debug=True)
            # 创建creative

            fields = [
            ]
            params = {
                'name': post_name,
                'object_story_id': object_story_id,

            }
            adCreativeID = AdAccount(adaccount_no).create_ad_creative(
                fields=fields,
                params=params,
            )

            print("adCreativeID is ", adCreativeID)

            creative_id = adCreativeID["id"]

            # 创建广告
            fields = [
            ]
            params = {
                'name': post_name,
                'adset_id': adset_no,
                'creative': {'creative_id': creative_id},
                'status': 'PAUSED',
            }

            fb_ad = AdAccount(adaccount_no).create_ad(
                fields=fields,
                params=params,
            )
        except Exception as e:
            print(e)
            error = e.api_error_message()
            ad.publish_error = error
            ad.save()
            break

        print("new ad is ", fb_ad)
        ad.ad_id = fb_ad.get("id")
        ad.published = True
        ad.published_time = dt.now()
        ad.save()

        time.sleep(60)