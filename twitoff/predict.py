"""Prediction of user based on tweet embeddings"""

import numpy as np
from sklearn.linear_model import LogisticRegression
from .models import User, Comparison, DB
from .twitter import BASILICA


def predict_user(user1_name, user2_name, tweet_text):
    """
    Returns a prediction of which user would
    be more likely to tweet a given string
    """
    user1 = User.query.filter(User.name == user1_name).one()
    user2 = User.query.filter(User.name == user2_name).one()
    user1_embeddings = np.array([tweet.embedding for tweet in user1.tweets])
    user2_embeddings = np.array([tweet.embedding for tweet in user2.tweets])
    embeddings = np.vstack([user1_embeddings, user2_embeddings])
    labels = np.concatenate([np.ones(len(user1.tweets)),
                             np.zeros(len(user2.tweets))])
    log_reg = LogisticRegression(solver='lbfgs', max_iter=1000).fit(embeddings, labels)
    tweet_embedding = BASILICA.embed_sentence(tweet_text, model='twitter')
    prediction = log_reg.predict(np.array(tweet_embedding).reshape(1, -1))[0]
    predicted_user = user1_name if prediction == 1 else user2_name
    pred_proba = log_reg.predict_proba(
        np.array(tweet_embedding).reshape(1, -1))[0]
    user1_prob = pred_proba[0]
    user2_prob = pred_proba[1]
    db_comparison = Comparison(text=tweet_text, predicted_user=predicted_user,
                               user1_name=user1_name, user2_name=user2_name,
                               user1_prob=user1_prob, user2_prob=user2_prob)
    DB.session.add(db_comparison)
    DB.session.commit()
    return db_comparison
