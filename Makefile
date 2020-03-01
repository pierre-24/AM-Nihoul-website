install:
	python setup.py develop

init-db:
	export FLASK_APP=AM_Nihoul_website; flask init-db

init-directories:
	export FLASK_APP=AM_Nihoul_website; flask init-directories

init: install init-directories init-db

lint:
	flake8 AM_Nihoul_website --max-line-length=120 --ignore=N802

css:
	lesscpy AM_Nihoul_website/assets/style.less AM_Nihoul_website/static/style.css

run:
	export FLASK_APP=AM_Nihoul_website; export FLASK_DEBUG=1; flask run -h 127.0.0.1 -p 5000