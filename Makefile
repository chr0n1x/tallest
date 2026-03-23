default: dev


dev:
	docker compose run --rm -ti --entrypoint bash tallest


venv:
	@python3 -m venv .venv
	@.venv/bin/pip install -r requirements.txt


dev-deps:
	.venv/bin/pip install -r requirements.txt
	.venv/bin/pip install -r dev-requirements.txt


ci-lint: lint-flake8
ci-lint: lint-pylint


lint: lint-autoflake
lint: lint-flake8
lint: lint-pep8
lint: lint-pylint


lint-pep8:
	.venv/bin/python -m autopep8 --in-place $(shell find . -type f -name '*.py' ! -path './.venv/*')

lint-pylint:
	.venv/bin/python -m pylint $(shell find . -type f -name '*.py' ! -path './.venv/*')

lint-flake8:
	.venv/bin/python -m pyflakes $(shell find . -type f -name '*.py' ! -path './.venv/*')


lint-autoflake:
	.venv/bin/python -m autoflake --remove-all-unused-imports --remove-unused-variables $(shell find . -type f -name '*.py' ! -path './.venv/*')
