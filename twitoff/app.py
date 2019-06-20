"""
Main application and routing for TwitOff
"""
import os
from decouple import config
from flask import Flask, render_template, request
from .models import DB, User
from .twitter import add_or_update_user, add_users
from .predict import predict_user


def create_app():
    """Create and configure and instance of the
     Flask Application"""

    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['ENV'] = config('ENV')

    DB .init_app(app)

    @app.route('/')
    def root():
        users = User.query.all()
        return render_template('base.html', title='Home', users=users)

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
            tweets = []
        return render_template('user.html', title=name,
                               tweets=tweets, message=message)

    @app.route('/predict', methods=['POST'])
    def predict(message=''):
        user1_name, user2_name = sorted([request.values['user1'],
                                         request.values['user2']])
        if user1_name == user2_name:
            message = 'Cannot compare since user is the same for both fields!'
        else:
            tweet_text = request.values['tweet_text']
            prediction = predict_user(user1_name, user2_name, tweet_text)
            message = '"{}" is more likely to be said by {} than {}.'.format(
                tweet_text, user1_name if prediction else user2_name,
                user2_name if prediction else user1_name)

        return render_template('prediction.html', title='Prediction', message=message)

            # tweets = User.query.filter(User.name == name).one().tweets

    @app.route("/reset")
    def reset():
        DB.drop_all()
        DB.create_all()
        add_users()
        return render_template('base.html', title='Reset database!')

    return app
