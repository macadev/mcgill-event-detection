from flask import Flask, request, json, Response, render_template
import sys
import numpy as np
import os
import subprocess
import uuid

sys.path.append('/home/ubuntu/projects/Event_Detection')
sys.path.append('/home/ubuntu/projects/Event_Detection/src')
sys.path.append('/home/ubuntu/projects/Event_Detection/src/EventDetectionWebServer')
sys.path.append('/home/ubuntu/projects/Event_Detection/src/computer_vision_engine')

from videoextractor import VideoExtractor
from computer_vision_engine.pallete.motion_tracker.HSV_tracker import start
from celery import Celery
from flask.ext.mail import Mail, Message
from flask.ext.cors import CORS, cross_origin

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

option  purpose
-X  specify HTTP request method e.g. POST
-H  specify request headers e.g. "Content-type: application/json"
-d  specify request data e.g. '{"message":"Hello Data"}'
--data-binary specify binary request data e.g. @file.bin
-i  shows the response headers
-u  specify username and password e.g. "admin:secret"
-v  enables verbose mode which outputs info such as request and response headers and errors

Useful for testing:

curl -X POST http://127.0.0.1:5000
curl -H "Content-type: application/json" -X POST http://ec2-54-200-65-191.us-west-2.compute.amazonaws.com/predict -d '{"youtube_url":"https://www.youtube.com/watch?v=uNTpPNo3LBg"}'
curl -H "Content-type: application/json" -X POST http://0.0.0.0:6060/predict -d '{"youtube_url":"https://www.youtube.com/watch?v=uNTpPNo3LBg", "user_email":"danielmacario5@gmail.com"}'
curl -H "Content-type: application/json" -X POST http://127.0.0.1:5000/predict -d '{"youtube_url":"https://www.youtube.com/watch?v=DLtvrv4isLA", "user_email":"danielmacario5@gmail.com"}'
'''

### ROUTES ###

@app.route('/')
def api_hello():
    app.logger.info("api_hello request being processed")
    return render_template('index.html', page='index')


@app.route('/submit-event', methods = ['POST']) # TODO: update the name of this route
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


'''
Client has to send a POST request with a JSON object that follows the
following structure:
{ 'youtube_url' : 'http://...' }
'''
@app.route('/predict', methods = ['POST']) # TODO refactor the name of this route
@cross_origin() # Allows servers under different domains to access this endpoint
def process_predict():
    app.logger.info("predict request being processed")
    if request.headers['Content-Type'] == 'application/json':
        tracking_attr = request.get_json()

        if tracking_attr .get('youtube_url') and tracking_attr .get('user_email') and tracking_attr .get('points') and tracking_attr .get('time'):
            youtube_url, user_email, coordinates_roi, time_roi = extract_request_data(tracking_attr )
            process_motion_tracking_request.delay(youtube_url, user_email, coordinates_roi, time_roi)
            return "Generating predictions for the following URL: " + youtube_url

    data = {
        'error_message' : 'The submitted data is not JSON, or the request is incomplete.'
    }
    js = json.dumps(data)

    resp = Response(js, status=400, mimetype='application/json')
    app.logger.info("predict request failed")
    return resp


@app.route('/submit-detection-request', methods = ['POST'])
def process_object_detection():
    app.logger.info("Object detection request being processed")
    if request.headers['Content-Type'] == 'application/json':
        detection_attr = request.get_json()

        if detection_attr.get('youtube_url') and detection_attr.get('user_email') and detection_attr.get('points') and detection_attr.get('time'):
            youtube_url, user_email, coordinates_roi, time_roi = extract_request_data(detection_attr)
	    process_object_detection_request.delay(youtube_url, user_email, coordinates_roi, time_roi)
            return "Generating predictions for the following URL: " + youtube_url

    data = {
        'error_message' : 'The submitted data is not JSON, or the request is incomplete.'
    }
    js = json.dumps(data)

    resp = Response(js, status=400, mimetype='application/json')
    app.logger.info("predict request failed")
    return resp


def extract_request_data(request_attr):
    youtube_url = request_attr['youtube_url']
    print youtube_url
    user_email = request_attr['user_email']
    print user_email
    coordinates_roi_list = [float(number) for number in request_attr.get('points').split(',')]
    it = iter(coordinates_roi_list)
    # Coordinates array([[ TL.x, TL.y], [TR.x, Tr.y], [BR.x, BR.y], [BL.x, BL.y]])
    coordinates_roi = np.array([list(elem) for elem in zip(it, it)])
    # The timestamp must be stored in milliseconds
    time_roi = float(request_attr.get('time')) * 1000.0
    return youtube_url, user_email, coordinates_roi, time_roi


@app.errorhandler(404)
def not_found(error=None):
    message = {
        'status': 404,
        'message': 'Not Found: ' + request.url,
    }
    resp = json.dumps(message)
    return resp


### FUNCTIONS CELERY TASKS RELY ON ###

def convert_video_to_lower_quality(video_id, quality='640x360'):
    # Convert the resulting AVI video to a lower quality MP4
    # Chrome supports attachment up to 25 MB.
    print "Converting video to a lower quality MP4"
    subprocess.call(['avconv', '-i', 'output' + video_id + '.avi','-c:v', 'libx264', '-s', quality, '-c:a', 'copy', 'output' + video_id +'.mp4'])

def send_results_via_email(video_attachment_path, roi_image_filename, destination_email, video_id, text):
    msg = Message('Hey there!', sender='eventdetectionmcgill@gmail.com', recipients=[destination_email])
    msg.body = text

    with app.open_resource(video_attachment_path) as fp:
        msg.attach(video_attachment_path, 'video/mp4', fp.read())

    with app.open_resource(roi_image_filename) as fp:
        msg.attach(roi_image_filename, 'image/png', fp.read())

    with app.app_context():
        mail.send(msg)

def remove_attachment_files(video_path, roi_image_filename, video_attachment_path, video_with_roi_path):
    # Remove all the video files
    os.remove(video_path)
    os.remove(roi_image_filename)
    os.remove(video_attachment_path)
    os.remove(video_with_roi_path)

def log_request_information(coordinates_roi, time_roi, email):
    print "Processing motion tracking request"
    print "ROI Coordinates"
    print coordinates_roi
    print "Time = " + str(time_roi)
    print "Destination Email = " + email


### CELERY TASKS ###


@celery.task
def process_motion_tracking_request(youtube_url, email, coordinates_roi, time_roi):
    video_id = str(uuid.uuid4())
    video_with_roi_path = 'output' + video_id + '.avi'
    video_attachment_path = 'output' + video_id + '.mp4'
    roi_image_filename = 'roi_image' + video_id + '.png'

    log_request_information(coordinates_roi, time_roi, email)

    video_extractor = VideoExtractor(video_id)

    # The name of the downloaded video will be dled_video + video_id
    # This variable is used for uniqueness, it will allow multiple requests
    # to be processed in parallel
    video_extractor.download_video(youtube_url)
    video_path = 'dled_video' + video_id + '.mp4'

    # Begin the CV engine processing
    print "Submitting video to the CV Engine"
    timestamps = start(video_path, coordinates_roi, time_roi, video_id)

    # Convert video so that it can be sent via email
    convert_video_to_lower_quality(video_id)

    # Send email to the user
    timestamps_email = ', '.join(map(str, timestamps))
    text = "Hello! You requested predictions for: " + youtube_url + " These are the timestamps obtained by the CV engine!\n" + timestamps_email
    send_results_via_email(video_attachment_path, roi_image_filename, email, video_id, text)

    # Remove all the video files
    remove_attachment_files(video_path, roi_image_filename, video_attachment_path, video_with_roi_path)

@celery.task
def process_object_detection_request(youtube_url, email, coordinates_roi, time_roi):
    video_id = str(uuid.uuid4())
    video_with_roi_path = 'output' + video_id + '.avi'
    video_attachment_path = 'output' + video_id + '.mp4'
    roi_image_filename = 'roi_image' + video_id + '.png'

    log_request_information(coordinates_roi, time_roi, email)

    video_extractor = VideoExtractor(video_id)

    # The name of the downloaded video will be dled_video + video_id
    # This variable is used for uniqueness, it will allow multiple requests
    # to be processed in parallel
    video_extractor.download_video(youtube_url)
    video_path = 'dled_video' + video_id + '.mp4'

    # Begin the CV engine processing
    print "Submitting video to the CV Engine"
    subprocess.call(['./../computer_vision_engine/pallete/motion_tracker/object_detector', str(coordinates_roi[0][0]), str(coordinates_roi[0][1]), str(coordinates_roi[2][0]), str(coordinates_roi[2][1]), str(time_roi), video_id])

    # Convert video so that it can be sent via email
    convert_video_to_lower_quality(video_id)

    # Send email to the user
    text = "Hello! You requested predictions for: " + youtube_url + " These are the timestamps obtained by the CV engine!\n"
    send_results_via_email(video_attachment_path, roi_image_filename, email, video_id, text)

    # Remove all the video files
    remove_attachment_files(video_path, roi_image_filename, video_attachment_path, video_with_roi_path)


if __name__ == '__main__':
    port_num = os.environ.get('PORT')
    if port_num is not None:
        app.run(host='0.0.0.0', port=int(port_num))
    else:
        app.run(debug=True)
