"""
Github Webhook receiver
"""

import logging
import os
import time
from github_webhook import Webhook
from flask import Flask, request
from prometheus_client import Histogram, Counter, Gauge, REGISTRY
from prometheus_client import generate_latest

APP = Flask(__name__)  # Standard Flask app
WEBHOOK = Webhook(APP)  # Defines '/postreceive' endpoint

FLASK_REQUEST_LATENCY = Histogram(
    'flask_request_latency_seconds',
    'Flask Request Latency',
    ['method', 'endpoint']
)

FLASK_REQUEST_COUNT = Counter(
    'flask_request_count',
    'Flask Request Count',
    ['method', 'endpoint', 'http_status']
)

FLASK_REQUEST_SIZE = Gauge(
    'flask_request_size_bytes',
    'Flask Response Size',
    ['method', 'endpoint', 'http_status']
)

APP.lastpush = {}
LOGFORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
logging.basicConfig(level=logging.DEBUG, format=LOGFORMAT)


@APP.route("/")
def hello():
    """
    Default root route for my testing
    """
    return "Hello<br>last push: {0}".format(APP.lastpush)


@WEBHOOK.hook()
def on_push(data):
    """
    Route that gets triggered through github
    """
    APP.lastpush = data
    logging.debug(data)


@APP.route('/metrics')
def metrics():
    """
    Route returning metrics to prometheus
    """
    return generate_latest(REGISTRY)


def before_request():
    """
    annotate the processing start time to each flask request
    """
    request.start_time = time.time()


def after_request(response):
    """
    after returning the request calculate metrics about this request
    """
    # time can go backwards...
    request_latency = max(time.time() - request.start_time, 0)
    # pylint: disable-msg=no-member
    FLASK_REQUEST_LATENCY.labels(request.method, request.path)\
                         .observe(request_latency)
    FLASK_REQUEST_SIZE.labels(request.method,
                              request.path,
                              response.status_code)\
                      .set(len(response.data))
    FLASK_REQUEST_COUNT.labels(request.method,
                               request.path,
                               response.status_code)\
                       .inc()
    return response


if __name__ == "__main__":
    APP.before_request(before_request)
    APP.after_request(after_request)
    APP.run(host='0.0.0.0', port=os.environ.get('listenport', 8080))
