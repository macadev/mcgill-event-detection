from __future__ import unicode_literals
import youtube_dl

__author__ = 'danielmacario'

def my_hook(d):
    if d['status'] == 'finished':
        print('Done downloading, now converting ...')

ydl_opts = {
    # 'format': 'bestaudio/best',
    # 'postprocessors': [{
    #     'key': 'FFmpegExtractAudio',
    #     'preferredcodec': 'mp3',
    #     'preferredquality': '192',
    # }],
    'outtmpl': 'dled_video.mp4',
    'progress_hooks': [my_hook],
}

class VideoExtractor:

    def download_video(self, url='https://www.youtube.com/watch?v=jO5IaAKTKsQ'):
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])