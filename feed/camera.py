import time
import io
import threading
import datetime
import cv2
import imutils
import time
import picamera

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
            print 'Camera.thread is None in initalize'
            Camera.thread = threading.Thread(target=self._thread)
            Camera.thread.start()
            while self.frame is None:
                time.sleep(0)

    def get_frame(self):
        Camera.last_access = time.time()
        self.initialize()
        return self.frame

    @classmethod
    def _thread(cls):
        print 'Gonna try for a new cam'
        with picamera.PiCamera() as camera:
            print "New Camera"

            camera.resolution = (320, 240)
            camera.hflip = True
            camera.vflip = True
            camera.start_preview()
            stream = picamera.array.PiRGBArray(camera, size=camera.resolution)

            avg = None
            for f in camera.capture_continuous(stream, 'bgr', use_video_port=True):

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
                im, cnts, other = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL,
                    cv2.CHAIN_APPROX_SIMPLE)

                for c in cnts:
                    if cv2.contourArea(c) < 1000:
                        continue
                    (x, y, w, h) = cv2.boundingRect(c)
                    cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
                    text = "Occupied"

                ts = timestamp.strftime("%A %d %B %y %I:%M:%S%p")
                cv2.putText(frame, "Status: {}".format(text), (10, 20),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
                cv2.putText(frame, ts, (10, frame.shape[0] - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 0, 255), 1)

                cls.frame = cv2.imencode(".png", frame)[1].tostring()

                stream.seek(0)
                stream.truncate()
                if time.time() - cls.last_access > app.config['TIMEOUT']:
                    break

        print 'Setting thread to None'
        cls.thread = None
