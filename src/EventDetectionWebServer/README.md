# A Platform for Manually Guided Automated Event-Detection

Supervisor:  Jeremy Cooperstock
Undergraduate Students: Yarden Arane, Daniel Macario, Brett Leighton

## Goal of the Project

This project aims to develop a platform for generalized event detection which will fulfill two primary use cases: the non-supervised generation of labels for arbitrary events described by users, and the integration with a platform that allows users to visualize the generated events.

## Overview of the architecture

Please see the attached architecture diagram in the `doc` directory. Note the presence of two different web-servers; the one on the left is being developed by the Video-Tagger team to fulfill their use-cases. This is the server that delivers the web application to the client. Note that our server does not deliver any files to the client, it simply exposes a route through which it receives incoming predict requests.

### Structure Overview

The `EventDetectionWebServer` folder contains all the files that implement the webserver. Below we provide a brief overview of the files in this directory:

- `EventDetectionWebServer.py` implements the routes and all the logic related to passing requests to the feature extraction and label generation pipeline.
- `dboperations.py` is the layer used to communicate with the Firebase DB that the VideoTagger's platform uses to retrieve and store labels.
- `videoextractor.py` Implements a simple class with a static method to download videos form Youtube. For this to work you'll need to have the youtube-dl dependencies installed. See dependencies section.
- `cvenginerequesttype.py` Is a class which implements an Enum through the use of python's range function (enums don't exist in python 2.7). It is used to tell Celery workers what kind of processing to do for a particular request.

### Web Server Dependencies

You'll need to install the following packages in your host in order to run the web server.

- `youtube-dl` - You'll need this to download videos from youtube. See the following link for install instructions https://github.com/rg3/youtube-dl/blob/master/README.md
- `python celery` - This is the package we used to setup a simple task queue that allows concurrent processing of the requests. The following link contains install instructions http://www.celeryproject.org/install/
- `redis` - Redis is a light key-value data store that celery needs in order to store the information of incoming requests. It's really simple to use - you can download it here: http://www.celeryproject.org/install/ (we used version 3.0.6)
- `Many other python libraries` - See the requirements.txt file for a list of the python packages that you'll need to run install to run the server. Note that installing them is as simple as executing `pip install -r requirements.txt`

