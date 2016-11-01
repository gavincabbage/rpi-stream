__all__ = ['app']

from flask import Flask

app = Flask(__name__)

app.config['DEBUG'] = True
app.config['TIMEOUT'] = 18000 # 30 minutes

from feed.camera import Camera
app.camera = Camera()

import feed.routes
