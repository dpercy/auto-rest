
default: lint test

lint:
	flake8

test:
	py.test
