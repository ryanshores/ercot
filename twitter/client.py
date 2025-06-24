import tweepy

from twitter import TWITTER_API_KEY, TWITTER_API_SECRET, TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_SECRET


def post_to_twitter(text, image_path = None):
    auth = tweepy.OAuth1UserHandler(
        TWITTER_API_KEY, TWITTER_API_SECRET,
        TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_SECRET
    )
    api = tweepy.API(auth)
    if image_path:
        media = api.media_upload(image_path)
        api.update_status(status=text, media_ids=[media.media_id])
    else:
        api.update_status(status=text)