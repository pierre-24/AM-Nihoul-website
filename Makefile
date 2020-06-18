install:
	pip-sync && pip3 install -e .

init-back:
	export FLASK_APP=AM_Nihoul_website; flask init

front:
	mkdir -p AM_Nihoul_website/static
	lesscpy AM_Nihoul_website/assets/style.less AM_Nihoul_website/static/style.css
	python -mrjsmin < AM_Nihoul_website/assets/main.js > AM_Nihoul_website/static/main.bundled.js
	python -mrjsmin < AM_Nihoul_website/assets/editor.js > AM_Nihoul_website/static/editor.bundled.js
	if [ ! -L "AM_Nihoul_website/static/images" ]; then ln -s ../assets/images AM_Nihoul_website/static; fi;

init: install init-back front

lint:
	flake8 AM_Nihoul_website --max-line-length=120 --ignore=N802

run:
	export FLASK_APP=AM_Nihoul_website; export FLASK_DEBUG=1; flask run -h 127.0.0.1 -p 5000