from flask import Flask
# from run import run

application = Flask(__name__)
# run()


@application.route('/')
def main_route():
    return "Hello Pico Notifier!"
