from __future__ import unicode_literals
import youtube_dl

__author__ = 'danielmacario'

def my_hook(d):
    if d['status'] == 'finished':
        print('Done downloading.')

class VideoExtractor():

    def __init__(self, video_id):
        self.video_id = video_id

    def download_video(self, url='https://www.youtube.com/watch?v=jO5IaAKTKsQ'):

        ydl_opts = {
            'outtmpl': 'dled_video' + str(self.video_id) + '.mp4',
            'progress_hooks': [my_hook],
	    'merge_output_format': 'mp4'
	    #'verbose': True,
	    #'format': 'bestvideo+bestaudio/best'
        }

        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
