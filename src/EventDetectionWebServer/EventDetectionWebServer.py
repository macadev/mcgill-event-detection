from flask import Flask, request, json, Response
from videoextractor import VideoExtractor
from ../computer_vision_engine/pallete/feature_extractor/ROI_extractor import *
from celery import Celery
from flask.ext.mail import Mail, Message
import logging
import os

# Initialize Web Server along with Celery

app = Flask(__name__)

redis_url = os.environ.get('REDIS_URL')
if redis_url is None:
    redis_url = 'redis://localhost:6379/0'

# Redis and Celery configuration
app.config['BROKER_URL'] = redis_url
app.config['CELERY_RESULT_BACKEND'] = redis_url

# Flask-Mail module configuration
app.config.update(
    MAIL_SERVER='smtp.gmail.com',
    MAIL_PORT= 465,
    MAIL_USERNAME = 'eventdetectionmcgill@gmail.com',
    MAIL_PASSWORD = 'designproject',
    MAIL_USE_TLS = False,
    MAIL_USE_SSL = True
)

#file_handler = logging.FileHandler('app.log')
#app.logger.addHandler(file_handler)
#app.logger.setLevel(logging.INFO)

# Initialize Flask-Mail
mail = Mail(app)

# Initialize Celery worker
celery = Celery(app.name, broker=redis_url)
celery.conf.update(BROKER_URL=redis_url,
                CELERY_RESULT_BACKEND=redis_url)

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
curl -H "Content-type: application/json" -X POST http://ec2-54-200-65-191.us-west-2.compute.amazonaws.com/predict -d '{"youtube_url":"https://www.youtube.com/watch?v=uNTpPNo3LBg"}'
curl -H "Content-type: application/json" -X POST http://0.0.0.0:6060/predict -d '{"youtube_url":"https://www.youtube.com/watch?v=uNTpPNo3LBg", "user_email":"danielmacario5@gmail.com"}'
'''

### ROUTES ###

@app.route('/')
def api_hello():
    app.logger.info("api_hello request being processed")
    if 'name' in request.args:
        return 'Hello ' + request.args['name']
    else:
        return "Hello Anonymous, the server is up."

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

        if predict_attr.get('youtube_url') and predict_attr.get('user_email'):
            youtube_url = predict_attr['youtube_url']
            print youtube_url
            user_email = predict_attr['user_email']
            print user_email

            # TODO: Obtain the coordinates of the mask through OpenCV
            # TODO: PLUG IN CV ENGINE CODE HERE

            ROI_extractor.main()


            # Test send mail to user
            print "sending email to user"
            send_email.delay(user_email, youtube_url, ['daniel'])
            print "Succeeded in sending email"

            # Test down load video
            #test_download_video.delay(youtube_url)
            result = add_together.delay(23, 42)
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

@celery.task
def send_email(email, youtube_url,results):
    print "In send_mail() function"
    text = "Hello! You requested predictions for: " + youtube_url + " Hey Steve! We targeted your email to test the platform. Sorry if you get a ton of them!"
    msg = Message('Hey there!', sender='eventdetectionmcgill@gmail.com', recipients=[email])
    msg.body = text
    with app.app_context():
        mail.send(msg)

if __name__ == '__main__':
    port_num = os.environ.get('PORT')
    if port_num is not None:
        app.run(host='0.0.0.0', port=int(port_num))
    else:
        app.run(debug=True)
