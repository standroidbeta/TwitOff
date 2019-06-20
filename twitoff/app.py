"""
Main application and routing for TwitOff
"""

from decouple import config
from flask import Flask, render_template, request
from .models import DB, User
from .twitter import add_or_update_user
from .predict import predict_user


def create_app():
    """Create and configure and instance of the
     Flask Application"""

    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = config('DATABASE_URL')
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
    def predict():
        user1_name, user2_name = request.values['user1']
        user2_name = request.values['user2']
        tweet_text = request.values['tweet_text']
        if user1_name == user2_name:
            return 'Error'
        else:
            prediction = predict_user(user1_name, user2_name, tweet_text)
            return user1_name if prediction else user2_name

            # tweets = User.query.filter(User.name == name).one().tweets

    return app
