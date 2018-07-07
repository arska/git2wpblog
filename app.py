import logging
import os
import time
from github_webhook import Webhook
from flask import Flask, Response, request, abort
from prometheus_client import Histogram, Counter, Summary, Gauge, REGISTRY, generate_latest

app = Flask(__name__) # Standard Flask app
webhook = Webhook(app) # Defines '/postreceive' endpoint
FLASK_REQUEST_LATENCY = Histogram('flask_request_latency_seconds', 'Flask Request Latency', ['method', 'endpoint'])
FLASK_REQUEST_COUNT = Counter('flask_request_count', 'Flask Request Count', ['method', 'endpoint', 'http_status'])
FLASK_REQUEST_SIZE = Gauge('flask_request_size_bytes', 'Flask Response Size', ['method', 'endpoint', 'http_status'])

lastpush = {}

@app.route("/")
def hello():
    return "Hello<br>last push: {0}".format(lastpush)

@webhook.hook()
def on_push(data):
    lastpush = data

@app.route('/metrics')
def metrics():
    return generate_latest(REGISTRY)

def before_request():
    request.start_time = time.time()

def after_request(response):
    request_latency = max(time.time() - request.start_time, 0) # time can go backwards...
    FLASK_REQUEST_LATENCY.labels(request.method, request.path).observe(request_latency)
    FLASK_REQUEST_SIZE.labels(request.method, request.path, response.status_code).set(len(response.data))
    FLASK_REQUEST_COUNT.labels(request.method, request.path, response.status_code).inc()
    return response

if __name__ == "__main__":
    app.before_request(before_request)
    app.after_request(after_request)
    app.run(host='0.0.0.0',port=os.environ.get('listenport', 8080))
