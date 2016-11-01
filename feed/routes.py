from flask import Response, render_template

from feed import app
from camera import generate_feed, Camera

@app.route('/')
def index():
    return render_template('./index.html')

@app.route('/feed')
def feed():
    return Response(generate_feed(app.camera),
            mimetype='multipart/x-mixed-replace; boundary=frame')
