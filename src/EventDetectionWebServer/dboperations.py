from firebase import firebase
from datetime import datetime

'''
This class is the layer used to interact with the database. The functions defined here
will let you add, remove, update records on the database. Just create an instance of this
class and use it communicate with the DB. Feel free to add more operations!
'''

fireDB = firebase.FirebaseApplication('https://flickering-heat-6138.firebaseio.com', None)

class RequestStatus(object):
    def __init__(self):
        self.processing = 'processing'
        self.completed = 'completed'
        self.failed = 'failed'

STATUS_CODES = RequestStatus()

class DBOperations():

    @staticmethod
    def submit_tag_generation_request(user_email, video_url):
        if user_email is None or video_url is None:
            print "Tag generation request cannot be completed, please supply email and video url"
            return None

        request_data = {
            'user_email': user_email,
            'video_url': video_url,
            'status': STATUS_CODES.processing,
            'time': datetime.now().strftime("%c")
        }

        response_data = fireDB.post('/tag-generation-request', request_data)
        # Return the ID of the request
        return response_data['name']

    @staticmethod
    def change_request_status(req_id, status):
        if req_id is None:
            print "Cannot change status of tag, no req with the ID exists"
            return False

        request_data = {
            'status': status
        }

        fireDB.patch('/tag-generation-request/' + req_id, request_data)
        return True


