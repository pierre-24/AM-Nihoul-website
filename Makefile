app=AM_Nihoul_website

install:
	pip install -r requirements.txt

install-dev: install
	pip install -e .[dev]

sync:
	pip-sync

init-back:
	flask --app $(app) init

front:
	npm i
	npm run grunt

init: install init-back front

lint:
	flake8 AM_Nihoul_website --max-line-length=120 --ignore=N802

run:
	export FLASK_DEBUG=1; flask run --app $(app)

test:
	python -m unittest discover -s AM_Nihoul_website.tests

bot:
	flask --app $(app) bot