
default: lint test todos

lint:
	flake8

test:
	py.test

todos:
	rg -n '[T]ODO' | cat
