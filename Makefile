.PHONY: run lint autopep8

run: 
	python3 ./src/app/main.py
	
lint:
	isort .
	flake8 --config setup.cfg
	black --config pyproject.toml .

autopep8:
	autopep8 --in-place --aggressive --aggressive -r .
