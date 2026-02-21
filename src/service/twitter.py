import os

import tweepy
from dotenv import load_dotenv

from src.logger.logger import get_logger

load_dotenv()
logger = get_logger(__name__)


class Twitter:
    def __init__(
        self,
        api_key=None,
        api_secret=None,
        access_token=None,
        access_secret=None,
        bearer_token=None,
    ):
        self.api_key = api_key or os.getenv("TWITTER_API_KEY")
        self.api_secret = api_secret or os.getenv("TWITTER_API_SECRET")
        self.access_token = access_token or os.getenv("TWITTER_ACCESS_TOKEN")
        self.access_secret = access_secret or os.getenv("TWITTER_ACCESS_SECRET")
        self.bearer_token = bearer_token or os.getenv("TWITTER_BEARER_TOKEN")

        self.client = None
        self.api = None

    def __enter__(self):
        logger.debug("Enter Twitter")
        auth = tweepy.OAuth1UserHandler(
            self.api_key, self.api_secret, self.access_token, self.access_secret
        )
        self.api = tweepy.API(auth)
        self.client = tweepy.Client(
            consumer_key=self.api_key,
            consumer_secret=self.api_secret,
            access_token=self.access_token,
            access_token_secret=self.access_secret,
            bearer_token=self.bearer_token,
        )
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        logger.debug("Exit Twitter")
        self.client = None
        self.api = None

    def post(self, text, image_path=None):
        logger.info(text)
        if image_path:
            logger.info(image_path)
            media = self.api.media_upload(image_path)
            return self.client.create_tweet(
                text=text, media_ids=[media.media_id], user_auth=True
            )
        else:
            return self.client.create_tweet(text=text, user_auth=True)

    def verify_credentials(self):
        if not self.client:
            return False

        try:
            me = self.client.get_me()
            if me and me.data:
                logger.info(f"Authenticated as: @{me.data.username}")
                return True
        except Exception as e:
            logger.error(f"Failed to verify credentials: {e}")
            return False

    def post_test_tweet(self):
        test_text = "Test tweet from ERCOT bot - verifying tweepy v2 setup"
        try:
            response = self.post(test_text)
            logger.info(f"Test tweet posted: {response}")
            return True
        except Exception as e:
            logger.error(f"Failed to post test tweet: {e}")
            return False
