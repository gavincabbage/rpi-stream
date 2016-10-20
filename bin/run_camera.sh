#!/bin/bash

sudo ~/.virtualenvs/cv/bin/gunicorn --timeout 3600 -w 1 -b 0.0.0.0:9090 --error-logfile - --access-logfile - feed:app
