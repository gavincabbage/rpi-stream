__all__ = ['app']

from flask import Flask

app = Flask(__name__)

app.config['DEBUG'] = True
app.config['TIMEOUT'] = 18000 # 30 minutes

import feed.routes
