"""
Main application and routing for TwitOff
"""
import os
from decouple import config
from flask import Flask, render_template, request
from sqlalchemy import Column

from .models import DB, User
from .twitter import add_or_update_user, add_users, update_all_users
from .predict import predict_user


def create_app():
    """Create and configure and instance of the
     Flask Application"""

    app = Flask(__name__)
    # app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite3'
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('HEROKU_POSTGRESQL_COPPER_URL')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['ENV'] = config('ENV')

    DB.init_app(app)

    @app.route('/')
    def root():
        return render_template('base.html', title='Home', users=User.query.all())

    @app.route('/update')
    def update():
        update_all_users()
        return render_template('base.html', title='Update all users!', users=User.query.all())

    @app.route('/user', methods=['POST'])
    @app.route('/user/<name>', methods=['GET'])
    def user(name=None, message=''):
        name = name or request.values['user_name']
        try:
            if request.method == 'POST':
                add_or_update_user(name)
                message = "User {} successfully added".format(name)
            tweets = User.query.filter(User.name == name).one().tweets
        except Exception as e:
            message = "Error adding {}: {}".format(name, e)
            return message
        else:
            return render_template('user.html', title=name,
                                   tweets=tweets, message=message)

    @app.route('/predict', methods=['POST'])
    def predict(message=''):
        user1, user2 = sorted((request.values['user1'],
                               request.values['user2']))
        if user1 == user2:
            message = 'Cannot compare a user the same user in both fields!'
        else:
            comparison = predict_user(user1, user2,
                                      request.values['tweet_text'])
            user1_name = comparison.user1_name
            user2_name = comparison.user2_name
            user1_prob = comparison.user1_prob
            user2_prob = comparison.user2_prob
            prediction = comparison.predicted_user
            message = '"{}" is more likely to be said by {} than {}'.format(
                request.values['tweet_text'],
                user1_name if prediction else user2_name,
                user2_name if prediction else user1_name)
        return render_template('prediction.html', title='Prediction',
                               message=message,
                               user1_name=user1_name, user1_prob=user1_prob,
                               user2_name=user2_name, user2_prob=user2_prob
                               )

    @app.route("/reset")
    def reset():
        DB.drop_all()
        DB.create_all()
        add_users()
        return render_template('base.html', title='Reset database!')

    return app
