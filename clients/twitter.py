import os
from dotenv import load_dotenv
import tweepy
from logger import get_logger

load_dotenv()
logger = get_logger(__name__)

class Twitter:
    def __init__(self, api_key=None, api_secret=None, access_token=None, access_secret=None):
        self.api_key = api_key or os.getenv('TWITTER_API_KEY')
        self.api_secret = api_secret or os.getenv('TWITTER_API_SECRET')
        self.access_token = access_token or os.getenv('TWITTER_ACCESS_TOKEN')
        self.access_secret = access_secret or os.getenv('TWITTER_ACCESS_SECRET')

        self.api = None

    def __enter__(self):
        logger.debug('Enter Twitter')
        auth = tweepy.OAuth1UserHandler(
            self.api_key, self.api_secret,
            self.access_token, self.access_secret
        )
        self.api = tweepy.API(auth)
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        logger.debug('Exit Twitter')
        self.api = None

    def post(self, text, image_path=None):
        logger.info(text)
        if image_path:
            logger.info(image_path)
            media = self.api.media_upload(image_path)
            self.api.update_status(status=text, media_ids=[media.media_id])
        else:
            self.api.update_status(status=text)