"""
Retrieve tweets, embeddings, and persist in the database.
"""

import basilica
import tweepy
from decouple import config
from .models import DB, Tweet, User

# https://greatlist.com/happiness/must-follow-twitter-accounts
TWITTER_USERS = ['calebhicks', 'elonmusk', 'rrherr', 'SteveMartinToGo',
                 'nasa', 'sadserver', 'jkhowland', 'austen',
                 'common_squirrel', 'KenJennings', 'conanobrien',
                 'big_ben_clock', 'IAM_SHAKESPEARE']

TWITTER_AUTH = tweepy.OAuthHandler(config('TWITTER_CONSUMER_KEY'),
                                   config('TWITTER_CONSUMER_SECRET'))
TWITTER_AUTH.set_access_token(config('TWITTER_ACCESS_TOKEN'),
                              config('TWITTER_ACCESS_TOKEN_SECRET'))
TWITTER = tweepy.API(TWITTER_AUTH)

BASILICA = basilica.Connection(config('BASILICA_KEY'))


def add_or_update_user(username):
    """Add or update a user and their Tweets, error if not a Twitter user."""
    try:
        twitter_user = TWITTER.get_user(username)
        db_user = (User.query.get(twitter_user.id) or
                   User(id=twitter_user.id, name=username))
        DB.session.add(db_user)
        # We want as many recent non-retweet/reply statuses as we can get
        # 200 is a Twitter API limit, we'll usually see less due to exclusions
        tweets = twitter_user.timeline(
            count=250, exclude_replies=True, include_rts=False,
            tweet_mode='extended', since_id=db_user.newest_tweet_id)
        if tweets:
            db_user.newest_tweet_id = tweets[0].id
        for tweet in tweets:
            # Calculate embedding on the full tweet, but truncate for storing
            embedding = BASILICA.embed_sentence(tweet.full_text,
                                                model='twitter')
            db_tweet = Tweet(id=tweet.id, text=tweet.full_text[:500],
                             embedding=embedding)
            db_user.tweets.append(db_tweet)
            DB.session.add(db_tweet)
    except Exception as e:
        print('Error processing {}: {}'.format(username, e))
        raise e
    else:
        DB.session.commit()


def add_users(users=TWITTER_USERS):
    """
    Add/update a list of users (strings of user names).
    May take awhile, so run "offline" (flask shell).
    """
    for user in users:
        add_or_update_user(user)


def update_all_users():
    """Update all Tweets for all Users in the User table."""
    for user in User.query.all():
        add_or_update_user(user.name)
