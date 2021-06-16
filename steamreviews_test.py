import steamreviews
from pprint import pprint

app_ids = [329070, 573170]
#steamreviews.download_reviews_for_app_id_batch(app_ids)
# creates a idprocessed_on...txt file and puts resulting per-app info as json files into data 

# processes ids from idlist.txt and puts resulting per-app info as json files into data 
#steamreviews.download_reviews_for_app_id_batch()


# better: read in ids from idlist.txt via python and run download_reviews_for_app_id()
with open("idlist.txt", "r") as fo:
    lines = fo.readlines() # makes list of lines
    for id in lines:
        app_id = int(id)
        review_dict, query_count = steamreviews.download_reviews_for_app_id(app_id)
        print("appid:",id)
        rev0 = list(review_dict["reviews"].keys())[0] # hack to get key for first review
        print("Review", rev0, ":")
        pprint(review_dict["reviews"][rev0])

