from flask import Flask


def create_app():
    """Create and configure and instance of the
     Flask Application"""

    app = Flask(__name__)

    @app.route('/')
    def root():
        return "Hello TwitOff!"

    return app

