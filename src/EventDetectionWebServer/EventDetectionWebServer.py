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
from flask.ext.cors import cross_origin
from dboperations import DBOperations as db
from dboperations import STATUS_CODES
from cvenginerequesttype import CVEngineRequestType
from computer_vision_engine.pallete.processing_options.options import HSV_Options

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

### ROUTES ###

'''
This route is used to deliver a barebones UI we use for testing
that the pipeline works. Now that integration with the Video-Tagger
team is complete, we have started to move away from this system
'''
@app.route('/')
def api_hello():
    app.logger.info("api_hello request being processed")
    return render_template('index.html', page='index')


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

        if tracking_attr.get('youtube_url') and tracking_attr.get('user_email') and tracking_attr.get('points') \
                and tracking_attr.get('time') and tracking_attr.get('cv_type') and tracking_attr.get('sampling_rate'):

            youtube_url, user_email, coordinates_roi, time_roi, cv_type, sampling_rate, start_time, \
            end_time = extract_request_data(tracking_attr)

            if cv_type == 'HSV' and tracking_attr.get('hsv_directions'):

                directions_of_interest = extract_HSV_specific_request_data(tracking_attr)
                process_cv_engine_request.delay(youtube_url, user_email, coordinates_roi, time_roi,
                                                CVEngineRequestType.MotionTracking, sampling_rate,
                                                start_time, end_time, directions_of_interest=directions_of_interest)
                return "Generating predictions for the following URL: " + youtube_url

            elif cv_type == 'SURF' and tracking_attr.get('surf_option'):
                surf_event_filter = extract_SURF_specific_request_data(tracking_attr)
                process_cv_engine_request.delay(youtube_url, user_email, coordinates_roi, time_roi,
                                                CVEngineRequestType.ObjectDetection, sampling_rate,
                                                start_time, end_time, surf_event_filter=surf_event_filter)
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
    print "Video URL:", youtube_url

    user_email = request_attr['user_email']
    print user_email

    coordinates_roi_list = [float(number) for number in request_attr.get('points').split(',')]
    it = iter(coordinates_roi_list)
    # Coordinates array([[ TL.x, TL.y], [TR.x, Tr.y], [BR.x, BR.y], [BL.x, BL.y]])
    coordinates_roi = np.array([list(elem) for elem in zip(it, it)])

    # The timestamp must be stored in milliseconds
    time_roi = float(request_attr.get('time')) * 1000.0

    # Get the type of request to be processed - either SURF or HSV
    cv_type = request_attr.get('cv_type')
    print "CV Type: ", cv_type

    sampling_rate = int(request_attr.get('sampling_rate'))
    print "Sampling rate: ", sampling_rate

    start_time = 0
    end_time = 0
    try:
        # extract start and end time of video processing
        start_time = float(request_attr.get('start_time')) * 1000.0
        end_time = float(request_attr.get('end_time')) * 1000.0
    except:
        print "Did not receive start and end time"

    return youtube_url, user_email, coordinates_roi, time_roi, cv_type, sampling_rate, start_time, end_time

def extract_HSV_specific_request_data(tracking_attr):
    # The directions are received from the client-side as a string
    # separated by spaces. The string ends with a trailing space.
    # Here I split the string on spaces, and then return an array
    # with all the directions except the last element (which is a space)
    directions_of_interest = tracking_attr['hsv_directions'].split(', ')
    print "Directions of interest: ", directions_of_interest
    return directions_of_interest

def extract_SURF_specific_request_data(tracking_attr):
    # The surf option attribute is one of two options:
    # in_scene or enter_exit_scene
    # in_scene means we want tags when the object is detected
    # enter_exit_scene means we want tags when the object enters or leaves the scene
    surf_event_filter = tracking_attr['surf_option']
    return surf_event_filter


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


