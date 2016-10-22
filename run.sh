#!/bin/bash

. venv/bin/activate
export WERKZEUG_DEBUG_PIN=off
export FLASK_DEBUG=1
export FLASK_APP=main.py
flask run
