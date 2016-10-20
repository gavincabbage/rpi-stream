from flask import Response

from feed import app
from camera import generate_feed, Camera

@app.route('/feed')
def feed():
    return Response(generate_feed(Camera()),
            mimetype='multipart/x-mixed-replace; boundary=frame')