def send_results_via_email(video_attachment_path, roi_image_filename, destination_email, video_id, youtube_url):
    msg = Message('Event Detection Results', sender='eventdetectionmcgill@gmail.com', recipients=[destination_email])

    # get size of the video in megabytes
    video_size_bytes = (os.path.getsize(video_attachment_path)) / (1000000.0)

    if video_size_bytes < 25:
        msg.body = "Hello! You requested predictions for: " + youtube_url + " You'll find the video and region of" \
                                                                            " interest attached.\n"
        with app.open_resource(video_attachment_path) as fp:
            msg.attach(video_attachment_path, 'video/mp4', fp.read())
    else:
        print "Video is too large. Will not email it."
        msg.body = "Hello! You requested predictions for: " + youtube_url + " You'll find the region of interest" \
                                                                            " attached. The video output it too large" \
                                                                            "too be sent over email, sorry!\n"

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


def perform_request_preprocessing(youtube_url, email, coordinates_roi, time_roi):
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

    return video_path, video_id, video_attachment_path, roi_image_filename, video_with_roi_path


def perform_request_postprocessing(video_id, youtube_url, video_attachment_path, roi_image_filename,
                                   email, video_path, video_with_roi_path):

    # Convert video so that it can be sent via email
    convert_video_to_lower_quality(video_id)

    # Send email to the user
    send_results_via_email(video_attachment_path, roi_image_filename, email, video_id, youtube_url)

    # Remove all the video files
    remove_attachment_files(video_path, roi_image_filename, video_attachment_path, video_with_roi_path)


# Compresses the timestamps to find tags
def create_tags(timestamps):
    delta = 0.25 # We compress timestamps that are less than half 1/4th of a second apart
    i = 0
    tags = []
    while i < len(timestamps) - 1:
        start_index = i
        while i < len(timestamps) - 1 and abs(timestamps[i] - timestamps[i+1]) < delta:
            i += 1

        tags.append({'starttime': timestamps[start_index], 'endtime': timestamps[i]})
        i += 1
    return tags


### CELERY TASKS ###


@celery.task
def process_cv_engine_request(youtube_url, email, coordinates_roi, time_roi, request_type, sampling_rate,
                              start_time, end_time, directions_of_interest=None, surf_event_filter=None):

    # Submit the request to the Firebase DB so that the user can track its status
    req_id = db.submit_tag_generation_request(email, youtube_url)
    timestamps = []

    try:
        video_path, video_id, video_attachment_path, roi_image_filename, video_with_roi_path = \
            perform_request_preprocessing(youtube_url, email, coordinates_roi, time_roi)

        # Begin the CV engine processing
        print "Submitting video to the CV Engine"

        print "start time ", start_time
        print "end time ", end_time

        if request_type == CVEngineRequestType.MotionTracking:
            hsvOptions = HSV_Options(directions_of_interest, start_time, end_time, sampling_rate)
            timestamps = start(video_path, coordinates_roi, time_roi, video_id, hsvOptions)
            for direction in timestamps['directions_used']:
                print "ITERATING OVER DIRECTION", direction
                tags = create_tags(timestamps[direction])
                print "CREATED TAGS"
                for tag in tags:
                    print tag
                # Store the tags generated by the platform
                db.store_generated_tags(req_id, tags, youtube_url, request_type, 'Motion Tracking - ' + direction)

        elif request_type == CVEngineRequestType.ObjectDetection:
            timestamps = subprocess.check_output(['./../computer_vision_engine/pallete/motion_tracker/object_detector',
                             str(coordinates_roi[0][0]), str(coordinates_roi[0][1]), str(coordinates_roi[2][0]),
                             str(coordinates_roi[2][1]), str(time_roi), video_id, str(start_time), str(end_time), str(sampling_rate)])
            timestamps = timestamps.split(', ')[:-1]
            timestamps = [float(timestamp) for timestamp in timestamps]
            tags = create_tags(timestamps)
            # Store the tags generated by the platform
            db.store_generated_tags(req_id, tags, youtube_url, request_type, 'Object Detected')

        # Delete video files, send email
        perform_request_postprocessing(video_id, youtube_url, video_attachment_path, roi_image_filename,
                                       email, video_path, video_with_roi_path)

        # Change request status to completed
        db.change_request_status(req_id, STATUS_CODES.completed)
    except:
        print "Error occurred while completing motion tracking request"
        # Change request status to failed
        db.change_request_status(req_id, STATUS_CODES.failed)


if __name__ == '__main__':
    port_num = os.environ.get('PORT')
    if port_num is not None:
        app.run(host='0.0.0.0', port=int(port_num))
    else:
        app.run(debug=True)
