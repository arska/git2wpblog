import logging
from github_webhook import Webhook
from flask import Flask

app = Flask(__name__) # Standard Flask app
webhook = Webhook(app) # Defines '/postreceive' endpoint

lastpush = {}

@app.route("/")
def hello():
    return "Hello<br>last push: {0}".format(lastpush)

@webhook.hook()
def on_push(data):
    lastpush = data

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
