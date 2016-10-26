
default: todos lint test

run: venv/bin/activate
	. venv/bin/activate && \
	WERKZEUG_DEBUG_PIN=off \
	FLASK_DEBUG=1 \
	FLASK_APP=main.py \
	flask run

lint: venv/bin/activate
	. venv/bin/activate && flake8

test: venv/bin/activate
	. venv/bin/activate && py.test

todos:
	@rg -n '[T]ODO' | cat

venv/bin/activate: requirements.txt
	virtualenv --no-site-packages venv
	. venv/bin/activate && pip install -r requirements.txt
