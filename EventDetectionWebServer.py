from flask import Flask, request, json, Response
from videoextractor import VideoExtractor
from celery import Celery
import logging

# Initialize Web Server along with Celery

app = Flask(__name__)
app.config['CELERY_BROKER_URL'] = 'redis://localhost:6379/0'
app.config['CELERY_RESULT_BACKEND'] = 'redis://localhost:6379/0'

file_handler = logging.FileHandler('app.log')
app.logger.addHandler(file_handler)
app.logger.setLevel(logging.INFO)

celery = Celery(app.name, broker=app.config['CELERY_BROKER_URL'])
celery.conf.update(app.config)

'''
Note:
For this server to work properly you need three terminal windows doing the following:
    - Running Redis (~/Downloads/redis-3.0.6/src/redis-server)
    - Celery ($ celery worker -A EventDetectionWebServer.celery --loglevel=info)
    - This server! (Use PyCharm, it's really comfortable!)

'''

'''
curl reference

option	purpose
-X	specify HTTP request method e.g. POST
-H	specify request headers e.g. "Content-type: application/json"
-d	specify request data e.g. '{"message":"Hello Data"}'
--data-binary	specify binary request data e.g. @file.bin
-i	shows the response headers
-u	specify username and password e.g. "admin:secret"
-v	enables verbose mode which outputs info such as request and response headers and errors

Useful for testing:

curl -X POST http://127.0.0.1:5000
curl -H "Content-type: application/json" -X POST http://127.0.0.1:5000/predict -d '{"youtube_url":"https://www.youtube.com/watch?v=uNTpPNo3LBg"}'

'''

### ROUTES ###

@app.route('/')
def api_hello():
    app.logger.info("api_hello request being processed")
    if 'name' in request.args:
        return 'Hello ' + request.args['name']
    else:
        return "Hello Anonymous"

'''
Client has to send a POST request with a JSON object that follows the
following structure:
{ 'youtube_url' : 'http://...' }
'''
@app.route('/predict', methods = ['POST'])
def process_predict():
    app.logger.info("predict request being processed")
    if request.headers['Content-Type'] == 'application/json':
        predict_attr = request.get_json()

        if predict_attr.get('youtube_url'):
            youtube_url = predict_attr['youtube_url']
            app.logger.info("predict request succeeded")
            print youtube_url
            test_download_video.delay(youtube_url)
            #result = add_together.delay(23, 42)
            return "Generating predictions for the following URL: " + youtube_url

    data = {
        'error_message' : 'The submitted data is not JSON'
    }
    js = json.dumps(data)

    resp = Response(js, status=400, mimetype='application/json')
    app.logger.info("predict request failed")
    return resp

@app.route('/submit-event', methods = ['POST'])
def submit_labeled_event():
    app.logger.info("submit labeled event being processed")
    if request.headers['Content-Type'] == 'application/json':
        event_attr = request.get_json()

        if event_attr.get('event_name'):
            event_name = event_attr['event_name']
            print event_name
            return "Submitting labeled event with name: " + event_name

    data = {
        'error_message' : 'The submitted data is not JSON or the request was not properly formatted.'
    }
    js = json.dumps(data)

    resp = Response(js, status=400, mimetype='application/json')
    app.logger.info("predict request failed")
    return resp

@app.errorhandler(404)
def not_found(error=None):
    message = {
        'status': 404,
        'message': 'Not Found: ' + request.url,
    }
    resp = json.dumps(message)
    resp.status_code = 404
    return resp

### HELPER FUNCTIONS ###

@celery.task
def test_download_video(youtube_url):
    videoextractor = VideoExtractor()
    videoextractor.download_video(youtube_url)

@celery.task
def add_together(a, b):
    print "Running add_together"
    return a + b

if __name__ == '__main__':
    app.run()
