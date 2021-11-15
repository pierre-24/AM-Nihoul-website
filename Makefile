install:
	pip-sync && pip3 install -e .

sync:
	pip-sync

init-back:
	export FLASK_APP=AM_Nihoul_website; flask init

front:
	npm i
	grunt

init: install init-back front

lint:
	flake8 AM_Nihoul_website --max-line-length=120 --ignore=N802

run:
	export FLASK_APP=AM_Nihoul_website; export FLASK_DEBUG=1; flask run -h 127.0.0.1 -p 5000

test:
	python -m unittest discover -s AM_Nihoul_website.tests

bot:
	export FLASK_APP=AM_Nihoul_website; flask bot