
default: todos lint test

lint: venv/bin/activate
	. venv/bin/activate && flake8

test: venv/bin/activate
	. venv/bin/activate && py.test

todos:
	@rg -n '[T]ODO' | cat

venv/bin/activate: requirements.txt
	virtualenv --no-site-packages venv
	. venv/bin/activate && pip install -r requirements.txt
