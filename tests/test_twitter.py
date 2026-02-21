import pytest
import tweepy
import tweepy.errors
from dotenv import load_dotenv

from src.logger.logger import get_logger
from src.service.twitter import Twitter

logger = get_logger(__name__)
load_dotenv()


class TestTwitter:
    """Test suite for Twitter service integration with tweepy v2."""

    @pytest.fixture
    def twitter(self):
        """Fixture to create a Twitter client instance."""
        return Twitter()

    def test_twitter_credentials_configured(self, twitter):
        """Test that Twitter credentials are properly loaded from environment."""
        assert twitter.api_key is not None, "Twitter API key not configured"
        assert twitter.api_secret is not None, "Twitter API secret not configured"
        assert twitter.access_token is not None, "Twitter access token not configured"
        assert twitter.access_secret is not None, "Twitter access secret not configured"
        assert twitter.bearer_token is not None, "Twitter bearer token not configured"

    def test_twitter_context_manager(self, twitter):
        """Test that Twitter context manager properly initializes tweepy v2 client."""
        with Twitter() as twitter_client:
            assert twitter_client.client is not None, "Tweepy client not initialized"
            assert isinstance(twitter_client.client, tweepy.Client), (
                "Client is not a Tweepy Client instance"
            )
            assert twitter_client.api is not None, "Tweepy API (v1) not initialized"
            assert isinstance(twitter_client.api, tweepy.API), (
                "API is not a Tweepy API instance"
            )

    def test_verify_credentials(self, twitter):
        """Test that Twitter credentials are valid with Twitter API."""
        with twitter:
            assert twitter.verify_credentials(), "Failed to verify Twitter credentials"

    def test_post_text_tweet(self, twitter):
        """Test posting a text-only tweet using tweepy v2 Client.

        Note: This test will fail if your Twitter app doesn't have the required
        OAuth1 Read and Write permissions. You need to configure your Twitter app
        in the Twitter Developer Portal with appropriate permissions.
        """
        test_text = "Test tweet from ERCOT bot - checking tweepy v2 setup"

        with twitter:
            try:
                response = twitter.post(test_text)
                logger.info(f"Test tweet response: {response}")
                assert response is not None, "Failed to post test tweet"
            except tweepy.errors.Forbidden as e:
                pytest.skip(
                    f"Twitter API permissions error: {e}\n"
                    "Configure your Twitter app with OAuth1 Read and Write permissions."
                )
            except Exception as e:
                pytest.fail(f"Failed to post test tweet: {e}")

    def test_twitter_with_custom_credentials(self):
        """Test creating Twitter client with custom credentials."""
        custom_twitter = Twitter(
            api_key="test_key",
            api_secret="test_secret",
            access_token="test_token",
            access_secret="test_secret",
            bearer_token="test_bearer",
        )
        assert custom_twitter.api_key == "test_key"
        assert custom_twitter.api_secret == "test_secret"
        assert custom_twitter.access_token == "test_token"
        assert custom_twitter.access_secret == "test_secret"
        assert custom_twitter.bearer_token == "test_bearer"
