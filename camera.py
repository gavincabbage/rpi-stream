# This code adapted from an article written by Miguel Grinberg that can be
# found here: http://blog.miguelgrinberg.com/post/video-streaming-with-flask
# Used under the MIT license:

###
# The MIT License (MIT)

# Copyright (c) 2014 Miguel Grinberg

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
###

import time
import io
import threading
import picamera

import datetime
import cv2
import imutils
import time
from picamera.array import PiRGBArray
from picamera import PiCamera

from feed import app


def generate_feed(camera):
    while True:
        frame = camera.get_frame()
        yield (b'--frame\r\n'
               b'Content-Type: image/png\r\n\r\n' + frame + b'\r\n')


class Camera(object):
    thread = None  # background thread that reads frames from camera
    frame = None  # current frame is stored here by background thread
    last_access = 0  # time of last client access to the camera
    last_pic = 0

    def initialize(self):
        if Camera.thread is None:
            # start background frame thread
            Camera.thread = threading.Thread(target=self._thread)
            Camera.thread.start()

            # wait until frames start to be available
            while self.frame is None:
                time.sleep(0)

    def get_frame(self):
        Camera.last_access = time.time()
        self.initialize()
        return self.frame

    @classmethod
    def _thread(cls):
        with PiCamera() as camera:

            camera.resolution = (320, 240)
            camera.hflip = True
            camera.vflip = True
            camera.start_preview()
            time.sleep(2)  # let camera warm up
            #stream = io.BytesIO()
            stream = PiRGBArray(camera, size=camera.resolution)

            ### IMAGING
            avg = None
            for f in camera.capture_continuous(stream, 'bgr', use_video_port=True):
                # store frame
                #stream.seek(0)
                #cls.frame = stream.read()

                ### MY IMAGING
                # if time.time() - cls.last_pic > 10:
                #     cls.last_pic = time.time()
                #     with open("frame"+str(cls.last_pic)+".jpeg", "wb+") as f:
                #         f.write(cls.frame)

                ### IMAGING

                #data = np.fromstring(stream.getvalue(), dtype=np.uint8)
                #image = cv2.imdecode(data, 1)

                frame = f.array
                timestamp = datetime.datetime.now()
                text = "Unoccupied"

                frame = imutils.resize(frame, width=500)
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                gray = cv2.GaussianBlur(gray, (21, 21), 0)

                if avg is None:
                    print "starting avg"
                    avg = gray.copy().astype("float")
                    stream.truncate(0)
                    continue

                cv2.accumulateWeighted(gray, avg, 0.5)
                frameDelta = cv2.absdiff(gray, cv2.convertScaleAbs(avg))

                thresh = cv2.threshold(frameDelta, 5, 255,
                    cv2.THRESH_BINARY)[1]
                thresh = cv2.dilate(thresh, None, iterations=2)
                cnts = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL,
                    cv2.CHAIN_APPROX_SIMPLE)

                for c in cnts[0]:
                    if cv2.contourArea(c) < 5000:
                        continue

                    (x, y, w, h) = cv2.boundingRect(c)
                    cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
                    text = "Occupied"

                #if text == "Unoccupied":
                #    cv2.accumulateWeighted(gray, avg, 0.5)

                ts = timestamp.strftime("%A %d %B %y %I:%M:%S%p")
                cv2.putText(frame, "Status: {}".format(text), (10, 20),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
                cv2.putText(frame, ts, (10, frame.shape[0] - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 0, 255), 1)

                #_, frame = cv2.imencode('.jpeg', frame)
                #cls.frame = frame
                #cls.last_pic = time.time()
                #cv2.imwrite("frame"+str(cls.last_pic)+".jpeg", frame)
                cls.frame = cv2.imencode(".png", frame)[1].tostring()
                ### END IMAGING

                # reset stream for next frame
                stream.seek(0)
                stream.truncate()

                # if there hasn't been any clients asking for frames in
                # the last 10 seconds stop the thread
                if time.time() - cls.last_access > app.config['TIMEOUT']:
                    break

        cls.thread = None



##### IMAGE CODE AND NOTES

# note on computing average...
#   only take frames without motion?
#   simple solution
#       take average of 5 minutes, 5 minutes ago
#       assumes any sequence of motion frames will be < 5 min
#   sligtly better solution?
#       just use frames that don't have motion
#       should still allow for light changes since they are slight
#           and don't trigger motion detection

# # http://picamera.readthedocs.org/en/latest/recipes1.html
# # capture jpeg frame into opencv object
#
# import io
# import time
# import picamera
# import cv2
# import numpy as np
#
# # Create the in-memory stream
# stream = io.BytesIO()
# with picamera.PiCamera() as camera:
#     camera.start_preview()
#     time.sleep(2)
#     camera.capture(stream, format='jpeg')
# # Construct a numpy array from the stream
# data = np.fromstring(stream.getvalue(), dtype=np.uint8)
# # "Decode" the image from the array, preserving colour
# image = cv2.imdecode(data, 1)
# # OpenCV returns an array with data in BGR order. If you want RGB instead
# # use the following...
# image = image[:, :, ::-1]
